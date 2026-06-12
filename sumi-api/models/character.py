from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(60), nullable=False, server_default="Personagem")
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    skin_tone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ethnicity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[str | None] = mapped_column(String(30), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    outfit: Mapped[str | None] = mapped_column(Text, nullable=True)
    traits: Mapped[str | None] = mapped_column(String(500), nullable=True)  # CSV
    style: Mapped[str] = mapped_column(String(60), nullable=False, server_default="classic-shoujo")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    narrator_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("narration_voices.id", ondelete="SET NULL"), nullable=True
    )
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=_utcnow
    )
