from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_serializer

from prompt_clinica.styles import DEFAULT_STYLE, StyleId


class ScenarioCreate(BaseModel):
    name: str
    kind: str = "Cenário"
    summary: str | None = None
    location_type: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    atmosphere: str | None = None
    details: str | None = None
    style: StyleId = DEFAULT_STYLE
    image_url: str | None = None


class ScenarioUpdate(BaseModel):
    name: str | None = None
    kind: str | None = None
    summary: str | None = None
    location_type: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    atmosphere: str | None = None
    details: str | None = None
    image_url: str | None = None


class SceneCandidate(BaseModel):
    id: str
    url: str
    notes: str


class DeleteUnusedBody(BaseModel):
    ids: list[uuid.UUID] = Field(default_factory=list)


class SceneRequest(BaseModel):
    style: StyleId = DEFAULT_STYLE
    color_mode: str | None = None
    location: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    atmosphere: str | None = None
    # Texto livre anexado após os atributos.
    extra: str | None = None
    # Modo "prompt livre": envia o texto literal à IA, sem montagem por template.
    prompt: str = ""
    raw: bool = False


class SceneJobOut(BaseModel):
    job_id: str
    status: str  # pending | running | done | error
    scenes: list[SceneCandidate] = Field(default_factory=list)
    detail: str = ""


class ScenarioOut(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    summary: str | None
    location_type: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    atmosphere: str | None = None
    details: str | None = None
    style: str
    approved: bool
    image_url: str | None
    project_count: int = 0

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: uuid.UUID) -> str:
        return str(v)
