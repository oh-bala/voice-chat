import io
import json
import logging
from typing import List, Dict, Optional

import requests

from config import Config


class ElevenLabsClient:
    """Minimal ElevenLabs API client for listing voices and generating speech.

    Docs: https://api.elevenlabs.io
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ELEVENLABS_API_KEY
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabsClient")

    def _headers(self) -> Dict[str, str]:
        return {
            "xi-api-key": self.api_key,
            "accept": "application/json",
        }

    def list_voices(self) -> List[Dict[str, str]]:
        """Return a simplified list of voices with id and name."""
        try:
            url = f"{self.BASE_URL}/voices"
            resp = requests.get(url, headers=self._headers(), timeout=20)
            resp.raise_for_status()
            data = resp.json()
            voices = data.get("voices", [])
            result = []
            for v in voices:
                result.append({
                    "id": v.get("voice_id"),
                    "name": v.get("name"),
                    "category": v.get("category"),
                    "labels": v.get("labels", {}),
                    "preview_url": v.get("preview_url"),
                })
            return result
        except Exception as e:
            logging.error(f"Error listing ElevenLabs voices: {e}")
            return []

    def text_to_speech(self, text: str, voice_id: Optional[str] = None, model_id: Optional[str] = None) -> Optional[bytes]:
        """Synthesize speech and return audio bytes (mp3)."""
        if not text or not text.strip():
            return None
        voice = voice_id or Config.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"  # default Rachel if accessible
        model = model_id or Config.ELEVENLABS_MODEL_ID
        url = f"{self.BASE_URL}/text-to-speech/{voice}"
        try:
            headers = {
                **self._headers(),
                "Content-Type": "application/json",
                "accept": "audio/mpeg",
            }
            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logging.error(f"Error generating ElevenLabs TTS: {e}")
            return None


