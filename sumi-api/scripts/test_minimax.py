"""
Teste direto dos endpoints MiniMax por modalidade.

Uso:
    uv run python scripts/test_minimax.py            # texto + voz + imagem
    uv run python scripts/test_minimax.py --video    # adiciona submit de vídeo (sem aguardar)
    uv run python scripts/test_minimax.py --all      # texto + voz + imagem + vídeo completo (lento)

Não depende do banco nem do servidor FastAPI — só lê o .env.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Windows: força saída UTF-8 para evitar UnicodeEncodeError com caracteres especiais
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

# resolve imports do pacote sem instalar
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from prompt_clinica.ai.minimax import (
    MinimaxConfig,
    MinimaxError,
    MinimaxImageClient,
    MinimaxTextClient,
    MinimaxVideoClient,
    MinimaxVoiceClient,
)

SEP = "─" * 64
OK  = "✅"
ERR = "❌"
OUT = Path("/tmp/minimax_test")
OUT.mkdir(parents=True, exist_ok=True)


def _cfg() -> MinimaxConfig:
    return MinimaxConfig()


def _header(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ── Diagnóstico de configuração ──────────────────────────────────────────────

def check_env() -> None:
    _header("CONFIG  →  variáveis de ambiente")
    cfg = _cfg()
    fields = {
        "MINIMAX_API_KEY":    (cfg.api_key,    "obrigatória"),
        "MINIMAX_BASE_URL":   (cfg.base_url,   "obrigatória"),
        "MINIMAX_GROUP_ID":   (cfg.group_id,   "opcional — usada no polling de vídeo (GET)"),
        "MINIMAX_TEXT_MODEL": (cfg.text.model, ""),
        "MINIMAX_IMAGE_MODEL":(cfg.image.model,""),
        "MINIMAX_VOICE_MODEL":(cfg.voice.model,""),
        "MINIMAX_VIDEO_MODEL":(cfg.video.model,""),
    }
    all_ok = True
    for key, (value, note) in fields.items():
        status = OK if value else ("⚠️ " if "opcional" in note else ERR)
        if not value and "obrigatória" in note:
            all_ok = False
        display = value[:12] + "…" if value and len(value) > 12 else (value or "<vazio>")
        tag = f"  [{note}]" if note else ""
        print(f"  {status}  {key:<28} {display}{tag}")

    jwt = os.getenv("JWT_SECRET_KEY", "")
    print(f"\n  {'⚠️ ' if not jwt else OK}  JWT_SECRET_KEY               {'<vazio>  [API de autenticação quebrada]' if not jwt else jwt[:8] + '…'}")

    if not all_ok:
        print(f"\n  {ERR}  Corrija as variáveis obrigatórias antes de continuar.")
        sys.exit(1)
    print(f"\n  {OK}  Configuração básica OK.")


# ── Texto ────────────────────────────────────────────────────────────────────

def test_text() -> str:
    _header(f"TEXTO  →  {_cfg().text.model}")
    client = MinimaxTextClient(_cfg())
    messages = [
        {"role": "system", "content": "Você é roteirista de mangá. Responda em português, de forma concisa."},
        {"role": "user",   "content": (
            "Descreva em 2 frases o visual de um quadro de mangá shojo: "
            "uma estudante encontra uma carta anônima no livro emprestado. "
            "Inclua enquadramento, expressão e tom emocional."
        )},
    ]
    t0 = time.perf_counter()
    result = client.generate(messages, max_tokens=200)
    elapsed = time.perf_counter() - t0

    print(f"  Modelo   : {result.model}")
    print(f"  Tokens   : {result.input_tokens} in  /  {result.output_tokens} out")
    print(f"  Tempo    : {elapsed:.2f}s")
    print(f"\n  Resposta :\n  {result.content}")
    print(f"\n  {OK}  Texto OK.")
    return result.content


# ── Voz ──────────────────────────────────────────────────────────────────────

def test_voice() -> None:
    _header(f"VOZ  →  {_cfg().voice.model}")
    client = MinimaxVoiceClient(_cfg())
    text = "Num último dia de verão, uma carta dobrada caiu silenciosamente do livro emprestado."
    t0 = time.perf_counter()
    result = client.synthesize(text, voice_id="Portuguese_Narrator")
    elapsed = time.perf_counter() - t0

    out_path = OUT / f"test_voice.{result.audio_format}"
    out_path.write_bytes(result.audio)
    print(f"  Modelo   : {result.model}")
    print(f"  Formato  : {result.audio_format}")
    print(f"  Tamanho  : {len(result.audio) // 1024} KB")
    print(f"  Tempo    : {elapsed:.2f}s")
    print(f"  Arquivo  : {out_path}")
    print(f"\n  {OK}  Voz OK.")


# ── Imagem ───────────────────────────────────────────────────────────────────

def test_image(description: str = "") -> None:
    _header(f"IMAGEM  →  {_cfg().image.model}")
    client = MinimaxImageClient(_cfg())
    prompt = (
        "manga shojo panel, black and white screentone, clean line art, "
        "no text, no speech bubbles, expressive eyes, high contrast. "
        + (description or "A student finds a folded letter in a borrowed book, close-up, soft lighting.")
    )
    print(f"  Prompt   : {prompt[:100]}…")
    t0 = time.perf_counter()
    result = client.generate(prompt, response_format="base64")
    elapsed = time.perf_counter() - t0

    print(f"  Modelo   : {result.model}")
    print(f"  Tempo    : {elapsed:.2f}s")

    if result.b64:
        import base64
        img_bytes = base64.b64decode(result.b64[0])
        out_path = OUT / "test_image.png"
        out_path.write_bytes(img_bytes)
        print(f"  Tamanho  : {len(img_bytes) // 1024} KB")
        print(f"  Arquivo  : {out_path}")
    elif result.urls:
        print(f"  URL      : {result.urls[0]}")

    print(f"\n  {OK}  Imagem OK.")


# ── Vídeo (submit) ───────────────────────────────────────────────────────────

def test_video_submit() -> str:
    _header(f"VÍDEO (submit)  →  {_cfg().video.model}")
    client = MinimaxVideoClient(_cfg())
    prompt = "Manga shojo scene, a girl opens a letter, close-up on her surprised expression, soft light"
    print(f"  Prompt   : {prompt}")
    t0 = time.perf_counter()
    task_id = client.submit(prompt, duration=6, resolution="768P")
    elapsed = time.perf_counter() - t0

    print(f"  task_id  : {task_id}")
    print(f"  Tempo    : {elapsed:.2f}s")
    print(f"\n  {OK}  Submit OK. Use task_id para poll manual.")
    return task_id


def test_video_full() -> None:
    _header(f"VÍDEO (completo)  →  {_cfg().video.model}")
    print("  ⚠️   Pode demorar vários minutos — aguardando geração…")
    client = MinimaxVideoClient(_cfg())
    prompt = "Manga shojo scene, a girl opens a letter, close-up on her surprised expression, soft light"
    t0 = time.perf_counter()
    result = client.generate(prompt, duration=6, resolution="768P", poll_interval=15.0, timeout=600.0)
    elapsed = time.perf_counter() - t0

    print(f"  Modelo   : {result.model}")
    print(f"  task_id  : {result.task_id}")
    print(f"  Status   : {result.status}")
    print(f"  file_id  : {result.file_id}")
    print(f"  URL      : {result.download_url}")
    print(f"  Tempo    : {elapsed:.1f}s")
    print(f"\n  {OK}  Vídeo OK.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Teste de endpoints MiniMax")
    parser.add_argument("--video",    action="store_true", help="Adiciona submit de vídeo (sem aguardar resultado)")
    parser.add_argument("--all",      action="store_true", help="Ciclo completo incluindo vídeo (lento)")
    parser.add_argument("--text",     action="store_true", help="Só texto")
    parser.add_argument("--voice",    action="store_true", help="Só voz")
    parser.add_argument("--image",    action="store_true", help="Só imagem")
    args = parser.parse_args()

    print("🚀  MiniMax — teste de comunicação direto")
    print(f"   Base URL : {os.getenv('MINIMAX_BASE_URL', 'https://api.minimax.io')}")

    try:
        check_env()

        run_all = not any([args.text, args.voice, args.image, args.video, args.all])

        description = ""
        if run_all or args.text:
            description = test_text()

        if run_all or args.voice:
            test_voice()

        if run_all or args.image:
            test_image(description)

        if args.video:
            test_video_submit()

        if args.all:
            test_video_full()

        print(f"\n{SEP}")
        print(f"  {OK}  Todos os testes passaram.")
        print(f"  Arquivos gerados em: {OUT}")
        print(SEP)

    except MinimaxError as exc:
        print(f"\n{ERR}  MinimaxError: {exc}  (HTTP/API status={exc.status_code})")
        sys.exit(1)
    except Exception as exc:
        print(f"\n{ERR}  {type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
