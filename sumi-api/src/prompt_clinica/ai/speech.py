from __future__ import annotations

from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from prompt_clinica.ai.registry import AIConfig


class OpenAISpeechToText:
    """Voz → texto via API de transcrição OpenAI-compatível (/audio/transcriptions)."""

    def __init__(self, config: AIConfig) -> None:
        self._client = OpenAI(api_key=config.api_key or "none", base_url=config.base_url)
        self._model = config.model
        self._language = config.language

    @property
    def model(self) -> str:
        return self._model

    def transcribe(self, audio: bytes, filename: str) -> str:
        result = self._client.audio.transcriptions.create(
            model=self._model,
            file=(filename, audio),
            language=self._language or None,  # type: ignore[arg-type]
        )
        return result.text.strip()
