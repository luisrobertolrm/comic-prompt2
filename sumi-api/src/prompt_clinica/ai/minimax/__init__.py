"""
Conjunto de classes MiniMax, separado por modalidade.

Cada client é independente e recebe a mesma `MinimaxConfig`:

    from prompt_clinica.ai.minimax import MinimaxConfig, MinimaxImageClient

    cfg = MinimaxConfig()
    img = MinimaxImageClient(cfg).generate("manga panel, rain over a city")

Para texto/imagem também há o adaptador em ai/providers/minimax_provider.py,
que pluga no singleton `ai` via AI_PROVIDER=minimax.
"""
from __future__ import annotations

from .config import (
    MinimaxConfig,
    MinimaxImageConfig,
    MinimaxTextConfig,
    MinimaxVideoConfig,
    MinimaxVoiceConfig,
)
from .errors import MinimaxError
from .image import MinimaxImageClient, MinimaxImageResult
from .text import MinimaxTextClient, MinimaxTextResult
from .video import MinimaxVideoClient, MinimaxVideoResult
from .voice import MinimaxVoiceClient, MinimaxVoiceResult

__all__ = [
    "MinimaxConfig",
    "MinimaxError",
    "MinimaxImageClient",
    "MinimaxImageConfig",
    "MinimaxImageResult",
    "MinimaxTextClient",
    "MinimaxTextConfig",
    "MinimaxTextResult",
    "MinimaxVideoClient",
    "MinimaxVideoConfig",
    "MinimaxVideoResult",
    "MinimaxVoiceClient",
    "MinimaxVoiceConfig",
    "MinimaxVoiceResult",
]
