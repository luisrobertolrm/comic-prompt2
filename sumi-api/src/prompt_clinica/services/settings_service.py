from __future__ import annotations

import logging

import httpx
import prompt_clinica._paths  # noqa: F401
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from user import User
from user_settings import UserSettings

from prompt_clinica.ai import AIProvider, build_local_text_provider
from prompt_clinica.schemas.settings import SettingsOut, SettingsUpdate

logger = logging.getLogger(__name__)


def _get_or_create(user: User, db: Session) -> UserSettings:
    row: UserSettings | None = (
        db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    )
    if row is None:
        row = UserSettings(user_id=user.id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _to_out(row: UserSettings) -> SettingsOut:
    return SettingsOut(
        local_ai_url=row.local_ai_url,
        local_ai_model=row.local_ai_model,
        local_ai_enabled=row.local_ai_enabled,
    )


def get_settings(user: User, db: Session) -> SettingsOut:
    return _to_out(_get_or_create(user, db))


def update_settings(patch: SettingsUpdate, user: User, db: Session) -> SettingsOut:
    row = _get_or_create(user, db)
    if patch.local_ai_url is not None:
        row.local_ai_url = patch.local_ai_url.strip()
    if patch.local_ai_model is not None:
        row.local_ai_model = patch.local_ai_model.strip()
    if patch.local_ai_enabled is not None:
        row.local_ai_enabled = patch.local_ai_enabled
    db.commit()
    db.refresh(row)
    return _to_out(row)


def list_local_models(url: str) -> list[str]:
    """Lista os modelos disponíveis no Ollama em `url` (GET /api/tags).

    Serve também como teste de conexão. 400 se a URL estiver vazia;
    503 se o servidor não responder.
    """
    base = (url or "").strip().rstrip("/")
    if not base:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe a URL da IA local.",
        )
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    try:
        resp = httpx.get(f"{base}/api/tags", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"IA local inacessível em {base}.",
        ) from exc
    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    return sorted(models)


def resolve_local_provider(user: User, db: Session) -> AIProvider:
    """Provider de texto da IA local do usuário, validando config e conexão.

    400 se não houver URL/modelo cadastrados; 503 se o servidor não responder.
    """
    row = _get_or_create(user, db)
    if not row.local_ai_url or not row.local_ai_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IA local não configurada. Configure a URL e o modelo em Configurações.",
        )
    # Ping de conexão para dar erro claro antes de iniciar a geração.
    list_local_models(row.local_ai_url)
    return build_local_text_provider(row.local_ai_url, row.local_ai_model)
