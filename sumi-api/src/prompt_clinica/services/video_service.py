"""Render de motion comic: quadros + balões desenhados + narração TTS → .mp4.

Pipeline (por quadro, em ordem):
  1. Sintetiza o áudio de cada "beat" (caption = voz do narrador; cada balão = voz
     do personagem em cena) via MiniMax.
  2. Compõe um frame 1920x1080: imagem do quadro (letterbox) + balões desenhados
     reproduzindo o estilo da prévia (say/thought/shout/whisper/narration + cauda).
  3. Gera um clipe ffmpeg (imagem estática + áudio do quadro).
Por fim concatena os clipes e salva o .mp4 no storage. Sem dependência de ffmpeg
no sistema — usa o binário que vem no pacote imageio-ffmpeg.
"""
from __future__ import annotations

import io
import json
import logging
import re
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import imageio_ffmpeg
from character import Character
from narration_voice import NarrationVoice
from panel import Panel
from PIL import Image, ImageDraw, ImageFont
from project import Project
from project_character import ProjectCharacter
from sqlalchemy.orm import Session

import prompt_clinica._paths  # noqa: F401
from prompt_clinica.ai.minimax import MinimaxConfig, MinimaxError, MinimaxVoiceClient
from prompt_clinica.storage import get_storage

logger = logging.getLogger(__name__)

ProgressCb = Callable[[int, str], None]

# ── Constantes visuais (espelham os design tokens do front) ──────────
CANVAS_W, CANVAS_H = 1920, 1080
MARGIN = 80
REF_W = 480  # largura de referência do painel para escalar fontes (12px @ 480)

INK = (30, 24, 18)
INK3 = (125, 107, 82)
PAPER = (255, 250, 236)
PAPER2 = (245, 237, 216)
RULE = (212, 196, 168)

_CHAR_PALETTE = ["#F4D6D7", "#F6DEC2", "#DBEADF", "#E1D8EC", "#D8E2EC"]

_ASPECT = {"16-9": 16 / 9, "4-3": 4 / 3, "1-1": 1.0, "3-4": 3 / 4}

SILENT_DUR = 2.0

# Caminhos de fonte tentados em ordem (Windows → Linux → fallback PIL).
_FONT_REGULAR = [
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_FONT_BOLD = [
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in (_FONT_BOLD if bold else _FONT_REGULAR):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, capture_output=True, check=False)


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _char_color(name: str) -> tuple[int, int, int]:
    acc = 0
    for ch in name:
        acc = (acc * 31 + ord(ch)) & 0xFFFFFFFF
    return _hex_rgb(_CHAR_PALETTE[acc % len(_CHAR_PALETTE)])


# ── Áudio / narração ─────────────────────────────────────────────────

def _media_duration(path: Path) -> float:
    """Lê a duração via ffmpeg (parse do stderr)."""
    out = _run([_ffmpeg(), "-i", str(path)])
    m = re.search(rb"Duration: (\d+):(\d+):(\d+\.\d+)", out.stderr)
    if not m:
        return 0.0
    hh, mm, ss = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return hh * 3600 + mm * 60 + ss


def _synthesize(client: MinimaxVoiceClient, text: str, voice_id: str) -> bytes:
    result = client.synthesize(text, voice_id=voice_id)
    return result.audio


# ── Composição do frame ──────────────────────────────────────────────

def _panel_rect(aspect: str) -> tuple[int, int, int, int]:
    ar = _ASPECT.get(aspect, 4 / 3)
    avail_w, avail_h = CANVAS_W - 2 * MARGIN, CANVAS_H - 2 * MARGIN
    w = avail_w
    h = w / ar
    if h > avail_h:
        h = avail_h
        w = h * ar
    rect_w, rect_h = int(w), int(h)
    return (CANVAS_W - rect_w) // 2, (CANVAS_H - rect_h) // 2, rect_w, rect_h


def _draw_panel_image(canvas: Image.Image, img_bytes: bytes | None,
                      rect: tuple[int, int, int, int],
                      character_name: str | None) -> None:
    x, y, w, h = rect
    if img_bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        iw, ih = img.size
        scale = max(w / iw, h / ih)
        nw, nh = max(w, int(iw * scale)), max(h, int(ih * scale))
        img = img.resize((nw, nh))
        left, top = (nw - w) // 2, (nh - h) // 2
        canvas.paste(img.crop((left, top, left + w, top + h)), (x, y))
    else:
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([x, y, x + w, y + h], fill=PAPER2)
        if character_name:
            cx, cy = x + w // 2, y + int(h * 0.5)
            r = int(min(w, h) * 0.12)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         fill=_char_color(character_name), outline=INK, width=2)
            f = _load_font(r)
            initial = character_name[0].upper()
            tb = draw.textbbox((0, 0), initial, font=f)
            draw.text((cx - (tb[2] - tb[0]) / 2, cy - (tb[3] - tb[1]) / 2 - tb[1]),
                      initial, font=f, fill=INK)
    ImageDraw.Draw(canvas).rectangle([x, y, x + w - 1, y + h - 1], outline=INK, width=3)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
          max_w: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        cur = ""
        for word in paragraph.split():
            trial = f"{cur} {word}".strip()
            if cur and draw.textlength(trial, font=font) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines or [""]


