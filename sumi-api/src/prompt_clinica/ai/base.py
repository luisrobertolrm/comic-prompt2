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
