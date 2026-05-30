from __future__ import annotations

import prompt_clinica._paths  # noqa: F401
from sqlalchemy.orm import Session

from character import Character
from prompt_clinica.schemas.character import CharacterCreate
from user import User


def list_all(user: User, db: Session) -> list[Character]:
    return (
        db.query(Character)
        .filter(Character.user_id == user.id)
        .order_by(Character.updated_at.desc())
        .all()
    )


def list_recent(user: User, db: Session, limit: int = 8) -> list[Character]:
    return list_all(user, db)[:limit]


def create(req: CharacterCreate, user: User, db: Session) -> Character:
    char = Character(
        user_id=user.id,
        name=req.name.strip(),
        role=req.role,
        age=req.age,
        height=req.height,
        summary=req.summary,
        outfit=req.outfit,
        traits=", ".join(req.traits) if req.traits else None,
        approved=True,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char
