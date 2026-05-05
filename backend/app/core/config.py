import os
from pathlib import Path


APP_NAME = "J.A.R.V.I.S"
APP_VERSION = "v1"

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("JARVIS_DATA_DIR", BASE_DIR / "data"))
PLUGIN_DIR = Path(os.environ.get("JARVIS_PLUGIN_DIR", BASE_DIR / "plugins"))
DATABASE_PATH = DATA_DIR / "jarvis.db"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
