from __future__ import annotations

from datetime import UTC, datetime

from base import Base
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AppSettings(Base):
    """Configurações globais do sistema (linha única, id=1). Vazio = valor do .env."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ai_text_provider: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    ai_text_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    ai_image_provider: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    ai_image_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    seedream_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    stt_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    stt_language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="")
    minimax_text_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    minimax_image_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    minimax_voice_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    minimax_video_model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    minimax_group_id: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    # Chaves criptografadas (utils/crypto.py).
    openai_api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    minimax_api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    byteplus_api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )
