"""
Configuração do MiniMax separada por modalidade.

A chave e o endpoint são compartilhados; cada modalidade tem seu próprio
modelo e parâmetros, lidos do ambiente. `MinimaxConfig.from_env()` monta tudo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class MinimaxTextConfig:
    model: str = field(default_factory=lambda: _env("MINIMAX_TEXT_MODEL", "MiniMax-M3"))
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass(frozen=True)
class MinimaxImageConfig:
    model: str = field(default_factory=lambda: _env("MINIMAX_IMAGE_MODEL", "image-01"))
    aspect_ratio: str = "1:1"
    response_format: str = "url"  # "url" | "base64"


@dataclass(frozen=True)
class MinimaxVoiceConfig:
    model: str = field(default_factory=lambda: _env("MINIMAX_VOICE_MODEL", "speech-2.8-hd"))
    voice_id: str = "English_Graceful_Lady"
    sample_rate: int = 32000
    bitrate: int = 128000
    audio_format: str = "mp3"


@dataclass(frozen=True)
class MinimaxVideoConfig:
    model: str = field(default_factory=lambda: _env("MINIMAX_VIDEO_MODEL", "MiniMax-Hailuo-2.3-Fast"))
    duration: int = 6
    resolution: str = "768P"


@dataclass(frozen=True)
class MinimaxConfig:
    api_key: str = field(default_factory=lambda: _env("MINIMAX_API_KEY"))
    base_url: str = field(default_factory=lambda: _env("MINIMAX_BASE_URL", "https://api.minimax.io"))
    group_id: str = field(default_factory=lambda: _env("MINIMAX_GROUP_ID"))
    text: MinimaxTextConfig = field(default_factory=MinimaxTextConfig)
    image: MinimaxImageConfig = field(default_factory=MinimaxImageConfig)
    voice: MinimaxVoiceConfig = field(default_factory=MinimaxVoiceConfig)
    video: MinimaxVideoConfig = field(default_factory=MinimaxVideoConfig)

    def require_key(self) -> str:
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY não definida no ambiente.")
        return self.api_key
