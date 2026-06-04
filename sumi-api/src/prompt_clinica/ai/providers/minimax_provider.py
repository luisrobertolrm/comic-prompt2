"""
Adaptador que pluga texto e imagem do MiniMax no protocolo AIProvider,
permitindo AI_PROVIDER=minimax sem tocar nos consumidores do singleton `ai`.

Voz e vídeo não fazem parte do protocolo (que só cobre text/image) e
continuam acessíveis pelos clients standalone em ai/minimax/.
"""
from __future__ import annotations

from prompt_clinica.ai.minimax import (
    MinimaxConfig,
    MinimaxImageClient,
    MinimaxTextClient,
)
from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    TextRequest,
    TextResponse,
)


class MinimaxProvider:
    def __init__(self, config: MinimaxConfig | None = None) -> None:
        cfg = config or MinimaxConfig()
        self._text = MinimaxTextClient(cfg)
        self._image = MinimaxImageClient(cfg)

    @property
    def name(self) -> str:
        return "minimax"

    def text(self, req: TextRequest) -> TextResponse:
        result = self._text.generate(
            messages=[{"role": m.role, "content": m.content} for m in req.messages],
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return TextResponse(
            content=result.content,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )

    def image(self, req: ImageRequest) -> ImageResponse:
        result = self._image.generate(prompt=req.prompt, n=req.n)
        return ImageResponse(
            model=result.model,
            url=result.urls[0] if result.urls else "",
            b64_json=result.b64[0] if result.b64 else "",
        )
