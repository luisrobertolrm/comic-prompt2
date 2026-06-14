"""migrate legacy visual style ids to the 3 real styles

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-14 00:30:00.000000

Os ids antigos (`classic-shoujo`, `modern-line`, `webtoon`, `ink-heavy`) deixam
de existir: as linhas são reescritas para um dos 3 estilos reais e o default das
colunas passa a `anime-90s`. Migração de dados — não invertível.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# id antigo -> estilo real
_MAP = {
    "classic-shoujo": "anime-90s",
    "modern-line": "anime-90s",
    "webtoon": "anime-90s",
    "ink-heavy": "dark-fantasy",
}


def upgrade() -> None:
    for table in ("characters", "projects"):
        for old, new in _MAP.items():
            op.execute(f"UPDATE {table} SET style = '{new}' WHERE style = '{old}'")
        op.alter_column(table, "style", server_default="anime-90s")


def downgrade() -> None:
    for table in ("characters", "projects"):
        op.alter_column(table, "style", server_default="classic-shoujo")
