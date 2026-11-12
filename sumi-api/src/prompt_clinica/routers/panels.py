import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.panel import GeneratePanelBody, PanelOut, PanelPatch
from prompt_clinica.services import panel_service

router = APIRouter(tags=["panels"])


@router.patch("/panels/{panel_id}", response_model=PanelOut)
def update_panel(
    panel_id: uuid.UUID,
    patch: PanelPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PanelOut:
    return panel_service.update_panel(panel_id, patch, user, db)


@router.delete("/panels/{panel_id}", status_code=204)
def delete_panel(
    panel_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    panel_service.delete_panel(panel_id, user, db)


@router.post("/panels/{panel_id}/generate", response_model=PanelOut)
def generate_panel_content(
    panel_id: uuid.UUID,
    body: GeneratePanelBody = GeneratePanelBody(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PanelOut:
    return panel_service.generate_one(panel_id, user, db, use_local=body.use_local)


@router.post("/panels/{panel_id}/image", response_model=PanelOut)
def generate_panel_image(
    panel_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PanelOut:
    return panel_service.generate_image(panel_id, user, db)


@router.post("/panels/{panel_id}/bubbles/generate", response_model=PanelOut)
def generate_bubbles(
    panel_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PanelOut:
    return panel_service.generate_bubbles(panel_id, user, db)
