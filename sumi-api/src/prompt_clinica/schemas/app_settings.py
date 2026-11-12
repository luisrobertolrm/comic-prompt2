from __future__ import annotations

from pydantic import BaseModel, Field


class AppSettingsValues(BaseModel):
    ai_text_provider: str = Field(default="", max_length=40)
    ai_text_model: str = Field(default="", max_length=120)
    ai_image_provider: str = Field(default="", max_length=40)
    ai_image_model: str = Field(default="", max_length=120)
    seedream_model: str = Field(default="", max_length=120)
    stt_model: str = Field(default="", max_length=120)
    stt_language: str = Field(default="", max_length=10)


class AppSettingsOut(BaseModel):
    values: AppSettingsValues
    # Valores do .env, usados quando o campo correspondente está vazio.
    defaults: AppSettingsValues


class TranscriptionOut(BaseModel):
    text: str