def _draw_bubble(canvas: Image.Image, draw: ImageDraw.ImageDraw,
                 bubble: dict[str, Any], rect: tuple[int, int, int, int],
                 scale: float) -> None:
    text = str(bubble.get("text", "")).strip()
    if not text:
        return
    kind = bubble.get("kind", "say")
    side = bubble.get("side", "left")
    tail = bubble.get("tail", "none")
    rx, ry, rw, rh = rect

    base = max(11, int(12 * scale))
    if kind == "shout":
        font = _load_font(int(base * 1.05), bold=True)
    elif kind == "whisper":
        font = _load_font(int(base * 0.85))
    elif kind == "narration":
        font = _load_font(int(base * 0.92))
    else:
        font = _load_font(base)

    pad_x, pad_y = int(10 * scale), int(6 * scale)
    max_text_w = int(0.58 * rw) - 2 * pad_x
    lines = _wrap(draw, text, font, max_text_w)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + int(3 * scale)
    text_w = max(int(draw.textlength(ln, font=font)) for ln in lines)
    box_w = text_w + 2 * pad_x
    box_h = line_h * len(lines) + 2 * pad_y

    top = ry + int(bubble.get("y", 12) / 100 * rh)
    off = int(bubble.get("x", 8) / 100 * rw)
    left = rx + rw - off - box_w if side == "right" else rx + off
    left = max(rx + 4, min(left, rx + rw - box_w - 4))
    top = max(ry + 4, min(top, ry + rh - box_h - 4))

    color = INK3 if kind == "whisper" else INK
    radius_map = {"say": 12, "thought": box_h // 2, "shout": 4,
                  "whisper": box_h // 2, "narration": 2}
    radius = int(radius_map.get(kind, 12) if kind in ("shout", "narration", "say")
                 else radius_map[kind])
    if kind in ("thought", "whisper"):
        radius = box_h // 2
    width = max(1, int((2 if kind == "shout" else 1.5) * scale))
    if kind in ("whisper", "narration"):
        width = max(1, int(1 * scale))

    box = [left, top, left + box_w, top + box_h]
    draw.rounded_rectangle(box, radius=radius, fill=PAPER, outline=INK, width=width)

    if tail in ("left", "right") and kind != "narration":
        ts = int(9 * scale)
        tx = left + int(14 * scale) if tail == "left" else left + box_w - int(14 * scale)
        by = top + box_h
        draw.polygon([(tx, by), (tx + ts, by), (tx, by + ts)], fill=INK)
        draw.polygon([(tx + int(2 * scale), by), (tx + ts - int(2 * scale), by),
                      (tx + int(2 * scale), by + ts - int(3 * scale))], fill=PAPER)

    ty = top + pad_y
    for ln in lines:
        draw.text((left + pad_x, ty), ln, font=font, fill=color)
        ty += line_h


def _compose_frame(panel: Panel, img_bytes: bytes | None) -> bytes:
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), PAPER)
    rect = _panel_rect(panel.aspect)
    _draw_panel_image(canvas, img_bytes, rect, panel.character_name)

    draw = ImageDraw.Draw(canvas)
    scale = rect[2] / REF_W
    bubbles: list[dict[str, Any]] = json.loads(panel.bubbles_json or "[]")
    for b in bubbles:
        if isinstance(b, dict):
            _draw_bubble(canvas, draw, b, rect, scale)

    out = io.BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()


# ── Clipes ffmpeg ────────────────────────────────────────────────────

_V_ARGS = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25"]
_A_ARGS = ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]


