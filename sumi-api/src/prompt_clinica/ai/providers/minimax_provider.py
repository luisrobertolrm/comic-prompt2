"""
Adaptador que pluga a imagem do MiniMax no protocolo AIProvider.

Voz e vídeo não fazem parte do protocolo (que só cobre text/image) e
continuam nos clients de ai/minimax/.
"""
from __future__ import annotations

from prompt_clinica.ai.minimax import (
    MinimaxConfig,
    MinimaxImageClient,
)
from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    TextRequest,
    TextResponse,
)


class MinimaxProvider:
    def __init__(self, config: MinimaxConfig) -> None:
        # image-01 síncrono (sobretudo com subject_reference) regularmente passa de 60s.
        self._image = MinimaxImageClient(config, timeout=180.0)

    @property
    def name(self) -> str:
        return "minimax"

    def text(self, req: TextRequest) -> TextResponse:
        raise NotImplementedError(
            "O texto MiniMax usa o tipo OpenAI-compatível (https://api.minimax.io/v1)."
        )

    def image(self, req: ImageRequest) -> ImageResponse:
        # Os consumidores (character/panel) decodificam b64_json para salvar no
        # storage, então pedimos base64 em vez da URL temporária do provider.
        # image-01 aceita apenas UMA referência ("image_reference must be one");
        # multi-referência é capacidade do Seedream. Usa só a primeira.
        refs = req.subject_reference[:1] if req.subject_reference else None
        result = self._image.generate(
            prompt=req.prompt,
            n=req.n,
            aspect_ratio=req.aspect_ratio,
            response_format="base64",
            subject_reference=refs,
        )
        return ImageResponse(
            model=result.model,
            url=result.urls[0] if result.urls else "",
            b64_json=result.b64[0] if result.b64 else "",
        )
