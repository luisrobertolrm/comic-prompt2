"""Backup completo de um projeto: exporta tudo (registros + imagens + vídeo)
para um .zip auto-contido e importa de volta criando um novo projeto.

O zip contém um `manifest.json` (guia legível com todos os registros do banco e
o mapa de arquivos) e a pasta `assets/` com os bytes de cada imagem/vídeo. Na
importação todos os UUIDs são regerados e as FKs remapeadas, então importar
nunca colide com dados existentes — sempre nasce um projeto novo.
"""
from __future__ import annotations

import io
import json
import uuid
import zipfile
from datetime import UTC, datetime

import prompt_clinica._paths  # noqa: F401

from character import Character
from fastapi import HTTPException, status
from narration_voice import NarrationVoice
from panel import Panel
from project import Project
from project_character import ProjectCharacter
from project_scenario import ProjectScenario
from scenario import Scenario
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session
from user import User
from youtube_metadata import VideoMetadata

from prompt_clinica.storage import get_storage

FORMAT = "sumi-project-backup"
VERSION = 1


# ── Helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(obj: object) -> dict:
    """Serializa todas as colunas de um modelo ORM em tipos JSON-safe."""
    data: dict = {}
    for col in sa_inspect(obj).mapper.column_attrs:
        value = getattr(obj, col.key)
        if isinstance(value, uuid.UUID):
            value = str(value)
        elif isinstance(value, datetime):
            value = value.isoformat()
        data[col.key] = value
    return data


def _url_to_key(url: str | None) -> str | None:
    """Extrai a storage key de um image_url/video_url, ignorando query string."""
    if not url:
        return None
    base = url.split("?", 1)[0]
    for marker in ("/static/images/", "/storage/"):
        idx = base.find(marker)
        if idx != -1:
            return base[idx + len(marker):]
    return None


# ── Export ───────────────────────────────────────────────────────────────────

