"""
Configuração de IA ativa por tipo (tabelas ai_*_config) e fábricas dos adaptadores.

O `kind` de cada linha escolhe o adaptador; URL, chave e modelo vêm da própria
linha. Nenhum adaptador lê variável de ambiente.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ai_image_config import AIImageConfig
from ai_text_config import AITextConfig
from ai_transcription_config import AITranscriptionConfig
from ai_video_config import AIVideoConfig
from ai_voice_config import AIVoiceConfig

import prompt_clinica._paths  # noqa: F401
from prompt_clinica.ai.base import AIProvider, SpeechToText, TextToSpeech
from prompt_clinica.database import SessionLocal
from prompt_clinica.utils.crypto import decrypt

if TYPE_CHECKING:
    from prompt_clinica.ai.minimax import MinimaxConfig

AI_TYPES: dict[str, Any] = {
    "text": AITextConfig,
    "image": AIImageConfig,
    "transcription": AITranscriptionConfig,
    "voice": AIVoiceConfig,
    "video": AIVideoConfig,
}

KINDS: dict[str, tuple[str, ...]] = {
    "text": ("openai", "anthropic"),
    "image": ("openai", "seedream", "minimax"),
    "transcription": ("openai",),
    "voice": ("minimax",),
    "video": ("minimax",),
}

LABELS: dict[str, str] = {
    "text": "texto",
    "image": "imagem",
    "transcription": "transcrição",
    "voice": "voz",
    "video": "vídeo",
}


@dataclass(frozen=True)
class AIConfig:
    kind: str
    base_url: str
    api_key: str
    model: str
    language: str = ""


class NoActiveConfig(Exception):
    def __init__(self, ai_type: str) -> None:
        super().__init__(
            f"Nenhuma IA de {LABELS[ai_type]} ativa. Configure em Configurações do sistema."
        )


def to_ai_config(row: Any) -> AIConfig:
    return AIConfig(
        kind=row.kind,
        base_url=row.base_url,
        api_key=decrypt(row.api_key),
        model=row.model,
        language=getattr(row, "language", ""),
    )


def get_active(ai_type: str) -> AIConfig:
    model = AI_TYPES[ai_type]
    with SessionLocal() as db:
        row = db.query(model).filter(model.active.is_(True)).first()
        if row is None:
            raise NoActiveConfig(ai_type)
        return to_ai_config(row)


def minimax_config(cfg: AIConfig) -> MinimaxConfig:
    from prompt_clinica.ai.minimax import MinimaxConfig

    return MinimaxConfig(api_key=cfg.api_key, base_url=cfg.base_url, model=cfg.model)


def build_text_provider(cfg: AIConfig) -> AIProvider:
    match cfg.kind:
        case "openai":
            from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

            return OpenAIProvider(api_key=cfg.api_key, base_url=cfg.base_url, text_model=cfg.model)
        case "anthropic":
            from prompt_clinica.ai.providers.anthropic_provider import AnthropicProvider

            return AnthropicProvider(api_key=cfg.api_key, base_url=cfg.base_url, model=cfg.model)
        case _:
            raise ValueError(f"Tipo de IA de texto desconhecido: '{cfg.kind}'.")


def build_image_provider(cfg: AIConfig) -> AIProvider:
    match cfg.kind:
        case "openai":
            from prompt_clinica.ai.providers.openai_provider import OpenAIProvider

            return OpenAIProvider(api_key=cfg.api_key, base_url=cfg.base_url, image_model=cfg.model)
        case "seedream":
            from prompt_clinica.ai.providers.seedream_provider import SeedreamProvider

            return SeedreamProvider(api_key=cfg.api_key, base_url=cfg.base_url, model=cfg.model)
        case "minimax":
            from prompt_clinica.ai.providers.minimax_provider import MinimaxProvider

            return MinimaxProvider(minimax_config(cfg))
        case _:
            raise ValueError(f"Tipo de IA de imagem desconhecido: '{cfg.kind}'.")


def speech_to_text_for(cfg: AIConfig) -> SpeechToText:
    from prompt_clinica.ai.speech import OpenAISpeechToText

    return OpenAISpeechToText(cfg)


def text_to_speech_for(cfg: AIConfig) -> TextToSpeech:
    from prompt_clinica.ai.minimax import MinimaxVoiceClient

    return MinimaxVoiceClient(minimax_config(cfg))


def build_speech_to_text() -> SpeechToText:
    return speech_to_text_for(get_active("transcription"))


def build_text_to_speech() -> TextToSpeech:
    return text_to_speech_for(get_active("voice"))
