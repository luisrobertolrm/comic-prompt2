from __future__ import annotations

import logging

import prompt_clinica._paths  # noqa: F401
from app_settings import AppSettings
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from prompt_clinica.ai import build_default, env_ai_config, reload_ai
from prompt_clinica.config import settings
from prompt_clinica.database import SessionLocal
from prompt_clinica.schemas.app_settings import AppSettingsOut, AppSettingsValues

logger = logging.getLogger(__name__)

_FIELDS = tuple(AppSettingsValues.model_fields)


def _get_row(db: Session) -> AppSettings:
    row = db.get(AppSettings, 1)
    if row is None:
        row = AppSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _values(row: AppSettings) -> AppSettingsValues:
    return AppSettingsValues(**{f: getattr(row, f) for f in _FIELDS})


def _defaults() -> AppSettingsValues:
    return AppSettingsValues(
        **env_ai_config(),
        stt_model=settings.stt_model,
        stt_language=settings.stt_language,
    )


def get_app_settings(db: Session) -> AppSettingsOut:
    return AppSettingsOut(values=_values(_get_row(db)), defaults=_defaults())


def update_app_settings(data: AppSettingsValues, db: Session) -> AppSettingsOut:
    clean = {f: getattr(data, f).strip() for f in _FIELDS}
    try:
        provider = build_default(clean)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuração de IA inválida: {exc}",
        ) from exc
    row = _get_row(db)
    for f, v in clean.items():
        setattr(row, f, v)
    db.commit()
    db.refresh(row)
    reload_ai(provider)
    return AppSettingsOut(values=_values(row), defaults=_defaults())


def stt_config(db: Session) -> tuple[str, str]:
    """(modelo, idioma) efetivos da transcrição de voz."""
    row = _get_row(db)
    return (row.stt_model or settings.stt_model, row.stt_language or settings.stt_language)


def apply_from_db() -> None:
    """Na subida da API: aplica ao `ai` o que estiver salvo no app_settings."""
    try:
        with SessionLocal() as db:
            values = _values(_get_row(db))
        reload_ai(build_default(values.model_dump()))
    except Exception:
        logger.exception("app_settings não aplicado; usando apenas o .env.")
