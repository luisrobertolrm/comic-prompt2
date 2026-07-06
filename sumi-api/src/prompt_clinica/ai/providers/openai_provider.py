from __future__ import annotations

from openai import OpenAI

from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    TextRequest,
    TextResponse,
)


class OpenAIProvider:
    """
    Provider OpenAI.

    Texto  → gpt-4o-mini  (chat completions)
    Imagem → gpt-image-1  (retorna base64; qualidade "medium")
    """

    def __init__(
        self,
        api_key: str,
        text_model: str = "gpt-4o-mini",
        image_model: str = "gpt-image-1",
        base_url: str | None = None,
    ) -> None:
        # base_url permite apontar para um servidor OpenAI-compat local (Ollama,
        # LM Studio, vLLM). None = API oficial da OpenAI.
        self._client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        self._text_model = text_model
        self._image_model = image_model
        self._name = "openai-local" if base_url else "openai"

    @property
    def name(self) -> str:
        return self._name

    def text(self, req: TextRequest) -> TextResponse:
        model = req.model or self._text_model
        extra: dict[str, object] = {}
        if req.max_tokens:
            extra["max_tokens"] = req.max_tokens
        if req.json_mode:
            extra["response_format"] = {"type": "json_object"}
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in req.messages],
            temperature=req.temperature,
            **extra,
        )
        choice = response.choices[0]
        usage = response.usage
        return TextResponse(
            content=choice.message.content or "",
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
