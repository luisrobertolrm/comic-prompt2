from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class TextRequest:
    messages: list[Message]
    model: str = ""          # vazio = usa o default do provider
    temperature: float = 0.7
    max_tokens: int | None = None
    json_mode: bool = False  # força response_format=json_object (OpenAI)


@dataclass
class TextResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int


@dataclass
class ImageRequest:
    prompt: str
    size: str = "1024x1024"  # "1024x1024" | "1792x1024" | "1024x1792"
    quality: str = "standard"  # "standard" | "hd"
    n: int = 1
    # Proporção da imagem (ex.: "16:9", "1:1"). Vazio = default do provider.
    aspect_ratio: str = ""
    # Referências de personagem (URL pública ou data-URI base64). MiniMax e Seedream usam.
    subject_reference: list[str] | None = None


@dataclass
class ImageResponse:
    model: str
    url: str = ""              # preenchido quando o provider retorna URL
    b64_json: str = ""         # preenchido quando o provider retorna base64
    revised_prompt: str | None = None

    def has_url(self) -> bool:
        return bool(self.url)

    def has_b64(self) -> bool:
        return bool(self.b64_json)
