"""
Camada de abstração de IA.

Uso básico:

    from prompt_clinica.ai import ai
    from prompt_clinica.ai.types import TextRequest, Message, ImageRequest

    resp = ai.text(TextRequest(messages=[Message("user", "Olá!")]))
    img  = ai.image(ImageRequest(prompt="Mangá, personagem correndo"))

Provider, modelos e chaves vêm do .env, sobrescritos pela tabela app_settings
(tela "Configurações do sistema"). Para um provider novo, implemente o
protocolo em base.py e registre em _build_provider.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_clinica.ai.base import AIProvider
from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    Message,
    TextRequest,
    TextResponse,
)

if TYPE_CHECKING:
    from prompt_clinica.ai.minimax import MinimaxConfig


def env_ai_config() -> dict[str, str]:
    """Valores de IA vindos do .env — base sobre a qual o app_settings sobrescreve."""
    from prompt_clinica.ai.minimax import MinimaxConfig
    from prompt_clinica.config import settings

    mm = MinimaxConfig()
    return {
        "ai_text_provider": settings.ai_text_provider or settings.ai_provider,
        "ai_text_model": settings.ai_text_model,
        "ai_image_provider": settings.ai_image_provider or settings.ai_provider,
        "ai_image_model": settings.ai_image_model,
        "seedream_model": settings.seedream_model,
        "minimax_text_model": mm.text.model,
        "minimax_image_model": mm.image.model,
        "minimax_voice_model": mm.voice.model,
        "minimax_video_model": mm.video.model,
        "minimax_group_id": mm.group_id,
        "stt_model": settings.stt_model,
        "stt_language": settings.stt_language,
        "openai_api_key": settings.openai_api_key,
        "minimax_api_key": mm.api_key,
        "byteplus_api_key": settings.byteplus_api_key,
    }


# Valores salvos no app_settings (já descriptografados); vazio = .env.
_overrides: dict[str, str] = {}


def current_config(overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Configuração efetiva: .env com os `overrides` não vazios por cima."""
    cfg = env_ai_config()
    source = _overrides if overrides is None else overrides
    cfg.update({k: v for k, v in source.items() if v and k in cfg})
    return cfg


def minimax_config(cfg: dict[str, str] | None = None) -> MinimaxConfig:
    from prompt_clinica.ai.minimax import (
        MinimaxConfig,
        MinimaxImageConfig,
        MinimaxTextConfig,
        MinimaxVideoConfig,
        MinimaxVoiceConfig,
    )

    c = cfg or current_config()
    return MinimaxConfig(
        api_key=c["minimax_api_key"],
        group_id=c["minimax_group_id"],
        text=MinimaxTextConfig(model=c["minimax_text_model"]),
        image=MinimaxImageConfig(model=c["minimax_image_model"]),
        voice=MinimaxVoiceConfig(model=c["minimax_voice_model"]),
        video=MinimaxVideoConfig(model=c["minimax_video_model"]),
    )


def _build_provider(name: str, cfg: dict[str, str]) -> AIProvider:
    match name:
        case "openai":
            from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

            if not cfg["openai_api_key"]:
                raise ValueError("Chave da OpenAI não configurada.")
            return OpenAIProvider(
                api_key=cfg["openai_api_key"],
                text_model=cfg["ai_text_model"],
                image_model=cfg["ai_image_model"],
            )
        case "minimax":
            from prompt_clinica.ai.providers.minimax_provider import MinimaxProvider

            return MinimaxProvider(minimax_config(cfg))
        case "comfyui":
            from prompt_clinica.ai.providers.comfyui_provider import ComfyUIProvider

            return ComfyUIProvider()
        case "seedream":
            from prompt_clinica.ai.providers.seedream_provider import SeedreamProvider

            return SeedreamProvider(model=cfg["seedream_model"], api_key=cfg["byteplus_api_key"])
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


def build_default(cfg: dict[str, str]) -> AIProvider:
    text_name = cfg["ai_text_provider"].lower()
    image_name = cfg["ai_image_provider"].lower()
    if text_name == image_name:
        return _build_provider(text_name, cfg)
    return _CompositeProvider(_build_provider(text_name, cfg), _build_provider(image_name, cfg))


class _ReloadableProvider:
    """Repassa ao provider atual, montado no primeiro uso a partir de `current_config()`.

    `configure` troca o alvo sem mudar os imports de `ai`.
    """

    def __init__(self) -> None:
        self._provider: AIProvider | None = None

    def _current(self) -> AIProvider:
        if self._provider is None:
            self._provider = build_default(current_config())
        return self._provider

    @property
    def name(self) -> str:
        return self._current().name

    def text(self, req: TextRequest) -> TextResponse:
        return self._current().text(req)

    def image(self, req: ImageRequest) -> ImageResponse:
        return self._current().image(req)

    def swap(self, provider: AIProvider | None) -> None:
        self._provider = provider


ai = _ReloadableProvider()


def configure(overrides: dict[str, str], provider: AIProvider | None = None) -> None:
    """Grava os overrides do app_settings. Sem `provider`, ele é montado no próximo uso."""
    _overrides.clear()
    _overrides.update(overrides)
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
    "configure",
    "current_config",
    "env_ai_config",
    "minimax_config",
]
