import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.ai.speech import transcribe
from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.app_settings import TranscriptionOut
from prompt_clinica.services import app_settings_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech", tags=["speech"])

_MAX_BYTES = 25 * 1024 * 1024  # limite da API de transcrição da OpenAI


@router.post("/transcribe", response_model=TranscriptionOut)
def transcribe_audio(
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TranscriptionOut:
    audio = file.file.read()
    if not audio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Áudio vazio.")
    if len(audio) > _MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Áudio acima de 25 MB.")
    model, language = app_settings_service.stt_config(db)
    try:
        text = transcribe(audio, file.filename or "audio.webm", model, language)
    except Exception as exc:
        logger.exception("Falha na transcrição")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao transcrever o áudio: {exc}",
        ) from exc
    return TranscriptionOut(text=text)
