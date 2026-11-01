"""Endpoint de teste de voz (MiniMax ou sumi-tts local) e catálogo de vozes de narração."""
import uuid

import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.ai import tts_server
from prompt_clinica.ai.minimax import MinimaxError
from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.voice import VoiceCreate, VoiceOut, VoiceUpdate
from prompt_clinica.services import voice_service

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceTestBody(BaseModel):
    text: str
    voice_id: str = ""


@router.post("/test")
def test_voice(
    body: VoiceTestBody,
    user: User = Depends(get_current_user),
) -> Response:
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Texto vazio.")
    try:
        audio = tts_server.synthesize(text, body.voice_id)
    except (MinimaxError, ValueError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Voz: {exc}"
        ) from exc
    return Response(content=audio, media_type="audio/mpeg")


@router.get("", response_model=list[VoiceOut])
def list_voices(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[VoiceOut]:
    return [VoiceOut.model_validate(v) for v in voice_service.list_all(user, db)]


@router.post("", status_code=201, response_model=VoiceOut)
def create_voice(
    req: VoiceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceOut:
    return VoiceOut.model_validate(voice_service.create(req, user, db))


@router.patch("/{voice_id}", response_model=VoiceOut)
def update_voice(
    voice_id: uuid.UUID,
    req: VoiceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceOut:
    return VoiceOut.model_validate(voice_service.update(voice_id, req, user, db))


@router.delete("/{voice_id}", status_code=204)
def delete_voice(
    voice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    voice_service.delete(voice_id, user, db)
