import logging

from fastapi import APIRouter, Depends, HTTPException, status
from user import User

from prompt_clinica.ai.text_organizer import TextOrganizer, build_text_organizer
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.text import TextIn, TextOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/text", tags=["text"])


@router.post("/organize", response_model=TextOut)
def organize_text(
    req: TextIn,
    _user: User = Depends(get_current_user),
    organizer: TextOrganizer = Depends(build_text_organizer),
) -> TextOut:
    try:
        text = organizer.organize(req.text)
    except Exception as exc:
        logger.exception("Falha ao organizar texto")
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=f"A IA de texto não conseguiu organizar o texto: {exc}",
        ) from exc
    return TextOut(text=text or req.text)
