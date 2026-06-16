import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.series import (
    ProjectIdsBody,
    SeriesCreate,
    SeriesOut,
    SeriesUpdate,
)
from prompt_clinica.services import series_service

router = APIRouter(prefix="/series", tags=["series"])


@router.get("", response_model=list[SeriesOut])
def list_series(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SeriesOut]:
    return series_service.list_series(user, db)


@router.post("", status_code=201, response_model=SeriesOut)
def create_series(
    req: SeriesCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SeriesOut:
    return series_service.create(req, user, db)


@router.get("/{series_id}", response_model=SeriesOut)
def get_series(
    series_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SeriesOut:
    return series_service.get_by_id(series_id, user, db)


@router.patch("/{series_id}", response_model=SeriesOut)
def update_series(
    series_id: uuid.UUID,
    patch: SeriesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SeriesOut:
    return series_service.update(series_id, patch, user, db)


@router.delete("/{series_id}", status_code=204)
def delete_series(
    series_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    series_service.delete(series_id, user, db)


@router.put("/{series_id}/projects", status_code=204)
def set_projects(
    series_id: uuid.UUID,
    body: ProjectIdsBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    series_service.set_projects(series_id, body.project_ids, user, db)
