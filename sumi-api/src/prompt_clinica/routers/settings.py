from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.settings import (
    LocalAiModelsOut,
    SettingsOut,
    SettingsUpdate,
)
from prompt_clinica.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettingsOut:
    return settings_service.get_settings(user, db)


@router.put("", response_model=SettingsOut)
def update_settings(
    patch: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettingsOut:
    return settings_service.update_settings(patch, user, db)


@router.get("/local-ai/models", response_model=LocalAiModelsOut)
def list_local_models(
    url: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LocalAiModelsOut:
    target = url or settings_service.get_settings(user, db).local_ai_url
    return LocalAiModelsOut(models=settings_service.list_local_models(target))
