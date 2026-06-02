from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field, field_serializer, field_validator


class CharacterCreate(BaseModel):
    name: str
    role: str = "Personagem"
    age: int | None = None
    height: str | None = None
    summary: str | None = None
    outfit: str | None = None
    traits: list[str] = Field(default_factory=list)
    image_url: str | None = None


class PortraitCandidate(BaseModel):
    id: str
    url: str
    notes: str


class PortraitRequest(BaseModel):
    prompt: str


class PortraitJobOut(BaseModel):
    job_id: str
    status: str  # pending | running | done | error
    portraits: list[PortraitCandidate] = Field(default_factory=list)
    detail: str = ""


class CharacterOut(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    age: int | None
    height: str | None
    summary: str | None
    outfit: str | None
    traits: list[str]
    approved: bool
    image_url: str | None

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
