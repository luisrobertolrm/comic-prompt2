from __future__ import annotations

import uuid

import prompt_clinica._paths  # noqa: F401
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from project import Project
from prompt_clinica.schemas.series import SeriesCreate, SeriesOut, SeriesUpdate
from series import Series
from series_project import SeriesProject
from user import User


def _project_ids(series_id: uuid.UUID, db: Session) -> list[uuid.UUID]:
    rows = (
        db.query(SeriesProject.project_id)
        .filter(SeriesProject.series_id == series_id)
        .all()
    )
    return [r[0] for r in rows]


def _to_out(series: Series, db: Session) -> SeriesOut:
    return SeriesOut(
        id=series.id,
        name=series.name,
        description=series.description,
        project_ids=_project_ids(series.id, db),
        updated_at=series.updated_at,
    )


def _get_owned(series_id: uuid.UUID, user: User, db: Session) -> Series:
    series: Series | None = (
        db.query(Series)
        .filter(Series.id == series_id, Series.user_id == user.id)
        .first()
    )
    if series is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Série não encontrada.")
    return series


def list_series(user: User, db: Session) -> list[SeriesOut]:
    series = (
        db.query(Series)
        .filter(Series.user_id == user.id)
        .order_by(Series.updated_at.desc())
        .all()
    )
    return [_to_out(s, db) for s in series]


def get_by_id(series_id: uuid.UUID, user: User, db: Session) -> SeriesOut:
    return _to_out(_get_owned(series_id, user, db), db)


def create(req: SeriesCreate, user: User, db: Session) -> SeriesOut:
    series = Series(user_id=user.id, name=req.name, description=req.description)
    db.add(series)
    db.commit()
    db.refresh(series)
    return _to_out(series, db)


def update(series_id: uuid.UUID, patch: SeriesUpdate, user: User, db: Session) -> SeriesOut:
    series = _get_owned(series_id, user, db)
    if patch.name is not None:
        series.name = patch.name
    if "description" in patch.model_fields_set:
        series.description = patch.description
    db.commit()
    db.refresh(series)
    return _to_out(series, db)


def delete(series_id: uuid.UUID, user: User, db: Session) -> None:
    series = _get_owned(series_id, user, db)
    db.delete(series)
    db.commit()


def set_projects(
    series_id: uuid.UUID,
    project_ids: list[uuid.UUID],
    user: User,
    db: Session,
) -> None:
    _get_owned(series_id, user, db)
    owned = {
        p.id
        for p in db.query(Project.id).filter(
            Project.id.in_(project_ids), Project.user_id == user.id
        )
    } if project_ids else set()
    db.query(SeriesProject).filter(SeriesProject.series_id == series_id).delete()
    for project_id in project_ids:
        if project_id in owned:
            db.add(SeriesProject(series_id=series_id, project_id=project_id))
    db.commit()
