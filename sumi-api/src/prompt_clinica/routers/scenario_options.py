"""Catálogo de atributos de cenário — o front consome daqui."""
from fastapi import APIRouter

from prompt_clinica.scenario_options import GROUPS

router = APIRouter(tags=["scenarios"])


@router.get("/scenario-options")
def list_scenario_options() -> list[dict[str, object]]:
    return [
        {
            "id": g.id,
            "label": g.label,
            "multi": g.multi,
            "options": [{"id": o.id, "label": o.label} for o in g.options],
        }
        for g in GROUPS.values()
    ]
