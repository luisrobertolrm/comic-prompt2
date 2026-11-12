from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AIConfigIn(BaseModel):
    name: str = Field(max_length=80)
    kind: str = Field(max_length=20)
    base_url: str = Field(max_length=300)
    api_key: str = Field(default="", max_length=500)
    model: str = Field(max_length=120)
    language: str = Field(default="", max_length=10)
    active: bool = False

    @field_validator("name", "model")
    @classmethod
    def _required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Campo obrigatório.")
        return value

    @field_validator("kind", "language")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @field_validator("base_url")
    @classmethod
    def _url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("A URL deve começar com http:// ou https://.")
        return value


class AIConfigUpdate(AIConfigIn):
    """`api_key`: None mantém a chave salva; "" apaga; texto substitui."""

    api_key: str | None = Field(default=None, max_length=500)  # type: ignore[assignment]


class AIConfigOut(BaseModel):
    id: int
    name: str
    kind: str
    base_url: str
    model: str
    language: str
    key_hint: str  # "…ab12"; "" sem chave
    active: bool
    updated_at: datetime


class ActiveIn(BaseModel):
    active: bool


class TextTestOut(BaseModel):
    response: str
    model: str
    elapsed_ms: int


class ImageTestOut(BaseModel):
    image: str  # URL ou data-URI
    model: str
    elapsed_ms: int


class TranscriptionTestOut(BaseModel):
    text: str
    model: str
    elapsed_ms: int


class VoiceTestOut(BaseModel):
    audio: str  # data:audio/mpeg;base64,...
    model: str
    elapsed_ms: int


class VideoTestOut(BaseModel):
    status: str
    model: str
    elapsed_ms: int


class TranscriptionOut(BaseModel):
    text: str
