"""Geração de metadados YouTube via IA."""
from __future__ import annotations

import json
import logging

from prompt_clinica.ai import Message, TextRequest, ai

logger = logging.getLogger(__name__)

_SYSTEM = """\
Você é um especialista em marketing de conteúdo no YouTube para HQs e animações.
Dado um projeto de HQ (título, premissa, gênero, tom, personagens e lista de cenas),
gere metadados otimizados para o YouTube.

Retorne APENAS um objeto JSON com:
- "title": str — título atraente para YouTube (máx 100 chars, em português)
- "description": str — descrição engajante (3-5 parágrafos em português, mencione a HQ, personagens e enredo)
- "tags": array de str — 10 a 15 tags relevantes em português e inglês
"""


def generate_youtube_metadata(
    project_title: str,
    premise: str,
    genre: str,
    tone: str,
    character_names: list[str],
    panel_labels: list[str],
) -> dict[str, object]:
    chars = ", ".join(character_names) if character_names else "nenhum"
    scenes = ", ".join(panel_labels[:8]) if panel_labels else "—"

    user_msg = (
        f"Título da HQ: {project_title}\n"
        f"Premissa: {premise}\n"
        f"Gênero: {genre} | Tom: {tone}\n"
        f"Personagens: {chars}\n"
        f"Cenas (primeiras): {scenes}\n\n"
        "Gere os metadados YouTube."
    )

    try:
        resp = ai.text(TextRequest(
            messages=[
                Message(role="system", content=_SYSTEM),
                Message(role="user", content=user_msg),
            ],
            temperature=0.75,
            max_tokens=1200,
            json_mode=True,
        ))
        data: dict[str, object] = json.loads(resp.content)
        if "title" not in data or "description" not in data or "tags" not in data:
            raise ValueError("JSON incompleto")
        return data
    except Exception as exc:
        logger.warning("generate_youtube_metadata falhou (%s) — usando fallback.", exc)
        return {
            "title": project_title,
            "description": premise,
            "tags": [genre, tone, "hq", "mangá", "motion comic", "animação"],
        }
