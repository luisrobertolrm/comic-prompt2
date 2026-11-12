from __future__ import annotations

import uuid
from datetime import datetime

from base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class RecomendacaoPositiva(Base):
    __tablename__ = "recomendacao_positiva"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class RecomendacaoNegativa(Base):
    __tablename__ = "recomendacao_negativa"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class RecomendacaoUsuario(Base):
    __tablename__ = "recomendacao_usuario"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    positivo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
