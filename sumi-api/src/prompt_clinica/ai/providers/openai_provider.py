from __future__ import annotations

import re
from urllib.parse import urlparse

from openai import BadRequestError, OpenAI

from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    TextRequest,
    TextResponse,
)

# Modelos de raciocínio (MiniMax-M3, DeepSeek-R1, Ollama) emitem o pensamento como
# <think>...</think> no início do content. Se max_tokens estourar no meio do
# raciocínio, o <think> vem sem fechamento: descarta-se dali até o fim.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINK_OPEN_RE = re.compile(r"<think>.*$", re.DOTALL)
# Em json_mode alguns modelos envolvem o JSON em cerca markdown ```json ... ```.
_FENCE_RE = re.compile(r"^```[a-zA-Z0-9]*\n(.*)\n```$", re.DOTALL)


def _fixed_temperature(model: str) -> bool:
    """gpt-5 e o-series só aceitam temperature padrão (1); omitir o parâmetro."""
    m = model.lower()
    return m.startswith(("o1", "o3", "o4", "gpt-5"))


def _clean(content: str, *, json_mode: bool) -> str:
    content = _THINK_RE.sub("", content)
    content = _THINK_OPEN_RE.sub("", content).strip()
    if json_mode:
        match = _FENCE_RE.match(content)
        if match:
            content = match.group(1).strip()
    return content


class OpenAIProvider:
    """Provider para qualquer API compatível com a da OpenAI (OpenAI, BytePlus, MiniMax, Ollama…)."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        text_model: str = "",
        image_model: str = "",
    ) -> None:
        # O SDK exige uma chave mesmo quando o servidor não usa (Ollama local).
        self._client = OpenAI(api_key=api_key or "none", base_url=base_url)
        self._base_url = base_url
        self._text_model = text_model
        self._image_model = image_model

    @property
    def name(self) -> str:
        return urlparse(self._base_url).hostname or self._base_url

    def text(self, req: TextRequest) -> TextResponse:
        model = req.model or self._text_model
        extra: dict[str, object] = {}
        if req.max_tokens:
            # A OpenAI rejeita max_tokens nos modelos gpt-5/o-series; os demais
            # servidores compatíveis ainda usam o nome antigo.
            if "api.openai.com" in self._base_url:
                extra["max_completion_tokens"] = req.max_tokens
            else:
                extra["max_tokens"] = req.max_tokens
        if req.json_mode:
            extra["response_format"] = {"type": "json_object"}
        payload: dict[str, object] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in req.messages],
            **extra,
        }
        send_temp = not _fixed_temperature(model)
        if send_temp:
            payload["temperature"] = req.temperature
        try:
            response = self._client.chat.completions.create(**payload)  # type: ignore[arg-type]
        except BadRequestError as exc:
            if send_temp and "temperature" in str(exc).lower():
                payload.pop("temperature", None)
                response = self._client.chat.completions.create(**payload)  # type: ignore[arg-type]
            else:
                raise
        choice = response.choices[0]
        usage = response.usage
        return TextResponse(
            content=_clean(choice.message.content or "", json_mode=req.json_mode),
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

    def image(self, req: ImageRequest) -> ImageResponse:
        # gpt-image-1 usa quality: "low" | "medium" | "high" | "auto"
        # Models legados (dall-e-2/3) usam quality: "standard" | "hd"
        response = self._client.images.generate(
            model=self._image_model,
            prompt=req.prompt,
            size=req.size,       # type: ignore[arg-type]
            quality=req.quality, # type: ignore[arg-type]
            n=req.n,
        )
        item = response.data[0]
        return ImageResponse(
            model=self._image_model,
            url=item.url or "",
            b64_json=item.b64_json or "",
            revised_prompt=getattr(item, "revised_prompt", None),
        )
