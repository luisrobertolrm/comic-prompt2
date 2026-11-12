from __future__ import annotations

from openai import OpenAI


def transcribe(audio: bytes, filename: str) -> str:
    """Voz → texto via API de transcrição da OpenAI (whisper-1, gpt-4o-*-transcribe)."""
    from prompt_clinica.ai import current_config

    cfg = current_config()
    if not cfg["openai_api_key"]:
        raise ValueError("Chave da OpenAI não configurada.")
    client = OpenAI(api_key=cfg["openai_api_key"])
    result = client.audio.transcriptions.create(
        model=cfg["stt_model"],
        file=(filename, audio),
        language=cfg["stt_language"] or None,  # type: ignore[arg-type]
    )
    return result.text.strip()
