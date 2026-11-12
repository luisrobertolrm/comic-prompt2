"""
Camada de abstração de IA.

Uso básico:

    from prompt_clinica.ai import ai
    from prompt_clinica.ai.types import TextRequest, Message, ImageRequest

    resp = ai.text(TextRequest(messages=[Message("user", "Olá!")]))
    img  = ai.image(ImageRequest(prompt="Mangá, personagem correndo"))

Provider e modelos vêm do .env, sobrescritos pela tabela app_settings
(tela "Configurações do sistema"). Para um provider novo, implemente o
protocolo em base.py e registre em _build_provider.
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


def _build_provider(name: str, cfg: dict[str, str]) -> AIProvider:
    from prompt_clinica.config import settings

    match name:
        case "openai":
            from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

            return OpenAIProvider(
                api_key=settings.openai_api_key,
                text_model=cfg["ai_text_model"],
                image_model=cfg["ai_image_model"],
            )
        case "minimax":
            from prompt_clinica.ai.providers.minimax_provider import MinimaxProvider

            return MinimaxProvider()
        case "comfyui":
            from prompt_clinica.ai.providers.comfyui_provider import ComfyUIProvider

            return ComfyUIProvider()
        case "seedream":
            from prompt_clinica.ai.providers.seedream_provider import SeedreamProvider

            return SeedreamProvider(model=cfg["seedream_model"])
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


def build_local_text_provider(base_url: str, model: str) -> AIProvider:
    """Provider de TEXTO apontando para um servidor OpenAI-compat local (Ollama etc.).

    `base_url` é a raiz do servidor (ex.: http://localhost:11434); o sufixo /v1
    é acrescentado aqui. Ollama ignora a api_key, mas o SDK exige uma.
    """
    from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

    root = base_url.rstrip("/")
    v1 = root if root.endswith("/v1") else f"{root}/v1"
    return OpenAIProvider(api_key="local", text_model=model, base_url=v1)


def env_ai_config() -> dict[str, str]:
    """Valores de IA vindos do .env — base sobre a qual o app_settings sobrescreve."""
    from prompt_clinica.config import settings

    return {
        "ai_text_provider": settings.ai_text_provider or settings.ai_provider,
        "ai_text_model": settings.ai_text_model,
        "ai_image_provider": settings.ai_image_provider or settings.ai_provider,
        "ai_image_model": settings.ai_image_model,
        "seedream_model": settings.seedream_model,
    }


def build_default(overrides: dict[str, str] | None = None) -> AIProvider:
    """Monta o provider a partir do .env, com `overrides` não vazios por cima."""
    cfg = env_ai_config()
    cfg.update({k: v for k, v in (overrides or {}).items() if v and k in cfg})
    text_name = cfg["ai_text_provider"].lower()
    image_name = cfg["ai_image_provider"].lower()
    if text_name == image_name:
        return _build_provider(text_name, cfg)
    return _CompositeProvider(_build_provider(text_name, cfg), _build_provider(image_name, cfg))


class _ReloadableProvider:
    """Repassa ao provider atual. `swap` troca o alvo sem mudar os imports de `ai`."""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    @property
    def name(self) -> str:
        return self._provider.name

    def text(self, req: TextRequest) -> TextResponse:
        return self._provider.text(req)

    def image(self, req: ImageRequest) -> ImageResponse:
        return self._provider.image(req)

    def swap(self, provider: AIProvider) -> None:
        self._provider = provider


ai = _ReloadableProvider(build_default())


def reload_ai(provider: AIProvider) -> None:
    ai.swap(provider)


__all__ = [
    "AIProvider",
    "ImageRequest",
    "ImageResponse",
    "Message",
    "TextRequest",
    "TextResponse",
    "ai",
    "build_default",
    "build_local_text_provider",
    "env_ai_config",
    "reload_ai",
]
