"""
Camada de abstração de IA.

Uso básico:

    from prompt_clinica.ai import ai
    from prompt_clinica.ai.types import TextRequest, Message, ImageRequest

    resp = ai.text(TextRequest(messages=[Message("user", "Olá!")]))
    img  = ai.image(ImageRequest(prompt="Mangá, personagem correndo"))

Para trocar de provider, altere AI_PROVIDER no .env e implemente
um novo provider seguindo o protocolo em base.py.
"""

from __future__ import annotations

from prompt_clinica.ai.base import AIProvider
from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    Message,
    TextRequest,
    TextResponse,
)


def _build_provider(name: str) -> AIProvider:
    from prompt_clinica.config import settings

    match name:
        case "openai":
            from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

            return OpenAIProvider(
                api_key=settings.openai_api_key,
                text_model=settings.ai_text_model,
                image_model=settings.ai_image_model,
            )
        case "minimax":
            from prompt_clinica.ai.providers.minimax_provider import MinimaxProvider

            return MinimaxProvider()
        case "comfyui":
            from prompt_clinica.ai.providers.comfyui_provider import ComfyUIProvider

            return ComfyUIProvider()
        case "seedream":
            from prompt_clinica.ai.providers.seedream_provider import SeedreamProvider

            return SeedreamProvider()
        case _:
            raise ValueError(f"Provider desconhecido: '{name}'. Implemente em ai/providers/ e registre aqui.")


class _CompositeProvider:
    """Roteia texto e imagem para providers distintos (AI_TEXT/IMAGE_PROVIDER)."""

    def __init__(self, text_provider: AIProvider, image_provider: AIProvider) -> None:
        self._text = text_provider
        self._image = image_provider

    @property
    def name(self) -> str:
        return f"{self._text.name}+{self._image.name}"

    def text(self, req: TextRequest) -> TextResponse:
        return self._text.text(req)

    def image(self, req: ImageRequest) -> ImageResponse:
        return self._image.image(req)


def _build_default() -> AIProvider:
    from prompt_clinica.config import settings

    text_name = (settings.ai_text_provider or settings.ai_provider).lower()
    image_name = (settings.ai_image_provider or settings.ai_provider).lower()
    if text_name == image_name:
        return _build_provider(text_name)
    return _CompositeProvider(_build_provider(text_name), _build_provider(image_name))


# Instância singleton — criada na primeira importação.
ai: AIProvider = _build_default()

__all__ = [
    "ai",
    "AIProvider",
    "Message",
    "TextRequest",
    "TextResponse",
    "ImageRequest",
    "ImageResponse",
]
