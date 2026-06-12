"""Catálogo de atributos de personagem — o front consome daqui."""
from fastapi import APIRouter

from prompt_clinica.character_options import GROUPS

router = APIRouter(tags=["characters"])


@router.get("/character-options")
def list_character_options() -> list[dict[str, object]]:
    return [
        {
            "id": g.id,
            "label": g.label,
            "multi": g.multi,
            "options": [{"id": o.id, "label": o.label} for o in g.options],
        }
        for g in GROUPS.values()
    ]
