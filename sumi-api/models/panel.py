from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Panel(Base):
    __tablename__ = "panels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    index_order: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    aspect: Mapped[str] = mapped_column(String(10), nullable=False, server_default="4-3")
    tone: Mapped[str] = mapped_column(String(20), nullable=False, server_default="dots")
    character_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    caption: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    framing: Mapped[str] = mapped_column(String(60), nullable=False, server_default="Plano médio")
    prompt: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="pending")
    bubbles_json: Mapped[str] = mapped_column(Text, nullable=False, server_default="[]")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    synopsis_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    synopsis_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=_utcnow
    )
