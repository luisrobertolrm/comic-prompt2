from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class VideoMetadata(Base):
    __tablename__ = "video_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    yt_title: Mapped[str] = mapped_column(String(100), nullable=False, server_default="")
    yt_description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    yt_tags: Mapped[str] = mapped_column(Text, nullable=False, server_default="[]")
    yt_category_id: Mapped[str] = mapped_column(String(10), nullable=False, server_default="1")
    privacy_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="private")
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    thumbnail_panel_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=_utcnow
    )
