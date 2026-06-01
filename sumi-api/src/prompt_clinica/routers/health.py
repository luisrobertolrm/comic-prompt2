from fastapi import APIRouter

from prompt_clinica.ai import Message, TextRequest, ai
from prompt_clinica.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ai")
def ai_health_check() -> dict[str, str]:
    resp = ai.text(TextRequest(
        messages=[Message(role="user", content="Responda apenas: ok")],
        max_tokens=10,
    ))
    return {
        "status": "ok",
        "provider": settings.ai_provider,
        "model": settings.ai_text_model,
        "response": resp.content.strip(),
    }
