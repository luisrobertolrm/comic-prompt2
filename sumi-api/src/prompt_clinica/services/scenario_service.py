from __future__ import annotations

import base64
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import HTTPException, status
from project_scenario import ProjectScenario
from scenario import Scenario
from sqlalchemy import func
from sqlalchemy.orm import Session
from user import User

import prompt_clinica._paths  # noqa: F401
from prompt_clinica import scenario_options, styles
from prompt_clinica.ai import ImageRequest, ai
from prompt_clinica.schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    SceneCandidate,
)
from prompt_clinica.storage import get_storage

logger = logging.getLogger("sumi.api")

# Duas amostras (seeds diferentes) do mesmo prompt de cena.
_SCENE_VARIANTS = [("1", ""), ("2", "")]


def _count_projects(scenario_id: uuid.UUID, db: Session) -> int:
    return (
        db.query(func.count(ProjectScenario.project_id))
        .filter(ProjectScenario.scenario_id == scenario_id)
        .scalar()
        or 0
    )


def list_all(user: User, db: Session) -> list[Scenario]:
    rows = (
        db.query(Scenario, func.count(ProjectScenario.scenario_id))
        .outerjoin(ProjectScenario, ProjectScenario.scenario_id == Scenario.id)
        .filter(Scenario.user_id == user.id)
        .group_by(Scenario.id)
        .order_by(Scenario.updated_at.desc())
        .all()
    )
    result: list[Scenario] = []
    for scenario, count in rows:
        scenario.project_count = count
        result.append(scenario)
    return result


def create(req: ScenarioCreate, user: User, db: Session) -> Scenario:
    scenario = Scenario(
        user_id=user.id,
        name=req.name.strip(),
        kind=req.kind,
        summary=req.summary,
        location_type=req.location_type,
        time_of_day=req.time_of_day,
        weather=req.weather,
        atmosphere=req.atmosphere,
        details=req.details,
        style=req.style,
        image_url=req.image_url,
        approved=True,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    scenario.project_count = 0
    return scenario


def update(scenario_id: uuid.UUID, req: ScenarioUpdate, user: User, db: Session) -> Scenario:
    scenario = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.user_id == user.id)
        .first()
    )
    if scenario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cenário não encontrado.")

    data = req.model_dump(exclude_unset=True)

    if "image_url" in data and data["image_url"] != scenario.image_url and scenario.image_url:
        old_key = scenario.image_url.split("/storage/")[-1]
        get_storage().delete(old_key)

    for key, value in data.items():
        if key == "name" and value is not None:
            scenario.name = value.strip()
        else:
            setattr(scenario, key, value)

    db.commit()
    db.refresh(scenario)
    scenario.project_count = _count_projects(scenario.id, db)
    return scenario


def _delete_image_file(image_url: str | None) -> None:
    if not image_url:
        return
    for marker in ("/static/images/", "/storage/"):
        idx = image_url.find(marker)
        if idx != -1:
            get_storage().delete(image_url[idx + len(marker):])
            return


def delete_unused(ids: list[uuid.UUID], user: User, db: Session) -> int:
    """Apaga cenários do usuário sem vínculo a nenhum projeto. Restrito aos ids dados."""
    query = (
        db.query(Scenario)
        .outerjoin(ProjectScenario, ProjectScenario.scenario_id == Scenario.id)
        .filter(Scenario.user_id == user.id, ProjectScenario.scenario_id.is_(None))
    )
    if ids:
        query = query.filter(Scenario.id.in_(ids))
    unused = query.all()
    for scenario in unused:
        _delete_image_file(scenario.image_url)
        db.delete(scenario)
    db.commit()
    return len(unused)


def build_scene_prompt(
    style: str = styles.DEFAULT_STYLE,
    color_mode: str | None = None,
    location: str | None = None,
    time_of_day: str | None = None,
    weather: str | None = None,
    atmosphere: str | None = None,
    extra: str | None = None,
) -> str:
    # Painéis/cenas usam o descritor curto de estilo, não o template de retrato.
    parts = [
        styles.prompt_fragment(style, color_mode),
        scenario_options.prompt_for("location", location),
        scenario_options.prompt_for("time_of_day", time_of_day),
        scenario_options.prompt_for("weather", weather),
        scenario_options.prompt_for("atmosphere", atmosphere),
        (extra or "").strip(),
        "wide establishing shot, environment background concept art",
    ]
    prompt = ", ".join(p for p in parts if p)
    return prompt + ". No people, no characters, no text, no speech bubbles."


def generate_scene(
    style: str = styles.DEFAULT_STYLE,
    color_mode: str | None = None,
    location: str | None = None,
    time_of_day: str | None = None,
    weather: str | None = None,
    atmosphere: str | None = None,
    extra: str | None = None,
    prompt: str = "",
    raw: bool = False,
) -> list[SceneCandidate]:
    base_prompt = prompt if raw else build_scene_prompt(
        style, color_mode, location, time_of_day, weather, atmosphere, extra
    )

    logger.info("generate_scene provider=%s style=%r -> %s", ai.name, style, base_prompt)

    def _generate_one(variant_id: str, variant_suffix: str) -> SceneCandidate:
        full_prompt = f"{base_prompt}, {variant_suffix}" if variant_suffix else base_prompt
        resp = ai.image(ImageRequest(prompt=full_prompt, size="1024x1024", quality="medium"))
        if not resp.b64_json:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Nenhuma imagem retornada pelo provider.",
            )
        img_bytes = base64.b64decode(resp.b64_json)
        img_id = str(uuid.uuid4())
        url = get_storage().save(f"scenes/{img_id}.png", img_bytes)
        return SceneCandidate(id=img_id, url=url, notes=variant_id)

    results: list[SceneCandidate] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_generate_one, vid, vsuffix): vid
            for vid, vsuffix in _SCENE_VARIANTS
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda c: [v[0] for v in _SCENE_VARIANTS].index(c.notes))
    return results
