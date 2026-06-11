"""add_body_type_skin_tone_to_character

Revision ID: a7b8c9d0e1f2
Revises: e6f7a8b9c0d1
Create Date: 2026-06-10 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("body_type", sa.String(length=30), nullable=True))
    op.add_column("characters", sa.Column("skin_tone", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("characters", "skin_tone")
    op.drop_column("characters", "body_type")
