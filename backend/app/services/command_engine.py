import json
import os
import platform
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus


try:
    import psutil
except Exception:
    psutil = None


SAFE_ACTIONS = {
    "open_app",
    "close_app",
    "open_url",
    "search_youtube",
    "play_media",
    "pause_media",
    "volume_control",
    "take_screenshot",
    "keyboard_input",
    "mouse_action",
    "file_operation",
    "clipboard"
}

DANGEROUS_FILE_OPS = {"delete", "move", "overwrite"}


@dataclass
class CommandResult:
    ok: bool
    message: str
    needs_confirmation: bool = False
    command: dict[str, Any] | None = None


class CommandEngine:
    def _pyautogui(self):
        try:
            import pyautogui
            return pyautogui
        except Exception:
            return None

    def validate(self, command: dict[str, Any], confirmed: bool = False) -> CommandResult:
        action = command.get("action")
        params = command.get("params") or {}
        if action not in SAFE_ACTIONS:
            return CommandResult(False, f"Blocked unsupported action: {action}")
        if action == "file_operation":
            operation = str(params.get("operation", "")).lower()
            if operation in DANGEROUS_FILE_OPS and not confirmed:
                return CommandResult(False, "This file operation needs confirmation.", True, command)
        if action in {"keyboard_input", "mouse_action"} and not confirmed:
            return CommandResult(False, "Input automation needs confirmation.", True, command)
        return CommandResult(True, "Validated")

    def execute(self, command: dict[str, Any], confirmed: bool = False) -> CommandResult:
        validation = self.validate(command, confirmed)
        if not validation.ok:
            return validation
        action = command["action"]
        params = command.get("params") or {}
        try:
            handler = getattr(self, f"_handle_{action}")
            return handler(params)
        except Exception as error:
            return CommandResult(False, f"Command failed: {error}")

    def _handle_open_app(self, params: dict[str, Any]) -> CommandResult:
        name = str(params.get("name", "")).strip()
        if not name:
            return CommandResult(False, "App name is required.")
        system = platform.system().lower()
        if system == "windows":
            subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
        elif system == "darwin":
            subprocess.Popen(["open", "-a", name])
        else:
            executable = shutil.which(name.lower()) or shutil.which(name)
            subprocess.Popen([executable or name])
        return CommandResult(True, f"Opening {name}.")

    def _handle_close_app(self, params: dict[str, Any]) -> CommandResult:
        name = str(params.get("name", "")).lower().strip()
        if not name or psutil is None:
            return CommandResult(False, "Process control requires an app name and psutil.")
        closed = 0
        for proc in psutil.process_iter(["name"]):
            proc_name = (proc.info.get("name") or "").lower()
            if name in proc_name:
                proc.terminate()
                closed += 1
        return CommandResult(True, f"Closed {closed} process(es) matching {name}.")

    def _handle_open_url(self, params: dict[str, Any]) -> CommandResult:
        url = str(params.get("url", "")).strip()
        if not url:
            return CommandResult(False, "URL is required.")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return CommandResult(True, f"Opened {url}.")

    def _handle_search_youtube(self, params: dict[str, Any]) -> CommandResult:
        query = quote_plus(str(params.get("query", "")).strip())
        if not query:
            return CommandResult(False, "Search query is required.")
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return CommandResult(True, "Opened YouTube search.")

    def _handle_play_media(self, _params: dict[str, Any]) -> CommandResult:
        return self._press_key("playpause", "Toggled media playback.")

    def _handle_pause_media(self, _params: dict[str, Any]) -> CommandResult:
        return self._press_key("playpause", "Toggled media playback.")

    def _handle_volume_control(self, params: dict[str, Any]) -> CommandResult:
        direction = str(params.get("direction", "up")).lower()
        key = "volumeup" if direction in {"up", "increase"} else "volumedown"
        return self._press_key(key, f"Adjusted volume {direction}.")

    def _handle_take_screenshot(self, params: dict[str, Any]) -> CommandResult:
        pyautogui = self._pyautogui()
        if pyautogui is None:
            return CommandResult(False, "Screenshot requires pyautogui.")
        target = Path(params.get("path") or Path.home() / "Pictures" / "jarvis-screenshot.png")
        target.parent.mkdir(parents=True, exist_ok=True)
        image = pyautogui.screenshot()
        image.save(target)
        return CommandResult(True, f"Saved screenshot to {target}.")

    def _handle_keyboard_input(self, params: dict[str, Any]) -> CommandResult:
        pyautogui = self._pyautogui()
        if pyautogui is None:
            return CommandResult(False, "Keyboard automation requires pyautogui.")
        text = params.get("text")
        hotkey = params.get("hotkey")
        if hotkey:
            keys = [part.strip() for part in str(hotkey).split("+") if part.strip()]
            pyautogui.hotkey(*keys)
            return CommandResult(True, f"Pressed {hotkey}.")
        if text:
            pyautogui.write(str(text), interval=0.01)
            return CommandResult(True, "Typed text.")
        return CommandResult(False, "Text or hotkey is required.")

    def _handle_mouse_action(self, params: dict[str, Any]) -> CommandResult:
        pyautogui = self._pyautogui()
        if pyautogui is None:
            return CommandResult(False, "Mouse automation requires pyautogui.")
        action = str(params.get("type", "click")).lower()
        x = params.get("x")
        y = params.get("y")
        if x is not None and y is not None:
            pyautogui.moveTo(int(x), int(y), duration=0.1)
        if action == "double_click":
            pyautogui.doubleClick()
        elif action == "right_click":
            pyautogui.rightClick()
        else:
            pyautogui.click()
        return CommandResult(True, f"Mouse {action} completed.")

    def _handle_file_operation(self, params: dict[str, Any]) -> CommandResult:
        operation = str(params.get("operation", "")).lower()
        path = Path(str(params.get("path", ""))).expanduser()
        if not path:
            return CommandResult(False, "Path is required.")
        if operation == "create_folder":
            path.mkdir(parents=True, exist_ok=True)
            return CommandResult(True, f"Created folder {path}.")
        if operation == "create_file":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            return CommandResult(True, f"Created file {path}.")
        if operation == "delete":
            if path.is_dir():
                os.rmdir(path)
            else:
                path.unlink()
            return CommandResult(True, f"Deleted {path}.")
        return CommandResult(False, f"Unsupported file operation: {operation}.")

    def _handle_clipboard(self, params: dict[str, Any]) -> CommandResult:
        pyautogui = self._pyautogui()
        if pyautogui is None:
            return CommandResult(False, "Clipboard control requires pyautogui.")
        text = params.get("text")
        if text is None:
            pyautogui.hotkey("ctrl", "c")
            return CommandResult(True, "Copied selection.")
        try:
            import pyperclip
            pyperclip.copy(str(text))
        except Exception:
            return CommandResult(False, "Clipboard write requires pyperclip.")
        return CommandResult(True, "Copied text to clipboard.")

    def _press_key(self, key: str, message: str) -> CommandResult:
        pyautogui = self._pyautogui()
        if pyautogui is None:
            return CommandResult(False, "Media keys require pyautogui.")
        pyautogui.press(key)
        return CommandResult(True, message)

    def parse_json_command(self, text: str) -> dict[str, Any] | None:
        stripped = text.strip()
        if not stripped.startswith("{"):
            return None
        try:
            command = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if isinstance(command, dict) and "action" in command:
            return command
        return None
