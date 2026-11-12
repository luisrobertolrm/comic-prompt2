"""
Fonte dos estilos visuais (ESTILO VISUAL).

O prompt completo de cada estilo vive na tabela `visual_styles` (banco). Aqui
ficam o cache em memória, a resolução de ids (incluindo aliases antigos) e a
montagem do prompt a partir do template + atributos do personagem.

Cada estilo é um prompt próprio com placeholders nomeados:
    {sexo} {faixa_etaria} {etinia} {cabelo} {paleta_cor}
O render preenche só os slots presentes no template e ignora o resto, então
estilos diferentes podem expor conjuntos diferentes de placeholders. A cor entra
pelo slot {paleta_cor}, com wording por estilo (coluna `color_wording`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Annotated

from pydantic import AfterValidator

import prompt_clinica._paths  # noqa: F401  (coloca models/ no sys.path)

DEFAULT_STYLE = "anime-90s"
DEFAULT_COLOR_MODE = "tons-cinza"


@dataclass(frozen=True)
class VisualStyle:
    id: str
    label: str
    note: str
    prompt_template: str
    color_wording: dict[str, str] = field(default_factory=dict)
    aspect_ratio: str = "1:1"
    resolution: str = "2K"

    def render(self, slots: dict[str, str], color_mode_id: str | None) -> str:
        data = dict(slots)
        data["paleta_cor"] = (
            self.color_wording.get(color_mode_id or "", "") if self.color_wording else ""
        )
        return _clean(self.prompt_template.format_map(_SafeDict(data)))


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


def _clean(text: str) -> str:
    """Remove buracos deixados por slots vazios (espaços/pontuação soltos)."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.])", r"\1", text)
    text = re.sub(r"(?:,\s*){2,}", ", ", text)
    text = re.sub(r"\.\s*,", ".", text)
    text = re.sub(r"\.(?:\s*\.)+", ".", text)
    text = re.sub(r",\s*\.", ".", text)
    return text.strip().strip(",").strip()


# Os ids antigos (classic-shoujo, modern-line, webtoon, ink-heavy) foram
# reescritos nos dados pela migration d0e1f2a3b4c5; não há mais aliases.
_LEGACY_ALIASES: dict[str, str] = {}


# ── Modos de cor (rótulos para o front; o wording real vem do estilo) ──

@dataclass(frozen=True)
class ColorMode:
    id: str
    label: str
    note: str


COLOR_MODES: dict[str, ColorMode] = {
    "tons-cinza": ColorMode("tons-cinza", "Tons de cinza", "mangá moderno, gradientes em cinza"),
    "p-e-b": ColorMode("p-e-b", "Preto e branco", "tinta pura, sem meios-tons"),
    "colorido": ColorMode("colorido", "Colorido", "ilustração em cores"),
}


# ── Cache em memória da tabela visual_styles ──

_CACHE: dict[str, VisualStyle] | None = None


def _load() -> dict[str, VisualStyle]:
    from visual_style import VisualStyle as Row

    from prompt_clinica.database import SessionLocal

    with SessionLocal() as db:
        rows = (
            db.query(Row)
            .filter(Row.enabled.is_(True))
            .order_by(Row.sort_order)
            .all()
        )
    return {
        r.id: VisualStyle(
            id=r.id,
            label=r.label,
            note=r.note,
            prompt_template=r.prompt_template,
            color_wording=dict(r.color_wording or {}),
            aspect_ratio=r.aspect_ratio,
            resolution=r.resolution,
        )
        for r in rows
    }


def all_styles() -> dict[str, VisualStyle]:
    global _CACHE
    if _CACHE is None:
        _CACHE = _load()
    return _CACHE


def reload_cache() -> None:
    global _CACHE
    _CACHE = None


def resolve(style_id: str | None) -> VisualStyle:
    styles = all_styles()
    sid = _LEGACY_ALIASES.get(style_id or "", style_id or "")
    return styles.get(sid) or styles.get(DEFAULT_STYLE) or next(iter(styles.values()))


def resolve_color(color_mode_id: str | None) -> ColorMode:
    return COLOR_MODES.get(color_mode_id or "", COLOR_MODES[DEFAULT_COLOR_MODE])


def render_prompt(
    style_id: str | None,
    slots: dict[str, str],
    color_mode_id: str | None = None,
) -> str:
    """Prompt final do estilo: template preenchido com os atributos do personagem."""
    return resolve(style_id).render(slots, color_mode_id)


# ── Fragmento de estilo para PAINÉIS (cena) ──
# Os painéis (comic) usam um descritor de estilo curto, não o template de retrato.
# Esse caminho não faz parte da migração para o banco; o descritor em inglês fica
# aqui, separado por propósito do prompt_template de retrato.
_PANEL_STYLE = {
    "manga-pb": "black and white manga panel, clean line art, thin precise lines, minimal shading, no screentones, {color}",
    "anime-90s": "classic 90s anime screenshot, hard cel-shading, clean solid outlines, retro anime grading, {color}",
    "dark-fantasy": "dark fantasy semi-realistic digital painting, painterly, {color}, dramatic chiaroscuro lighting",
}
_PANEL_COLOR = {
    "colorido": "full color",
    "tons-cinza": "shades of gray",
    "p-e-b": "pure black and white, no gray tones",
}


def prompt_fragment(style_id: str | None, color_mode_id: str | None = None) -> str:
    sid = _LEGACY_ALIASES.get(style_id or "", style_id or "")
    tmpl = _PANEL_STYLE.get(sid) or _PANEL_STYLE[DEFAULT_STYLE]
    color = _PANEL_COLOR.get(color_mode_id or "", _PANEL_COLOR[DEFAULT_COLOR_MODE])
    return tmpl.format(color=color)


def _known_ids() -> set[str]:
    return set(all_styles()) | set(_LEGACY_ALIASES)


def _require_known(style_id: str) -> str:
    if style_id not in _known_ids():
        raise ValueError(f"Estilo inválido: '{style_id}'.")
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
