from __future__ import annotations

from typing import Protocol, runtime_checkable

from .types import ImageRequest, ImageResponse, TextRequest, TextResponse


@runtime_checkable
class AIProvider(Protocol):
    """Contrato que todo provider deve implementar."""

    @property
    def name(self) -> str: ...

    def text(self, req: TextRequest) -> TextResponse:
        """Gera texto via chat completion."""
        ...

    def image(self, req: ImageRequest) -> ImageResponse:
        """Gera imagem e retorna a URL."""
        ...


@runtime_checkable
class SpeechToText(Protocol):
    """Transcreve áudio em texto."""

    @property
    def model(self) -> str: ...

    def transcribe(self, audio: bytes, filename: str) -> str: ...


@runtime_checkable
class TextToSpeech(Protocol):
    """Sintetiza texto em áudio (mp3). `voice_id` vazio = voz padrão do provider."""

    @property
    def model(self) -> str: ...

    def synthesize(self, text: str, voice_id: str = "") -> bytes: ...
