import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.panel import InsertPanelBody, PanelOut, ReorderBody
from prompt_clinica.schemas.project import CharacterIdsBody, ProjectCreate, ProjectDetailOut, ProjectOut
from prompt_clinica.services import panel_service, project_service
from user import User

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectOut]:
    return [ProjectOut.model_validate(p) for p in project_service.list_projects(user, db)]


@router.post("", status_code=201, response_model=ProjectOut)
def create_project(
    req: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    return ProjectOut.model_validate(project_service.create(req, user, db))


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDetailOut:
    return project_service.get_by_id(project_id, user, db)


@router.put("/{project_id}/characters", status_code=204)
def set_characters(
    project_id: uuid.UUID,
    body: CharacterIdsBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    project_service.set_characters(project_id, body.character_ids, user, db)


@router.get("/{project_id}/panels", response_model=list[PanelOut])
def list_panels(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PanelOut]:
    return panel_service.list_panels(project_id, user, db)


@router.post("/{project_id}/panels/generate", response_model=list[PanelOut])
def generate_panels(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PanelOut]:
    return panel_service.generate(project_id, user, db)


@router.post("/{project_id}/panels", status_code=201, response_model=PanelOut)
def insert_panel(
    project_id: uuid.UUID,
    body: InsertPanelBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PanelOut:
    return panel_service.insert_panel(project_id, body, user, db)


@router.put("/{project_id}/panels/order", status_code=204)
def reorder_panels(
    project_id: uuid.UUID,
    body: ReorderBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    panel_service.reorder(project_id, body, user, db)
