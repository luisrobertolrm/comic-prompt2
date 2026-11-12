"""add_keys_and_minimax_to_app_settings

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-11-11 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STRING_COLUMNS = (
    "minimax_text_model",
    "minimax_image_model",
    "minimax_voice_model",
    "minimax_video_model",
    "minimax_group_id",
)
_KEY_COLUMNS = ("openai_api_key", "minimax_api_key", "byteplus_api_key")


def upgrade() -> None:
    for name in _STRING_COLUMNS:
        op.add_column("app_settings", sa.Column(name, sa.String(length=120), server_default="", nullable=False))
    for name in _KEY_COLUMNS:
        op.add_column("app_settings", sa.Column(name, sa.Text(), server_default="", nullable=False))


def downgrade() -> None:
    for name in (*_KEY_COLUMNS, *_STRING_COLUMNS):
        op.drop_column("app_settings", name)
