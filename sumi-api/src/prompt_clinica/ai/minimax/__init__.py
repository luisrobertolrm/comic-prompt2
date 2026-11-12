"""
Conjunto de classes MiniMax, separado por modalidade.

Cada client é independente e recebe a mesma `MinimaxConfig`:

    from prompt_clinica.ai.minimax import MinimaxConfig, MinimaxImageClient

    cfg = MinimaxConfig(api_key="...", base_url="https://api.minimax.io", model="image-01")
    img = MinimaxImageClient(cfg).generate("manga panel, rain over a city")

Texto MiniMax usa o adaptador OpenAI-compatível (https://api.minimax.io/v1).
Para imagem há o adaptador em ai/providers/minimax_provider.py.
"""
from __future__ import annotations

from .config import (
    MinimaxConfig,
    MinimaxImageConfig,
    MinimaxVideoConfig,
    MinimaxVoiceConfig,
)
from .errors import MinimaxError
from .image import MinimaxImageClient, MinimaxImageResult
from .video import MinimaxVideoClient, MinimaxVideoResult
from .voice import MinimaxVoiceClient

__all__ = [
    "MinimaxConfig",
    "MinimaxError",
    "MinimaxImageClient",
    "MinimaxImageConfig",
    "MinimaxImageResult",
    "MinimaxVideoClient",
    "MinimaxVideoConfig",
    "MinimaxVideoResult",
    "MinimaxVoiceClient",
    "MinimaxVoiceConfig",
]
