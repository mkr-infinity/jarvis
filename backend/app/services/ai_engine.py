import json
import urllib.error
import urllib.request
from typing import AsyncGenerator

from backend.app.core.config import OLLAMA_URL


class AIEngine:
    def __init__(self, db):
        self.db = db

    def list_ollama_models(self) -> list[str]:
        try:
            with urllib.request.urlopen(
                f"{OLLAMA_URL}/api/tags", timeout=1.5
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
                return [item["name"] for item in data.get("models", [])]
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            return []

    async def stream_chat(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        settings = self.db.settings()
        provider = settings.get("provider", "ollama")
        if provider != "ollama":
            async for token in self._single_response_provider(
                provider, messages, settings
            ):
                yield token
            return

        models = self.list_ollama_models()
        model = settings.get("model") or (models[0] if models else "")
        if not model:
            yield "Ollama not running. Install Ollama and run 'ollama pull llama3.1', or use Settings to add an API key."
            return

        payload = json.dumps(
            {"model": model, "messages": messages, "stream": True}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                for line in response:
                    if not line:
                        continue
                    try:
                        event = json.loads(line.decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
                    token = event.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if event.get("done"):
                        break
        except (OSError, urllib.error.URLError) as error:
            yield f"Local AI error: {error}"

    async def _single_response_provider(
        self, provider: str, messages: list[dict[str, str]], settings: dict[str, str]
    ) -> AsyncGenerator[str, None]:
        key_name = {
            "openai": "openai_key",
            "anthropic": "anthropic_key",
            "gemini": "gemini_key",
            "groq": "groq_key",
        }.get(provider)

        if not key_name:
            yield f"Unknown provider: {provider}"
            return

        api_key = settings.get(key_name, "")
        if not api_key:
            yield f"No API key for {provider.upper()}. Add key in Settings."
            return

        model = settings.get("model", "").strip() or self._get_default_model(provider)

        try:
            if provider == "openai":
                yield self._openai_api(
                    "https://api.openai.com/v1/chat/completions",
                    api_key,
                    model,
                    messages,
                )
            elif provider == "groq":
                yield self._openai_api(
                    "https://api.groq.com/openai/v1/chat/completions",
                    api_key,
                    model,
                    messages,
                )
            elif provider == "anthropic":
                yield self._anthropic_api(api_key, model, messages)
            elif provider == "gemini":
                yield self._gemini_api(api_key, model, messages)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                yield f"Invalid API key. Check your {provider.upper()} key in Settings."
            elif e.code == 429:
                yield "Rate limit. Wait and try again."
            else:
                yield f"HTTP Error {e.code}: {e.reason}"
        except Exception as e:
            yield f"Error: {str(e)}"

    def _get_default_model(self, provider: str) -> str:
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307",
            "gemini": "gemini-1.5-flash",
            "groq": "llama-3.1-8b-instant",
        }
        return defaults.get(provider, "gpt-4o-mini")

    def _request_json(self, url: str, payload: dict, headers: dict) -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))

    def _openai_api(self, url: str, api_key: str, model: str, messages: list) -> str:
        data = self._request_json(
            url,
            {"model": model, "messages": messages},
            {"Authorization": f"Bearer {api_key}"},
        )
        return data["choices"][0]["message"]["content"]

    def _anthropic_api(self, api_key: str, model: str, messages: list) -> str:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        chat_msgs = [
            {
                "role": "assistant" if m["role"] == "assistant" else "user",
                "content": m["content"],
            }
            for m in messages
            if m["role"] != "system"
        ]
        data = self._request_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": model,
                "max_tokens": 2048,
                "system": "\n".join(system_parts),
                "messages": chat_msgs,
            },
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
        return "".join(p.get("text", "") for p in data.get("content", []))

    def _gemini_api(self, api_key: str, model: str, messages: list) -> str:
        contents = []
        system_text = ""
        for m in messages:
            if m["role"] == "system":
                system_text += m["content"] + "\n"
                continue
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        payload = {"contents": contents}
        if system_text.strip():
            payload["systemInstruction"] = {"parts": [{"text": system_text.strip()}]}
        data = self._request_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            payload,
            {},
        )
        return data["candidates"][0]["content"]["parts"][0]["text"]
