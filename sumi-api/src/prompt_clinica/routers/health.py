import time

from fastapi import APIRouter

from prompt_clinica.ai import Message, TextRequest, ai, current_config
from prompt_clinica.config import settings
from prompt_clinica.storage import get_storage

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/storage")
def storage_health_check() -> dict[str, str]:
    try:
        payload = b"sumi storage health check"
        url = get_storage().save("health-check.txt", payload)
        return {"status": "ok", "backend": settings.storage_backend, "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "backend": settings.storage_backend, "detail": str(exc)}


@router.get("/health/storage/config")
def storage_config_check() -> dict[str, str]:
    endpoint = settings.railway_bucket_endpoint_url
    return {
        "backend": settings.storage_backend,
        "endpoint": endpoint or "<vazio>",
        "bucket": settings.railway_bucket_name or "<vazio>",
        "region": settings.railway_bucket_region or "<vazio>",
        "access_key": (settings.railway_bucket_access_key[:6] + "...") if settings.railway_bucket_access_key else "<vazio>",
        "public_url": settings.railway_public_url or "<vazio>",
    }


def _text_model(cfg: dict[str, str]) -> str:
    return cfg["minimax_text_model"] if cfg["ai_text_provider"] == "minimax" else cfg["ai_text_model"]


@router.get("/health/ai")
def ai_health_check() -> dict[str, str]:
    cfg = current_config()
    provider, model = cfg["ai_text_provider"], _text_model(cfg)
    start = time.monotonic()
    try:
        resp = ai.text(TextRequest(
            messages=[Message(role="user", content="Responda apenas: ok")],
            max_tokens=200,
        ))
        return {
            "status": "ok",
            "provider": provider,
            "model": resp.model or model,
            "response": resp.content.strip(),
            "elapsed_ms": str(int((time.monotonic() - start) * 1000)),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "provider": provider,
            "model": model,
            "detail": str(exc),
        }
