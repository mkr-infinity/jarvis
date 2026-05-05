import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class JarvisDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def init(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                """
            )
            self._conn.commit()
        self.ensure_defaults()

    def ensure_defaults(self) -> None:
        if not self.list_projects():
            project = self.create_project("General")
            self.create_chat(project["id"], "New Chat")
        defaults = {
            "provider": "ollama",
            "model": "",
            "language": "auto",
            "voice": "en-US-GuyNeural",
            "voice_mode": "manual",
            "openai_key": "",
            "anthropic_key": "",
            "gemini_key": "",
            "groq_key": "",
            "confirm_dangerous_actions": "true",
            "onboarding_completed": "false"
        }
        for key, value in defaults.items():
            if self.get_setting(key) is None:
                self.set_setting(key, value)

    def _now(self) -> int:
        return int(time.time())

    def _id(self) -> str:
        return uuid.uuid4().hex

    def list_projects(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def create_project(self, name: str) -> dict[str, Any]:
        project = {"id": self._id(), "name": name.strip() or "Untitled", "created_at": self._now(), "updated_at": self._now()}
        with self._lock:
            self._conn.execute(
                "INSERT INTO projects(id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (project["id"], project["name"], project["created_at"], project["updated_at"])
            )
            self._conn.commit()
        return project

    def rename_project(self, project_id: str, name: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
                (name.strip() or "Untitled", self._now(), project_id)
            )
            self._conn.commit()

    def delete_project(self, project_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            self._conn.commit()
        if not self.list_projects():
            project = self.create_project("General")
            self.create_chat(project["id"], "New Chat")

    def list_chats(self, project_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM chats WHERE project_id = ? ORDER BY updated_at DESC",
                (project_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def create_chat(self, project_id: str, title: str = "New Chat") -> dict[str, Any]:
        chat = {"id": self._id(), "project_id": project_id, "title": title, "created_at": self._now(), "updated_at": self._now()}
        with self._lock:
            self._conn.execute(
                "INSERT INTO chats(id, project_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (chat["id"], chat["project_id"], chat["title"], chat["created_at"], chat["updated_at"])
            )
            self._conn.commit()
        return chat

    def update_chat_title(self, chat_id: str, title: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
                (title[:80] or "New Chat", self._now(), chat_id)
            )
            self._conn.commit()

    def list_messages(self, chat_id: str, limit: int = 80) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC LIMIT ?",
                (chat_id, limit)
            ).fetchall()
        return [dict(row) for row in rows]

    def add_message(self, chat_id: str, role: str, content: str) -> dict[str, Any]:
        message = {"id": self._id(), "chat_id": chat_id, "role": role, "content": content, "created_at": self._now()}
        with self._lock:
            self._conn.execute(
                "INSERT INTO messages(id, chat_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (message["id"], message["chat_id"], message["role"], message["content"], message["created_at"])
            )
            self._conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (self._now(), chat_id))
            self._conn.commit()
        return message

    def list_memories(self, project_id: str, limit: int = 20) -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT content FROM memories WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
                (project_id, limit)
            ).fetchall()
        return [row["content"] for row in rows]

    def add_memory(self, project_id: str, content: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO memories(id, project_id, content, created_at) VALUES (?, ?, ?, ?)",
                (self._id(), project_id, content.strip(), self._now())
            )
            self._conn.commit()

    def get_setting(self, key: str) -> str | None:
        with self._lock:
            row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["value"]

    def set_setting(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value)
            )
            self._conn.commit()

    def settings(self) -> dict[str, str]:
        with self._lock:
            rows = self._conn.execute("SELECT key, value FROM settings").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def export_bootstrap(self) -> dict[str, Any]:
        projects = self.list_projects()
        current_project = projects[0]
        chats = self.list_chats(current_project["id"])
        if not chats:
            chats = [self.create_chat(current_project["id"], "New Chat")]
        return {
            "settings": self.settings(),
            "projects": projects,
            "currentProjectId": current_project["id"],
            "chats": chats,
            "currentChatId": chats[0]["id"],
            "messages": self.list_messages(chats[0]["id"]),
        }

    def update_settings(self, patch: dict[str, Any]) -> dict[str, str]:
        for key, value in patch.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.set_setting(str(key), str(value))
        return self.settings()
