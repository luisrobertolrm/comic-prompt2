"""
Geração de vídeo via MiniMax (Hailuo, assíncrono).

Fluxo: submit → poll do status → retrieve do arquivo. `generate` faz o
ciclo completo e devolve a URL de download; `submit`/`poll`/`retrieve_url`
ficam expostos para quem quiser controlar o polling.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from .client import MinimaxHTTPBase
from .errors import MinimaxError


@dataclass
class MinimaxVideoResult:
    model: str
    task_id: str
    status: str
    file_id: str = ""
    download_url: str = ""


class MinimaxVideoClient(MinimaxHTTPBase):
    def submit(
        self,
        prompt: str,
        *,
        model: str = "",
        first_frame_image: str = "",
        duration: int | None = None,
        resolution: str = "",
    ) -> str:
        cfg = self.config.video
        payload: dict[str, object] = {
            "model": model or self.config.model,
            "prompt": prompt,
            "duration": duration or cfg.duration,
            "resolution": resolution or cfg.resolution,
        }
        if first_frame_image:
            payload["first_frame_image"] = first_frame_image
        body = self._post("/v1/video_generation", payload)
        task_id = body.get("task_id", "")
        if not task_id:
            raise MinimaxError("Resposta sem task_id.")
        return task_id

    def poll(self, task_id: str) -> tuple[str, str]:
        """Retorna (status, file_id). Status: Queueing | Processing | Success | Fail."""
        body = self._get("/v1/query/video_generation", {"task_id": task_id})
        return body.get("status", ""), body.get("file_id", "")

    def retrieve_url(self, file_id: str) -> str:
        body = self._get("/v1/files/retrieve", {"file_id": file_id})
        return (body.get("file") or {}).get("download_url", "")

    def generate(
        self,
        prompt: str,
        *,
        model: str = "",
        first_frame_image: str = "",
        duration: int | None = None,
        resolution: str = "",
        poll_interval: float = 10.0,
        timeout: float = 600.0,
    ) -> MinimaxVideoResult:
        model_name = model or self.config.model
        task_id = self.submit(
            prompt,
            model=model_name,
            first_frame_image=first_frame_image,
            duration=duration,
            resolution=resolution,
        )

        deadline = time.monotonic() + timeout
        while True:
            status, file_id = self.poll(task_id)
            if status == "Success":
                return MinimaxVideoResult(
                    model=model_name,
                    task_id=task_id,
                    status=status,
                    file_id=file_id,
                    download_url=self.retrieve_url(file_id),
                )
            if status == "Fail":
                raise MinimaxError(f"Geração de vídeo falhou (task {task_id}).")
            if time.monotonic() >= deadline:
                raise MinimaxError(f"Timeout aguardando vídeo (task {task_id}, status {status}).")
            time.sleep(poll_interval)
