"""
Fonte única dos estilos visuais (ESTILO VISUAL).

O front e o banco guardam apenas o `id`; o backend resolve aqui o fragmento
de prompt usado na geração de imagem (personagem e painel). Mudou de provider
ou de estilo? É aqui que se mexe — em um lugar só.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import AfterValidator


@dataclass(frozen=True)
class VisualStyle:
    id: str
    label: str
    note: str
    image_fragment: str


DEFAULT_STYLE = "classic-shoujo"
DEFAULT_COLOR_MODE = "tons-cinza"

STYLES: dict[str, VisualStyle] = {
    "classic-shoujo": VisualStyle(
        id="classic-shoujo",
        label="Shojo clássico (olhos grandes)",
        note="70s–80s, traços líricos",
        image_fragment=(
            "Classic shoujo manga style, black and white screentone, clean ink line art, "
            "large expressive eyes, delicate lyrical linework, high contrast"
        ),
    ),
    "modern-line": VisualStyle(
        id="modern-line",
        label="Linha moderna limpa",
        note="contornos finos, screentones suaves",
        image_fragment=(
            "Modern manga style, clean thin line art, soft gentle screentones, "
            "minimal heavy blacks, crisp inking, subtle contrast"
        ),
    ),
    "ink-heavy": VisualStyle(
        id="ink-heavy",
        label="Tinta marcada",
        note="sombras profundas, contraste alto",
        image_fragment=(
            "Heavy ink manga style, deep blacks and dramatic shadows, bold brush strokes, "
            "strong spotting blacks, high contrast chiaroscuro"
        ),
    ),
}


@dataclass(frozen=True)
class ColorMode:
    id: str
    label: str
    color_fragment: str


COLOR_MODES: dict[str, ColorMode] = {
    "p-e-b": ColorMode(
        id="p-e-b",
        label="Preto e branco",
        color_fragment=(
            "strictly black and white only, no gray tones, no color whatsoever, "
            "high-contrast ink, monochrome"
        ),
    ),
    "tons-cinza": ColorMode(
        id="tons-cinza",
        label="Tons de cinza",
        color_fragment=(
            "grayscale only, no color, black white and gray tones, monochrome"
        ),
    ),
    "colorido": ColorMode(
        id="colorido",
        label="Colorido",
        color_fragment=(
            "full color illustration, vivid colors, colored artwork"
        ),
    ),
}


def resolve_color(color_mode_id: str | None) -> ColorMode:
    return COLOR_MODES.get(color_mode_id or "", COLOR_MODES[DEFAULT_COLOR_MODE])


def color_fragment(color_mode_id: str | None) -> str:
    return resolve_color(color_mode_id).color_fragment


def _require_known_color(color_mode_id: str) -> str:
    if color_mode_id not in COLOR_MODES:
        raise ValueError(
            f"Modo de cor inválido: '{color_mode_id}'. Válidos: {', '.join(COLOR_MODES)}."
        )
    return color_mode_id


ColorModeId = Annotated[str, AfterValidator(_require_known_color)]


def resolve(style_id: str | None) -> VisualStyle:
    return STYLES.get(style_id or "", STYLES[DEFAULT_STYLE])


def image_fragment(style_id: str | None) -> str:
    return resolve(style_id).image_fragment


def _require_known(style_id: str) -> str:
    if style_id not in STYLES:
        raise ValueError(f"Estilo inválido: '{style_id}'. Válidos: {', '.join(STYLES)}.")
    return style_id


# Tipo para schemas Pydantic: valida o id contra STYLES na entrada da API.
StyleId = Annotated[str, AfterValidator(_require_known)]
