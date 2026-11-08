import json
import os
from pathlib import Path

APP_DATA = Path(os.getenv("APPDATA", Path.home())) / "EmulatorHub"
APP_DATA.mkdir(parents=True, exist_ok=True)
SETTINGS_PATH = APP_DATA / "settings.json"

class Settings:
    def __init__(self):
        self.data = {}
        if SETTINGS_PATH.exists():
            try:
                self.data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            except Exception:
                self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        SETTINGS_PATH.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
