from __future__ import annotations

import logging
import time

import prompt_clinica._paths  # noqa: F401
from app_settings import AppSettings
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from prompt_clinica.ai import (
    ImageRequest,
    ai,
    build_default,
    configure,
    current_config,
    env_ai_config,
)
from prompt_clinica.database import SessionLocal
from prompt_clinica.schemas.app_settings import (
    ApiKeysUpdate,
    ApiKeyStatus,
    AppSettingsOut,
    AppSettingsUpdate,
    AppSettingsValues,
    ImageTestOut,
)
from prompt_clinica.utils.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)

_FIELDS = tuple(AppSettingsValues.model_fields)
_KEYS = tuple(ApiKeysUpdate.model_fields)


def _get_row(db: Session) -> AppSettings:
    row = db.get(AppSettings, 1)
    if row is None:
        row = AppSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _overrides(row: AppSettings) -> dict[str, str]:
    """Valores do banco em texto puro (chaves descriptografadas), no formato do current_config."""
    data = {f: getattr(row, f) for f in _FIELDS}
    data.update({k: decrypt(getattr(row, k)) for k in _KEYS})
    return data


def _hint(value: str) -> str:
    return f"…{value[-4:]}" if len(value) > 4 else "…"


def _out(row: AppSettings) -> AppSettingsOut:
    env = env_ai_config()
    saved = _overrides(row)
    keys: dict[str, ApiKeyStatus] = {}
    for k in _KEYS:
        if saved[k]:
            keys[k] = ApiKeyStatus(source="db", hint=_hint(saved[k]))
        elif env[k]:
            keys[k] = ApiKeyStatus(source="env", hint=_hint(env[k]))
        else:
            keys[k] = ApiKeyStatus(source="", hint="")
    return AppSettingsOut(
        values=AppSettingsValues(**{f: saved[f] for f in _FIELDS}),
        defaults=AppSettingsValues(**{f: env[f] for f in _FIELDS}),
        keys=keys,
    )


def get_app_settings(db: Session) -> AppSettingsOut:
    return _out(_get_row(db))


def update_app_settings(data: AppSettingsUpdate, db: Session) -> AppSettingsOut:
    row = _get_row(db)
    overrides = _overrides(row)
    overrides.update({f: getattr(data, f).strip() for f in _FIELDS})
    for k in _KEYS:
        new = getattr(data, k)
        if new is not None:
            overrides[k] = new.strip()
    try:
        provider = build_default(current_config(overrides))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuração de IA inválida: {exc}",
        ) from exc
    for f in _FIELDS:
        setattr(row, f, overrides[f])
    for k in _KEYS:
        if getattr(data, k) is not None:
            setattr(row, k, encrypt(overrides[k]))
    db.commit()
    db.refresh(row)
    configure(overrides, provider)
    return _out(row)


def apply_from_db() -> None:
    """Na subida da API: aplica ao `ai` o que estiver salvo no app_settings."""
    try:
        with SessionLocal() as db:
            configure(_overrides(_get_row(db)))
    except Exception:
        logger.exception("app_settings não aplicado; usando apenas o .env.")


def test_image() -> ImageTestOut:
    cfg = current_config()
    provider_name = cfg["ai_image_provider"]
    start = time.monotonic()
    try:
        resp = ai.image(ImageRequest(
            prompt="Simple manga-style ink drawing of a cat sitting on a windowsill",
            quality="low" if provider_name == "openai" else "standard",
            aspect_ratio="1:1",
        ))
    except Exception as exc:
        logger.exception("Teste de imagem falhou")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao gerar imagem ({provider_name}): {exc}",
        ) from exc
    return ImageTestOut(
        provider=provider_name,
        model=resp.model,
        image=resp.url or f"data:image/png;base64,{resp.b64_json}",
        elapsed_ms=int((time.monotonic() - start) * 1000),
    )
