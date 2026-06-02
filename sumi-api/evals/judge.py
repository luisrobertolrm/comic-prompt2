"""
Juiz de evals (LLM-as-judge). Desacoplado do app: importa apenas `openai`,
então roda contra o Ollama local sem subir a API.

`--judge local`  → Ollama (endpoint OpenAI-compatible em localhost:11434)
`--judge remote` → OpenAI (gpt-4o) como ground truth sob demanda
"""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

LOCAL_BASE_URL = "http://localhost:11434/v1"


@dataclass
class JudgeConfig:
    mode: str
    base_url: str | None
    api_key: str
    text_model: str
    vision_model: str


def make_config(mode: str, openai_api_key: str = "") -> JudgeConfig:
    if mode == "local":
        return JudgeConfig(
            mode="local",
            base_url=LOCAL_BASE_URL,
            api_key="ollama",  # dummy: Ollama ignora, mas o SDK exige algo
            text_model="qwen2.5:14b",
            vision_model="qwen2.5vl:7b",
        )
    if mode == "remote":
        if not openai_api_key:
            msg = "Modo remote exige OPENAI_API_KEY."
            raise ValueError(msg)
        return JudgeConfig(
            mode="remote",
            base_url=None,
            api_key=openai_api_key,
            text_model="gpt-4o",
            vision_model="gpt-4o",
        )
    msg = f"Modo de juiz desconhecido: '{mode}' (use 'local' ou 'remote')."
    raise ValueError(msg)


_ROTEIRO_SYSTEM = """\
Você é um avaliador rigoroso de roteiros de quadrinhos/mangá. Recebe um BRIEFING
(o que se esperava) e os QUADROS gerados pela IA. Avalie objetivamente se os
quadros respeitam a ambientação e os personagens esperados, e detecte qualquer
anacronismo ou elemento proibido.

Retorne APENAS um objeto JSON (sem markdown, sem texto extra) com:
- "ambientacao_score": int 0-5 — quão fiel é a ambientação (época/lugar) esperada
- "personagens_score": int 0-5 — quão fiéis são os personagens esperados (traços, etnia, idade)
- "anacronismos": string[] — elementos presentes que NÃO deveriam existir (vazio se nenhum)
- "justificativa": string — 1-2 frases concretas em português

Seja exigente: se um quadro de estabelecimento descreve algo fora da época/lugar,
penalize a ambientação e liste o anacronismo.\
"""

_IMAGE_SYSTEM = """\
Você é um avaliador rigoroso de ILUSTRAÇÕES de mangá/quadrinhos (preto e branco,
screentone, sem texto). Recebe um BRIEFING (ambientação e personagens esperados) e
UMA IMAGEM gerada. Avalie objetivamente se a imagem retrata a época/lugar esperados
e os personagens, e liste anacronismos/elementos visíveis que não deveriam existir.

Retorne APENAS um objeto JSON (sem markdown, sem texto extra) com:
- "ambientacao_score": int 0-5 — fidelidade da época/lugar
- "personagens_score": int 0-5 — fidelidade dos personagens (traços, idade)
- "anacronismos": string[] — elementos visíveis que não deveriam existir (vazio se nenhum)
- "justificativa": string — 1-2 frases concretas em português

Regras importantes:
- Em "anacronismos" liste SOMENTE o que você REALMENTE vê na imagem. NUNCA repita itens de uma
  lista de "anacronismos proibidos" que não aparecem de fato — essa lista é só referência.
- IGNORE a paleta de cores e a colorização: cor (ou ausência de cor) NÃO é anacronismo.
- Avalie etnia/idade só se claramente perceptível; senão não penalize por isso.\
"""


def _client(cfg: JudgeConfig) -> OpenAI:
    return OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)


def _mediatype(image_bytes: bytes) -> str:
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return "image/png"


def _panels_view(roteiro: dict[str, Any]) -> str:
    panels = roteiro.get("panels") or []
    lines: list[str] = []
    for i, p in enumerate(panels, start=1):
        if not isinstance(p, dict):
            continue
        framing = str(p.get("framing", "?"))
        char = str(p.get("character_name") or "—")
        caption = str(p.get("caption", ""))
        prompt = str(p.get("prompt", ""))
        lines.append(
            f"[{i}] enquadramento={framing} | personagem={char}\n"
            f"     cena: {caption}\n"
            f"     prompt_img: {prompt}"
        )
    return "\n".join(lines) if lines else "(nenhum quadro)"


def _parse_json(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            msg = f"Resposta do juiz sem JSON: {content[:200]}"
            raise ValueError(msg) from None
        return json.loads(match.group())


def judge_roteiro(
    case: dict[str, Any],
    roteiro: dict[str, Any],
    cfg: JudgeConfig,
) -> dict[str, Any]:
    """Avalia um roteiro contra o briefing esperado. Retorna o veredito."""
    user_msg = (
        f"BRIEFING ESPERADO\n{_expect_block(case)}\n"
        f"- Premissa original: {case.get('premise', '')}\n\n"
        f"QUADROS GERADOS\n{_panels_view(roteiro)}\n\n"
        "Avalie e retorne APENAS o JSON."
    )

    resp = _client(cfg).chat.completions.create(
        model=cfg.text_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _ROTEIRO_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    data = _parse_json(resp.choices[0].message.content or "")
    return _verdict_from(data, chars_expected=_chars_expected(case))


def _expect_block(case: dict[str, Any]) -> str:
    expect = case.get("expect", {})
    proibidos = ", ".join(expect.get("anacronismos_proibidos", [])) or "(nenhum listado)"
    return (
        f"- Ambientação: {expect.get('ambientacao', '?')}\n"
        f"- Personagens: {expect.get('personagens', '?')}\n"
        f"- Anacronismos proibidos: {proibidos}"
    )


def _chars_expected(case: dict[str, Any]) -> bool:
    p = str(case.get("expect", {}).get("personagens", "")).strip().lower()
    if not p or p in {"—", "-", "n/a", "none"}:
        return False
    return "nenhum" not in p and "sem personagem" not in p


def _verdict_from(data: dict[str, Any], *, chars_expected: bool) -> dict[str, Any]:
    amb = int(data.get("ambientacao_score", 0))
    pers = int(data.get("personagens_score", 0))
    anac = [str(a) for a in (data.get("anacronismos") or []) if a]
    # O eixo de personagens só conta quando o briefing espera personagens.
    pers_ok = pers >= 3 or not chars_expected
    return {
        "ambientacao_score": amb,
        "personagens_score": pers,
        "anacronismos": anac,
        "justificativa": str(data.get("justificativa", "")),
        "passed": amb >= 3 and pers_ok and not anac,
    }


def judge_image(
    case: dict[str, Any],
    image_bytes: bytes,
    cfg: JudgeConfig,
) -> dict[str, Any]:
    """Avalia uma imagem gerada contra o briefing esperado (juiz de visão)."""
    b64 = base64.b64encode(image_bytes).decode("ascii")
    media = _mediatype(image_bytes)
    user_text = (
        f"BRIEFING ESPERADO\n{_expect_block(case)}\n"
        f"- Premissa original: {case.get('premise', '')}\n\n"
        "Avalie a IMAGEM e retorne APENAS o JSON."
    )

    resp = _client(cfg).chat.completions.create(
        model=cfg.vision_model,
        temperature=0,
        messages=[
            {"role": "system", "content": _IMAGE_SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media};base64,{b64}"},
                    },
                ],
            },
        ],
    )
    data = _parse_json(resp.choices[0].message.content or "")
    return _verdict_from(data, chars_expected=_chars_expected(case))
