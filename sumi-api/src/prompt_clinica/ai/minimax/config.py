"""
Configuração do MiniMax.

Chave, endpoint e modelo vêm da configuração de IA ativa (tabelas ai_*_config);
cada modalidade só guarda parâmetros técnicos fixos.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class MinimaxImageConfig:
    aspect_ratio: str = "1:1"
    response_format: str = "url"  # "url" | "base64"
    # image-01 tem prompt_optimizer=true por padrão, o que reescreve o prompt e
    # descarta atributos específicos (estilo, corpo, pele). Desligado para o modelo
    # aderir ao prompt literal.
    prompt_optimizer: bool = False
    # Grava o payload de cada geração em sumi-api/minimax_payload.log.
    payload_log: bool = field(default_factory=lambda: _env_bool("MINIMAX_PAYLOAD_LOG", True))


@dataclass(frozen=True)
class MinimaxVoiceConfig:
    voice_id: str = "English_Graceful_Lady"
    sample_rate: int = 32000
    bitrate: int = 128000
    audio_format: str = "mp3"


@dataclass(frozen=True)
class MinimaxVideoConfig:
    duration: int = 6
    resolution: str = "768P"


@dataclass(frozen=True)
class MinimaxConfig:
    api_key: str
    base_url: str
    model: str
    image: MinimaxImageConfig = field(default_factory=MinimaxImageConfig)
    voice: MinimaxVoiceConfig = field(default_factory=MinimaxVoiceConfig)
    video: MinimaxVideoConfig = field(default_factory=MinimaxVideoConfig)

    def require_key(self) -> str:
        if not self.api_key:
            raise ValueError("Chave do MiniMax não configurada.")
        return self.api_key
