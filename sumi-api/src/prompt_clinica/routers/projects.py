import io
import json
import logging
import threading
import uuid
import zipfile
from dataclasses import dataclass, field

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from user import User
from youtube_metadata import VideoMetadata

from prompt_clinica.ai.youtube_metadata import generate_youtube_metadata
from prompt_clinica.database import SessionLocal, get_db
from prompt_clinica.deps import get_current_user
from prompt_clinica.schemas.panel import (
    DeletePanelsBody,
    GeneratePanelsBody,
    InsertPanelBody,
    PanelOut,
    ReorderBody,
    VideoJobOut,
)
from prompt_clinica.schemas.project import (
    CharacterIdsBody,
    ProjectCreate,
    ProjectDetailOut,
    ProjectOut,
    ProjectPatch,
    ScenarioIdsBody,
)
from prompt_clinica.schemas.youtube_metadata import (
    VideoMetadataOut,
    VideoMetadataUpdate,
)
from prompt_clinica.services import panel_service, project_service, video_service
from prompt_clinica.storage import get_storage

logger = logging.getLogger(__name__)

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


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    patch: ProjectPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    return ProjectOut.model_validate(project_service.update(project_id, patch, user, db))


@router.post("/{project_id}/synopsis/generate", response_model=ProjectDetailOut)
def generate_synopsis(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDetailOut:
    return project_service.generate_synopsis(project_id, user, db)


@router.put("/{project_id}/characters", status_code=204)
def set_characters(
    project_id: uuid.UUID,
    body: CharacterIdsBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    project_service.set_characters(project_id, body.character_ids, user, db)


@router.put("/{project_id}/scenarios", status_code=204)
def set_scenarios(
    project_id: uuid.UUID,
    body: ScenarioIdsBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    project_service.set_scenarios(project_id, body.scenario_ids, user, db)


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
    body: GeneratePanelsBody = GeneratePanelsBody(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PanelOut]:
    return panel_service.generate(project_id, user, db, target_panels=body.target_panels)


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
    storage = get_storage()

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
                img_data = storage.read(f"{p.id}.png")
                if img_data is not None:
                    zf.writestr(f"{p.index_order:02d}_{p.label}.png", img_data)

        zf.writestr("storyboard.txt", "".join(lines))

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="sumi-{project_id}.zip"'},
    )


# ── Render de vídeo (motion comic) ───────────────────────────────────

@dataclass
class _VideoJob:
    status: str = "pending"
    progress: int = 0
    video_url: str | None = None
    detail: str = ""


_video_jobs: dict[str, _VideoJob] = {}
_video_lock = threading.Lock()


def _run_video_job(job_id: str, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
    def progress(pct: int, label: str) -> None:
        with _video_lock:
            _video_jobs[job_id].progress = pct
            _video_jobs[job_id].detail = label

    with _video_lock:
        _video_jobs[job_id].status = "running"
    try:
        with SessionLocal() as db:
            url = video_service.render(project_id, user_id, db, progress)
        with _video_lock:
            _video_jobs[job_id].status = "done"
            _video_jobs[job_id].video_url = url
            _video_jobs[job_id].progress = 100
    except Exception as exc:  # noqa: BLE001
        logger.exception("Render de vídeo falhou — projeto %s", project_id)
        with _video_lock:
            _video_jobs[job_id].status = "error"
            _video_jobs[job_id].detail = str(exc)


@router.post("/{project_id}/export/video", status_code=202, response_model=VideoJobOut)
def start_video_export(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VideoJobOut:
    _get_project_or_404(project_id, user, db)
    job_id = str(uuid.uuid4())
    with _video_lock:
        _video_jobs[job_id] = _VideoJob()
    background_tasks.add_task(_run_video_job, job_id, project_id, user.id)
    return VideoJobOut(job_id=job_id, status="pending")


@router.get("/{project_id}/export/video/{job_id}", response_model=VideoJobOut)
def get_video_export(
    project_id: uuid.UUID,
    job_id: str,
    user: User = Depends(get_current_user),
) -> VideoJobOut:
    with _video_lock:
        job = _video_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job não encontrado.")
    return VideoJobOut(
        job_id=job_id,
        status=job.status,
        progress=job.progress,
        video_url=job.video_url,
        detail=job.detail,
    )


@router.put("/{project_id}/panels/order", status_code=204)
def reorder_panels(
    project_id: uuid.UUID,
    body: ReorderBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    panel_service.reorder(project_id, body, user, db)


@router.post("/{project_id}/panels/delete", status_code=204)
def delete_panels(
    project_id: uuid.UUID,
    body: DeletePanelsBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    panel_service.delete_panels(project_id, body.panel_ids, user, db)


# ── YouTube Metadata ─────────────────────────────────────────────────────────

def _get_project_or_404(project_id: uuid.UUID, user: User, db: Session):
    from project import Project
    p = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    return p


def _meta_to_out(m: VideoMetadata) -> VideoMetadataOut:
    return VideoMetadataOut(
        yt_title=m.yt_title,
        yt_description=m.yt_description,
        yt_tags=json.loads(m.yt_tags or "[]"),
        yt_category_id=m.yt_category_id,
        privacy_status=m.privacy_status,
        publish_at=m.publish_at,
        thumbnail_panel_id=m.thumbnail_panel_id,
    )


@router.get("/{project_id}/youtube-metadata", response_model=VideoMetadataOut)
def get_youtube_metadata(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VideoMetadataOut:
    _get_project_or_404(project_id, user, db)
    m = db.query(VideoMetadata).filter(VideoMetadata.project_id == project_id).first()
    if m is None:
        return VideoMetadataOut(
            yt_title="", yt_description="", yt_tags=[], yt_category_id="1",
            privacy_status="private", publish_at=None, thumbnail_panel_id=None,
        )
    return _meta_to_out(m)


@router.put("/{project_id}/youtube-metadata", response_model=VideoMetadataOut)
def save_youtube_metadata(
    project_id: uuid.UUID,
    body: VideoMetadataUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VideoMetadataOut:
    _get_project_or_404(project_id, user, db)
    m = db.query(VideoMetadata).filter(VideoMetadata.project_id == project_id).first()
    if m is None:
        m = VideoMetadata(project_id=project_id)
        db.add(m)
    m.yt_title = body.yt_title
    m.yt_description = body.yt_description
    m.yt_tags = json.dumps(body.yt_tags, ensure_ascii=False)
    m.yt_category_id = body.yt_category_id
    m.privacy_status = body.privacy_status
    m.publish_at = body.publish_at
    m.thumbnail_panel_id = body.thumbnail_panel_id
    db.commit()
    db.refresh(m)
    return _meta_to_out(m)


@router.post("/{project_id}/youtube-metadata/generate", response_model=VideoMetadataOut)
def generate_youtube_metadata_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VideoMetadataOut:
    project = _get_project_or_404(project_id, user, db)
    panels = panel_service.list_panels(project_id, user, db)

    from character import Character
    from project_character import ProjectCharacter
    chars = (
        db.query(Character)
        .join(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(ProjectCharacter.project_id == project_id)
        .all()
    )
    char_names = [c.name for c in chars]
    panel_labels = [p.label for p in panels]

    data = generate_youtube_metadata(
        project_title=project.title,
        premise=project.premise or "",
        genre=project.genre,
        tone=project.tone,
        character_names=char_names,
        panel_labels=panel_labels,
    )

    m = db.query(VideoMetadata).filter(VideoMetadata.project_id == project_id).first()
    if m is None:
        m = VideoMetadata(project_id=project_id)
        db.add(m)
    m.yt_title = str(data.get("title", project.title))[:100]
    m.yt_description = str(data.get("description", ""))
    m.yt_tags = json.dumps(data.get("tags", []), ensure_ascii=False)
    if not m.yt_category_id:
        m.yt_category_id = "1"
    if not m.privacy_status:
        m.privacy_status = "private"
    db.commit()
    db.refresh(m)
    return _meta_to_out(m)
