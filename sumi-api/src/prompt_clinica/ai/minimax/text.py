"""Geração de texto via MiniMax (endpoint OpenAI-compatível /v1/chat/completions)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .client import MinimaxHTTPBase
from .errors import MinimaxError

# MiniMax-M3 é um modelo de raciocínio: emite o pensamento como <think>...</think>
# no início do content. Removemos para devolver só a resposta final.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
# Em json_mode o modelo às vezes envolve o JSON em cerca markdown ```json ... ```.
_FENCE_RE = re.compile(r"^```[a-zA-Z0-9]*\n(.*)\n```$", re.DOTALL)


def _clean(content: str, *, json_mode: bool) -> str:
    content = _THINK_RE.sub("", content).strip()
    if json_mode:
        match = _FENCE_RE.match(content)
        if match:
            content = match.group(1).strip()
    return content


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
        json_mode: bool = False,
    ) -> MinimaxTextResult:
        cfg = self.config.text
        payload: dict[str, object] = {
            "model": model or cfg.model,
            "messages": messages,
            "temperature": cfg.temperature if temperature is None else temperature,
            "max_tokens": cfg.max_tokens if max_tokens is None else max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        body = self._post("/v1/chat/completions", payload)

        choices = body.get("choices") or []
        if not choices:
            raise MinimaxError("Resposta sem 'choices'.")
        usage = body.get("usage") or {}
        return MinimaxTextResult(
            content=_clean(choices[0].get("message", {}).get("content", "") or "", json_mode=json_mode),
            model=body.get("model", payload["model"]),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
