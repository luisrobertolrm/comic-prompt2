"""
Script de validação da camada de IA.

Roda:
    uv run python scripts/test_ai.py

Testa:
    1. Geração de texto  — gpt-4o-mini descreve um quadro de mangá
    2. Geração de imagem — gpt-image-1 gera a arte em base64, salva em /tmp/test_panel.png
"""

from __future__ import annotations

import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prompt_clinica.ai import ImageRequest, Message, TextRequest, ai

SEP = "─" * 60


def test_text() -> str:
    print(f"\n{SEP}")
    print("📝  TEXTO  →  gpt-4o-mini")
    print(SEP)

    req = TextRequest(
        messages=[
            Message(
                role="system",
                content=(
                    "Você é roteirista de mangá. "
                    "Responda sempre em português, de forma concisa e visual."
                ),
            ),
            Message(
                role="user",
                content=(
                    "Descreva em até 3 frases o visual de um quadro de mangá shojo: "
                    "uma estudante encontra uma carta anônima dobrada no livro emprestado. "
                    "Inclua enquadramento, expressão do personagem e tom emocional."
                ),
            ),
        ],
        temperature=0.75,
        max_tokens=200,
    )

    t0 = time.perf_counter()
    resp = ai.text(req)
    elapsed = time.perf_counter() - t0

    print(f"Modelo   : {resp.model}")
    print(f"Tokens   : {resp.input_tokens} in  /  {resp.output_tokens} out")
    print(f"Tempo    : {elapsed:.2f}s")
    print(f"\nResposta :\n{resp.content}")
    return resp.content


def test_image(panel_description: str) -> None:
    print(f"\n{SEP}")
    print("🖼   IMAGEM  →  gpt-image-1")
    print(SEP)

    prompt = (
        "Manga shojo panel, black and white screentone, clean line art, "
        "no text or speech bubbles, expressive eyes, high contrast. "
        f"{panel_description}"
    )

    req = ImageRequest(
        prompt=prompt,
        size="1024x1024",
        quality="medium",
    )

    print(f"Prompt   : {prompt[:140]}…")
    t0 = time.perf_counter()
    resp = ai.image(req)
    elapsed = time.perf_counter() - t0

    print(f"Modelo   : {resp.model}")
    print(f"Tempo    : {elapsed:.2f}s")

    if resp.has_b64():
        img_bytes = base64.b64decode(resp.b64_json)
        out = Path("/tmp/test_panel.png")
        out.write_bytes(img_bytes)
        print(f"Base64   : {len(resp.b64_json):,} chars  →  {len(img_bytes) // 1024} KB")
        print(f"Salvo em : {out}")

    if resp.has_url():
        print(f"URL      : {resp.url}")

    if resp.revised_prompt:
        print(f"Revisado : {resp.revised_prompt[:120]}…")


if __name__ == "__main__":
    print("🚀  Sumi AI — validação da camada de abstração")
    print(f"   Provider : {ai.name}")

    try:
        description = test_text()
        test_image(description)
        print(f"\n{SEP}")
        print("✅  Todos os testes passaram.")
    except Exception as exc:
        print(f"\n❌  Erro: {exc}")
        raise
