"""Motores de voz. Cada um carrega o modelo na GPU e devolve (waveform float32 mono, sample_rate).

Vozes: `voices/<voice_id>.wav` é usado como referência para clonagem. Para o
OmniVoice, `voices/<voice_id>.txt` com a transcrição evita a transcrição
automática (que baixa o Whisper). Sem arquivo, cada motor usa sua voz padrão.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import torch

VOICES_DIR = Path(__file__).parent / "voices"
LANGUAGE = os.getenv("TTS_LANGUAGE", "pt")
# O modo automático do OmniVoice sorteia uma voz a cada chamada; com instrução
# e seed fixos a voz padrão fica estável entre os trechos de um mesmo vídeo.
OMNIVOICE_DEFAULT_INSTRUCT = os.getenv("OMNIVOICE_DEFAULT_INSTRUCT", "male, middle-aged, low pitch")
DEFAULT_SEED = 1234


def _reference(voice_id: str) -> tuple[Path | None, str | None]:
    if not voice_id:
        return None, None
    wav = VOICES_DIR / f"{voice_id}.wav"
    if not wav.is_file():
        return None, None
    txt = wav.with_suffix(".txt")
    return wav, txt.read_text(encoding="utf-8").strip() if txt.is_file() else None


class OmniVoiceEngine:
    name = "omnivoice"

    def __init__(self) -> None:
        from omnivoice import OmniVoice

        self.model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cuda:0", dtype=torch.float16)

    def synthesize(self, text: str, voice_id: str) -> tuple[np.ndarray, int]:
        ref_wav, ref_text = _reference(voice_id)
        torch.manual_seed(DEFAULT_SEED)
        if ref_wav:
            audios = self.model.generate(text=text, language=LANGUAGE, ref_audio=str(ref_wav), ref_text=ref_text)
        else:
            audios = self.model.generate(text=text, language=LANGUAGE, instruct=OMNIVOICE_DEFAULT_INSTRUCT)
        return audios[0], self.model.sampling_rate


class ChatterboxEngine:
    name = "chatterbox"

    def __init__(self) -> None:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        self.model = ChatterboxMultilingualTTS.from_pretrained(device=torch.device("cuda"))

    def synthesize(self, text: str, voice_id: str) -> tuple[np.ndarray, int]:
        ref_wav, _ = _reference(voice_id)
        torch.manual_seed(DEFAULT_SEED)
        wav = self.model.generate(text, language_id=LANGUAGE, audio_prompt_path=str(ref_wav) if ref_wav else None)
        return wav.squeeze(0).cpu().numpy(), self.model.sr


ENGINES = {e.name: e for e in (OmniVoiceEngine, ChatterboxEngine)}
