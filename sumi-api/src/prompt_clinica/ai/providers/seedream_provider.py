"""
Provider de imagem Seedream (BytePlus ModelArk).

API compatível com OpenAI (`/images/generations`). Aceita prompt + até 10
imagens de referência (campo `image`). Só implementa `image()`; texto continua
no provider configurado em AI_TEXT_PROVIDER.
"""
from __future__ import annotations

import httpx

from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    TextRequest,
    TextResponse,
)

# Seedream usa `size` como dimensão concreta (1K~4K). Mapeamos as proporções
# que o app pede para um lado ~2K mantendo o aspecto.
_ASPECT_TO_SIZE = {
    "16:9": "2048x1152",
    "9:16": "1152x2048",
    "4:3": "2048x1536",
    "3:4": "1536x2048",
    "1:1": "2048x2048",
}

_MAX_REFERENCE_IMAGES = 10  # limite do Seedream 4.0


def _resolve_size(req: ImageRequest) -> str:
    if req.aspect_ratio:
        return _ASPECT_TO_SIZE.get(req.aspect_ratio, req.aspect_ratio)
    return req.size or "2048x2048"


class SeedreamProvider:
    def __init__(self) -> None:
        from prompt_clinica.config import settings

        self._api_key = settings.byteplus_api_key
        self._base_url = settings.byteplus_base_url.rstrip("/")
        self._model = settings.seedream_model

    @property
    def name(self) -> str:
        return "seedream"

    def text(self, req: TextRequest) -> TextResponse:
        raise NotImplementedError(
            "Seedream é provider de imagem. Use AI_TEXT_PROVIDER para o texto."
        )

    def image(self, req: ImageRequest) -> ImageResponse:
        if not self._api_key:
            raise ValueError("BYTEPLUS_API_KEY não definida no ambiente.")

        payload: dict[str, object] = {
            "model": self._model,
            "prompt": req.prompt,
            "size": _resolve_size(req),
            "sequential_image_generation": "disabled",
            "response_format": "b64_json",
            "watermark": False,
        }
        if req.subject_reference:
            payload["image"] = req.subject_reference[:_MAX_REFERENCE_IMAGES]

        resp = httpx.post(
            f"{self._base_url}/images/generations",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=180.0,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Seedream HTTP {resp.status_code}: {resp.text}")

        data = (resp.json().get("data") or [{}])[0]
        return ImageResponse(
            model=self._model,
            url=data.get("url", ""),
            b64_json=data.get("b64_json", ""),
            revised_prompt=data.get("revised_prompt"),
        )
