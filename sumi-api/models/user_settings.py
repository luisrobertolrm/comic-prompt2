from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UserSettings(Base):
    """Configurações por usuário. Hoje guarda a IA local; extensível por colunas."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # URL base do servidor OpenAI-compat local (ex.: http://localhost:11434).
    local_ai_url: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    local_ai_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    local_ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )
