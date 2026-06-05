from __future__ import annotations

import json
import uuid
from typing import Literal

from pydantic import BaseModel


class BubbleSchema(BaseModel):
    text: str
    kind: Literal["say", "thought", "shout", "whisper", "narration"] = "say"
    side: Literal["left", "right"] = "left"
    tail: Literal["none", "left", "right"] = "none"
    x: int = 8
    y: int = 12


class PanelOut(BaseModel):
    id: str
    project_id: str
    index_order: int
    label: str
    aspect: str
    tone: str
    character_name: str | None
    caption: str
    framing: str
    prompt: str
    status: str
    bubbles: list[BubbleSchema]
    image_url: str | None


class PanelPatch(BaseModel):
    label: str | None = None
    aspect: str | None = None
    tone: str | None = None
    character_name: str | None = None
    caption: str | None = None
    framing: str | None = None
    prompt: str | None = None
    status: str | None = None
    bubbles: list[BubbleSchema] | None = None


class InsertPanelBody(BaseModel):
    after_index: int


class ReorderBody(BaseModel):
    panel_ids: list[uuid.UUID]


def panel_to_out(p: object) -> PanelOut:
    """Convert ORM Panel to PanelOut, handling bubbles_json."""
    from panel import Panel  # local import to avoid circular
    assert isinstance(p, Panel)
    try:
        raw = json.loads(p.bubbles_json or "[]")
        bubbles = [BubbleSchema.model_validate(b) for b in raw]
    except (json.JSONDecodeError, Exception):
        bubbles = []
    return PanelOut(
        id=str(p.id),
        project_id=str(p.project_id),
        index_order=p.index_order,
        label=p.label,
        aspect=p.aspect,
        tone=p.tone,
        character_name=p.character_name,
        caption=p.caption,
        framing=p.framing,
        prompt=p.prompt,
        status=p.status,
        bubbles=bubbles,
        image_url=p.image_url,
    )
