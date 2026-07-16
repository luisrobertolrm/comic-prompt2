"""add_groups_and_user_approval

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-07-07 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9c0d1e2f3a4"
down_revision: Union[str, None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADMIN_EMAIL = "luisrobertolrm@gmail.com"


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type"),
    )
    op.execute("INSERT INTO groups (type) VALUES ('admin'), ('padrao')")

    op.add_column("users", sa.Column("group_id", sa.UUID(), nullable=True))
    op.add_column(
        "users",
        sa.Column("approved", sa.Boolean(), server_default="false", nullable=False),
    )
    # Usuários existentes: aprovados no grupo padrão
    op.execute(
        "UPDATE users SET group_id = (SELECT id FROM groups WHERE type = 'padrao'), approved = true"
    )
    op.execute(
        "UPDATE users SET group_id = (SELECT id FROM groups WHERE type = 'admin') "
        f"WHERE lower(email) = '{ADMIN_EMAIL}'"
    )
    op.alter_column("users", "group_id", nullable=False)
    op.create_foreign_key("fk_users_group_id", "users", "groups", ["group_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_users_group_id", "users", type_="foreignkey")
    op.drop_column("users", "approved")
    op.drop_column("users", "group_id")
    op.drop_table("groups")