def export_project(project_id: uuid.UUID, user: User, db: Session) -> tuple[bytes, str]:
    project: Project | None = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")

    characters = (
        db.query(Character)
        .join(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(ProjectCharacter.project_id == project_id)
        .all()
    )
    scenarios = (
        db.query(Scenario)
        .join(ProjectScenario, ProjectScenario.scenario_id == Scenario.id)
        .filter(ProjectScenario.project_id == project_id)
        .all()
    )
    panels = (
        db.query(Panel)
        .filter(Panel.project_id == project_id)
        .order_by(Panel.index_order)
        .all()
    )
    video_meta = (
        db.query(VideoMetadata).filter(VideoMetadata.project_id == project_id).first()
    )

    voice_ids = {project.narrator_voice_id}
    voice_ids.update(c.narrator_voice_id for c in characters)
    voice_ids.discard(None)
    voices = (
        db.query(NarrationVoice)
        .filter(NarrationVoice.id.in_(voice_ids), NarrationVoice.user_id == user.id)
        .all()
        if voice_ids
        else []
    )

    storage = get_storage()
    assets: list[dict] = []

    def bundle(zf: zipfile.ZipFile, record: dict, url: str | None, zip_path: str) -> None:
        """Lê o arquivo do storage, grava no zip e anota _asset_path no registro."""
        key = _url_to_key(url)
        if not key:
            return
        data = storage.read(key)
        if data is None:
            return
        zf.writestr(zip_path, data)
        record["_asset_path"] = zip_path
        assets.append({"zip_path": zip_path, "storage_key": key})

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        project_d = _row_to_dict(project)
        bundle(zf, project_d, project.video_url, f"assets/video/{project.id}.mp4")

        characters_d = []
        for c in characters:
            cd = _row_to_dict(c)
            bundle(zf, cd, c.image_url, f"assets/portraits/{c.id}.png")
            characters_d.append(cd)

        scenarios_d = []
        for s in scenarios:
            sd = _row_to_dict(s)
            bundle(zf, sd, s.image_url, f"assets/scenes/{s.id}.png")
            scenarios_d.append(sd)

        panels_d = []
        for p in panels:
            pd = _row_to_dict(p)
            bundle(zf, pd, p.image_url, f"assets/panels/{p.id}.png")
            panels_d.append(pd)

        manifest = {
            "format": FORMAT,
            "version": VERSION,
            "exported_at": datetime.now(UTC).isoformat(),
            "source_project_id": str(project.id),
            "project": project_d,
            "narration_voices": [_row_to_dict(v) for v in voices],
            "characters": characters_d,
            "scenarios": scenarios_d,
            "panels": panels_d,
            "video_metadata": _row_to_dict(video_meta) if video_meta else None,
            "assets": assets,
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    buf.seek(0)
    safe_title = "".join(ch for ch in project.title if ch.isalnum() or ch in " -_").strip() or "projeto"
    filename = f"sumi-backup-{safe_title}-{project.id}.zip"
    return buf.getvalue(), filename


# ── Import ───────────────────────────────────────────────────────────────────

_PROJECT_FIELDS = (
    "title", "subtitle", "genre", "tone", "status", "pages", "language", "style",
    "color_mode", "premise", "synopsis", "synopsis_temperature", "panels_temperature",
    "cover_accent", "cover_tone",
)
_CHARACTER_FIELDS = (
    "name", "role", "gender", "body_type", "skin_tone", "ethnicity", "age", "height",
    "summary", "outfit", "traits", "style", "approved",
)
_SCENARIO_FIELDS = (
    "name", "kind", "summary", "location_type", "time_of_day", "weather",
    "atmosphere", "details", "style", "approved",
)
_PANEL_FIELDS = (
    "index_order", "label", "aspect", "tone", "character_name", "caption", "framing",
    "prompt", "status", "bubbles_json", "synopsis_start", "synopsis_end",
)
_VOICE_FIELDS = ("name", "voice_id", "age_start", "age_end", "sex", "details")
_META_FIELDS = (
    "yt_title", "yt_description", "yt_tags", "yt_category_id", "privacy_status",
)


def _pick(record: dict, fields: tuple[str, ...]) -> dict:
    return {f: record.get(f) for f in fields if record.get(f) is not None}


def import_project(
    zip_bytes: bytes,
    user: User,
    db: Session,
    project_id: uuid.UUID | None = None,
) -> Project:
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        manifest = json.loads(zf.read("manifest.json"))
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo de backup inválido.")

    if project_id is not None and db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um projeto com esse ID. Gere outro.",
        )

    if manifest.get("format") != FORMAT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de backup não reconhecido.")
    if manifest.get("version") != VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Versão de backup não suportada: {manifest.get('version')}.",
        )

    storage = get_storage()

    def read_asset(record: dict) -> bytes | None:
        path = record.get("_asset_path")
        if not path:
            return None
        try:
            return zf.read(path)
        except KeyError:
            return None

    # Vozes de narração — referenciadas por projeto e personagens.
    voice_map: dict[str, uuid.UUID] = {}
    for v in manifest.get("narration_voices", []):
        nv = NarrationVoice(user_id=user.id, **_pick(v, _VOICE_FIELDS))
        db.add(nv)
        db.flush()
        voice_map[v["id"]] = nv.id

    # Projeto.
    pdata = manifest["project"]
    project = Project(user_id=user.id, **_pick(pdata, _PROJECT_FIELDS))
    if project_id is not None:
        project.id = project_id
    project.narrator_voice_id = voice_map.get(pdata.get("narrator_voice_id"))
    db.add(project)
    db.flush()

    video_bytes = read_asset(pdata)
    if video_bytes is not None:
        url = storage.save(f"videos/{project.id}/{uuid.uuid4().hex}.mp4", video_bytes)
        project.video_url = url

    # Personagens (+ vínculo ao projeto).
    for c in manifest.get("characters", []):
        char = Character(user_id=user.id, **_pick(c, _CHARACTER_FIELDS))
        char.narrator_voice_id = voice_map.get(c.get("narrator_voice_id"))
        db.add(char)
        db.flush()
        img = read_asset(c)
        if img is not None:
            char.image_url = storage.save(f"portraits/{uuid.uuid4()}.png", img)
        db.add(ProjectCharacter(project_id=project.id, character_id=char.id))

    # Cenários (+ vínculo ao projeto).
    for s in manifest.get("scenarios", []):
        scn = Scenario(user_id=user.id, **_pick(s, _SCENARIO_FIELDS))
        db.add(scn)
        db.flush()
        img = read_asset(s)
        if img is not None:
            scn.image_url = storage.save(f"scenes/{uuid.uuid4()}.png", img)
        db.add(ProjectScenario(project_id=project.id, scenario_id=scn.id))

    # Quadros — guarda o remapeamento p/ a thumbnail do vídeo.
    panel_map: dict[str, str] = {}
    for p in manifest.get("panels", []):
        panel = Panel(project_id=project.id, **_pick(p, _PANEL_FIELDS))
        db.add(panel)
        db.flush()
        panel_map[str(p["id"])] = str(panel.id)
        img = read_asset(p)
        if img is not None:
            saved = storage.save(f"{panel.id}.png", img)
            panel.image_url = f"{saved}?v={uuid.uuid4().hex[:8]}"

    # Metadados de YouTube.
    meta = manifest.get("video_metadata")
    if meta:
        vm = VideoMetadata(project_id=project.id, **_pick(meta, _META_FIELDS))
        if meta.get("publish_at"):
            vm.publish_at = datetime.fromisoformat(meta["publish_at"])
        old_thumb = meta.get("thumbnail_panel_id")
        if old_thumb:
            vm.thumbnail_panel_id = panel_map.get(str(old_thumb))
        db.add(vm)

    db.commit()
    db.refresh(project)
    return project
