from __future__ import annotations

import base64
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import prompt_clinica._paths  # noqa: F401
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from character import Character
from prompt_clinica.ai import ImageRequest, ai
from prompt_clinica.config import settings
from prompt_clinica.schemas.character import CharacterCreate, PortraitCandidate
from user import User

_PORTRAIT_VARIANTS = [
    ("frontal", "Frontal portrait, neutral expression, looking directly at viewer"),
    ("perfil", "Three-quarter view, gentle smile, soft lighting from the side"),
    ("reflexivo", "Side profile, pensive expression, looking into the distance"),
    ("determinado", "Close-up face, determined expression, intense gaze"),
]


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
        image_url=req.image_url,
        approved=True,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char


def generate_portrait(prompt: str) -> list[PortraitCandidate]:
    portraits_dir = Path(settings.images_dir) / "portraits"
    portraits_dir.mkdir(parents=True, exist_ok=True)

    base_prompt = (
        "Manga shojo character portrait, black and white screentone, "
        "clean ink line art, no text, no speech bubbles, no background, "
        "expressive eyes, high contrast, detailed face. "
        f"Character: {prompt}. "
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
        (portraits_dir / f"{img_id}.png").write_bytes(img_bytes)
        return PortraitCandidate(
            id=img_id,
            url=f"/static/images/portraits/{img_id}.png",
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
