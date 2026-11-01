"""Servidor local de voz do Sumi.

    GET  /config      → modelo ativo e modelos disponíveis
    PUT  /config      → troca o modelo ativo (descarrega o anterior da GPU)
    POST /synthesize  → texto → áudio MP3
"""
from __future__ import annotations

import gc
import json
import subprocess
import threading
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from engines import ENGINES, VOICES_DIR

CONFIG_FILE = Path(__file__).parent / "config.json"

app = FastAPI(title="sumi-tts")
# Um modelo na GPU por vez e uma geração por vez.
_lock = threading.Lock()
_engine = None


class ConfigBody(BaseModel):
    model: str


class SynthesizeBody(BaseModel):
    text: str
    voice_id: str = ""


def _saved_model() -> str:
    if CONFIG_FILE.is_file():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))["model"]
    return "omnivoice"


def _load(model: str) -> None:
    global _engine
    _engine = None
    gc.collect()
    torch.cuda.empty_cache()
    _engine = ENGINES[model]()
    CONFIG_FILE.write_text(json.dumps({"model": model}), encoding="utf-8")


def _to_mp3(wav: np.ndarray, sr: int) -> bytes:
    res = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
         "-f", "mp3", "-b:a", "128k", "pipe:1"],
        input=wav.astype(np.float32).tobytes(), capture_output=True, check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode(errors="ignore")[-400:])
    return res.stdout


@app.on_event("startup")
def startup() -> None:
    with _lock:
        _load(_saved_model())


@app.get("/config")
def get_config() -> dict[str, object]:
    return {
        "model": _engine.name if _engine else None,
        "available": list(ENGINES),
        "voices": sorted(p.stem for p in VOICES_DIR.glob("*.wav")),
    }


@app.put("/config")
def put_config(body: ConfigBody) -> dict[str, object]:
    if body.model not in ENGINES:
        raise HTTPException(422, f"Modelo desconhecido. Disponíveis: {', '.join(ENGINES)}")
    with _lock:
        if not (_engine and _engine.name == body.model):
            _load(body.model)
    return get_config()


@app.post("/synthesize")
def synthesize(body: SynthesizeBody) -> Response:
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Texto vazio.")
    with _lock:
        if _engine is None:
            raise HTTPException(503, "Nenhum modelo carregado.")
        wav, sr = _engine.synthesize(text, body.voice_id)
    return Response(content=_to_mp3(wav, sr), media_type="audio/mpeg")
