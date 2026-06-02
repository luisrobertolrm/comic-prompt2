"""
Geração de roteiro de mangá via GPT-4o-mini.
Retorna {title, panels} ou {} em caso de falha (o serviço usa fallback).
"""
from __future__ import annotations

import json
import logging

from prompt_clinica.ai import Message, TextRequest, ai

logger = logging.getLogger(__name__)

_SYSTEM = """\
Você é roteirista de mangá. Gere um storyboard estruturado.

Retorne APENAS um objeto JSON com:
- "title": str — título criativo da HQ (2-6 palavras em português)
- "synopsis": str — sinopse narrativa da história em 1-2 frases (português), apresentando o enredo de forma envolvente (não é direção de cena)
- "panels": array de quadros

Cada quadro deve ter:
- "label": str — nome curto (máx 3 palavras, ex: "Estabelecimento")
- "aspect": "16-9" | "4-3" | "1-1" | "3-4"
- "tone": "dots" | "diag" | "dense"
- "character_name": str | null — nome do personagem principal em cena (null se sem personagem)
- "caption": str — direção de cena em português, 1-2 frases concretas e visuais
- "framing": um de: Plano geral | Plano americano | Plano médio | Close-up | Extreme close | Inserto | Detalhe | Plongée | Contra-plongée
- "prompt": str — prompt em inglês para gerador de imagem (manga style, sem texto, sem balões, 1-2 frases)
- "bubbles": array de {"text": str, "kind": "say"|"thought"|"shout", "side": "left"|"right", "x": int, "y": int}

Varie enquadramentos e aspectos. Inclua balões só onde fizerem sentido narrativo.\
"""


def generate_roteiro(
    premise: str,
    genre: str,
    tone: str,
    pages: int,
    character_names: list[str],
) -> dict[str, object]:
    """
    Chama GPT e retorna {"title": str, "panels": list[dict]}.
    Retorna {} se a chamada falhar — o serviço aplica fallback mock.
    """
    n_panels = max(5, pages * 3)
    chars = ", ".join(character_names) if character_names else "nenhum definido ainda"

    user_msg = (
        f"Premissa: {premise}\n"
        f"Gênero: {genre} | Tom: {tone}\n"
        f"Páginas: {pages} → gere exatamente {n_panels} quadros\n"
        f"Personagens disponíveis: {chars}\n\n"
        "Distribua os personagens de forma coerente com a história. "
        "Retorne o objeto JSON."
    )

    try:
        resp = ai.text(TextRequest(
            messages=[
                Message(role="system", content=_SYSTEM),
                Message(role="user", content=user_msg),
            ],
            temperature=0.85,
            max_tokens=3500,
            json_mode=True,
        ))
        data: dict[str, object] = json.loads(resp.content)
        if "panels" not in data or not isinstance(data["panels"], list):
            raise ValueError("JSON sem chave 'panels'")
        logger.info(
            "Roteiro gerado: %d quadros, %d tokens out.",
            len(data["panels"]),  # type: ignore[arg-type]
            resp.output_tokens,
        )
        return data
    except Exception as exc:
        logger.warning("generate_roteiro falhou (%s) — usando fallback mock.", exc)
        return {}
