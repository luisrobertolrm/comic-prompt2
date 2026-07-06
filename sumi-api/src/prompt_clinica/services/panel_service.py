from __future__ import annotations

import base64
import io
import json
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from character import Character
from fastapi import HTTPException, status
from panel import Panel
from project import Project
from project_character import ProjectCharacter
from sqlalchemy.orm import Session

import prompt_clinica._paths  # noqa: F401
from prompt_clinica import styles
from prompt_clinica.ai import AIProvider, ImageRequest, Message, TextRequest, ai
from prompt_clinica.ai.roteiro import generate_outline, generate_panel
from prompt_clinica.services import settings_service

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
from user import User

from prompt_clinica.schemas.panel import (
    InsertPanelBody,
    PanelOut,
    PanelPatch,
    ReorderBody,
    panel_to_out,
)
from prompt_clinica.storage import get_storage

logger = logging.getLogger(__name__)


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


# Traduz o enquadramento do quadro em instrução de câmera para o gerador de
# imagem. Sem isso, o modelo ignora o plano escolhido e tende ao close de rosto.
_FRAMING_PROMPT: dict[str, str] = {
    "Plano geral": "wide establishing shot, full figure visible, subject small in the frame, lots of environment",
    "Plano americano": "american shot, character framed from the knees up",
    "Plano médio": "medium shot, character framed from the waist up",
    "Close-up": "close-up shot of the face",
    "Extreme close": "extreme close-up",
    "Inserto": "insert shot, close-up of an object or detail, no face",
    "Detalhe": "detail macro shot of a single element, no face",
    "Plongée": "high-angle shot looking down on the scene",
    "Contra-plongée": "low-angle shot looking up",
}

# Planos sem rosto: o retrato usado como subject_reference é um close de rosto e
# puxa a câmera para perto. Nesses planos (geral/inserto/detalhe) omitimos a
# referência para não contaminar a composição.
_WIDE_FRAMINGS = frozenset({"Plano geral", "Inserto", "Detalhe"})

# Plano que mostra a figura inteira: reforça corpo inteiro/distância para vencer
# o viés de close. (Inserto/Detalhe são closes de objeto — não levam isso.)
_FULLBODY_FRAMINGS = frozenset({"Plano geral"})


def _img_prompt(style: str, color_mode: str, base_prompt: str, framing: str | None = None) -> str:
    parts = [styles.prompt_fragment(style, color_mode)]
    shot = _FRAMING_PROMPT.get(framing or "")
    if shot:
        parts.append(shot)
    if framing in _FULLBODY_FRAMINGS:
        parts.append("full body, whole figure visible, character framed at a distance")
    parts.append("no text, no speech bubbles.")
    return f"{', '.join(parts)} {base_prompt}"


def _portrait_reference(image_url: str | None) -> str | None:
    """
    Referência visual do personagem para o subject_reference.

    Quando o retrato está no nosso storage, lê os bytes e devolve um data-URI
    base64 (o MiniMax não acessa localhost). Se o `image_url` aponta para um host
    externo que nós não servimos, devolve a própria URL para o MiniMax buscar.
    """
    if not image_url:
        return None
    key: str | None = None
    for marker in ("/static/images/", "/storage/"):
        idx = image_url.find(marker)
        if idx != -1:
            key = image_url[idx + len(marker):]
            break
    if key is None:
        return image_url if image_url.startswith("http") else None
    data = get_storage().read(key)
    if not data:
        return None
    mime = "image/png" if data[:8].startswith(b"\x89PNG") else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


_MAX_PANEL_REFS = 10  # limite de imagens de referência por geração (Seedream)


