"""Endpoint de teste de voz MiniMax (t2a_v2). Retorna o áudio sintetizado."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from user import User

from prompt_clinica.ai.minimax import MinimaxConfig, MinimaxError, MinimaxVoiceClient
from prompt_clinica.deps import get_current_user

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceTestBody(BaseModel):
    text: str
    voice_id: str = ""


@router.post("/test")
def test_voice(
    body: VoiceTestBody,
    user: User = Depends(get_current_user),
) -> Response:
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Texto vazio.")
    try:
        result = MinimaxVoiceClient(MinimaxConfig()).synthesize(text, voice_id=body.voice_id)
    except (MinimaxError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"MiniMax: {exc}"
        ) from exc
    return Response(content=result.audio, media_type="audio/mpeg")
