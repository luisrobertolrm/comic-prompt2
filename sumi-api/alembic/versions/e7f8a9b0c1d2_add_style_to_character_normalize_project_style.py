"""add_style_to_character_and_normalize_project_style

Revision ID: e7f8a9b0c1d2
Revises: d4e5f6a7b8c9
Create Date: 2026-06-04 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_VALID = ("classic-shoujo", "modern-line", "ink-heavy")


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("style", sa.String(length=60), nullable=False, server_default="classic-shoujo"),
    )
    # Reconcilia o default antigo ("mangá") e estilos removidos ("minimal").
    op.execute(
        "UPDATE projects SET style = 'classic-shoujo' "
        "WHERE style NOT IN ('classic-shoujo', 'modern-line', 'ink-heavy')"
    )
    op.alter_column("projects", "style", server_default="classic-shoujo")


def downgrade() -> None:
    op.alter_column("projects", "style", server_default="mangá")
    op.drop_column("characters", "style")
