"""add_synopsis_link_to_panel

Revision ID: f5a6b7c8d9e0
Revises: f4a5b6c7d8e9
Create Date: 2026-06-17 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("panels", sa.Column("synopsis_start", sa.Integer(), nullable=True))
    op.add_column("panels", sa.Column("synopsis_end", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("panels", "synopsis_end")
    op.drop_column("panels", "synopsis_start")
