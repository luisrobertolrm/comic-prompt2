"""add_narrator_voice_to_project_and_character

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-09 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("narrator_voice_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_projects_narrator_voice_id",
        "projects", "narration_voices",
        ["narrator_voice_id"], ["id"],
        ondelete="SET NULL",
    )

    op.add_column("characters", sa.Column("narrator_voice_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_characters_narrator_voice_id",
        "characters", "narration_voices",
        ["narrator_voice_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_characters_narrator_voice_id", "characters", type_="foreignkey")
    op.drop_column("characters", "narrator_voice_id")

    op.drop_constraint("fk_projects_narrator_voice_id", "projects", type_="foreignkey")
    op.drop_column("projects", "narrator_voice_id")
