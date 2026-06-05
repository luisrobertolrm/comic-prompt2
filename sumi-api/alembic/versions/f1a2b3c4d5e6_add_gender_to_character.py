"""add_gender_to_character

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-06-04 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("gender", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("characters", "gender")
