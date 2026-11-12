from __future__ import annotations

from openai import OpenAI


def transcribe(audio: bytes, filename: str, model: str, language: str) -> str:
    """Voz → texto via API de transcrição da OpenAI (whisper-1, gpt-4o-*-transcribe)."""
    from prompt_clinica.config import settings

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY não definida no ambiente.")
    client = OpenAI(api_key=settings.openai_api_key)
    result = client.audio.transcriptions.create(
        model=model,
        file=(filename, audio),
        language=language or None,  # type: ignore[arg-type]
    )
    return result.text.strip()
