from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from prompt_clinica.schemas.character import CharacterOut


class ProjectCreate(BaseModel):
    premise: str
    genre: str
    tone: str
    pages: int = Field(default=4, ge=1, le=20)
    language: str = "pt-BR"
    style: str = "classic-shoujo"


class ProjectPatch(BaseModel):
    premise: str | None = None
    genre: str | None = None
    tone: str | None = None
    pages: int | None = Field(default=None, ge=1, le=20)
    style: str | None = None


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
    cover_accent: str
    cover_tone: str
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: uuid.UUID) -> str:
        return str(v)


class ProjectDetailOut(ProjectOut):
    premise: str | None
    characters: list[CharacterOut] = Field(default_factory=list)
