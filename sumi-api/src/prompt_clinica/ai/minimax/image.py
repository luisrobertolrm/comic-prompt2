"""Geração de imagem via MiniMax (image-01, síncrono)."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .client import MinimaxHTTPBase

logger = logging.getLogger("sumi.api")

# sumi-api/minimax_payload.log — registra cada payload enviado ao image-01.
_PAYLOAD_LOG = Path(__file__).resolve().parents[4] / "minimax_payload.log"


@dataclass
class MinimaxImageResult:
    model: str
    urls: list[str] = field(default_factory=list)
    b64: list[str] = field(default_factory=list)


class MinimaxImageClient(MinimaxHTTPBase):
    def generate(
        self,
        prompt: str,
        *,
        model: str = "",
        aspect_ratio: str = "",
        n: int = 1,
        response_format: str = "",
        subject_reference: list[str] | None = None,
    ) -> MinimaxImageResult:
        cfg = self.config.image
        payload: dict[str, object] = {
            "model": model or self.config.model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio or cfg.aspect_ratio,
            "n": n,
            "response_format": response_format or cfg.response_format,
            "prompt_optimizer": cfg.prompt_optimizer,
        }
        if subject_reference:
            payload["subject_reference"] = [
                {"type": "character", "image_file": ref} for ref in subject_reference
            ]
        raw_json = json.dumps(payload, ensure_ascii=False)
        logger.info("minimax image_generation payload: %s", raw_json)
        if cfg.payload_log:
            try:
                with _PAYLOAD_LOG.open("a", encoding="utf-8") as fh:
                    fh.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} ===\n")
                    fh.write(raw_json)
                    fh.write("\n")
            except Exception:
                pass
        body = self._post("/v1/image_generation", payload)

        data = body.get("data") or {}
        return MinimaxImageResult(
            model=payload["model"],  # type: ignore[arg-type]
            urls=data.get("image_urls") or [],
            b64=data.get("image_base64") or [],
        )
