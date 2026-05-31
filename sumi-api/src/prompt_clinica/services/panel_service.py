from __future__ import annotations

import base64
import json
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import prompt_clinica._paths  # noqa: F401
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from character import Character
from panel import Panel
from project import Project
from project_character import ProjectCharacter
from prompt_clinica.ai import ImageRequest, Message, TextRequest, ai
from prompt_clinica.ai.roteiro import generate_roteiro

_BUBBLES_SYSTEM = """\
Você é roteirista de mangá shojo. Gere balões de diálogo para um quadro específico.

Retorne APENAS um array JSON (sem markdown, sem texto extra). Exemplo:
[{"text": "Eu não sei o que dizer.", "kind": "say", "side": "left", "x": 8, "y": 10},
 {"text": "(Por que agora?)", "kind": "thought", "side": "right", "x": 50, "y": 55}]

Regras:
- Gere entre 1 e 3 balões por quadro
- "say" = fala, "thought" = pensamento interno, "shout" = grito/emoção intensa
- "side" indica o lado de origem do balão: "left" ou "right"
- x e y são posições percentuais (5–70); distribua verticalmente para não sobrepor
- Em enquadramentos Close-up ou Extreme close, prefira "thought"
- Texto em português, conciso e natural para mangá\
"""
from prompt_clinica.config import settings
from prompt_clinica.schemas.panel import (
    BubbleSchema,
    InsertPanelBody,
    PanelOut,
    PanelPatch,
    ReorderBody,
    panel_to_out,
)
from user import User

logger = logging.getLogger(__name__)

_MOCK_TEMPLATES = [
    {"label": "Estabelecimento", "aspect": "16-9", "tone": "dots",
     "caption": "Plano geral de abertura. Ambiente estabelecido.",
     "framing": "Plano geral",
     "prompt": "Wide establishing shot of a Japanese school setting, soft light, manga screentone, no characters.",
     "character_name": None, "bubbles": []},
    {"label": "Reação", "aspect": "4-3", "tone": "dots",
     "caption": "Close no protagonista. Expressão de surpresa.",
     "framing": "Close-up",
     "prompt": "Close-up of a shojo manga character with wide expressive eyes, surprised expression, blurred background.",
     "character_name": None, "bubbles": [{"text": "...", "kind": "say", "side": "left", "x": 8, "y": 8}]},
    {"label": "Reveal", "aspect": "1-1", "tone": "diag",
     "caption": "Segundo personagem aparece em cena. Postura serena.",
     "framing": "Plano médio",
     "prompt": "Manga character standing calmly, diagonal screentone background, gentle wind.",
     "character_name": None, "bubbles": [{"text": "Você estava me esperando?", "kind": "say", "side": "right", "x": 6, "y": 10}]},
    {"label": "Confronto interno", "aspect": "3-4", "tone": "dense",
     "caption": "Protagonista hesitante. Conflito interno visível.",
     "framing": "Plano americano",
     "prompt": "Shojo manga panel, character looking conflicted, dense dot screentone background, emotional expression.",
     "character_name": None,
     "bubbles": [
         {"text": "Eu não sei o que dizer.", "kind": "say", "side": "left", "x": 8, "y": 8},
         {"text": "(Por que justo agora?)", "kind": "thought", "side": "left", "x": 8, "y": 60},
     ]},
    {"label": "Beat de tensão", "aspect": "16-9", "tone": "dots",
     "caption": "Inserto. Detalhe simbólico em primeiro plano.",
     "framing": "Inserto",
     "prompt": "Close-up detail of symbolic object, manga screentone, shallow depth of field, petal falling.",
     "character_name": None, "bubbles": []},
    {"label": "Resposta", "aspect": "4-3", "tone": "dots",
     "caption": "Personagem responde com expressão suave.",
     "framing": "Plano médio",
     "prompt": "Manga character with soft smile, warm golden light, gentle screentone.",
     "character_name": None, "bubbles": [{"text": "Tudo bem se demorar.", "kind": "say", "side": "right", "x": 6, "y": 10}]},
    {"label": "Cliffhanger", "aspect": "16-9", "tone": "diag",
     "caption": "Fechamento emocional. Elemento que gera suspense.",
     "framing": "Detalhe",
     "prompt": "Dramatic closing manga panel, diagonal screentone, emotional atmosphere, symbolic detail.",
     "character_name": None, "bubbles": []},
]


def _images_dir() -> Path:
    p = Path(settings.images_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _check_project(project_id: uuid.UUID, user: User, db: Session) -> Project:
    p: Project | None = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    return p


def _get_char_names(project_id: uuid.UUID, db: Session) -> list[str]:
    chars = (
        db.query(Character)
        .join(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(ProjectCharacter.project_id == project_id)
        .all()
    )
    return [c.name for c in chars]


def _panel_from_dict(data: dict[str, Any], project_id: uuid.UUID, index: int) -> Panel:
    """Cria um objeto Panel a partir de um dict (AI ou mock)."""
    raw_bubbles: list[dict[str, Any]] = data.get("bubbles") or []  # type: ignore[assignment]
    valid_bubbles: list[dict[str, Any]] = []
    for b in raw_bubbles:
        if not isinstance(b, dict):
            continue
        valid_bubbles.append({
            "text": str(b.get("text", "")),
            "kind": b.get("kind", "say") if b.get("kind") in ("say", "thought", "shout") else "say",
            "side": b.get("side", "left") if b.get("side") in ("left", "right") else "left",
            "x": max(5, min(75, int(b.get("x", 8)))),
            "y": max(5, min(75, int(b.get("y", 12)))),
        })

    valid_aspects = ("16-9", "4-3", "1-1", "3-4")
    valid_tones = ("dots", "diag", "dense")
    return Panel(
        project_id=project_id,
        index_order=index,
        label=str(data.get("label", f"Quadro {index}"))[:100],
        aspect=data.get("aspect", "4-3") if data.get("aspect") in valid_aspects else "4-3",  # type: ignore[arg-type]
        tone=data.get("tone", "dots") if data.get("tone") in valid_tones else "dots",  # type: ignore[arg-type]
        character_name=str(data["character_name"]) if data.get("character_name") else None,
        caption=str(data.get("caption", ""))[:2000],
        framing=str(data.get("framing", "Plano médio"))[:60],
        prompt=str(data.get("prompt", ""))[:2000],
        bubbles_json=json.dumps(valid_bubbles),
    )


# ── CRUD público ────────────────────────────────────────────────────

def list_panels(project_id: uuid.UUID, user: User, db: Session) -> list[PanelOut]:
    _check_project(project_id, user, db)
    panels = (
        db.query(Panel)
        .filter(Panel.project_id == project_id)
        .order_by(Panel.index_order)
        .all()
    )
    return [panel_to_out(p) for p in panels]


def generate(project_id: uuid.UUID, user: User, db: Session) -> list[PanelOut]:
    project = _check_project(project_id, user, db)
    char_names = _get_char_names(project_id, db)

    # Chama IA (retorna {} em caso de falha)
    ai_data = generate_roteiro(
        premise=project.premise or project.title,
        genre=project.genre,
        tone=project.tone,
        pages=project.pages,
        character_names=char_names,
    )

    templates: list[dict[str, Any]] = ai_data.get("panels") or []  # type: ignore[assignment]
    if not templates:
        templates = list(_MOCK_TEMPLATES)  # type: ignore[assignment]

    # Atualiza título se IA retornou um
    ai_title: str = str(ai_data.get("title", "")).strip()
    if ai_title:
        project.title = ai_title[:200]

    # Apaga painéis anteriores e cria os novos
    db.query(Panel).filter(Panel.project_id == project_id).delete()
    panels: list[Panel] = []
    for i, tpl in enumerate(templates, start=1):
        p = _panel_from_dict(tpl, project_id, i)
        db.add(p)
        panels.append(p)

    db.commit()
    for p in panels:
        db.refresh(p)
    return [panel_to_out(p) for p in panels]


def generate_image(panel_id: uuid.UUID, user: User, db: Session) -> PanelOut:
    """Gera imagem para um quadro via gpt-image-1 e persiste em disco."""
    panel: Panel | None = (
        db.query(Panel)
        .join(Project, Project.id == Panel.project_id)
        .filter(Panel.id == panel_id, Project.user_id == user.id)
        .first()
    )
    if panel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quadro não encontrado.")

    base_prompt = panel.prompt or panel.caption or "manga panel"
    img_prompt = (
        "Manga shojo style, black and white screentone, clean ink line art, "
        "no text, no speech bubbles, expressive eyes, high contrast. "
        f"{base_prompt}"
    )

    try:
        resp = ai.image(ImageRequest(prompt=img_prompt, size="1024x1024", quality="medium"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Geração de imagem falhou: {exc}",
        ) from exc

    img_bytes = base64.b64decode(resp.b64_json) if resp.b64_json else b""
    if not img_bytes:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Nenhuma imagem retornada pelo provider.",
        )

    out_path = _images_dir() / f"{panel.id}.png"
    out_path.write_bytes(img_bytes)

    panel.image_url = f"/static/images/{panel.id}.png"
    db.commit()
    db.refresh(panel)
    logger.info("Imagem gerada: %s (%d KB)", panel.image_url, len(img_bytes) // 1024)
    return panel_to_out(panel)


def update_panel(panel_id: uuid.UUID, patch: PanelPatch, user: User, db: Session) -> PanelOut:
    panel: Panel | None = (
        db.query(Panel)
        .join(Project, Project.id == Panel.project_id)
        .filter(Panel.id == panel_id, Project.user_id == user.id)
        .first()
    )
    if panel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quadro não encontrado.")

    if patch.label is not None: panel.label = patch.label
    if patch.aspect is not None: panel.aspect = patch.aspect
    if patch.tone is not None: panel.tone = patch.tone
    if patch.character_name is not None: panel.character_name = patch.character_name
    if patch.caption is not None: panel.caption = patch.caption
    if patch.framing is not None: panel.framing = patch.framing
    if patch.prompt is not None: panel.prompt = patch.prompt
    if patch.status is not None: panel.status = patch.status
    if patch.bubbles is not None:
        panel.bubbles_json = json.dumps([b.model_dump() for b in patch.bubbles])

    db.commit()
    db.refresh(panel)
    return panel_to_out(panel)


def delete_panel(panel_id: uuid.UUID, user: User, db: Session) -> None:
    panel: Panel | None = (
        db.query(Panel)
        .join(Project, Project.id == Panel.project_id)
        .filter(Panel.id == panel_id, Project.user_id == user.id)
        .first()
    )
    if panel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quadro não encontrado.")
    project_id = panel.project_id
    db.delete(panel)
    db.commit()
    _reindex(project_id, db)


def insert_panel(project_id: uuid.UUID, body: InsertPanelBody, user: User, db: Session) -> PanelOut:
    _check_project(project_id, user, db)
    after = body.after_index
    db.query(Panel).filter(
        Panel.project_id == project_id, Panel.index_order > after
    ).update({Panel.index_order: Panel.index_order + 1})  # type: ignore[arg-type]
    new_panel = Panel(
        project_id=project_id, index_order=after + 1,
        label="Novo", aspect="4-3", tone="dots",
        caption="Quadro novo — descreva o que acontece aqui.",
        framing="Plano médio", prompt="", bubbles_json="[]",
    )
    db.add(new_panel)
    db.commit()
    db.refresh(new_panel)
    return panel_to_out(new_panel)


def reorder(project_id: uuid.UUID, body: ReorderBody, user: User, db: Session) -> None:
    _check_project(project_id, user, db)
    for i, panel_id in enumerate(body.panel_ids, start=1):
        db.query(Panel).filter(
            Panel.id == panel_id, Panel.project_id == project_id
        ).update({Panel.index_order: i})  # type: ignore[arg-type]
    db.commit()


def generate_bubbles(panel_id: uuid.UUID, user: User, db: Session) -> PanelOut:
    """Gera balões de diálogo via IA baseado na direção de cena do quadro."""
    panel: Panel | None = (
        db.query(Panel)
        .join(Project, Project.id == Panel.project_id)
        .filter(Panel.id == panel_id, Project.user_id == user.id)
        .first()
    )
    if panel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quadro não encontrado.")

    user_msg = (
        f"Quadro: {panel.label}\n"
        f"Enquadramento: {panel.framing}\n"
        f"Personagem em cena: {panel.character_name or 'não especificado'}\n"
        f"Direção de cena: {panel.caption}\n\n"
        "Gere os balões para este quadro. Retorne APENAS o array JSON."
    )

    try:
        resp = ai.text(TextRequest(
            messages=[
                Message(role="system", content=_BUBBLES_SYSTEM),
                Message(role="user", content=user_msg),
            ],
            temperature=0.8,
            max_tokens=600,
        ))
        match = re.search(r'\[.*?\]', resp.content, re.DOTALL)
        if not match:
            raise ValueError("Nenhum array JSON na resposta.")
        raw: list[dict[str, Any]] = json.loads(match.group())

        valid: list[dict[str, Any]] = []
        for b in raw:
            if not isinstance(b, dict) or not b.get("text"):
                continue
            valid.append({
                "text": str(b["text"])[:300],
                "kind": b.get("kind") if b.get("kind") in ("say", "thought", "shout") else "say",
                "side": b.get("side") if b.get("side") in ("left", "right") else "left",
                "x": max(5, min(70, int(b.get("x", 8)))),
                "y": max(5, min(70, int(b.get("y", 12)))),
            })

        panel.bubbles_json = json.dumps(valid, ensure_ascii=False)
        db.commit()
        db.refresh(panel)
        logger.info("Balões gerados — quadro %s: %d balões", panel_id, len(valid))
        return panel_to_out(panel)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Geração de balões falhou: {exc}",
        ) from exc


def generate_all_images(project_id: uuid.UUID, user: User, db: Session) -> list[PanelOut]:
    """Gera imagens para todos os quadros do projeto em paralelo."""
    _check_project(project_id, user, db)
    panels = (
        db.query(Panel)
        .filter(Panel.project_id == project_id)
        .order_by(Panel.index_order)
        .all()
    )

    def _gen_one(panel: Panel) -> None:
        base_prompt = panel.prompt or panel.caption or "manga panel"
        img_prompt = (
            "Manga shojo style, black and white screentone, clean ink line art, "
            "no text, no speech bubbles, expressive eyes, high contrast. "
            f"{base_prompt}"
        )
        try:
            resp = ai.image(ImageRequest(prompt=img_prompt, size="1024x1024", quality="medium"))
            if resp.b64_json:
                img_bytes = base64.b64decode(resp.b64_json)
                out_path = _images_dir() / f"{panel.id}.png"
                out_path.write_bytes(img_bytes)
                panel.image_url = f"/static/images/{panel.id}.png"
                logger.info("Imagem gerada: quadro %s", panel.id)
        except Exception as exc:
            logger.warning("Falha ao gerar imagem — quadro %s: %s", panel.id, exc)

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(_gen_one, panels))

    db.commit()
    for p in panels:
        db.refresh(p)
    return [panel_to_out(p) for p in panels]


def _reindex(project_id: uuid.UUID, db: Session) -> None:
    panels = (
        db.query(Panel)
        .filter(Panel.project_id == project_id)
        .order_by(Panel.index_order)
        .all()
    )
    for i, p in enumerate(panels, start=1):
        p.index_order = i
    db.commit()
