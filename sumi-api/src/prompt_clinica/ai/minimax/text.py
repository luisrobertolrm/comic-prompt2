"""Geração de texto via MiniMax (chatcompletion_v2, síncrono)."""
from __future__ import annotations

from dataclasses import dataclass

from .client import MinimaxHTTPBase
from .errors import MinimaxError


@dataclass
class MinimaxTextResult:
    content: str
    model: str
    input_tokens: int
    output_tokens: int


class MinimaxTextClient(MinimaxHTTPBase):
    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> MinimaxTextResult:
        cfg = self.config.text
        payload = {
            "model": model or cfg.model,
            "messages": messages,
            "temperature": cfg.temperature if temperature is None else temperature,
            "max_tokens": cfg.max_tokens if max_tokens is None else max_tokens,
        }
        body = self._post("/v1/text/chatcompletion_v2", payload)

        choices = body.get("choices") or []
        if not choices:
            raise MinimaxError("Resposta sem 'choices'.")
        usage = body.get("usage") or {}
        return MinimaxTextResult(
            content=choices[0].get("message", {}).get("content", "") or "",
            model=body.get("model", payload["model"]),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