def _panel_clip(frame_png: Path, audio: Path | None, dur: float, out: Path) -> None:
    if audio is not None:
        args = [_ffmpeg(), "-y", "-loop", "1", "-i", str(frame_png),
                "-i", str(audio), *_V_ARGS, *_A_ARGS, "-shortest",
                "-movflags", "+faststart", str(out)]
    else:
        args = [_ffmpeg(), "-y", "-loop", "1", "-i", str(frame_png),
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", f"{dur:.3f}", *_V_ARGS, *_A_ARGS, "-shortest", str(out)]
    res = _run(args)
    if not out.exists():
        raise RuntimeError(f"ffmpeg falhou no clipe: {res.stderr.decode(errors='ignore')[-400:]}")


def _concat_audio(parts: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    _run([_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
          "-c", "copy", str(out)])


def _concat_clips(clips: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips), encoding="utf-8")
    res = _run([_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                "-c", "copy", "-movflags", "+faststart", str(out)])
    if not out.exists():
        raise RuntimeError(f"ffmpeg falhou na concatenação: {res.stderr.decode(errors='ignore')[-400:]}")


# ── Resolução de vozes ───────────────────────────────────────────────

def _voice_map(project: Project, db: Session) -> tuple[str | None, dict[str, str]]:
    """Devolve (voz do narrador, {nome_personagem: voz}). voz = voice_id MiniMax."""
    def resolve(vid: uuid.UUID | None) -> str | None:
        if vid is None:
            return None
        nv = db.query(NarrationVoice).filter(NarrationVoice.id == vid).first()
        return nv.voice_id if nv else None

    narrator = resolve(project.narrator_voice_id)
    chars = (
        db.query(Character)
        .join(ProjectCharacter, ProjectCharacter.character_id == Character.id)
        .filter(ProjectCharacter.project_id == project.id)
        .all()
    )
    char_voices: dict[str, str] = {}
    for c in chars:
        v = resolve(c.narrator_voice_id)
        if v:
            char_voices[c.name] = v
    return narrator, char_voices


# ── Orquestração ─────────────────────────────────────────────────────

def render(project_id: uuid.UUID, user_id: uuid.UUID, db: Session,
           progress: ProgressCb | None = None) -> str:
    def report(pct: int, label: str) -> None:
        if progress:
            progress(pct, label)

    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user_id)
        .first()
    )
    if project is None:
        raise RuntimeError("Projeto não encontrado.")

    panels = (
        db.query(Panel)
        .filter(Panel.project_id == project_id)
        .order_by(Panel.index_order)
        .all()
    )
    if not panels:
        raise RuntimeError("O projeto não tem quadros para gerar o vídeo.")

    narrator_voice, char_voices = _voice_map(project, db)
    default_voice = MinimaxConfig().voice.voice_id
    client = MinimaxVoiceClient(MinimaxConfig())
    storage = get_storage()

    with tempfile.TemporaryDirectory(prefix="sumi-video-") as tmp:
        tmpdir = Path(tmp)
        clips: list[Path] = []

        for i, panel in enumerate(panels):
            report(int(i / len(panels) * 85), f"Cena {i + 1}/{len(panels)}")

            # Beats: caption (narrador) + balões (voz do personagem em cena).
            beats: list[tuple[str, str]] = []
            if panel.caption and panel.caption.strip():
                beats.append((panel.caption.strip(), narrator_voice or default_voice))
            char_voice = char_voices.get(panel.character_name or "", narrator_voice or default_voice)
            for b in json.loads(panel.bubbles_json or "[]"):
                if isinstance(b, dict) and str(b.get("text", "")).strip():
                    beats.append((str(b["text"]).strip(), char_voice))

            # Frame
            img_bytes = storage.read(f"{panel.id}.png") if panel.image_url else None
            frame_png = tmpdir / f"frame_{i:03d}.png"
            frame_png.write_bytes(_compose_frame(panel, img_bytes))

            # Áudio do quadro = concatenação dos beats
            audio_path: Path | None = None
            dur = SILENT_DUR
            beat_files: list[Path] = []
            for j, (text, vid) in enumerate(beats):
                try:
                    audio = _synthesize(client, text, vid)
                except (MinimaxError, ValueError) as exc:
                    logger.warning("TTS falhou (cena %d beat %d): %s", i, j, exc)
                    continue
                bf = tmpdir / f"beat_{i:03d}_{j:02d}.mp3"
                bf.write_bytes(audio)
                beat_files.append(bf)
            if beat_files:
                audio_path = tmpdir / f"audio_{i:03d}.mp3"
                _concat_audio(beat_files, audio_path)
                dur = _media_duration(audio_path) or SILENT_DUR

            clip = tmpdir / f"clip_{i:03d}.mp4"
            _panel_clip(frame_png, audio_path, dur, clip)
            clips.append(clip)

        report(90, "Montando o vídeo final…")
        final = tmpdir / "final.mp4"
        _concat_clips(clips, final)

        report(96, "Salvando…")
        url = storage.save(f"videos/{project_id}.mp4", final.read_bytes())

    project.video_url = url
    db.commit()

    report(100, "Pronto!")
    logger.info("Vídeo gerado: %s (%d cenas)", url, len(panels))
    return url
