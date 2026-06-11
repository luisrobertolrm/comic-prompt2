"""Catálogo de estilos visuais e modos de cor — o front consome daqui."""
from fastapi import APIRouter

from prompt_clinica import styles

router = APIRouter(tags=["styles"])


@router.get("/styles")
def list_styles() -> dict[str, object]:
    return {
        "styles": [
            {"id": s.id, "label": s.label, "note": s.note}
            for s in styles.STYLES.values()
        ],
        "color_modes": [
            {"id": c.id, "label": c.label, "note": c.note}
            for c in styles.COLOR_MODES.values()
        ],
        "default_style": styles.DEFAULT_STYLE,
        "default_color_mode": styles.DEFAULT_COLOR_MODE,
    }
