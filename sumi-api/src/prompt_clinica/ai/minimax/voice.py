"""Síntese de voz via MiniMax (t2a_v2, síncrono). Implementa TextToSpeech."""
from __future__ import annotations

from .client import MinimaxHTTPBase
from .errors import MinimaxError


class MinimaxVoiceClient(MinimaxHTTPBase):
    @property
    def model(self) -> str:
        return self.config.model

    def synthesize(self, text: str, voice_id: str = "") -> bytes:
        cfg = self.config.voice
        payload = {
            "model": self.config.model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id or cfg.voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0,
            },
            "audio_setting": {
                "sample_rate": cfg.sample_rate,
                "bitrate": cfg.bitrate,
                "format": cfg.audio_format,
                "channel": 1,
            },
        }
        body = self._post("/v1/t2a_v2", payload)

        audio_hex = (body.get("data") or {}).get("audio", "")
        if not audio_hex:
            raise MinimaxError("Resposta sem áudio em data.audio.")
        return bytes.fromhex(audio_hex)
