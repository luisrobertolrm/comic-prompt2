from __future__ import annotations

from pydantic import BaseModel


class SettingsOut(BaseModel):
    local_ai_url: str
    local_ai_model: str
    local_ai_enabled: bool


class SettingsUpdate(BaseModel):
    local_ai_url: str | None = None
    local_ai_model: str | None = None
    local_ai_enabled: bool | None = None


class LocalAiModelsOut(BaseModel):
    models: list[str]
