from __future__ import annotations

import base64
import logging
import time
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from prompt_clinica.ai import ImageRequest, Message, TextRequest, ai
from prompt_clinica.ai.minimax import MinimaxError, MinimaxVideoClient
from prompt_clinica.ai.registry import (
    AI_TYPES,
    KINDS,
    build_image_provider,
    build_text_provider,
    minimax_config,
    speech_to_text_for,
    text_to_speech_for,
    to_ai_config,
)
from prompt_clinica.schemas.ai_config import (
    AIConfigIn,
    AIConfigOut,
    AIConfigUpdate,
    ImageTestOut,
    TextTestOut,
    TranscriptionTestOut,
    VideoTestOut,
    VoiceTestOut,
)
from prompt_clinica.utils.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)

# status_code do base_resp do MiniMax para chave inválida.
_MINIMAX_INVALID_KEY = 1004


def _table(ai_type: str) -> Any:
    model = AI_TYPES.get(ai_type)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de IA desconhecido.")
    return model


def _hint(api_key: str) -> str:
    if not api_key:
        return ""
    return f"…{api_key[-4:]}" if len(api_key) > 4 else "…"


def _out(row: Any) -> AIConfigOut:
    return AIConfigOut(
        id=row.id,
        name=row.name,
        kind=row.kind,
        base_url=row.base_url,
        model=row.model,
        language=getattr(row, "language", ""),
        key_hint=_hint(decrypt(row.api_key)),
        active=row.active,
        updated_at=row.updated_at,
    )


def _get(ai_type: str, config_id: int, db: Session) -> Any:
    row = db.get(_table(ai_type), config_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuração não encontrada.")
    return row


def _check_kind(ai_type: str, kind: str) -> None:
    if kind not in KINDS[ai_type]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tipo '{kind}' inválido para esta IA. Use: {', '.join(KINDS[ai_type])}.",
        )


def _deactivate_others(ai_type: str, keep_id: int | None, db: Session) -> None:
    model = _table(ai_type)
    query = db.query(model).filter(model.active.is_(True))
    if keep_id is not None:
        query = query.filter(model.id != keep_id)
    query.update({model.active: False}, synchronize_session="fetch")


def _apply(row: Any, ai_type: str, data: AIConfigIn | AIConfigUpdate) -> None:
    row.name = data.name
    row.kind = data.kind
    row.base_url = data.base_url
    row.model = data.model
    if ai_type == "transcription":
        row.language = data.language
    if data.api_key is not None:
        row.api_key = encrypt(data.api_key.strip())


def list_configs(ai_type: str, db: Session) -> list[AIConfigOut]:
    model = _table(ai_type)
    rows = db.query(model).order_by(model.active.desc(), model.name).all()
    return [_out(r) for r in rows]


def create_config(ai_type: str, data: AIConfigIn, db: Session) -> AIConfigOut:
    model = _table(ai_type)
    _check_kind(ai_type, data.kind)
    if data.active:
        _deactivate_others(ai_type, None, db)
    row = model(active=data.active)
    _apply(row, ai_type, data)
    db.add(row)
    db.commit()
    db.refresh(row)
    ai.invalidate()
    return _out(row)


def update_config(ai_type: str, config_id: int, data: AIConfigUpdate, db: Session) -> AIConfigOut:
    row = _get(ai_type, config_id, db)
    _check_kind(ai_type, data.kind)
    if data.active:
        _deactivate_others(ai_type, config_id, db)
    _apply(row, ai_type, data)
    row.active = data.active
    db.commit()
    db.refresh(row)
    ai.invalidate()
    return _out(row)


def set_active(ai_type: str, config_id: int, active: bool, db: Session) -> list[AIConfigOut]:
    row = _get(ai_type, config_id, db)
    if active:
        _deactivate_others(ai_type, config_id, db)
    row.active = active
    db.commit()
    ai.invalidate()
    return list_configs(ai_type, db)


def delete_config(ai_type: str, config_id: int, db: Session) -> None:
    row = _get(ai_type, config_id, db)
    if row.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Desative a configuração antes de excluir.",
        )
    db.delete(row)
    db.commit()
    ai.invalidate()


def _provider_error(exc: Exception) -> HTTPException:
    logger.exception("Teste de configuração de IA falhou")
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


def test_text(config_id: int, db: Session) -> TextTestOut:
    cfg = to_ai_config(_get("text", config_id, db))
    start = time.monotonic()
    try:
        resp = build_text_provider(cfg).text(TextRequest(
            messages=[Message(role="user", content="Responda apenas: ok")],
            max_tokens=200,
        ))
    except Exception as exc:
        raise _provider_error(exc) from exc
    return TextTestOut(
        response=resp.content.strip(),
        model=resp.model or cfg.model,
        elapsed_ms=_elapsed_ms(start),
    )


def test_image(config_id: int, db: Session) -> ImageTestOut:
    cfg = to_ai_config(_get("image", config_id, db))
    start = time.monotonic()
    try:
        resp = build_image_provider(cfg).image(ImageRequest(
            prompt="Simple manga-style ink drawing of a cat sitting on a windowsill",
            quality="low" if cfg.kind == "openai" else "standard",
            aspect_ratio="1:1",
        ))
    except Exception as exc:
        raise _provider_error(exc) from exc
    return ImageTestOut(
        image=resp.url or f"data:image/png;base64,{resp.b64_json}",
        model=resp.model or cfg.model,
        elapsed_ms=_elapsed_ms(start),
    )


def test_transcription(config_id: int, audio: bytes, filename: str, db: Session) -> TranscriptionTestOut:
    cfg = to_ai_config(_get("transcription", config_id, db))
    if not audio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Áudio vazio.")
    start = time.monotonic()
    try:
        text = speech_to_text_for(cfg).transcribe(audio, filename)
    except Exception as exc:
        raise _provider_error(exc) from exc
    return TranscriptionTestOut(text=text, model=cfg.model, elapsed_ms=_elapsed_ms(start))


def test_voice(config_id: int, db: Session) -> VoiceTestOut:
    cfg = to_ai_config(_get("voice", config_id, db))
    start = time.monotonic()
    try:
        audio = text_to_speech_for(cfg).synthesize("Olá, este é um teste de voz.")
    except Exception as exc:
        raise _provider_error(exc) from exc
    return VoiceTestOut(
        audio=f"data:audio/mpeg;base64,{base64.b64encode(audio).decode()}",
        model=cfg.model,
        elapsed_ms=_elapsed_ms(start),
    )


def test_video(config_id: int, db: Session) -> VideoTestOut:
    """Só valida a conexão: consulta uma tarefa inexistente, sem gerar vídeo."""
    cfg = to_ai_config(_get("video", config_id, db))
    start = time.monotonic()
    try:
        MinimaxVideoClient(minimax_config(cfg), timeout=30.0).poll("0")
    except MinimaxError as exc:
        if exc.status_code in (status.HTTP_401_UNAUTHORIZED, _MINIMAX_INVALID_KEY):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Chave inválida.") from exc
    except Exception as exc:
        raise _provider_error(exc) from exc
    return VideoTestOut(status="ok", model=cfg.model, elapsed_ms=_elapsed_ms(start))
