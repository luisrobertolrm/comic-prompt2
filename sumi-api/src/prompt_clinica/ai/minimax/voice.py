"""Síntese de voz via MiniMax (t2a_v2, síncrono). Retorna o áudio em bytes."""
from __future__ import annotations

from dataclasses import dataclass

from .client import MinimaxHTTPBase
from .errors import MinimaxError


@dataclass
class MinimaxVoiceResult:
    model: str
    audio: bytes
    audio_format: str


class MinimaxVoiceClient(MinimaxHTTPBase):
    def synthesize(
        self,
        text: str,
        *,
        model: str = "",
        voice_id: str = "",
        speed: float = 1.0,
        vol: float = 1.0,
        pitch: int = 0,
        emotion: str = "",
    ) -> MinimaxVoiceResult:
        cfg = self.config.voice
        voice_setting: dict[str, object] = {
            "voice_id": voice_id or cfg.voice_id,
            "speed": speed,
            "vol": vol,
            "pitch": pitch,
        }
        if emotion:
            voice_setting["emotion"] = emotion
        payload = {
            "model": model or cfg.model,
            "text": text,
            "stream": False,
            "voice_setting": voice_setting,
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
        return MinimaxVoiceResult(
            model=payload["model"],  # type: ignore[arg-type]
            audio=bytes.fromhex(audio_hex),
            audio_format=cfg.audio_format,
        )
