"""add_temperatures_to_project

Revision ID: a1c2e3f4b5d6
Revises: f5a6b7c8d9e0
Create Date: 2026-06-23 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1c2e3f4b5d6"
down_revision: str | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("synopsis_temperature", sa.Float(), nullable=False, server_default="0.8"),
    )
    op.add_column(
        "projects",
        sa.Column("panels_temperature", sa.Float(), nullable=False, server_default="0.4"),
    )


def downgrade() -> None:
    op.drop_column("projects", "panels_temperature")
    op.drop_column("projects", "synopsis_temperature")
