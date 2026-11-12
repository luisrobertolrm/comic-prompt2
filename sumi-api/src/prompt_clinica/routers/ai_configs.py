from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_admin
from prompt_clinica.schemas.ai_config import (
    ActiveIn,
    AIConfigIn,
    AIConfigOut,
    AIConfigUpdate,
    ImageTestOut,
    TextTestOut,
    TranscriptionTestOut,
    VideoTestOut,
    VoiceTestOut,
)
from prompt_clinica.services import ai_config_service

router = APIRouter(prefix="/admin/ai-configs", tags=["admin"])


@router.get("/{ai_type}", response_model=list[AIConfigOut])
def list_configs(
    ai_type: str,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AIConfigOut]:
    return ai_config_service.list_configs(ai_type, db)


@router.post("/{ai_type}", status_code=201, response_model=AIConfigOut)
def create_config(
    ai_type: str,
    data: AIConfigIn,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AIConfigOut:
    return ai_config_service.create_config(ai_type, data, db)


@router.put("/{ai_type}/{config_id}", response_model=AIConfigOut)
def update_config(
    ai_type: str,
    config_id: int,
    data: AIConfigUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AIConfigOut:
    return ai_config_service.update_config(ai_type, config_id, data, db)


@router.patch("/{ai_type}/{config_id}/active", response_model=list[AIConfigOut])
def set_active(
    ai_type: str,
    config_id: int,
    data: ActiveIn,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AIConfigOut]:
    return ai_config_service.set_active(ai_type, config_id, data.active, db)


@router.delete("/{ai_type}/{config_id}", status_code=204)
def delete_config(
    ai_type: str,
    config_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    ai_config_service.delete_config(ai_type, config_id, db)


@router.post("/text/{config_id}/test", response_model=TextTestOut)
def test_text(
    config_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TextTestOut:
    return ai_config_service.test_text(config_id, db)


@router.post("/image/{config_id}/test", response_model=ImageTestOut)
def test_image(
    config_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ImageTestOut:
    return ai_config_service.test_image(config_id, db)


@router.post("/transcription/{config_id}/test", response_model=TranscriptionTestOut)
def test_transcription(
    config_id: int,
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TranscriptionTestOut:
    audio = file.file.read()
    return ai_config_service.test_transcription(config_id, audio, file.filename or "audio.webm", db)


@router.post("/voice/{config_id}/test", response_model=VoiceTestOut)
def test_voice(
    config_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> VoiceTestOut:
    return ai_config_service.test_voice(config_id, db)


@router.post("/video/{config_id}/test", response_model=VideoTestOut)
def test_video(
    config_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> VideoTestOut:
    return ai_config_service.test_video(config_id, db)
