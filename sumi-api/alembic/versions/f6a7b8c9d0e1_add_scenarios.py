"""add_scenarios

Revision ID: f6a7b8c9d0e1
Revises: a1c2e3f4b5d6
Create Date: 2026-06-27 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'a1c2e3f4b5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scenarios',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('kind', sa.String(length=60), server_default='Cenário', nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('location_type', sa.String(length=40), nullable=True),
        sa.Column('time_of_day', sa.String(length=30), nullable=True),
        sa.Column('weather', sa.String(length=30), nullable=True),
        sa.Column('atmosphere', sa.String(length=30), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('style', sa.String(length=60), server_default='anime-90s', nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('approved', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'project_scenarios',
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('scenario_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id', 'scenario_id'),
    )


def downgrade() -> None:
    op.drop_table('project_scenarios')
    op.drop_table('scenarios')
