from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from project import Project
from recomendacao import RecomendacaoNegativa, RecomendacaoPositiva, RecomendacaoUsuario
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from user import User

import prompt_clinica._paths  # noqa: F401
from prompt_clinica.schemas.project import ReactionOut

_COUNTER = {True: RecomendacaoPositiva, False: RecomendacaoNegativa}


def _increment(positivo: bool, project_id: uuid.UUID, db: Session) -> None:
    model = _COUNTER[positivo]
    stmt = pg_insert(model).values(project_id=project_id, quantidade=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=["project_id"],
        set_={"quantidade": model.quantidade + 1},
    )
    db.execute(stmt)


def _decrement(positivo: bool, project_id: uuid.UUID, db: Session) -> None:
    model = _COUNTER[positivo]
    db.query(model).filter(model.project_id == project_id).update(
        {"quantidade": func.greatest(model.quantidade - 1, 0)}
    )


def counters(project_id: uuid.UUID, db: Session) -> tuple[int, int]:
    pos = (
        db.query(RecomendacaoPositiva.quantidade)
        .filter(RecomendacaoPositiva.project_id == project_id)
        .scalar()
    )
    neg = (
        db.query(RecomendacaoNegativa.quantidade)
        .filter(RecomendacaoNegativa.project_id == project_id)
        .scalar()
    )
    return pos or 0, neg or 0


def user_reaction(project_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> bool | None:
    row: RecomendacaoUsuario | None = db.get(RecomendacaoUsuario, (user_id, project_id))
    return row.positivo if row else None


def react(project_id: uuid.UUID, positivo: bool, user: User, db: Session) -> ReactionOut:
    exists = (
        db.query(Project.id)
        .filter(Project.id == project_id, Project.status == "Público")
        .first()
    )
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")

    reacao: RecomendacaoUsuario | None = db.get(RecomendacaoUsuario, (user.id, project_id))
    try:
        if reacao is None:
            db.add(RecomendacaoUsuario(user_id=user.id, project_id=project_id, positivo=positivo))
            _increment(positivo, project_id, db)
            minha_reacao: bool | None = positivo
        elif reacao.positivo == positivo:
            db.delete(reacao)
            _decrement(positivo, project_id, db)
            minha_reacao = None
        else:
            _decrement(reacao.positivo, project_id, db)
            reacao.positivo = positivo
            reacao.created_at = datetime.now(UTC)
            _increment(positivo, project_id, db)
            minha_reacao = positivo
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tente novamente.")

    pos, neg = counters(project_id, db)
    return ReactionOut(quantidade_positiva=pos, quantidade_negativa=neg, minha_reacao=minha_reacao)
