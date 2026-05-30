from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.character import CharacterCreate, CharacterOut
from prompt_clinica.services import character_service
from user import User

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("", response_model=list[CharacterOut])
def list_characters(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CharacterOut]:
    return [CharacterOut.model_validate(c) for c in character_service.list_all(user, db)]


@router.post("", status_code=201, response_model=CharacterOut)
def create_character(
    req: CharacterCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CharacterOut:
    return CharacterOut.model_validate(character_service.create(req, user, db))
