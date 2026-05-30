from __future__ import annotations

import random
import uuid

import prompt_clinica._paths  # noqa: F401
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from character import Character
from project import Project
from project_character import ProjectCharacter
from prompt_clinica.schemas.character import CharacterOut
from prompt_clinica.schemas.project import ProjectCreate, ProjectDetailOut, ProjectOut
from user import User

_ACCENTS = ["accent", "mint", "peach", "blush", "lilac"]
_TONES = ["dots", "diag", "dense"]


def list_projects(user: User, db: Session) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.user_id == user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )


def get_by_id(project_id: uuid.UUID, user: User, db: Session) -> ProjectDetailOut:
    project: Project | None = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    chars = (
        db.query(Character)
        .join(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(ProjectCharacter.project_id == project_id)
        .all()
    )
    return ProjectDetailOut(
        **ProjectOut.model_validate(project).model_dump(),
        premise=project.premise,
        characters=[CharacterOut.model_validate(c) for c in chars],
    )


def create(req: ProjectCreate, user: User, db: Session) -> Project:
    title = req.premise[:60].strip() or "Novo projeto"
    subtitle = f"{req.genre.lower()} · {req.pages * 3}–{req.pages * 4} quadros"
    project = Project(
        user_id=user.id,
        title=title,
        subtitle=subtitle,
        genre=req.genre,
        tone=req.tone,
        pages=req.pages,
        language=req.language,
        style=req.style,
        premise=req.premise,
        cover_accent=random.choice(_ACCENTS),
        cover_tone=random.choice(_TONES),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def set_characters(
    project_id: uuid.UUID,
    char_ids: list[uuid.UUID],
    user: User,
    db: Session,
) -> None:
    project: Project | None = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    db.query(ProjectCharacter).filter(ProjectCharacter.project_id == project_id).delete()
    for char_id in char_ids:
        db.add(ProjectCharacter(project_id=project_id, character_id=char_id))
    db.commit()
