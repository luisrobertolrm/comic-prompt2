from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, field_serializer


class SeriesCreate(BaseModel):
    name: str
    description: str | None = None


class SeriesUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectIdsBody(BaseModel):
    project_ids: list[uuid.UUID]


class SeriesOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    project_ids: list[uuid.UUID]
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: uuid.UUID) -> str:
        return str(v)

    @field_serializer("project_ids")
    def serialize_project_ids(self, v: list[uuid.UUID]) -> list[str]:
        return [str(p) for p in v]
