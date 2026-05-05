import json
from pathlib import Path
from typing import Any


class PluginManager:
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir

    def list_plugins(self) -> list[dict[str, Any]]:
        plugins = []
        for path in sorted(self.plugin_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            plugins.append({
                "id": data.get("id", path.stem),
                "name": data.get("name", path.stem),
                "enabled": bool(data.get("enabled", False)),
                "description": data.get("description", ""),
                "actions": data.get("actions", [])
            })
        return plugins
