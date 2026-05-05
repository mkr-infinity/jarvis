from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import APP_NAME, APP_VERSION, DATABASE_PATH, PLUGIN_DIR
from backend.app.services.ai_engine import AIEngine
from backend.app.services.command_engine import CommandEngine
from backend.app.services.database import JarvisDatabase
from backend.app.services.language import detect_language, system_prompt
from backend.app.services.plugin_manager import PluginManager
from backend.app.services.speech_engine import SpeechEngine


app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = JarvisDatabase(DATABASE_PATH)
ai = AIEngine(db)
commands = CommandEngine()
plugins = PluginManager(PLUGIN_DIR)
speech = SpeechEngine()


@app.on_event("startup")
def startup() -> None:
    db.init()


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true", "app": APP_NAME, "version": APP_VERSION}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json(
        {"type": "bootstrap", "payload": with_runtime(db.export_bootstrap())}
    )
    try:
        while True:
            event = await websocket.receive_json()
            await handle_event(websocket, event)
    except WebSocketDisconnect:
        return


def with_runtime(payload: dict) -> dict:
    payload["ollamaModels"] = ai.list_ollama_models()
    payload["plugins"] = plugins.list_plugins()
    return payload


async def handle_event(websocket: WebSocket, event: dict) -> None:
    event_type = event.get("type")
    payload = event.get("payload") or {}

    if event_type == "bootstrap":
        await websocket.send_json(
            {"type": "bootstrap", "payload": with_runtime(db.export_bootstrap())}
        )
        return

    if event_type == "create_project":
        project = db.create_project(payload.get("name", "Untitled"))
        chat = db.create_chat(project["id"], "New Chat")
        await websocket.send_json(
            {"type": "project_created", "payload": {"project": project, "chat": chat}}
        )
        return

    if event_type == "rename_project":
        db.rename_project(payload["projectId"], payload.get("name", "Untitled"))
        await websocket.send_json(
            {"type": "bootstrap", "payload": with_runtime(db.export_bootstrap())}
        )
        return

    if event_type == "delete_project":
        db.delete_project(payload["projectId"])
        await websocket.send_json(
            {"type": "bootstrap", "payload": with_runtime(db.export_bootstrap())}
        )
        return

    if event_type == "create_chat":
        chat = db.create_chat(payload["projectId"], payload.get("title", "New Chat"))
        await websocket.send_json({"type": "chat_created", "payload": chat})
        return

    if event_type == "load_project":
        project_id = payload["projectId"]
        chats = db.list_chats(project_id)
        if not chats:
            chats = [db.create_chat(project_id, "New Chat")]
        await websocket.send_json(
            {
                "type": "chat_loaded",
                "payload": {
                    "projectId": project_id,
                    "chatId": chats[0]["id"],
                    "chats": chats,
                    "messages": db.list_messages(chats[0]["id"]),
                },
            }
        )
        return

    if event_type == "load_chat":
        await websocket.send_json(
            {
                "type": "chat_loaded",
                "payload": {
                    "projectId": payload["projectId"],
                    "chatId": payload["chatId"],
                    "chats": db.list_chats(payload["projectId"]),
                    "messages": db.list_messages(payload["chatId"]),
                },
            }
        )
        return

    if event_type == "settings_update":
        settings = db.update_settings(payload)
        await websocket.send_json({"type": "settings", "payload": settings})
        return

    if event_type == "execute_command":
        result = commands.execute(
            payload.get("command", {}), bool(payload.get("confirmed"))
        )
        await websocket.send_json(
            {"type": "command_result", "payload": result.__dict__}
        )
        return

    if event_type == "tts":
        result = await speech.synthesize(
            payload.get("text", ""), db.get_setting("voice") or "en-US-GuyNeural"
        )
        await websocket.send_json({"type": "tts_result", "payload": result})
        return

    if event_type == "detect_models":
        provider = payload.get("provider", "ollama")
        api_key = payload.get("api_key", "")
        result = ai.detect_models(provider, api_key)
        await websocket.send_json({"type": "models_detected", "payload": result})
        return

    if event_type == "user_message":
        await process_user_message(websocket, payload)


async def process_user_message(websocket: WebSocket, payload: dict) -> None:
    text = (payload.get("text") or "").strip()
    chat_id = payload["chatId"]
    project_id = payload["projectId"]
    if not text:
        await websocket.send_json(
            {"type": "error", "payload": {"message": "Empty message"}}
        )
        return

    # Get current settings
    settings = db.settings()
    provider = settings.get("provider", "ollama")
    print(f"=== Processing message with provider: {provider} ===")
    print(f"Settings: {settings}")

    db.add_message(chat_id, "user", text)
    if len(db.list_messages(chat_id)) <= 2:
        db.update_chat_title(chat_id, text[:60])

    direct_command = commands.parse_json_command(text)
    if direct_command:
        result = commands.execute(direct_command, bool(payload.get("confirmed")))
        db.add_message(chat_id, "assistant", result.message)
        await websocket.send_json(
            {"type": "command_result", "payload": result.__dict__}
        )
        await websocket.send_json(
            {
                "type": "message_saved",
                "payload": {
                    "chats": db.list_chats(project_id),
                    "messages": db.list_messages(chat_id),
                },
            }
        )
        return

    await websocket.send_json(
        {"type": "assistant_start", "payload": {"state": "thinking"}}
    )

    language = detect_language(text)
    history = db.list_messages(chat_id, limit=30)
    model_messages = [
        {
            "role": "system",
            "content": system_prompt(language, db.list_memories(project_id)),
        }
    ]
    for message in history:
        model_messages.append({"role": message["role"], "content": message["content"]})

    response = ""
    try:
        async for token in ai.stream_chat(model_messages):
            response += token
            await websocket.send_json(
                {"type": "assistant_token", "payload": {"token": token}}
            )
    except Exception as e:
        error_msg = f"AI Error: {str(e)}"
        print(error_msg)
        await websocket.send_json({"type": "error", "payload": {"message": error_msg}})
        response = "Sorry, I encountered an error. Please try again."
        await websocket.send_json(
            {"type": "assistant_token", "payload": {"token": response}}
        )

    if not response.strip():
        response = "I did not receive a response. Please try again."
        await websocket.send_json(
            {"type": "assistant_token", "payload": {"token": response}}
        )

    command = commands.parse_json_command(response)
    if command:
        result = commands.execute(command, False)
        await websocket.send_json(
            {"type": "command_result", "payload": result.__dict__}
        )

    db.add_message(chat_id, "assistant", response)
    await websocket.send_json(
        {
            "type": "assistant_end",
            "payload": {
                "chats": db.list_chats(project_id),
                "messages": db.list_messages(chat_id),
            },
        }
    )
