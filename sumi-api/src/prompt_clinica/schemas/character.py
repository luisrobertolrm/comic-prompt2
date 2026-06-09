from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field, field_serializer, field_validator

from prompt_clinica.styles import DEFAULT_STYLE, StyleId


class CharacterCreate(BaseModel):
    name: str
    role: str = "Personagem"
    gender: str | None = None
    age: int | None = None
    height: str | None = None
    summary: str | None = None
    outfit: str | None = None
    traits: list[str] = Field(default_factory=list)
    style: StyleId = DEFAULT_STYLE
    image_url: str | None = None
    narrator_voice_id: uuid.UUID | None = None


class CharacterUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    gender: str | None = None
    age: int | None = None
    height: str | None = None
    summary: str | None = None
    outfit: str | None = None
    traits: list[str] | None = None
    image_url: str | None = None
    narrator_voice_id: uuid.UUID | None = None


class PortraitCandidate(BaseModel):
    id: str
    url: str
    notes: str


class DeleteUnusedBody(BaseModel):
    ids: list[uuid.UUID] = Field(default_factory=list)


class PortraitRequest(BaseModel):
    prompt: str
    style: StyleId = DEFAULT_STYLE
    gender: str | None = None


class PortraitJobOut(BaseModel):
    job_id: str
    status: str  # pending | running | done | error
    portraits: list[PortraitCandidate] = Field(default_factory=list)
    detail: str = ""


class CharacterOut(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    gender: str | None
    age: int | None
    height: str | None
    summary: str | None
    outfit: str | None
    traits: list[str]
    style: str
    approved: bool
    image_url: str | None
    narrator_voice_id: uuid.UUID | None = None
    project_count: int = 0

    model_config = {"from_attributes": True}

    @field_validator("traits", mode="before")
    @classmethod
    def parse_traits(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        if v is None:
            return []
        return list(v)

    @field_serializer("id")
    def serialize_id(self, v: uuid.UUID) -> str:
        return str(v)

    @field_serializer("narrator_voice_id")
    def serialize_narrator_voice_id(self, v: uuid.UUID | None) -> str | None:
        return str(v) if v is not None else None
