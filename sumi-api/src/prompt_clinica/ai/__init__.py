"""
Camada de abstração de IA.

Uso básico:

    from prompt_clinica.ai import ai
    from prompt_clinica.ai.types import TextRequest, Message, ImageRequest

    resp = ai.text(TextRequest(messages=[Message("user", "Olá!")]))
    img  = ai.image(ImageRequest(prompt="Mangá, personagem correndo"))

Texto e imagem usam a configuração ativa de cada tipo (tabelas ai_*_config,
tela "Configurações do sistema"). Ver ai/registry.py.
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


def build_local_text_provider(base_url: str, model: str) -> AIProvider:
    """Provider de TEXTO apontando para um servidor OpenAI-compat local (Ollama etc.).

    `base_url` é a raiz do servidor (ex.: http://localhost:11434); o sufixo /v1
    é acrescentado aqui.
    """
    from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

    root = base_url.rstrip("/")
    v1 = root if root.endswith("/v1") else f"{root}/v1"
    return OpenAIProvider(api_key="", base_url=v1, text_model=model)


class _ReloadableProvider:
    """Repassa texto e imagem aos providers da configuração ativa de cada tipo.

    Cada modalidade é montada no primeiro uso e guardada até `invalidate()`;
    a falta de imagem ativa não impede o texto, e vice-versa.
    """

    def __init__(self) -> None:
        self._text: AIProvider | None = None
        self._image: AIProvider | None = None

    def _text_provider(self) -> AIProvider:
        if self._text is None:
            from prompt_clinica.ai.registry import build_text_provider, get_active

            self._text = build_text_provider(get_active("text"))
        return self._text

    def _image_provider(self) -> AIProvider:
        if self._image is None:
            from prompt_clinica.ai.registry import build_image_provider, get_active

            self._image = build_image_provider(get_active("image"))
        return self._image

    @property
    def name(self) -> str:
        return f"{self._text_provider().name}+{self._image_provider().name}"

    def text(self, req: TextRequest) -> TextResponse:
        return self._text_provider().text(req)

    def image(self, req: ImageRequest) -> ImageResponse:
        return self._image_provider().image(req)

    def invalidate(self) -> None:
        self._text = None
        self._image = None


ai = _ReloadableProvider()


__all__ = [
    "AIProvider",
    "ImageRequest",
    "ImageResponse",
    "Message",
    "TextRequest",
    "TextResponse",
    "ai",
    "build_local_text_provider",
]
