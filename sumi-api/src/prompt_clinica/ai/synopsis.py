"""
História trabalhada por IA a partir da ideia do escritor.
Desenvolve a ideia em uma narrativa criativa com início, meio e fim.
Levanta exceção em caso de falha — o serviço mapeia para HTTP 503.
"""
from __future__ import annotations

import logging

from prompt_clinica.ai import Message, TextRequest, ai

logger = logging.getLogger(__name__)

_SYSTEM = """\
Você é roteirista e escritor criativo. Recebe a ideia de um escritor (pode ser curta \
ou longa) e a desenvolve em uma HISTÓRIA completa e envolvente, fiel à intenção dele.

Regras:
- Estruture com início, meio e fim: apresente cenário e personagens, desenvolva o conflito e entregue um desfecho.
- Enriqueça com detalhes criativos — atmosfera, motivações, viradas dramáticas — sem inventar fatos que contradigam a ideia original.
- Use os personagens informados com naturalidade; se não houver nenhum, crie os que a história precisar.
- 3 a 6 parágrafos, em português, no gênero e tom indicados.
- Prosa corrida e imersiva, sem títulos, sem listas, sem aspas, sem comentários — apenas a história.\
"""


def generate_synopsis(
    premise: str,
    genre: str,
    tone: str,
    character_names: list[str],
    temperature: float = 0.8,
) -> str:
    chars = ", ".join(character_names) if character_names else "nenhum definido ainda"

    user_msg = (
        f"Ideia do escritor: {premise}\n"
        f"Gênero: {genre} | Tom: {tone}\n"
        f"Personagens: {chars}\n\n"
        "Desenvolva a história."
    )

    resp = ai.text(TextRequest(
        messages=[
            Message(role="system", content=_SYSTEM),
            Message(role="user", content=user_msg),
        ],
        temperature=temperature,
        max_tokens=3000,
    ))
    text = resp.content.strip()
    if not text:
        raise ValueError("A IA devolveu a sinopse vazia.")
    logger.info("Sinopse gerada: %d chars, %d tokens out.", len(text), resp.output_tokens)
    return text
