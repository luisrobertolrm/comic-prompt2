from __future__ import annotations

import base64
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from character import Character
from fastapi import HTTPException, status
from project_character import ProjectCharacter
from sqlalchemy import func
from sqlalchemy.orm import Session
from user import User

import prompt_clinica._paths  # noqa: F401
from prompt_clinica import styles
from prompt_clinica.ai import ImageRequest, ai
from prompt_clinica.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    PortraitCandidate,
)
from prompt_clinica.storage import get_storage

_PORTRAIT_VARIANTS = [
    ("frontal", "Frontal portrait, neutral expression, looking directly at viewer"),
    ("perfil", "Three-quarter view, gentle smile, soft lighting from the side"),
]


def _count_projects(char_id: uuid.UUID, db: Session) -> int:
    return (
        db.query(func.count(ProjectCharacter.project_id))
        .filter(ProjectCharacter.character_id == char_id)
        .scalar()
        or 0
    )


def list_all(user: User, db: Session) -> list[Character]:
    rows = (
        db.query(Character, func.count(ProjectCharacter.character_id))
        .outerjoin(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(Character.user_id == user.id)
        .group_by(Character.id)
        .order_by(Character.updated_at.desc())
        .all()
    )
    result: list[Character] = []
    for char, count in rows:
        char.project_count = count
        result.append(char)
    return result


def list_recent(user: User, db: Session, limit: int = 8) -> list[Character]:
    return list_all(user, db)[:limit]


def create(req: CharacterCreate, user: User, db: Session) -> Character:
    char = Character(
        user_id=user.id,
        name=req.name.strip(),
        role=req.role,
        gender=req.gender,
        age=req.age,
        height=req.height,
        summary=req.summary,
        outfit=req.outfit,
        traits=", ".join(req.traits) if req.traits else None,
        style=req.style,
        image_url=req.image_url,
        narrator_voice_id=req.narrator_voice_id,
        approved=True,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    char.project_count = 0
    return char


def update(char_id: uuid.UUID, req: CharacterUpdate, user: User, db: Session) -> Character:
    char = (
        db.query(Character)
        .filter(Character.id == char_id, Character.user_id == user.id)
        .first()
    )
    if char is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personagem não encontrado.")

    data = req.model_dump(exclude_unset=True)

    if "image_url" in data and data["image_url"] != char.image_url and char.image_url:
        old_key = char.image_url.split("/storage/")[-1]
        get_storage().delete(old_key)

    for key, value in data.items():
        if key == "traits":
            char.traits = ", ".join(value) if value else None
        elif key == "name" and value is not None:
            char.name = value.strip()
        else:
            setattr(char, key, value)

    db.commit()
    db.refresh(char)
    char.project_count = _count_projects(char.id, db)
    return char


def _delete_portrait_file(image_url: str | None) -> None:
    if not image_url:
        return
    for marker in ("/static/images/", "/storage/"):
        idx = image_url.find(marker)
        if idx != -1:
            get_storage().delete(image_url[idx + len(marker):])
            return


def delete_unused(ids: list[uuid.UUID], user: User, db: Session) -> int:
    """Apaga personagens do usuário sem vínculo a nenhum projeto. Restrito aos ids dados."""
    query = (
        db.query(Character)
        .outerjoin(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(Character.user_id == user.id, ProjectCharacter.character_id.is_(None))
    )
    if ids:
        query = query.filter(Character.id.in_(ids))
    unused = query.all()
    for char in unused:
        _delete_portrait_file(char.image_url)
        db.delete(char)
    db.commit()
    return len(unused)


_GENDER_PROMPT = {
    "Feminino": "female character",
    "Masculino": "male character",
    "Outro": "androgynous character",
    "Não especificado": "",
}


def generate_portrait(
    prompt: str,
    style: str = styles.DEFAULT_STYLE,
    color_mode: str | None = None,
    gender: str | None = None,
) -> list[PortraitCandidate]:
    gender_phrase = _GENDER_PROMPT.get(gender or "", "")
    subject = f"{gender_phrase}, {prompt}" if gender_phrase else prompt
    base_prompt = (
        f"{styles.image_fragment(style)}, {styles.color_fragment(color_mode)}, "
        "character portrait, "
        "no text, no speech bubbles, no background, detailed face. "
        f"Character: {subject}. "
    )

    def _generate_one(variant_id: str, variant_suffix: str) -> PortraitCandidate:
        full_prompt = base_prompt + variant_suffix
        resp = ai.image(ImageRequest(prompt=full_prompt, size="1024x1024", quality="medium"))
        if not resp.b64_json:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Nenhuma imagem retornada pelo provider.",
            )
        img_bytes = base64.b64decode(resp.b64_json)
        img_id = str(uuid.uuid4())
        url = get_storage().save(f"portraits/{img_id}.png", img_bytes)
        return PortraitCandidate(
            id=img_id,
            url=url,
            notes=variant_id,
        )

    results: list[PortraitCandidate] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_generate_one, vid, vsuffix): vid
            for vid, vsuffix in _PORTRAIT_VARIANTS
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda c: [v[0] for v in _PORTRAIT_VARIANTS].index(c.notes))
    return results
