"""
Provider de imagem via ComfyUI local (Stable Diffusion / SDXL / Illustrious).

Imagem: monta um workflow txt2img mínimo e o submete à API do ComfyUI
(POST /prompt → poll /history → GET /view). Suporta prompt negativo real.

Texto: o ComfyUI não gera texto, então delega ao MiniMax — AI_PROVIDER=comfyui
troca só o gerador de imagem, mantendo roteiro/sinopse como estão.

Variáveis de ambiente:
    COMFYUI_BASE_URL    default http://127.0.0.1:8188
    COMFYUI_CHECKPOINT  nome do arquivo do checkpoint em ComfyUI/models/checkpoints
    COMFYUI_STEPS       default 28
    COMFYUI_CFG         default 6.0
    COMFYUI_NEGATIVE    negativo padrão quando o request não traz um
"""
from __future__ import annotations

import base64
import os
import random
import time
import uuid

import httpx

from prompt_clinica.ai.types import (
    ImageRequest,
    ImageResponse,
    TextRequest,
    TextResponse,
)

_DEFAULT_NEGATIVE = "worst quality, low quality, blurry, jpeg artifacts, text, watermark, signature"


def _size_to_wh(size: str) -> tuple[int, int]:
    try:
        w, h = size.lower().split("x")
        return int(w), int(h)
    except ValueError:
        return 1024, 1024


class ComfyUIProvider:
    def __init__(self) -> None:
        self._base_url = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188").rstrip("/")
        self._checkpoint = os.getenv("COMFYUI_CHECKPOINT", "")
        self._steps = int(os.getenv("COMFYUI_STEPS", "28"))
        self._cfg = float(os.getenv("COMFYUI_CFG", "6.0"))
        self._negative = os.getenv("COMFYUI_NEGATIVE", _DEFAULT_NEGATIVE)

        from prompt_clinica.ai.providers.minimax_provider import MinimaxProvider

        self._text_provider = MinimaxProvider()

    @property
    def name(self) -> str:
        return "comfyui"

    def text(self, req: TextRequest) -> TextResponse:
        return self._text_provider.text(req)

    def _workflow(self, req: ImageRequest) -> dict:
        if not self._checkpoint:
            raise ValueError("COMFYUI_CHECKPOINT não definido no ambiente.")
        width, height = _size_to_wh(req.size)
        negative = req.negative_prompt or self._negative
        return {
            "ckpt": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": self._checkpoint},
            },
            "pos": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": req.prompt, "clip": ["ckpt", 1]},
            },
            "neg": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative, "clip": ["ckpt", 1]},
            },
            "latent": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1},
            },
            "sampler": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["ckpt", 0],
                    "positive": ["pos", 0],
                    "negative": ["neg", 0],
                    "latent_image": ["latent", 0],
                    "seed": random.randint(0, 2**32 - 1),  # noqa: S311
                    "steps": self._steps,
                    "cfg": self._cfg,
                    "sampler_name": "euler_ancestral",
                    "scheduler": "normal",
                    "denoise": 1.0,
                },
            },
            "decode": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["sampler", 0], "vae": ["ckpt", 2]},
            },
            "save": {
                "class_type": "SaveImage",
                "inputs": {"images": ["decode", 0], "filename_prefix": "sumi"},
            },
        }

    def image(self, req: ImageRequest) -> ImageResponse:
        payload = {"prompt": self._workflow(req), "client_id": str(uuid.uuid4())}
        with httpx.Client(timeout=300.0) as client:
            resp = client.post(f"{self._base_url}/prompt", json=payload)
            resp.raise_for_status()
            prompt_id = resp.json()["prompt_id"]

            deadline = time.monotonic() + 300.0
            outputs: dict = {}
            while time.monotonic() < deadline:
                hist = client.get(f"{self._base_url}/history/{prompt_id}").json()
                entry = hist.get(prompt_id)
                if entry:
                    status = entry.get("status", {})
                    if status.get("status_str") == "error":
                        raise RuntimeError(f"ComfyUI falhou: {status}")
                    outputs = entry.get("outputs", {})
                    if outputs:
                        break
                time.sleep(0.5)
            else:
                raise TimeoutError("ComfyUI não respondeu em 300s.")

            images = next(
                (o["images"] for o in outputs.values() if o.get("images")), None
            )
            if not images:
                raise RuntimeError("ComfyUI terminou sem imagens na saída.")
            img = images[0]
            view = client.get(
                f"{self._base_url}/view",
                params={
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                },
            )
            view.raise_for_status()

        return ImageResponse(
            model=f"comfyui/{self._checkpoint}",
            b64_json=base64.b64encode(view.content).decode("ascii"),
        )
