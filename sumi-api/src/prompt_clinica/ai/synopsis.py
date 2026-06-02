"""
Sinopse trabalhada por IA a partir da ideia do escritor.
Expande quando o texto é curto, lapida quando é longo.
Retorna a sinopse em texto puro ou "" em caso de falha (o serviço decide o fallback).
"""
from __future__ import annotations

import logging

from prompt_clinica.ai import Message, TextRequest, ai

logger = logging.getLogger(__name__)

_SYSTEM = """\
Você é editor de histórias. Recebe a ideia de um escritor (pode ser curta ou longa) \
e devolve uma SINOPSE trabalhada: clara, envolvente e fiel à intenção dele.

Regras:
- Se a ideia for curta, expanda com enredo, conflito e gancho — sem inventar fatos que a contradigam.
- Se a ideia for longa, lapide e condense mantendo o essencial.
- 2 a 4 frases, em português, no tom indicado.
- Texto corrido, sem títulos, sem listas, sem aspas, sem comentários — apenas a sinopse.\
"""


def generate_synopsis(
    premise: str,
    genre: str,
    tone: str,
    character_names: list[str],
) -> str:
    chars = ", ".join(character_names) if character_names else "nenhum definido ainda"

    user_msg = (
        f"Ideia do escritor: {premise}\n"
        f"Gênero: {genre} | Tom: {tone}\n"
        f"Personagens: {chars}\n\n"
        "Escreva a sinopse trabalhada."
    )

    try:
        resp = ai.text(TextRequest(
            messages=[
                Message(role="system", content=_SYSTEM),
                Message(role="user", content=user_msg),
            ],
            temperature=0.8,
            max_tokens=400,
        ))
        text = resp.content.strip()
        if not text:
            raise ValueError("Resposta vazia")
        logger.info("Sinopse gerada: %d chars, %d tokens out.", len(text), resp.output_tokens)
        return text
    except Exception as exc:
        logger.warning("generate_synopsis falhou (%s).", exc)
        return ""
