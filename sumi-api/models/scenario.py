from __future__ import annotations

import uuid
from datetime import UTC, datetime

from base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(60), nullable=False, server_default="Cenário")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    time_of_day: Mapped[str | None] = mapped_column(String(30), nullable=True)
    weather: Mapped[str | None] = mapped_column(String(30), nullable=True)
    atmosphere: Mapped[str | None] = mapped_column(String(30), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    style: Mapped[str] = mapped_column(String(60), nullable=False, server_default="anime-90s")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=_utcnow
    )
