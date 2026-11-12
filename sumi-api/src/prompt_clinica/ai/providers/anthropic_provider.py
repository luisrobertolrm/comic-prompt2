"""Provider de texto da Anthropic (Messages API, /v1/messages) via httpx."""
from __future__ import annotations

import httpx

from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    TextRequest,
    TextResponse,
)

_API_VERSION = "2023-06-01"
_JSON_INSTRUCTION = "Responda somente com JSON válido."


class AnthropicProvider:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return "anthropic"

    def text(self, req: TextRequest) -> TextResponse:
        system_parts = [m.content for m in req.messages if m.role == "system"]
        # A Messages API não tem response_format; o JSON é pedido por instrução.
        if req.json_mode:
            system_parts.append(_JSON_INSTRUCTION)
        payload: dict[str, object] = {
            "model": req.model or self._model,
            "max_tokens": req.max_tokens or 4096,
            "temperature": req.temperature,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in req.messages
                if m.role != "system"
            ],
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        resp = httpx.post(
            f"{self._base_url}/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": _API_VERSION,
                "content-type": "application/json",
            },
            json=payload,
            timeout=180.0,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Anthropic HTTP {resp.status_code}: {resp.text}")

        body = resp.json()
        content = "".join(
            block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"
        )
        usage = body.get("usage") or {}
        return TextResponse(
            content=content.strip(),
            model=body.get("model", self._model),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )

    def image(self, req: ImageRequest) -> ImageResponse:
        raise NotImplementedError("A Anthropic não gera imagens.")
