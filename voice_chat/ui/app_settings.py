import json
import os
from typing import Optional, Dict, Any


class AppSettings:
    """Simple JSON-backed settings stored in user's home directory."""

    FILENAME = os.path.join(os.path.expanduser("~"), ".voice_chat_settings.json")

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        try:
            if os.path.exists(self.FILENAME):
                with open(self.FILENAME, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = {}
        except Exception:
            self._data = {}

    def _save(self) -> None:
        try:
            with open(self.FILENAME, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()

    # Convenience accessors
    def get_tts_provider(self) -> str:
        return str(self.get("tts_provider", "pyttsx3"))

    def set_tts_provider(self, provider: str) -> None:
        self.set("tts_provider", provider)

    def get_elevenlabs_voice_id(self) -> Optional[str]:
        return self.get("elevenlabs_voice_id")

    def set_elevenlabs_voice_id(self, voice_id: Optional[str]) -> None:
        if voice_id:
            self.set("elevenlabs_voice_id", voice_id)
        else:
            # remove key if None
            if "elevenlabs_voice_id" in self._data:
                del self._data["elevenlabs_voice_id"]
                self._save()

    # Language settings
    def get_language(self) -> str:
        return str(self.get("language", "en"))

    def set_language(self, language: str) -> None:
        self.set("language", language)


