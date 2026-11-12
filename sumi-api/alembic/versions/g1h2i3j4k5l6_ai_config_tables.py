"""ai_config_tables

Cria uma tabela de configurações por tipo de IA, converte o que estava em
app_settings + .env e remove app_settings.

Revision ID: g1h2i3j4k5l6
Revises: e2f3a4b5c6d7
Create Date: 2026-11-12 00:00:00.000000

"""
from __future__ import annotations

import os
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "g1h2i3j4k5l6"
down_revision: str | None = "e2f3a4b5c6d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "ai_text_config",
    "ai_image_config",
    "ai_transcription_config",
    "ai_voice_config",
    "ai_video_config",
)

_OPENAI_URL = "https://api.openai.com/v1"
_MINIMAX_TEXT_URL = "https://api.minimax.io/v1"


def _create_table(name: str) -> None:
    columns = [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("base_url", sa.String(length=300), nullable=False),
        sa.Column("api_key", sa.Text(), server_default="", nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
    ]
    if name == "ai_transcription_config":
        columns.append(sa.Column("language", sa.String(length=10), server_default="", nullable=False))
    columns += [
        sa.Column("active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    ]
    op.create_table(name, *columns)
    op.create_index(
        f"uq_{name}_active",
        name,
        ["active"],
        unique=True,
        postgresql_where=sa.text("active"),
    )


def _convert_existing() -> None:
    from prompt_clinica.utils.crypto import encrypt

    bind = op.get_bind()
    row = bind.execute(sa.text("SELECT * FROM app_settings WHERE id = 1")).mappings().first()
    saved = dict(row) if row else {}

    def value(column: str, env: str, default: str = "") -> str:
        return (saved.get(column) or os.getenv(env, "") or default).strip()

    def key(column: str, env: str) -> str:
        """Chave já cifrada: a do app_settings como está, senão a do .env cifrada."""
        stored = saved.get(column) or ""
        return stored or encrypt(os.getenv(env, "").strip())

    general = os.getenv("AI_PROVIDER", "") or "openai"
    text_provider = value("ai_text_provider", "AI_TEXT_PROVIDER", general).lower()
    image_provider = value("ai_image_provider", "AI_IMAGE_PROVIDER", general).lower()

    openai_key = key("openai_api_key", "OPENAI_API_KEY")
    minimax_key = key("minimax_api_key", "MINIMAX_API_KEY")
    byteplus_key = key("byteplus_api_key", "BYTEPLUS_API_KEY")
    minimax_url = (os.getenv("MINIMAX_BASE_URL") or "https://api.minimax.io").rstrip("/")
    byteplus_url = (
        os.getenv("BYTEPLUS_BASE_URL") or "https://ark.ap-southeast.bytepluses.com/api/v3"
    ).rstrip("/")

    rows: dict[str, list[dict[str, object]]] = {t: [] for t in _TABLES}
    if openai_key:
        rows["ai_text_config"].append({
            "name": "OpenAI", "kind": "openai", "base_url": _OPENAI_URL, "api_key": openai_key,
            "model": value("ai_text_model", "AI_TEXT_MODEL", "gpt-4o-mini"),
            "active": text_provider == "openai",
        })
        rows["ai_image_config"].append({
            "name": "OpenAI", "kind": "openai", "base_url": _OPENAI_URL, "api_key": openai_key,
            "model": value("ai_image_model", "AI_IMAGE_MODEL", "gpt-image-1"),
            "active": image_provider == "openai",
        })
        rows["ai_transcription_config"].append({
            "name": "OpenAI", "kind": "openai", "base_url": _OPENAI_URL, "api_key": openai_key,
            "model": value("stt_model", "STT_MODEL", "gpt-4o-mini-transcribe"),
            "language": value("stt_language", "STT_LANGUAGE", "pt"),
            "active": True,
        })
    if minimax_key:
        # Com o ComfyUI na imagem, o texto rodava no MiniMax.
        rows["ai_text_config"].append({
            "name": "MiniMax", "kind": "openai", "base_url": _MINIMAX_TEXT_URL, "api_key": minimax_key,
            "model": value("minimax_text_model", "MINIMAX_TEXT_MODEL", "MiniMax-M3"),
            "active": text_provider in ("minimax", "comfyui"),
        })
        rows["ai_image_config"].append({
            "name": "MiniMax", "kind": "minimax", "base_url": minimax_url, "api_key": minimax_key,
            "model": value("minimax_image_model", "MINIMAX_IMAGE_MODEL", "image-01"),
            "active": image_provider == "minimax",
        })
        rows["ai_voice_config"].append({
            "name": "MiniMax", "kind": "minimax", "base_url": minimax_url, "api_key": minimax_key,
            "model": value("minimax_voice_model", "MINIMAX_VOICE_MODEL", "speech-2.8-hd"),
            "active": True,
        })
        rows["ai_video_config"].append({
            "name": "MiniMax", "kind": "minimax", "base_url": minimax_url, "api_key": minimax_key,
            "model": value("minimax_video_model", "MINIMAX_VIDEO_MODEL", "MiniMax-Hailuo-2.3-Fast"),
            "active": True,
        })
    if byteplus_key:
        rows["ai_image_config"].append({
            "name": "Seedream", "kind": "seedream", "base_url": byteplus_url, "api_key": byteplus_key,
            "model": value("seedream_model", "SEEDREAM_MODEL", "seedream-4-0-250828"),
            "active": image_provider == "seedream",
        })

    for table, items in rows.items():
        if not items:
            continue
        columns = list(items[0])
        names = ", ".join(columns)
        params = ", ".join(f":{c}" for c in columns)
        for item in items:
            bind.execute(sa.text(f"INSERT INTO {table} ({names}) VALUES ({params})"), item)


def upgrade() -> None:
    for name in _TABLES:
        _create_table(name)
    _convert_existing()
    op.drop_table("app_settings")


def downgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ai_text_provider", sa.String(length=40), server_default="", nullable=False),
        sa.Column("ai_text_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("ai_image_provider", sa.String(length=40), server_default="", nullable=False),
        sa.Column("ai_image_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("seedream_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("stt_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("stt_language", sa.String(length=10), server_default="", nullable=False),
        sa.Column("minimax_text_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("minimax_image_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("minimax_voice_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("minimax_video_model", sa.String(length=120), server_default="", nullable=False),
        sa.Column("minimax_group_id", sa.String(length=120), server_default="", nullable=False),
        sa.Column("openai_api_key", sa.Text(), server_default="", nullable=False),
        sa.Column("minimax_api_key", sa.Text(), server_default="", nullable=False),
        sa.Column("byteplus_api_key", sa.Text(), server_default="", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO app_settings (id) VALUES (1)")
    for name in _TABLES:
        op.drop_index(f"uq_{name}_active", table_name=name)
        op.drop_table(name)
