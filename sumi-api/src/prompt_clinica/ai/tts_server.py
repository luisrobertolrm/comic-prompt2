"""Voz via servidor local sumi-tts (OmniVoice/Chatterbox na GPU).

Ativo quando TTS_BASE_URL está definido; senão a voz continua no MiniMax.
"""
from __future__ import annotations

import os

import httpx

from prompt_clinica.ai.minimax import MinimaxConfig, MinimaxVoiceClient


def _base_url() -> str:
    return os.getenv("TTS_BASE_URL", "").rstrip("/")


def synthesize(text: str, voice_id: str) -> bytes:
    """Texto → MP3. Levanta httpx.HTTPError, MinimaxError ou ValueError em falha."""
    base = _base_url()
    if not base:
        return MinimaxVoiceClient(MinimaxConfig()).synthesize(text, voice_id=voice_id).audio
    resp = httpx.post(f"{base}/synthesize", json={"text": text, "voice_id": voice_id}, timeout=300)
    resp.raise_for_status()
    return resp.content