def _label_portrait(data_uri: str, name: str) -> str:
    """Desenha o nome do personagem numa faixa abaixo do retrato.

    Recebe e devolve um data-URI base64. O rótulo deixa o modelo distinguir
    cada referência quando vários personagens vão juntos. URLs externas (sem
    bytes em mãos) voltam sem alteração.
    """
    if not data_uri.startswith("data:"):
        return data_uri
    try:
        b64 = data_uri.split(",", 1)[1]
        img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    except Exception:
        return data_uri

    bar_h = max(48, img.height // 12)
    canvas = Image.new("RGB", (img.width, img.height + bar_h), "black")
    canvas.paste(img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=int(bar_h * 0.6))
    text = name[:40]
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text(
        ((img.width - tw) / 2 - box[0], img.height + (bar_h - th) / 2 - box[1]),
        text, fill="white", font=font,
    )

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def _project_character_refs(
    project_id: uuid.UUID, db: Session
) -> list[tuple[str, str]]:
    """Retrato rotulado de cada personagem do projeto que tem imagem.

    Devolve (nome, data-URI rotulado). A consistência entre painéis vem de
    passar esses retratos como referência.
    """
    chars = (
        db.query(Character)
        .join(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(ProjectCharacter.project_id == project_id)
        .order_by(Character.name)
        .all()
    )
    out: list[tuple[str, str]] = []
    for c in chars:
        ref = _portrait_reference(c.image_url)
        if ref:
            out.append((c.name, _label_portrait(ref, c.name)))
    return out


def _select_references(
    panel: Panel, refs: list[tuple[str, str]]
) -> list[str] | None:
    """Decide quais imagens de personagem entram como referência DESTE quadro.

    Primeira implementação: todos os personagens do projeto, com o personagem
    do quadro em primeiro — providers de referência única (MiniMax) usam só a
    primeira, então ela precisa ser a do quadro.
    Implementação futura: filtrar `refs` pelos personagens presentes no quadro.
    """
    ordered = sorted(refs, key=lambda r: r[0] != panel.character_name)
    selected = [data_uri for _name, data_uri in ordered[:_MAX_PANEL_REFS]]
    return selected or None


def _locate_excerpt(source: str, excerpt: str) -> tuple[int | None, int | None]:
    """Resolve o trecho citado pela IA em offsets de caractere na sinopse.

    Tenta casamento literal e, como fallback, ignorando diferenças de espaços
    em branco. Retorna (None, None) quando não encontra.
    """
    excerpt = (excerpt or "").strip()
    if not source or not excerpt:
        return None, None
    idx = source.find(excerpt)
    if idx != -1:
        return idx, idx + len(excerpt)
    pattern = re.compile(re.escape(excerpt).replace(r"\ ", r"\s+"), re.DOTALL)
    m = pattern.search(source)
    if m:
        return m.start(), m.end()
    return None, None


def _validated_bubbles(data: dict[str, Any]) -> str:
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
    return json.dumps(valid_bubbles)


def _apply_panel_fields(panel: Panel, data: dict[str, Any]) -> None:
    """Aplica os campos de conteúdo de um dict (IA/mock) a um Panel existente."""
    valid_aspects = ("16-9", "4-3", "1-1", "3-4")
    valid_tones = ("dots", "diag", "dense")
    panel.label = str(data.get("label", f"Quadro {panel.index_order}"))[:100]
    panel.aspect = data.get("aspect", "4-3") if data.get("aspect") in valid_aspects else "4-3"  # type: ignore[assignment]
    panel.tone = data.get("tone", "dots") if data.get("tone") in valid_tones else "dots"  # type: ignore[assignment]
    panel.character_name = str(data["character_name"]) if data.get("character_name") else None
    panel.caption = str(data.get("caption", ""))[:2000]
    panel.framing = str(data.get("framing", "Plano médio"))[:60]
    panel.prompt = str(data.get("prompt", ""))[:2000]
    panel.bubbles_json = _validated_bubbles(data)


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


def _outline_slot(
    item: dict[str, Any], project_id: uuid.UUID, index: int, source_text: str | None
) -> Panel:
    """Cria um quadro 'pending' só com o trecho ancorado — sem conteúdo pesado.

    Framing/prompt/caption/balões são preenchidos depois, individualmente, por
    generate_one (geração assíncrona quadro a quadro no front).
    """
    s, e = (
        _locate_excerpt(source_text, str(item.get("excerpt", "")))
        if source_text else (None, None)
    )
    return Panel(
        project_id=project_id, index_order=index,
        label=f"Quadro {index}", aspect="4-3", tone="dots",
        character_name=str(item["character_name"]) if item.get("character_name") else None,
        caption="", framing="Plano médio", prompt="", bubbles_json="[]",
        status="pending", synopsis_start=s, synopsis_end=e,
    )


def generate(
    project_id: uuid.UUID,
    user: User,
    db: Session,
    target_panels: int | None = None,
    use_local: bool = False,
) -> list[PanelOut]:
    """Passo 1 do storyboard: a IA divide o roteiro inteiro em quadros 'pending'.

    Envia o texto completo do roteiro à IA, que decide a divisão e a quantidade
    (em torno de target_panels). O conteúdo de cada quadro é gerado depois,
    individualmente, via generate_one (chamada assíncrona por quadro no front).
    Levanta 503 se a IA não retornar quadros — não há recorte determinístico.
    `use_local` roteia a geração para a IA local configurada pelo usuário.
    """
    project = _check_project(project_id, user, db)
    char_names = _get_char_names(project_id, db)
    source_text = project.synopsis or project.premise or project.title
    provider: AIProvider | None = (
        settings_service.resolve_local_provider(user, db) if use_local else None
    )

    outline = generate_outline(
        premise=source_text,
        genre=project.genre,
        tone=project.tone,
        pages=project.pages,
        character_names=char_names,
        target_panels=target_panels,
        temperature=project.panels_temperature,
        provider=provider,
    )

    items: list[dict[str, Any]] = outline.get("panels") or []  # type: ignore[assignment]
    if not items:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível gerar os quadros agora. Tente novamente.",
        )

    db.query(Panel).filter(Panel.project_id == project_id).delete()
    panels: list[Panel] = []
    for i, item in enumerate(items, start=1):
        p = _outline_slot(item, project_id, i, source_text=source_text)
        db.add(p)
        panels.append(p)

    db.commit()
    for p in panels:
        db.refresh(p)
    return [panel_to_out(p) for p in panels]


def generate_one(panel_id: uuid.UUID, user: User, db: Session, use_local: bool = False) -> PanelOut:
    """Gera (via IA) o conteúdo de um único quadro, ancorado no trecho vinculado.

    Usado para preencher quadros inseridos manualmente sem regerar o storyboard
    inteiro. Mantém o vínculo de sinopse existente; substitui os demais campos.
    `use_local` roteia a geração para a IA local configurada pelo usuário.
    """
    panel: Panel | None = (
        db.query(Panel)
        .join(Project, Project.id == Panel.project_id)
        .filter(Panel.id == panel_id, Project.user_id == user.id)
        .first()
    )
    if panel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quadro não encontrado.")

    project: Project | None = db.query(Project).filter(Project.id == panel.project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")

    source_text = project.synopsis or project.premise or project.title or ""
    excerpt = ""
    if panel.synopsis_start is not None and panel.synopsis_end is not None and source_text:
        s = max(0, min(panel.synopsis_start, len(source_text)))
        e = max(s, min(panel.synopsis_end, len(source_text)))
        excerpt = source_text[s:e]

    provider = settings_service.resolve_local_provider(user, db) if use_local else None
    data = generate_panel(
        excerpt=excerpt,
        synopsis=source_text,
        genre=project.genre,
        tone=project.tone,
        character_names=_get_char_names(panel.project_id, db),
        style=project.style,
        color_mode=project.color_mode,
        temperature=project.panels_temperature,
        provider=provider,
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Geração do quadro falhou.",
        )

    _apply_panel_fields(panel, data)
    db.commit()
    db.refresh(panel)
    return panel_to_out(panel)


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

    row = (
        db.query(Project.style, Project.color_mode)
        .filter(Project.id == panel.project_id)
        .first()
    )
    project_style = (row.style if row else None) or styles.DEFAULT_STYLE
    project_color_mode = (row.color_mode if row else None) or styles.DEFAULT_COLOR_MODE
    base_prompt = panel.prompt or panel.caption or "manga panel"
    img_prompt = _img_prompt(project_style, project_color_mode, base_prompt, panel.framing)
    subject_ref = (
        None if panel.framing in _WIDE_FRAMINGS
        else _select_references(panel, _project_character_refs(panel.project_id, db))
    )

    try:
        resp = ai.image(ImageRequest(
            prompt=img_prompt, size="1024x1024", quality="medium", aspect_ratio="16:9",
            subject_reference=subject_ref,
        ))
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

    saved_url = get_storage().save(f"{panel.id}.png", img_bytes)
    panel.image_url = f"{saved_url}?v={uuid.uuid4().hex[:8]}"
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
    if patch.synopsis_start is not None: panel.synopsis_start = patch.synopsis_start
    if patch.synopsis_end is not None: panel.synopsis_end = patch.synopsis_end
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


def delete_panels(project_id: uuid.UUID, panel_ids: list[uuid.UUID], user: User, db: Session) -> None:
    _check_project(project_id, user, db)
    if not panel_ids:
        return
    db.query(Panel).filter(
        Panel.project_id == project_id, Panel.id.in_(panel_ids)
    ).delete(synchronize_session=False)
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
        match = re.search(r"\[.*?\]", resp.content, re.DOTALL)
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
    project = _check_project(project_id, user, db)
    panels = (
        db.query(Panel)
        .filter(Panel.project_id == project_id)
        .order_by(Panel.index_order)
        .all()
    )

    project_style = project.style or styles.DEFAULT_STYLE
    project_color_mode = project.color_mode or styles.DEFAULT_COLOR_MODE

    # Resolve as referências no thread principal — a Session não é thread-safe.
    # Os retratos rotulados são iguais para todo o projeto: monta uma vez.
    # Planos abertos não usam referência de rosto (ver _WIDE_FRAMINGS).
    char_refs = _project_character_refs(project_id, db)
    refs: dict[uuid.UUID, list[str] | None] = {
        p.id: (
            None if p.framing in _WIDE_FRAMINGS
            else _select_references(p, char_refs)
        )
        for p in panels
    }

    def _gen_one(panel: Panel) -> None:
        base_prompt = panel.prompt or panel.caption or "manga panel"
        img_prompt = _img_prompt(project_style, project_color_mode, base_prompt, panel.framing)
        try:
            resp = ai.image(ImageRequest(
                prompt=img_prompt, size="1024x1024", quality="medium", aspect_ratio="16:9",
                subject_reference=refs[panel.id],
            ))
            if resp.b64_json:
                img_bytes = base64.b64decode(resp.b64_json)
                saved_url = get_storage().save(f"{panel.id}.png", img_bytes)
                panel.image_url = f"{saved_url}?v={uuid.uuid4().hex[:8]}"
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
