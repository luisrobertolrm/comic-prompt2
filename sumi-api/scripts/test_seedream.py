"""
Teste de comunicação direta com o Seedream (BytePlus ModelArk).

Independe de AI_PROVIDER — instancia o SeedreamProvider direto. Lê
BYTEPLUS_API_KEY / BYTEPLUS_BASE_URL / SEEDREAM_MODEL do ambiente (.env).

Uso:
    uv run python scripts/test_seedream.py
    uv run python scripts/test_seedream.py "prompt livre aqui"
    uv run python scripts/test_seedream.py "fundir os dois" ref1.png https://.../ref2.png

Argumentos opcionais: prompt e até 10 referências (caminho local ou URL).
Referências locais viram data-URI base64; URLs vão como estão.
"""
from __future__ import annotations

import base64
import mimetypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prompt_clinica.ai.providers.seedream_provider import SeedreamProvider
from prompt_clinica.ai.types import ImageRequest

SEP = "─" * 60


def _to_reference(arg: str) -> str:
    if arg.startswith("http://") or arg.startswith("https://"):
        return arg
    path = Path(arg)
    if not path.is_file():
        raise FileNotFoundError(f"Referência não encontrada: {arg}")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def main() -> None:
    args = sys.argv[1:]
    prompt = args[0] if args else (
        "Manga panel, black and white screentone, clean line art, no text, "
        "a samurai standing on a rooftop at dusk, dramatic wide shot"
    )
    references = [_to_reference(a) for a in args[1:]]

    provider = SeedreamProvider()
    print(f"\n{SEP}")
    print(f"🖼   SEEDREAM  →  {provider._model}")
    print(SEP)
    print(f"Prompt   : {prompt[:140]}…")
    print(f"Refs     : {len(references)} imagem(ns)")

    req = ImageRequest(
        prompt=prompt,
        aspect_ratio="16:9",
        subject_reference=references or None,
    )

    t0 = time.perf_counter()
    resp = provider.image(req)
    elapsed = time.perf_counter() - t0

    print(f"Modelo   : {resp.model}")
    print(f"Tempo    : {elapsed:.2f}s")

    if resp.has_b64():
        img_bytes = base64.b64decode(resp.b64_json)
        out = Path(__file__).resolve().parent.parent / "test_seedream.png"
        out.write_bytes(img_bytes)
        print(f"Base64   : {len(resp.b64_json):,} chars  →  {len(img_bytes) // 1024} KB")
        print(f"Salvo em : {out}")
    if resp.has_url():
        print(f"URL      : {resp.url}")
    if resp.revised_prompt:
        print(f"Revisado : {resp.revised_prompt[:120]}…")


if __name__ == "__main__":
    print("🚀  Sumi — teste de comunicação Seedream")
    try:
        main()
        print(f"\n{SEP}")
        print("✅  Teste passou.")
    except Exception as exc:
        print(f"\n❌  Erro: {exc}")
        raise
