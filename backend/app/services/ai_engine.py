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

    def detect_models(self, provider: str, api_key: str) -> dict:
        try:
            if provider == "openai":
                return self._detect_openai_models(api_key)
            elif provider == "anthropic":
                return self._detect_anthropic_models(api_key)
            elif provider == "gemini":
                return self._detect_gemini_models(api_key)
            elif provider == "groq":
                return self._detect_groq_models(api_key)
            elif provider == "ollama":
                return {"ok": True, "models": self.list_ollama_models(), "error": ""}
            else:
                return {
                    "ok": False,
                    "models": [],
                    "error": f"Unknown provider: {provider}",
                }
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            error = self._parse_api_error(provider, e.code, body)
            return {"ok": False, "models": [], "error": error}
        except Exception as e:
            return {"ok": False, "models": [], "error": str(e)}

    def _parse_api_error(self, provider: str, code: int, body: str) -> str:
        if code == 401 or code == 403:
            reasons = {
                "openai": "API key is invalid or expired. Get a new key from platform.openai.com",
                "anthropic": "API key is invalid or expired. Get a new key from console.anthropic.com",
                "gemini": "API key is invalid or expired. Get a new key from aistudio.google.com",
                "groq": "API key is invalid or expired. Get a new key from console.groq.com",
            }
            return reasons.get(provider, "API key is invalid or expired")
        if code == 429:
            return "Too many requests. Your key has hit rate limits. Wait a moment and try again"
        if code == 404:
            return "API endpoint not found. The key may be for a different service or version"
        if code >= 500:
            return f"{provider.upper()} server error ({code}). Their service may be down temporarily"
        return f"{provider.upper()} returned error {code}: {body[:200]}"

    def _detect_openai_models(self, api_key: str) -> dict:
        request = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        all_models = [m["id"] for m in data.get("data", [])]
        preferred = [
            m
            for m in all_models
            if any(x in m for x in ["gpt-4o", "gpt-4", "gpt-3.5", "o1", "o3"])
        ]
        return {
            "ok": True,
            "models": preferred[:20] if preferred else all_models[:20],
            "error": "",
        }

    def _detect_anthropic_models(self, api_key: str) -> dict:
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "models-list-2025-05-14",
            },
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        all_models = [m["id"] for m in data.get("data", [])]
        return {"ok": True, "models": all_models[:20], "error": ""}

    def _detect_gemini_models(self, api_key: str) -> dict:
        with urllib.request.urlopen(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=15,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
        all_models = []
        for m in data.get("models", []):
            name = m.get("name", "").replace("models/", "")
            if name and "generateContent" in m.get("supportedGenerationMethods", []):
                all_models.append(name)
        return {"ok": True, "models": all_models[:20], "error": ""}

    def _detect_groq_models(self, api_key: str) -> dict:
        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        all_models = [m["id"] for m in data.get("data", [])]
        return {"ok": True, "models": all_models[:20], "error": ""}

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
        last_role = None

        for m in messages:
            if m["role"] == "system":
                system_text += m["content"] + "\n"
                continue

            role = "model" if m["role"] == "assistant" else "user"

            if role == last_role:
                contents[-1]["parts"][0]["text"] += "\n" + m["content"]
                continue

            contents.append({"role": role, "parts": [{"text": m["content"]}]})
            last_role = role

        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello"}]})

        payload = {"contents": contents}
        if system_text.strip():
            payload["systemInstruction"] = {"parts": [{"text": system_text.strip()}]}

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"Gemini API {e.code}: {body}")

        candidates = data.get("candidates", [])
        if not candidates:
            raise Exception("Gemini returned no candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise Exception("Gemini returned empty response")

        return parts[0].get("text", "")
