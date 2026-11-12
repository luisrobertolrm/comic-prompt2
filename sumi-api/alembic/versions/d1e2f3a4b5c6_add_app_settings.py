"""add_app_settings

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-11-11 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "c0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ai_text_provider", sa.String(length=40), server_default="", nullable=False),
        sa.Column("ai_text_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("ai_image_provider", sa.String(length=40), server_default="", nullable=False),
        sa.Column("ai_image_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("seedream_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("stt_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("stt_language", sa.String(length=10), server_default="", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO app_settings (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("app_settings")
