from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from prompt_clinica.schemas.character import CharacterOut
from prompt_clinica.styles import DEFAULT_COLOR_MODE, DEFAULT_STYLE, ColorModeId, StyleId


class ProjectCreate(BaseModel):
    title: str
    premise: str
    genre: str
    tone: str
    pages: int = Field(default=4, ge=1, le=20)
    language: str = "pt-BR"
    style: StyleId = DEFAULT_STYLE
    color_mode: ColorModeId = DEFAULT_COLOR_MODE
    narrator_voice_id: uuid.UUID | None = None


class ProjectPatch(BaseModel):
    title: str | None = None
    premise: str | None = None
    synopsis: str | None = None
    genre: str | None = None
    tone: str | None = None
    pages: int | None = Field(default=None, ge=1, le=20)
    style: StyleId | None = None
    color_mode: ColorModeId | None = None
    narrator_voice_id: uuid.UUID | None = None


class CharacterIdsBody(BaseModel):
    character_ids: list[uuid.UUID]


class ProjectOut(BaseModel):
    id: uuid.UUID
    title: str
    subtitle: str
    genre: str
    tone: str
    status: str
    pages: int
    style: str
    color_mode: str
    cover_accent: str
    cover_tone: str
    narrator_voice_id: uuid.UUID | None
    video_url: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: uuid.UUID) -> str:
        return str(v)

    @field_serializer("narrator_voice_id")
    def serialize_narrator_voice_id(self, v: uuid.UUID | None) -> str | None:
        return str(v) if v is not None else None


class ProjectDetailOut(ProjectOut):
    premise: str | None
    synopsis: str | None
    characters: list[CharacterOut] = Field(default_factory=list)
