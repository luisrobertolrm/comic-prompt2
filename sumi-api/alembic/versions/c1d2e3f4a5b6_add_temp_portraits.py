"""add temp_portraits

Revision ID: c1d2e3f4a5b6
Revises: f3a1b2c4d5e7
Create Date: 2026-06-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c1d2e3f4a5b6"
down_revision = "f3a1b2c4d5e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "temp_portraits",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("variant", sa.String(60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_temp_portraits_user_id", "temp_portraits", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_temp_portraits_user_id", table_name="temp_portraits")
    op.drop_table("temp_portraits")
