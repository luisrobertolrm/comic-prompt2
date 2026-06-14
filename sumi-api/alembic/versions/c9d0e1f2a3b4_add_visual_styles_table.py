"""add visual_styles table and seed

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-14 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLOR_CINEMATIC = {
    "colorido": "Warm color palette",
    "tons-cinza": "Black and white monochrome",
    "p-e-b": "high contrast black and white ink, no gray tones",
}

# Um estilo por prompt de referência em exemplo_prompt/<estilo>/README.md.
_SEED = [
    {
        "id": "manga-pb",
        "label": "Mangá PB (preto e branco)",
        "note": "traço de tinta, sem meios-tons",
        "prompt_template": (
            "Black and white manga style sketch portrait of a {faixa_etaria} {etinia} "
            "{sexo}, front-facing view, has {cabelo}, large expressive anime eyes. "
            "Clean line art style, thin precise lines, minimal shading, no screentones, "
            "plain white background, manga panel aesthetic, monochrome, no color, high "
            "contrast black ink on white paper, sketch illustration style"
        ),
        "color_wording": {},
        "sort_order": 0,
    },
    {
        "id": "anime-90s",
        "label": "Anime retrô anos 90",
        "note": "cel-shading, contornos sólidos",
        "prompt_template": (
            "1990s anime style portrait, close-up of a {faixa_etaria} {etinia} {sexo}, "
            "front view, centered composition. {cabelo}. Very large expressive anime "
            "eyes with big bright catchlight reflections, thick defined eyelashes, "
            "small minimalist nose, tiny neutral mouth. Classic 90s cel shaded anime "
            "aesthetic, soft lines, nostalgic vintage anime look. {paleta_cor}"
        ),
        "color_wording": _COLOR_CINEMATIC,
        "sort_order": 1,
    },
    {
        "id": "dark-fantasy",
        "label": "Dark fantasy semi-realista",
        "note": "pintura digital, luz dramática",
        "prompt_template": (
            "Photorealistic cinematic portrait, close-up of a {faixa_etaria} {etinia} "
            "{sexo}, 3/4 view. {cabelo}. Large expressive eyes with defined lashes, "
            "thin arched eyebrows, smooth skin. Cinematic lighting with sharp focus on "
            "the face, soft bokeh background, semi-3D digital painting aesthetic, high "
            "detail. {paleta_cor}"
        ),
        "color_wording": _COLOR_CINEMATIC,
        "sort_order": 2,
    },
]


def upgrade() -> None:
    table = op.create_table(
        "visual_styles",
        sa.Column("id", sa.String(length=60), primary_key=True),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("color_wording", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("aspect_ratio", sa.String(length=20), nullable=False, server_default="1:1"),
        sa.Column("resolution", sa.String(length=20), nullable=False, server_default="2K"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.bulk_insert(table, _SEED)


def downgrade() -> None:
    op.drop_table("visual_styles")
