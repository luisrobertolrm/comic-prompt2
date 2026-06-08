from __future__ import annotations

import uuid

from pydantic import BaseModel


class VoiceCreate(BaseModel):
    name: str
    voice_id: str
    age_start: int | None = None
    age_end: int | None = None
    sex: str | None = None
    details: str | None = None


class VoiceUpdate(BaseModel):
    name: str | None = None
    voice_id: str | None = None
    age_start: int | None = None
    age_end: int | None = None
    sex: str | None = None
    details: str | None = None


class VoiceOut(BaseModel):
    id: uuid.UUID
    name: str
    voice_id: str
    age_start: int | None
    age_end: int | None
    sex: str | None
    details: str | None

    model_config = {"from_attributes": True}
