from __future__ import annotations

from datetime import UTC, datetime

from base import Base
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AITextConfig(Base):
    """Configurações de IA de texto (chat). No máximo uma ativa."""

    __tablename__ = "ai_text_config"
    # Índice único parcial: no máximo uma linha com active = true.
    __table_args__ = (
        Index(
            "uq_ai_text_config_active",
            "active",
            unique=True,
            postgresql_where=text("active"),
            sqlite_where=text("active"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    base_url: Mapped[str] = mapped_column(String(300), nullable=False)
    # Cifrada com utils/crypto.encrypt.
    api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )
