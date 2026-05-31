"""add_image_url_to_character

Revision ID: a3f1b2c4d5e6
Revises: 9bd09689af71
Create Date: 2026-05-30

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1b2c4d5e6'
down_revision: Union[str, None] = '9bd09689af71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('characters', sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('characters', 'image_url')
