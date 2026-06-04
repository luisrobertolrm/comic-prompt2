from __future__ import annotations


class MinimaxError(RuntimeError):
    """Falha em uma chamada à API MiniMax (HTTP ou base_resp.status_code != 0)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
