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


def _build_default() -> AIProvider:
    from prompt_clinica.config import settings
    from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

    provider = settings.ai_provider.lower()
    match provider:
        case "openai":
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                text_model=settings.ai_text_model,
                image_model=settings.ai_image_model,
            )
        case "minimax":
            from prompt_clinica.ai.providers.minimax_provider import MinimaxProvider

            return MinimaxProvider()
        case _:
            raise ValueError(f"Provider desconhecido: '{provider}'. Implemente em ai/providers/ e registre aqui.")


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
