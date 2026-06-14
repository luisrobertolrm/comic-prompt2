from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from temp_portrait import TempPortrait
from user import User

from prompt_clinica.database import SessionLocal, get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.character import (
    CharacterCreate,
    CharacterOut,
    CharacterUpdate,
    DeleteUnusedBody,
    PortraitCandidate,
    PortraitJobOut,
    PortraitRequest,
)
from prompt_clinica.services import character_service
from prompt_clinica.storage import get_storage

logger = logging.getLogger("sumi.api")

router = APIRouter(prefix="/characters", tags=["characters"])


@dataclass
class _PortraitJob:
    status: str = "pending"
    portraits: list[PortraitCandidate] = field(default_factory=list)
    detail: str = ""


_jobs: dict[str, _PortraitJob] = {}
_lock = threading.Lock()


def _cleanup_old_portraits(user_id: str) -> None:
    with SessionLocal() as db:
        old = db.query(TempPortrait).filter(TempPortrait.user_id == uuid.UUID(user_id)).all()
        for p in old:
            get_storage().delete(p.storage_key)
            db.delete(p)
        db.commit()


def _save_portraits_to_db(user_id: str, portraits: list[PortraitCandidate]) -> None:
    with SessionLocal() as db:
        for p in portraits:
            storage_key = p.url.removeprefix("/storage/")
            record = TempPortrait(
                user_id=uuid.UUID(user_id),
                storage_key=storage_key,
                url=p.url,
                variant=p.notes,
            )
            db.add(record)
        db.commit()


def _run_job(
    job_id: str,
    user_id: str,
    style: str,
    color_mode: str | None,
    gender: str | None,
    age_range: str | None,
    ethnicity: str | None,
    hair: str | None,
    extra: str | None,
    prompt: str,
    raw: bool,
) -> None:
    _cleanup_old_portraits(user_id)
    with _lock:
        _jobs[job_id].status = "running"
    try:
        portraits = character_service.generate_portrait(
            style, color_mode, gender, age_range, ethnicity, hair, extra, prompt, raw
        )
        _save_portraits_to_db(user_id, portraits)
        with _lock:
            _jobs[job_id].portraits = portraits
            _jobs[job_id].status = "done"
    except Exception as exc:  # noqa: BLE001
        with _lock:
            _jobs[job_id].detail = str(exc)
            _jobs[job_id].status = "error"


@router.get("", response_model=list[CharacterOut])
def list_characters(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CharacterOut]:
    return [CharacterOut.model_validate(c) for c in character_service.list_all(user, db)]


@router.post("", status_code=201, response_model=CharacterOut)
def create_character(
    req: CharacterCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CharacterOut:
    char = character_service.create(req, user, db)
    # Apaga do S3 os candidatos não escolhidos e limpa a tabela temp
    all_temps = db.query(TempPortrait).filter(TempPortrait.user_id == user.id).all()
    for tp in all_temps:
        if tp.url != req.image_url:
            get_storage().delete(tp.storage_key)
        db.delete(tp)
    db.commit()
    return CharacterOut.model_validate(char)


@router.post("/delete-unused")
def delete_unused_characters(
    body: DeleteUnusedBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return {"deleted": character_service.delete_unused(body.ids, user, db)}


@router.patch("/{character_id}", response_model=CharacterOut)
def update_character(
    character_id: uuid.UUID,
    req: CharacterUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CharacterOut:
    char = character_service.update(character_id, req, user, db)
    # Apaga do S3 os candidatos não escolhidos e limpa a tabela temp
    all_temps = db.query(TempPortrait).filter(TempPortrait.user_id == user.id).all()
    for tp in all_temps:
        if tp.url != req.image_url:
            get_storage().delete(tp.storage_key)
        db.delete(tp)
    db.commit()
    return CharacterOut.model_validate(char)


@router.post("/generate-portrait", status_code=202, response_model=PortraitJobOut)
def generate_portrait(
    req: PortraitRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> PortraitJobOut:
    logger.info(
        "generate-portrait recebido: style=%r color_mode=%r gender=%r age=%r ethnicity=%r hair=%r raw=%s",
        req.style, req.color_mode, req.gender, req.age_range, req.ethnicity, req.hair, req.raw,
    )
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = _PortraitJob()
    background_tasks.add_task(
        _run_job,
        job_id,
        str(user.id),
        req.style,
        req.color_mode,
        req.gender,
        req.age_range,
        req.ethnicity,
        req.hair,
        req.extra,
        req.prompt,
        req.raw,
    )
    return PortraitJobOut(job_id=job_id, status="pending")


@router.get("/portrait-job/{job_id}", response_model=PortraitJobOut)
def get_portrait_job(
    job_id: str,
    user: User = Depends(get_current_user),
) -> PortraitJobOut:
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job não encontrado.")
    return PortraitJobOut(
        job_id=job_id,
        status=job.status,
        portraits=job.portraits,
        detail=job.detail,
    )
