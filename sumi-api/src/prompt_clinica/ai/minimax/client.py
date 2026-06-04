"""
Base HTTP compartilhada pelos clients MiniMax.

Centraliza autenticação Bearer, base URL e a verificação do envelope
`base_resp` que toda resposta da API traz. Cada modalidade herda daqui e
só implementa o payload específico.
"""
from __future__ import annotations

from typing import Any

import httpx

from .config import MinimaxConfig
from .errors import MinimaxError


class MinimaxHTTPBase:
    def __init__(self, config: MinimaxConfig, timeout: float = 60.0) -> None:
        self._config = config
        self._timeout = timeout

    @property
    def config(self) -> MinimaxConfig:
        return self._config

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.require_key()}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._config.base_url.rstrip('/')}{path}"

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = httpx.post(
            self._url(path),
            headers=self._headers(),
            json=payload,
            timeout=self._timeout,
        )
        return self._unwrap(resp)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._config.group_id:
            params = {**params, "GroupId": self._config.group_id}
        resp = httpx.get(
            self._url(path),
            headers=self._headers(),
            params=params,
            timeout=self._timeout,
        )
        return self._unwrap(resp)

    @staticmethod
    def _unwrap(resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code >= 400:
            raise MinimaxError(f"HTTP {resp.status_code}: {resp.text}", resp.status_code)
        body: dict[str, Any] = resp.json()
        base = body.get("base_resp") or {}
        status = base.get("status_code")
        if status not in (None, 0):
            raise MinimaxError(base.get("status_msg", "erro desconhecido"), status)
        return body
