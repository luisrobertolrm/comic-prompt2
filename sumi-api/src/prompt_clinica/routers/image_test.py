"""Endpoint de teste de geração de imagem MiniMax — repassa o payload JSON cru
para /v1/image_generation, para experimentar prompts/parâmetros direto da UI."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from user import User

from prompt_clinica.ai import minimax_config
from prompt_clinica.ai.minimax.client import MinimaxHTTPBase
from prompt_clinica.ai.minimax.errors import MinimaxError
from prompt_clinica.deps import get_current_user

router = APIRouter(prefix="/image-test", tags=["image-test"])


@router.post("")
def test_image(
    payload: dict[str, Any],
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if not str(payload.get("prompt", "")).strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O JSON precisa de um campo 'prompt' não vazio.",
        )
    try:
        body = MinimaxHTTPBase(minimax_config(), timeout=180.0)._post(  # noqa: SLF001
            "/v1/image_generation", payload
        )
    except (MinimaxError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"MiniMax: {exc}"
        ) from exc
    data = body.get("data") or {}
    return {
        "urls": data.get("image_urls") or [],
        "b64": data.get("image_base64") or [],
    }
