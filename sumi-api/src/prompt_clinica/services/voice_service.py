from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from narration_voice import NarrationVoice
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.schemas.voice import VoiceCreate, VoiceUpdate


def list_all(user: User, db: Session) -> list[NarrationVoice]:
    return (
        db.query(NarrationVoice)
        .filter(NarrationVoice.user_id == user.id)
        .order_by(NarrationVoice.name.asc())
        .all()
    )


def create(req: VoiceCreate, user: User, db: Session) -> NarrationVoice:
    voice = NarrationVoice(
        user_id=user.id,
        name=req.name.strip(),
        voice_id=req.voice_id.strip(),
        age_start=req.age_start,
        age_end=req.age_end,
        sex=req.sex,
        details=req.details,
    )
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return voice


def update(voice_id: uuid.UUID, req: VoiceUpdate, user: User, db: Session) -> NarrationVoice:
    voice = (
        db.query(NarrationVoice)
        .filter(NarrationVoice.id == voice_id, NarrationVoice.user_id == user.id)
        .first()
    )
    if voice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voz não encontrada.")

    data = req.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key in ("name", "voice_id") and value is not None:
            setattr(voice, key, value.strip())
        else:
            setattr(voice, key, value)

    db.commit()
    db.refresh(voice)
    return voice


def delete(voice_id: uuid.UUID, user: User, db: Session) -> None:
    voice = (
        db.query(NarrationVoice)
        .filter(NarrationVoice.id == voice_id, NarrationVoice.user_id == user.id)
        .first()
    )
    if voice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voz não encontrada.")
    db.delete(voice)
    db.commit()
