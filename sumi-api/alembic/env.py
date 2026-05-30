from __future__ import annotations

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

# ---------------------------------------------------------------------------
# Coloca src/ e models/ no sys.path para que Alembic encontre os pacotes
# ---------------------------------------------------------------------------
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root / "models"))

load_dotenv(_root / ".env")

# ---------------------------------------------------------------------------
# Importa a Base declarativa (e todos os modelos registrados nela)
# ---------------------------------------------------------------------------
from base import Base  # noqa: E402  (models/base.py)
import all_models  # noqa: F401, E402  (models/all_models.py — importa tudo)

# ---------------------------------------------------------------------------
# Configuração Alembic
# ---------------------------------------------------------------------------
alembic_cfg = context.config
fileConfig(alembic_cfg.config_file_name)  # type: ignore[arg-type]

database_url = os.environ["DATABASE_URL"]

target_metadata = Base.metadata

_managed_tables = set(target_metadata.tables.keys())


def include_object(obj: object, name: str, type_: str, reflected: bool, compare_to: object) -> bool:
    # ignora tabelas que existem no banco mas não estão nos nossos models
    if type_ == "table" and name not in _managed_tables:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
