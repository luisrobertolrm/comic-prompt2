from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class VideoMetadataOut(BaseModel):
    yt_title: str
    yt_description: str
    yt_tags: list[str]
    yt_category_id: str
    privacy_status: str
    publish_at: datetime | None
    thumbnail_panel_id: str | None

    model_config = {"from_attributes": True}


class VideoMetadataUpdate(BaseModel):
    yt_title: str
    yt_description: str
    yt_tags: list[str]
    yt_category_id: str
    privacy_status: str
    publish_at: datetime | None = None
    thumbnail_panel_id: str | None = None
