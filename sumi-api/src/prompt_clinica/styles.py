"""
Fonte única dos estilos visuais (ESTILO VISUAL).

O front e o banco guardam apenas o `id`; o front consome a lista via
GET /styles e o backend resolve aqui o fragmento de prompt usado na geração
de imagem (personagem e painel). Mudou de provider ou de estilo? É aqui que
se mexe — em um lugar só.

Formato validado nos testes com MiniMax (prompt_optimizer ativo):
    "<sujeito>, cartoon-style '<descrição do estilo>', <atributos>."
A cor entra DENTRO da descrição do estilo (slot {color}), porque o wording
de cor que funciona varia por estilo (ex.: "flat colors" no anime 90s vs
"smooth color gradients" no webtoon).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated

from pydantic import AfterValidator


DEFAULT_STYLE = "webtoon"
DEFAULT_COLOR_MODE = "tons-cinza"


@dataclass(frozen=True)
class VisualStyle:
    id: str
    label: str
    note: str
    description: str           # template com {color}; vai entre aspas simples no prompt
    colors: dict[str, str] = field(default_factory=dict)  # color_mode id -> wording do slot
    sd_fragment: str = ""      # tags danbooru, para Stable Diffusion (ComfyUI)
    sd_negative: str = ""      # negativo real do estilo (Stable Diffusion)

    def render(self, color_mode_id: str | None) -> str:
        mode = color_mode_id if color_mode_id in self.colors else DEFAULT_COLOR_MODE
        return self.description.format(color=self.colors[mode])


STYLES: dict[str, VisualStyle] = {
    "webtoon": VisualStyle(
        id="webtoon",
        label="Webtoon / Manhwa",
        note="traço limpo, luz cinematográfica",
        description=(
            "A digital illustration, modern Webtoon art style, manhwa aesthetic, "
            "sharp v-shaped jawline, almond-shaped expressive eyes, highly "
            "detailed hair with glossy highlights, clean lineart, {color}, "
            "cinematic lighting"
        ),
        colors={
            "colorido": "smooth color gradients",
            "tons-cinza": "shades of gray",
            "p-e-b": "pure black and white ink, no gray tones",
        },
        sd_fragment="manhwa, clean lineart, glossy hair, smooth shading",
        sd_negative="sketch, rough lineart, retro artstyle",
    ),
    "dark-fantasy": VisualStyle(
        id="dark-fantasy",
        label="Dark fantasy semi-realista",
        note="pintura digital, luz dramática",
        description=(
            "A dark fantasy digital painting, semi-realistic anime style, game "
            "concept art, realistic facial proportions, anatomically correct "
            "eyes, defined jawline, volumetric lips, painterly style, textured "
            "brushes, {color}, dramatic chiaroscuro lighting, no visible lineart"
        ),
        colors={
            "colorido": "rich moody colors",
            "tons-cinza": "monochrome shades of gray",
            "p-e-b": "stark black and white, no gray tones",
        },
        sd_fragment=(
            "semi-realistic, painterly, dark fantasy, chiaroscuro, "
            "dramatic lighting, high contrast"
        ),
        sd_negative="chibi, sparkling eyes, flat color, clean lineart",
    ),
    "anime-90s": VisualStyle(
        id="anime-90s",
        label="Anime retrô anos 90",
        note="cel-shading, contornos sólidos",
        description=(
            "A classic 90s anime screenshot, moe anime aesthetic, large round "
            "sparkling eyes, huge pupils with reflections, small stylized mouth, "
            "soft rounded face, {color}, hard cel-shading, clean solid outlines, "
            "retro anime grading"
        ),
        colors={
            "colorido": "flat colors",
            "tons-cinza": "shades of gray",
            "p-e-b": "pure black and white, no gray tones",
        },
        sd_fragment=(
            "retro artstyle, 1990s \\(style\\), anime screenshot, cel shading, "
            "flat color"
        ),
        sd_negative="realistic, painterly, 3d",
    ),
}

# Ids antigos ainda gravados em projetos/personagens existentes.
_LEGACY_ALIASES = {
    "classic-shoujo": "anime-90s",
    "modern-line": "webtoon",
    "ink-heavy": "dark-fantasy",
}


@dataclass(frozen=True)
class ColorMode:
    id: str
    label: str
    note: str
    sd_fragment: str = ""
    sd_negative: str = ""


COLOR_MODES: dict[str, ColorMode] = {
    "tons-cinza": ColorMode(
        id="tons-cinza",
        label="Tons de cinza",
        note="mangá moderno, gradientes em cinza",
        sd_fragment="monochrome, greyscale, screentone, halftone",
        sd_negative="color",
    ),
    "p-e-b": ColorMode(
        id="p-e-b",
        label="Preto e branco",
        note="tinta pura, sem meios-tons",
        sd_fragment="monochrome, greyscale, high contrast, lineart",
        sd_negative="color",
    ),
    "colorido": ColorMode(
        id="colorido",
        label="Colorido",
        note="ilustração em cores",
        sd_negative="monochrome, greyscale",
    ),
}


def resolve(style_id: str | None) -> VisualStyle:
    sid = _LEGACY_ALIASES.get(style_id or "", style_id or "")
    return STYLES.get(sid, STYLES[DEFAULT_STYLE])


def resolve_color(color_mode_id: str | None) -> ColorMode:
    return COLOR_MODES.get(color_mode_id or "", COLOR_MODES[DEFAULT_COLOR_MODE])


def prompt_fragment(style_id: str | None, color_mode_id: str | None = None) -> str:
    """Fragmento de estilo para prompts de imagem: cartoon-style '<descrição com cor>'."""
    return f"cartoon-style '{resolve(style_id).render(color_mode_id)}'"


def _require_known(style_id: str) -> str:
    if style_id not in STYLES and style_id not in _LEGACY_ALIASES:
        raise ValueError(f"Estilo inválido: '{style_id}'. Válidos: {', '.join(STYLES)}.")
    return style_id


def _require_known_color(color_mode_id: str) -> str:
    if color_mode_id not in COLOR_MODES:
        raise ValueError(
            f"Modo de cor inválido: '{color_mode_id}'. Válidos: {', '.join(COLOR_MODES)}."
        )
    return color_mode_id


# Tipos para schemas Pydantic: validam o id na entrada da API.
StyleId = Annotated[str, AfterValidator(_require_known)]
ColorModeId = Annotated[str, AfterValidator(_require_known_color)]
