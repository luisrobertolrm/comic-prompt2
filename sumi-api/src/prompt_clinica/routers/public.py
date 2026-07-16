import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from panel import Panel
from project import Project
from recomendacao import RecomendacaoNegativa, RecomendacaoPositiva
from sqlalchemy import func
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user, get_current_user_optional
from prompt_clinica.schemas.panel import panel_to_out
from prompt_clinica.schemas.project import (
    PublicProjectDetailOut,
    PublicProjectOut,
    ReactionIn,
    ReactionOut,
)
from prompt_clinica.services import recommendation_service

router = APIRouter(prefix="/public", tags=["public"])


def _public_out(
    project: Project,
    author_name: str,
    positivas: int = 0,
    negativas: int = 0,
    cover_image_url: str | None = None,
) -> PublicProjectOut:
    return PublicProjectOut(
        id=str(project.id),
        title=project.title,
        subtitle=project.subtitle,
        genre=project.genre,
        style=project.style,
        cover_accent=project.cover_accent,
        cover_tone=project.cover_tone,
        video_url=project.video_url,
        author_name=author_name,
        updated_at=project.updated_at,
        quantidade_positiva=positivas,
        quantidade_negativa=negativas,
        cover_image_url=cover_image_url,
    )


def _cover_urls(project_ids: list[uuid.UUID], db: Session) -> dict[uuid.UUID, str]:
    if not project_ids:
        return {}
    rows = (
        db.query(Panel.project_id, Panel.image_url)
        .filter(Panel.project_id.in_(project_ids), Panel.image_url.isnot(None))
        .order_by(Panel.project_id, Panel.index_order)
        .all()
    )
    covers: dict[uuid.UUID, str] = {}
    for project_id, image_url in rows:
        covers.setdefault(project_id, image_url)
    return covers


def _tamanho(rank: int, positivas: int) -> int:
    if positivas <= 0:
        return 1
    if rank == 0:
        return 3
    if rank <= 2:
        return 2
    return 1


@router.get("/projects", response_model=list[PublicProjectOut])
def list_public_projects(db: Session = Depends(get_db)) -> list[PublicProjectOut]:
    positivas = func.coalesce(RecomendacaoPositiva.quantidade, 0)
    negativas = func.coalesce(RecomendacaoNegativa.quantidade, 0)
    rows = (
        db.query(Project, User.name, positivas, negativas)
        .join(User, User.id == Project.user_id)
        .outerjoin(RecomendacaoPositiva, RecomendacaoPositiva.project_id == Project.id)
        .outerjoin(RecomendacaoNegativa, RecomendacaoNegativa.project_id == Project.id)
        .filter(Project.status == "Público")
        .order_by(positivas.desc(), Project.updated_at.desc())
        .all()
    )
    covers = _cover_urls([p.id for p, *_ in rows], db)
    out = []
    for rank, (project, name, pos, neg) in enumerate(rows):
        item = _public_out(project, name, pos, neg, covers.get(project.id))
        item.tamanho = _tamanho(rank, pos)
        out.append(item)
    return out


@router.get("/projects/{project_id}", response_model=PublicProjectDetailOut)
def get_public_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> PublicProjectDetailOut:
    row = (
        db.query(Project, User.name)
        .join(User, User.id == Project.user_id)
        .filter(Project.id == project_id, Project.status == "Público")
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    project, author_name = row
    panels = (
        db.query(Panel)
        .filter(Panel.project_id == project_id)
        .order_by(Panel.index_order)
        .all()
    )
    pos, neg = recommendation_service.counters(project_id, db)
    return PublicProjectDetailOut(
        **_public_out(project, author_name, pos, neg).model_dump(),
        panels=[panel_to_out(p) for p in panels],
        minha_reacao=(
            recommendation_service.user_reaction(project_id, user.id, db) if user else None
        ),
    )


@router.post("/projects/{project_id}/reaction", response_model=ReactionOut)
def react_to_project(
    project_id: uuid.UUID,
    body: ReactionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReactionOut:
    return recommendation_service.react(project_id, body.positivo, user, db)
