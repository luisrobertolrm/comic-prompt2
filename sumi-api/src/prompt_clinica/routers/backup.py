import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.project import ProjectOut
from prompt_clinica.services import backup_service

router = APIRouter(prefix="/projects", tags=["backup"])


@router.get("/{project_id}/backup")
def export_backup(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Baixa um .zip com tudo do projeto: registros, imagens e vídeo."""
    data, filename = backup_service.export_project(project_id, user, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", status_code=201, response_model=ProjectOut)
def import_backup(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    """Cria um novo projeto a partir de um .zip de backup.

    Se `project_id` for informado, ele é usado como ID do novo projeto (e do
    arquivo de vídeo). Caso contrário, um ID é gerado automaticamente.
    """
    pid: uuid.UUID | None = None
    if project_id:
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de projeto inválido.")
    project = backup_service.import_project(file.file.read(), user, db, project_id=pid)
    return ProjectOut.model_validate(project)
