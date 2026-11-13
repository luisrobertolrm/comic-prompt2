from typing import Any

import pytest
from fastapi.testclient import TestClient

from prompt_clinica.ai.text_organizer import (
    LangChainTextOrganizer,
    build_text_organizer,
)
from prompt_clinica.deps import get_current_user
from prompt_clinica.main import app


class _Reply:
    def __init__(self, content: Any) -> None:
        self.content = content


class _FakeModel:
    def __init__(self, content: Any) -> None:
        self.content = content
        self.messages: list[Any] = []

    def invoke(self, messages: list[Any]) -> _Reply:
        self.messages = messages
        return _Reply(self.content)


def test_organizer_returns_model_text() -> None:
    model = _FakeModel("  Uma carta cai do livro. Quem a colocou ali?  ")

    text = LangChainTextOrganizer(model).organize("uma carta cai do livro quem colocou ali")  # type: ignore[arg-type]

    assert text == "Uma carta cai do livro. Quem a colocou ali?"
    assert model.messages[-1] == ("human", "uma carta cai do livro quem colocou ali")


def test_organizer_joins_content_blocks() -> None:
    model = _FakeModel([{"type": "text", "text": "Olá."}, {"type": "text", "text": " Tudo bem?"}])

    assert LangChainTextOrganizer(model).organize("olá tudo bem") == "Olá. Tudo bem?"  # type: ignore[arg-type]


class _Upper:
    def organize(self, text: str) -> str:
        return text.upper()


@pytest.fixture
def user_client(client: TestClient) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[build_text_organizer] = _Upper
    return client


def test_organize_endpoint(user_client: TestClient) -> None:
    resp = user_client.post("/text/organize", json={"text": "abc def"})

    assert resp.status_code == 200
    assert resp.json() == {"text": "ABC DEF"}
