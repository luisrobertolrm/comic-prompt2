from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.character import (
    CharacterCreate,
    CharacterOut,
    PortraitCandidate,
    PortraitJobOut,
    PortraitRequest,
)
from prompt_clinica.services import character_service
from user import User

router = APIRouter(prefix="/characters", tags=["characters"])


@dataclass
class _PortraitJob:
    status: str = "pending"
    portraits: list[PortraitCandidate] = field(default_factory=list)
    detail: str = ""


_jobs: dict[str, _PortraitJob] = {}
_lock = threading.Lock()


def _run_job(job_id: str, prompt: str) -> None:
    with _lock:
        _jobs[job_id].status = "running"
    try:
        portraits = character_service.generate_portrait(prompt)
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
    return CharacterOut.model_validate(character_service.create(req, user, db))


@router.post("/generate-portrait", status_code=202, response_model=PortraitJobOut)
def generate_portrait(
    req: PortraitRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> PortraitJobOut:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = _PortraitJob()
    background_tasks.add_task(_run_job, job_id, req.prompt)
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
