from __future__ import annotations

from pydantic import BaseModel, Field


class AppSettingsValues(BaseModel):
    ai_text_provider: str = Field(default="", max_length=40)
    ai_text_model: str = Field(default="", max_length=120)
    ai_image_provider: str = Field(default="", max_length=40)
    ai_image_model: str = Field(default="", max_length=120)
    seedream_model: str = Field(default="", max_length=120)
    minimax_text_model: str = Field(default="", max_length=120)
    minimax_image_model: str = Field(default="", max_length=120)
    minimax_voice_model: str = Field(default="", max_length=120)
    minimax_video_model: str = Field(default="", max_length=120)
    minimax_group_id: str = Field(default="", max_length=120)
    stt_model: str = Field(default="", max_length=120)
    stt_language: str = Field(default="", max_length=10)


class ApiKeysUpdate(BaseModel):
    """None = mantém a chave salva; "" = remove; texto = grava a nova."""

    openai_api_key: str | None = Field(default=None, max_length=500)
    minimax_api_key: str | None = Field(default=None, max_length=500)
    byteplus_api_key: str | None = Field(default=None, max_length=500)


class AppSettingsUpdate(AppSettingsValues, ApiKeysUpdate):
    pass


class ApiKeyStatus(BaseModel):
    source: str  # "db" | "env" | ""
    hint: str  # últimos 4 caracteres, ex.: "…ab12"


class AppSettingsOut(BaseModel):
    values: AppSettingsValues
    # Valores do .env, usados quando o campo correspondente está vazio.
    defaults: AppSettingsValues
    keys: dict[str, ApiKeyStatus]


class TranscriptionOut(BaseModel):
    text: str


class ImageTestOut(BaseModel):
    provider: str
    model: str
    image: str  # URL ou data-URI
    elapsed_ms: int
