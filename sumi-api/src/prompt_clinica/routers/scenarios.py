from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from temp_portrait import TempPortrait
from user import User

from prompt_clinica.ai.scenario_agent import (
    ScenarioIntentResult,
    ScenarioIntentRouter,
    build_scenario_router,
)
from prompt_clinica.database import SessionLocal, get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.scenario import (
    DeleteUnusedBody,
    ScenarioCreate,
    ScenarioOut,
    ScenarioUpdate,
    SceneCandidate,
    SceneJobOut,
    SceneRequest,
)
from prompt_clinica.schemas.text import TextIn
from prompt_clinica.services import scenario_service
from prompt_clinica.storage import get_storage

logger = logging.getLogger("sumi.api")

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@dataclass
class _SceneJob:
    status: str = "pending"
    scenes: list[SceneCandidate] = field(default_factory=list)
    detail: str = ""


_jobs: dict[str, _SceneJob] = {}
_lock = threading.Lock()


def _cleanup_old_scenes(user_id: str) -> None:
    with SessionLocal() as db:
        old = db.query(TempPortrait).filter(TempPortrait.user_id == uuid.UUID(user_id)).all()
        for p in old:
            get_storage().delete(p.storage_key)
            db.delete(p)
        db.commit()


def _save_scenes_to_db(user_id: str, scenes: list[SceneCandidate]) -> None:
    with SessionLocal() as db:
        for s in scenes:
            storage_key = s.url.removeprefix("/storage/")
            record = TempPortrait(
                user_id=uuid.UUID(user_id),
                storage_key=storage_key,
                url=s.url,
                variant=s.notes,
            )
            db.add(record)
        db.commit()


def _run_job(
    job_id: str,
    user_id: str,
    style: str,
    color_mode: str | None,
    location: str | None,
    time_of_day: str | None,
    weather: str | None,
    atmosphere: str | None,
    extra: str | None,
    prompt: str,
    raw: bool,
) -> None:
    _cleanup_old_scenes(user_id)
    with _lock:
        _jobs[job_id].status = "running"
    try:
        scenes = scenario_service.generate_scene(
            style, color_mode, location, time_of_day, weather, atmosphere, extra, prompt, raw
        )
        _save_scenes_to_db(user_id, scenes)
        with _lock:
            _jobs[job_id].scenes = scenes
            _jobs[job_id].status = "done"
    except Exception as exc:  # noqa: BLE001
        with _lock:
            _jobs[job_id].detail = str(exc)
            _jobs[job_id].status = "error"


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ScenarioOut]:
    return [ScenarioOut.model_validate(s) for s in scenario_service.list_all(user, db)]


@router.post("/ai-draft", response_model=ScenarioIntentResult)
def ai_draft(
    req: TextIn,
    _user: User = Depends(get_current_user),
    intent_router: ScenarioIntentRouter = Depends(build_scenario_router),
) -> ScenarioIntentResult:
    try:
        return intent_router.route(req.text)
    except Exception as exc:
        logger.exception("Falha ao gerar cenário por IA")
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=f"A IA de texto não conseguiu interpretar a descrição: {exc}",
        ) from exc


@router.post("", status_code=201, response_model=ScenarioOut)
def create_scenario(
    req: ScenarioCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioOut:
    scenario = scenario_service.create(req, user, db)
    all_temps = db.query(TempPortrait).filter(TempPortrait.user_id == user.id).all()
    for tp in all_temps:
        if tp.url != req.image_url:
            get_storage().delete(tp.storage_key)
        db.delete(tp)
    db.commit()
    return ScenarioOut.model_validate(scenario)


@router.post("/delete-unused")
def delete_unused_scenarios(
    body: DeleteUnusedBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return {"deleted": scenario_service.delete_unused(body.ids, user, db)}


@router.patch("/{scenario_id}", response_model=ScenarioOut)
def update_scenario(
    scenario_id: uuid.UUID,
    req: ScenarioUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioOut:
    scenario = scenario_service.update(scenario_id, req, user, db)
    all_temps = db.query(TempPortrait).filter(TempPortrait.user_id == user.id).all()
    for tp in all_temps:
        if tp.url != req.image_url:
            get_storage().delete(tp.storage_key)
        db.delete(tp)
    db.commit()
    return ScenarioOut.model_validate(scenario)


@router.post("/generate-scene", status_code=202, response_model=SceneJobOut)
def generate_scene(
    req: SceneRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> SceneJobOut:
    logger.info(
        "generate-scene recebido: style=%r color_mode=%r location=%r time=%r weather=%r atmosphere=%r raw=%s",
        req.style, req.color_mode, req.location, req.time_of_day, req.weather, req.atmosphere, req.raw,
    )
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = _SceneJob()
    background_tasks.add_task(
        _run_job,
        job_id,
        str(user.id),
        req.style,
        req.color_mode,
        req.location,
        req.time_of_day,
        req.weather,
        req.atmosphere,
        req.extra,
        req.prompt,
        req.raw,
    )
    return SceneJobOut(job_id=job_id, status="pending")


@router.get("/scene-job/{job_id}", response_model=SceneJobOut)
def get_scene_job(
    job_id: str,
    user: User = Depends(get_current_user),
) -> SceneJobOut:
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job não encontrado.")
    return SceneJobOut(
        job_id=job_id,
        status=job.status,
        scenes=job.scenes,
        detail=job.detail,
    )
