from __future__ import annotations

import uuid
from datetime import UTC, datetime

from base import Base
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(300), nullable=False, server_default="")
    genre: Mapped[str] = mapped_column(String(60), nullable=False)
    tone: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False, server_default="Rascunho")
    pages: Mapped[int] = mapped_column(Integer, nullable=False, server_default="24")
    language: Mapped[str] = mapped_column(String(30), nullable=False, server_default="pt")
    style: Mapped[str] = mapped_column(String(60), nullable=False, server_default="anime-90s")
    color_mode: Mapped[str] = mapped_column(String(30), nullable=False, server_default="tons-cinza")
    premise: Mapped[str | None] = mapped_column(Text, nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    synopsis_temperature: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.8")
    panels_temperature: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.4")
    narrator_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("narration_voices.id", ondelete="SET NULL"), nullable=True
    )
    cover_accent: Mapped[str] = mapped_column(String(30), nullable=False, server_default="accent")
    cover_tone: Mapped[str] = mapped_column(String(30), nullable=False, server_default="dots")
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=_utcnow
    )
