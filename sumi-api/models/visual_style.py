from __future__ import annotations

from datetime import UTC, datetime

from base import Base
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class VisualStyle(Base):
    __tablename__ = "visual_styles"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    note: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    # Prompt completo com placeholders {sexo} {faixa_etaria} {etinia} {cabelo} {paleta_cor}.
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    # color_mode id -> wording do slot {paleta_cor}; {} para estilos monocromáticos.
    color_wording: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    aspect_ratio: Mapped[str] = mapped_column(String(20), nullable=False, server_default="1:1")
    resolution: Mapped[str] = mapped_column(String(20), nullable=False, server_default="2K")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=_utcnow
    )
