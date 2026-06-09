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

MIN_PANELS = 5
MAX_PANELS = 30


def _token_budget(n_panels: int) -> int:
    # raciocínio do M3 + ~230 tokens de JSON por quadro
    return min(9000, 1800 + n_panels * 230)


def generate_roteiro(
    premise: str,
    genre: str,
    tone: str,
    pages: int,
    character_names: list[str],
    target_panels: int | None = None,
) -> dict[str, object]:
    """
    Chama a IA e retorna {"title": str, "panels": list[dict]}.
    `target_panels` define quantos quadros gerar; se None, a IA decide pela história.
    Retorna {} se a chamada falhar — o serviço aplica fallback mock.
    """
    chars = ", ".join(character_names) if character_names else "nenhum definido ainda"

    if target_panels is not None:
        n = max(MIN_PANELS, min(MAX_PANELS, target_panels))
        count_line = f"Gere exatamente {n} quadros."
        budget = _token_budget(n)
    else:
        hint = max(MIN_PANELS, pages * 3)
        count_line = (
            f"Escolha quantos quadros a história precisa, entre {MIN_PANELS} e {MAX_PANELS} "
            f"(referência do autor: ~{hint}) — mais quadros se a história for rica, menos se for simples."
        )
        budget = _token_budget(MAX_PANELS)

    user_msg = (
        f"Premissa: {premise}\n"
        f"Gênero: {genre} | Tom: {tone}\n"
        f"{count_line}\n"
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
            max_tokens=budget,
            json_mode=True,
        ))
        data: dict[str, object] = json.loads(resp.content)
        if "panels" not in data or not isinstance(data["panels"], list):
            raise ValueError("JSON sem chave 'panels'")
        data["panels"] = data["panels"][:MAX_PANELS]  # type: ignore[index]
        logger.info(
            "Roteiro gerado: %d quadros, %d tokens out.",
            len(data["panels"]),  # type: ignore[arg-type]
            resp.output_tokens,
        )
        return data
    except Exception as exc:
        logger.warning("generate_roteiro falhou (%s) — usando fallback mock.", exc)
        return {}
