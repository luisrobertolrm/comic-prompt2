from __future__ import annotations

import random
import uuid

import prompt_clinica._paths  # noqa: F401
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from character import Character
from project import Project
from project_character import ProjectCharacter
from project_scenario import ProjectScenario
from prompt_clinica.ai.synopsis import generate_synopsis as ai_generate_synopsis
from prompt_clinica.schemas.character import CharacterOut
from prompt_clinica.schemas.project import ProjectCreate, ProjectDetailOut, ProjectOut, ProjectPatch
from prompt_clinica.schemas.scenario import ScenarioOut
from scenario import Scenario
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
    scenarios = _list_scenarios(project_id, db)
    return ProjectDetailOut(
        **ProjectOut.model_validate(project).model_dump(),
        premise=project.premise,
        synopsis=project.synopsis,
        characters=[CharacterOut.model_validate(c) for c in chars],
        scenarios=[ScenarioOut.model_validate(s) for s in scenarios],
    )


def create(req: ProjectCreate, user: User, db: Session) -> Project:
    title = req.title.strip() or "Novo projeto"
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
        narrator_voice_id=req.narrator_voice_id,
        cover_accent=random.choice(_ACCENTS),
        cover_tone=random.choice(_TONES),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update(project_id: uuid.UUID, patch: ProjectPatch, user: User, db: Session) -> Project:
    project: Project | None = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    if patch.title is not None:
        project.title = patch.title.strip() or project.title
    if patch.premise is not None:
        project.premise = patch.premise
    if patch.synopsis is not None:
        project.synopsis = patch.synopsis
    if patch.genre is not None:
        project.genre = patch.genre
    if patch.tone is not None:
        project.tone = patch.tone
    if patch.pages is not None:
        project.pages = patch.pages
    if patch.style is not None:
        project.style = patch.style
    if patch.color_mode is not None:
        project.color_mode = patch.color_mode
    if "narrator_voice_id" in patch.model_fields_set:
        project.narrator_voice_id = patch.narrator_voice_id
    if patch.synopsis_temperature is not None:
        project.synopsis_temperature = patch.synopsis_temperature
    if patch.panels_temperature is not None:
        project.panels_temperature = patch.panels_temperature
    if patch.genre is not None or patch.pages is not None:
        g = project.genre
        project.subtitle = f"{g.lower()} · {project.pages * 3}–{project.pages * 4} quadros"
    db.commit()
    db.refresh(project)
    return project


def generate_synopsis(project_id: uuid.UUID, user: User, db: Session) -> ProjectDetailOut:
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

    text = ai_generate_synopsis(
        premise=project.premise or project.title,
        genre=project.genre,
        tone=project.tone,
        character_names=[c.name for c in chars],
        temperature=project.synopsis_temperature,
    )
    if not text:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Geração de sinopse falhou.",
        )

    project.synopsis = text[:6000]
    db.commit()
    db.refresh(project)
    scenarios = _list_scenarios(project_id, db)
    return ProjectDetailOut(
        **ProjectOut.model_validate(project).model_dump(),
        premise=project.premise,
        synopsis=project.synopsis,
        characters=[CharacterOut.model_validate(c) for c in chars],
        scenarios=[ScenarioOut.model_validate(s) for s in scenarios],
    )


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


def _list_scenarios(project_id: uuid.UUID, db: Session) -> list[Scenario]:
    return (
        db.query(Scenario)
        .join(ProjectScenario, ProjectScenario.scenario_id == Scenario.id)
        .filter(ProjectScenario.project_id == project_id)
        .all()
    )


def set_scenarios(
    project_id: uuid.UUID,
    scenario_ids: list[uuid.UUID],
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
    db.query(ProjectScenario).filter(ProjectScenario.project_id == project_id).delete()
    for scenario_id in scenario_ids:
        db.add(ProjectScenario(project_id=project_id, scenario_id=scenario_id))
    db.commit()
