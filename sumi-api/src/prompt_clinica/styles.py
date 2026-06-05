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
