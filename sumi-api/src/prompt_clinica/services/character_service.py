from __future__ import annotations

import base64
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from character import Character
from fastapi import HTTPException, status
from project_character import ProjectCharacter
from sqlalchemy import func
from sqlalchemy.orm import Session
from user import User

import prompt_clinica._paths  # noqa: F401
from prompt_clinica import character_options, styles
from prompt_clinica.ai import ImageRequest, Message, TextRequest, ai
from prompt_clinica.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    PortraitCandidate,
)
from prompt_clinica.storage import get_storage

_PORTRAIT_VARIANTS = [
    ("frontal", "Frontal portrait, neutral expression, looking directly at viewer"),
    ("perfil", "Three-quarter view, gentle smile, soft lighting from the side"),
]

_SD_PORTRAIT_VARIANTS = [
    ("frontal", "portrait, upper body, looking at viewer, neutral expression"),
    ("perfil", "portrait, upper body, three-quarter view, light smile"),
]


def _count_projects(char_id: uuid.UUID, db: Session) -> int:
    return (
        db.query(func.count(ProjectCharacter.project_id))
        .filter(ProjectCharacter.character_id == char_id)
        .scalar()
        or 0
    )


def list_all(user: User, db: Session) -> list[Character]:
    rows = (
        db.query(Character, func.count(ProjectCharacter.character_id))
        .outerjoin(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(Character.user_id == user.id)
        .group_by(Character.id)
        .order_by(Character.updated_at.desc())
        .all()
    )
    result: list[Character] = []
    for char, count in rows:
        char.project_count = count
        result.append(char)
    return result


def list_recent(user: User, db: Session, limit: int = 8) -> list[Character]:
    return list_all(user, db)[:limit]


def create(req: CharacterCreate, user: User, db: Session) -> Character:
    char = Character(
        user_id=user.id,
        name=req.name.strip(),
        role=req.role,
        gender=req.gender,
        body_type=req.body_type,
        skin_tone=req.skin_tone,
        ethnicity=req.ethnicity,
        age=req.age,
        height=req.height,
        summary=req.summary,
        outfit=req.outfit,
        traits=", ".join(req.traits) if req.traits else None,
        style=req.style,
        image_url=req.image_url,
        narrator_voice_id=req.narrator_voice_id,
        approved=True,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    char.project_count = 0
    return char


def update(char_id: uuid.UUID, req: CharacterUpdate, user: User, db: Session) -> Character:
    char = (
        db.query(Character)
        .filter(Character.id == char_id, Character.user_id == user.id)
        .first()
    )
    if char is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personagem não encontrado.")

    data = req.model_dump(exclude_unset=True)

    if "image_url" in data and data["image_url"] != char.image_url and char.image_url:
        old_key = char.image_url.split("/storage/")[-1]
        get_storage().delete(old_key)

    for key, value in data.items():
        if key == "traits":
            char.traits = ", ".join(value) if value else None
        elif key == "name" and value is not None:
            char.name = value.strip()
        else:
            setattr(char, key, value)

    db.commit()
    db.refresh(char)
    char.project_count = _count_projects(char.id, db)
    return char


def _delete_portrait_file(image_url: str | None) -> None:
    if not image_url:
        return
    for marker in ("/static/images/", "/storage/"):
        idx = image_url.find(marker)
        if idx != -1:
            get_storage().delete(image_url[idx + len(marker):])
            return


def delete_unused(ids: list[uuid.UUID], user: User, db: Session) -> int:
    """Apaga personagens do usuário sem vínculo a nenhum projeto. Restrito aos ids dados."""
    query = (
        db.query(Character)
        .outerjoin(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(Character.user_id == user.id, ProjectCharacter.character_id.is_(None))
    )
    if ids:
        query = query.filter(Character.id.in_(ids))
    unused = query.all()
    for char in unused:
        _delete_portrait_file(char.image_url)
        db.delete(char)
    db.commit()
    return len(unused)


_GENDER_PROMPT = {
    "Feminino": "female character",
    "Masculino": "male character",
    "Outro": "androgynous character",
    "Não especificado": "",
}

_BODY_PROMPT = {
    "Magro": "slim thin build",
    "Médio": "average build",
    "Atlético": "athletic toned build",
    "Forte": "muscular heavy-set build, broad shoulders",
    "Gordo": "fat plus-size body, round chubby face",
}

_SKIN_PROMPT = {
    "Clara": "light fair skin",
    "Morena": "medium brown skin",
    "Negra": "Black person, very dark brown skin",
}


# Tags danbooru para Stable Diffusion (ComfyUI). A negação não vai no prompt
# positivo (SD não entende "NOT x" — só adiciona os tokens de x); vai no
# negative_prompt real, construído em build_portrait_prompts.
# "male focus" contrabalança tags com viés feminino forte (ex.: "shoujo").
_SD_GENDER = {
    "Feminino": "1girl",
    "Masculino": "1boy, male focus",
    "Outro": "androgynous",
    "Não especificado": "",
}

_SD_BODY = {
    "Magro": "slim, skinny",
    "Médio": "",
    "Atlético": "athletic, toned",
    "Forte": "muscular",
    "Gordo": "plump, fat, chubby cheeks, double chin",
}

_SD_SKIN = {
    "Clara": "pale skin",
    "Morena": "tan, brown skin",
    "Negra": "very dark skin, dark-skinned female",
}

_SD_BODY_NEGATIVE = {
    "Magro": "fat, plump",
    "Gordo": "slim, skinny, thin",
}

_SD_SKIN_NEGATIVE = {
    "Clara": "dark skin",
    "Morena": "pale skin",
    "Negra": "pale skin, white skin, light skin",
}

_SD_QUALITY = "masterpiece, best quality, newest, absurdres, highres"
# NoobAI é treinado em danbooru + e621 (furry): sem estes negativos, tags de
# corpo ("plump, fat") puxam para arte furry/cartoon do e621. "multiple views"
# evita folhas de expressões em grade.
_SD_NEGATIVE_BASE = (
    "worst quality, low quality, blurry, jpeg artifacts, text, watermark, signature, "
    "furry, anthro, feral, animal ears, animal nose, mammal, "
    "multiple views, expression chart, reference sheet, 3d, photorealistic"
)


_TAGS_SYSTEM = (
    "Converta a descrição de personagem para tags danbooru em inglês, curtas e "
    "separadas por vírgula (ex.: 'black hair, blunt bangs, school uniform, shy'). "
    "Traduza TODOS os atributos visuais — cabelo, olhos, roupa, corpo, acessórios — "
    "sem omitir nenhum. Descarte só o que não for visual (nome, papel narrativo). "
    "Responda APENAS as tags."
)


def _attrs_to_tags(text: str) -> str:
    """Traduz atributos livres (PT) para tags danbooru — tokens em português
    degradam muito a geração em modelos treinados em danbooru/e621."""
    cleaned = ", ".join(p.strip() for p in text.split(",") if p.strip())
    if not cleaned:
        return cleaned
    try:
        # max_tokens alto: o M3 gasta o orçamento no <think> antes da resposta.
        resp = ai.text(TextRequest(
            messages=[Message("system", _TAGS_SYSTEM), Message("user", cleaned)],
            temperature=0.0,
            max_tokens=2000,
        ))
        tags = resp.content.strip().strip(".")
        return tags or cleaned
    except Exception:
        return cleaned


def build_portrait_prompts(
    prompt: str,
    style: str = styles.DEFAULT_STYLE,
    color_mode: str | None = None,
    gender: str | None = None,
    body_type: str | None = None,
    skin_tone: str | None = None,
    ethnicity: str | None = None,
) -> tuple[str, str]:
    """Retorna (prompt, negative_prompt) no formato do provider ativo."""
    if ai.name != "comfyui":
        return build_portrait_prompt(prompt, style, color_mode, gender, body_type, skin_tone, ethnicity), ""

    skin = _SD_SKIN.get(skin_tone or "", "")
    if skin and gender == "Masculino":
        skin = skin.replace("dark-skinned female", "dark-skinned male")
    vs = styles.resolve(style)
    cm = styles.resolve_color(color_mode)
    positive_parts = [
        _SD_QUALITY,
        _SD_GENDER.get(gender or "", ""),
        "solo",
        _SD_BODY.get(body_type or "", ""),
        skin,
        character_options.prompt_for("ethnicity", ethnicity),
        _attrs_to_tags(prompt),
        vs.sd_fragment,
        cm.sd_fragment,
        "simple background",
    ]
    negative_parts = [
        _SD_NEGATIVE_BASE,
        vs.sd_negative,
        cm.sd_negative,
        _SD_BODY_NEGATIVE.get(body_type or "", ""),
        _SD_SKIN_NEGATIVE.get(skin_tone or "", ""),
    ]
    positive = ", ".join(p for p in positive_parts if p)
    negative = ", ".join(p for p in negative_parts if p)
    return positive, negative


def build_portrait_prompt(
    prompt: str,
    style: str = styles.DEFAULT_STYLE,
    color_mode: str | None = None,
    gender: str | None = None,
    body_type: str | None = None,
    skin_tone: str | None = None,
    ethnicity: str | None = None,
) -> str:
    # Formato validado nos testes (ver styles.py): sujeito curto, estilo entre
    # aspas simples com a cor embutida, atributos no final.
    subject = _GENDER_PROMPT.get(gender or "", "") or "character"
    attrs = ", ".join(d for d in (
        _BODY_PROMPT.get(body_type or "", ""),
        _SKIN_PROMPT.get(skin_tone or "", ""),
        character_options.prompt_for("ethnicity", ethnicity),
        prompt,
    ) if d)
    base_prompt = f"{subject}, {styles.prompt_fragment(style, color_mode)}"
    if attrs:
        base_prompt += f", {attrs}"
    return base_prompt + ", character portrait, no text, no speech bubbles. "


def generate_portrait(
    prompt: str,
    style: str = styles.DEFAULT_STYLE,
    color_mode: str | None = None,
    gender: str | None = None,
    body_type: str | None = None,
    skin_tone: str | None = None,
    ethnicity: str | None = None,
) -> list[PortraitCandidate]:
    base_prompt, negative = build_portrait_prompts(
        prompt, style, color_mode, gender, body_type, skin_tone, ethnicity
    )
    variants = _SD_PORTRAIT_VARIANTS if ai.name == "comfyui" else _PORTRAIT_VARIANTS

    # Debug temporário: prompt final no console e em portrait_debug.log.
    print(
        f"\n[generate_portrait] provider={ai.name} style={style!r} color_mode={color_mode!r} "
        f"body_type={body_type!r} skin_tone={skin_tone!r}\n{base_prompt}\nNEG: {negative}\n",
        flush=True,
    )
    try:
        from pathlib import Path as _Path
        _Path(__file__).resolve().parents[3].joinpath("portrait_debug.log").write_text(
            f"provider={ai.name}\nstyle={style!r}\ncolor_mode={color_mode!r}\n"
            f"skin_tone={skin_tone!r}\n\n{base_prompt}\nNEG: {negative}\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    def _generate_one(variant_id: str, variant_suffix: str) -> PortraitCandidate:
        full_prompt = f"{base_prompt}, {variant_suffix}" if ai.name == "comfyui" else base_prompt + variant_suffix
        resp = ai.image(ImageRequest(
            prompt=full_prompt, size="1024x1024", quality="medium", negative_prompt=negative,
        ))
        if not resp.b64_json:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Nenhuma imagem retornada pelo provider.",
            )
        img_bytes = base64.b64decode(resp.b64_json)
        img_id = str(uuid.uuid4())
        url = get_storage().save(f"portraits/{img_id}.png", img_bytes)
        return PortraitCandidate(
            id=img_id,
            url=url,
            notes=variant_id,
        )

    results: list[PortraitCandidate] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_generate_one, vid, vsuffix): vid
            for vid, vsuffix in variants
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda c: [v[0] for v in variants].index(c.notes))
    return results
