import io
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from prompt_clinica.config import settings
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


@router.post("/{project_id}/panels/generate-images", response_model=list[PanelOut])
def generate_all_images(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PanelOut]:
    return panel_service.generate_all_images(project_id, user, db)


@router.get("/{project_id}/export/panels")
def export_panels(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Retorna ZIP com os quadros do projeto (imagens + storyboard.txt)."""
    panels = panel_service.list_panels(project_id, user, db)
    images_dir = Path(settings.images_dir)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        lines: list[str] = [f"STORYBOARD — {project_id}\n{'='*50}\n"]
        for p in panels:
            lines.append(
                f"\nQUADRO {p.index_order:02d} · {p.label}\n"
                f"  Enquadramento : {p.framing}\n"
                f"  Personagem    : {p.character_name or '—'}\n"
                f"  Direção       : {p.caption}\n"
            )
            if p.bubbles:
                for b in p.bubbles:
                    lines.append(f"  [{b.kind.upper()}] {b.text}\n")

            if p.image_url:
                img_path = images_dir / f"{p.id}.png"
                if img_path.exists():
                    zf.write(img_path, f"{p.index_order:02d}_{p.label}.png")

        zf.writestr("storyboard.txt", "".join(lines))

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="sumi-{project_id}.zip"'},
    )


@router.put("/{project_id}/panels/order", status_code=204)
def reorder_panels(
    project_id: uuid.UUID,
    body: ReorderBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    panel_service.reorder(project_id, body, user, db)
