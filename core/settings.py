import json
import os
import platform
from pathlib import Path


def get_data_dir():
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    data_dir = base / "GSBWiFi"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class Settings:
    DEFAULTS = {
        "remember_credentials": False,
        "saved_tc": "",
        "saved_password": "",
        "auto_reconnect": False,
        "reconnect_interval": 15,
        "appearance_mode": "System",
        "login_interval": 0.3,
    }

    def __init__(self):
        self._path = get_data_dir() / "settings.json"
        self._data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for key in self.DEFAULTS:
                    if key in saved:
                        self._data[key] = saved[key]
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get(self, key):
        return self._data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def clear_credentials(self):
        self._data["saved_tc"] = ""
        self._data["saved_password"] = ""
        self._data["remember_credentials"] = False
        self.save()
