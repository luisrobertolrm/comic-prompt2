"""add_video_metadata

Revision ID: f3a1b2c4d5e7
Revises: 9bd09689af71
Create Date: 2026-05-31 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a1b2c4d5e7'
down_revision: Union[str, None] = 'a3f1b2c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'video_metadata',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('yt_title', sa.String(length=100), server_default='', nullable=False),
        sa.Column('yt_description', sa.Text(), server_default='', nullable=False),
        sa.Column('yt_tags', sa.Text(), server_default='[]', nullable=False),
        sa.Column('yt_category_id', sa.String(length=10), server_default='1', nullable=False),
        sa.Column('privacy_status', sa.String(length=20), server_default='private', nullable=False),
        sa.Column('publish_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('thumbnail_panel_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id'),
    )


def downgrade() -> None:
    op.drop_table('video_metadata')
