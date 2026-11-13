from typing import Any

import pytest
from fastapi.testclient import TestClient

from prompt_clinica.ai.character_agent import (
    CharacterDraft,
    IntentResult,
    LangChainIntentRouter,
    build_intent_router,
)
from prompt_clinica.deps import get_current_user
from prompt_clinica.main import app


class _FakeChain:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.messages: list[Any] = []

    def invoke(self, messages: list[Any]) -> dict[str, Any]:
        self.messages = messages
        return self.result


class _FakeModel:
    def __init__(self, result: dict[str, Any]) -> None:
        self.chain = _FakeChain(result)
        self.method = ""

    def with_structured_output(self, _schema: type, method: str) -> _FakeChain:
        self.method = method
        return self.chain


def test_router_maps_description_to_draft() -> None:
    model = _FakeModel({
        "intent": "preencher_personagem",
        "character": {"name": "Lia", "gender": "Feminino", "age": 16, "skin_tone": "Morena",
                      "traits": ["tímida", "curiosa"]},
    })

    result = LangChainIntentRouter(model).route("Lia, 16 anos, morena, tímida e curiosa")  # type: ignore[arg-type]

    assert model.method == "function_calling"
    assert model.chain.messages[-1] == ("human", "Lia, 16 anos, morena, tímida e curiosa")
    assert result.intent == "preencher_personagem"
    assert result.character is not None
    assert result.character.name == "Lia"
    assert result.character.traits == ["tímida", "curiosa"]


def test_router_drops_values_outside_catalog() -> None:
    model = _FakeModel({
        "intent": "preencher_personagem",
        "character": {"gender": "Mulher", "body_type": "Magro", "ethnicity": "marciana"},
    })

    draft = LangChainIntentRouter(model).route("…").character  # type: ignore[arg-type]

    assert draft is not None
    assert draft.gender is None
    assert draft.body_type == "Magro"
    assert draft.ethnicity is None


def test_router_out_of_scope() -> None:
    model = _FakeModel({"intent": "fora_do_escopo", "message": "Descreva a aparência do personagem."})

    result = LangChainIntentRouter(model).route("qual a capital da França?")  # type: ignore[arg-type]

    assert result.intent == "fora_do_escopo"
    assert result.character is None


class _StubRouter:
    def route(self, text: str) -> IntentResult:
        return IntentResult(intent="preencher_personagem", character=CharacterDraft(summary=text))


@pytest.fixture
def user_client(client: TestClient) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[build_intent_router] = _StubRouter
    return client


def test_ai_draft_endpoint(user_client: TestClient) -> None:
    resp = user_client.post("/characters/ai-draft", json={"text": "cabelo ruivo e sardas"})

    assert resp.status_code == 200
    assert resp.json()["character"]["summary"] == "cabelo ruivo e sardas"


def test_ai_draft_rejects_short_text(user_client: TestClient) -> None:
    assert user_client.post("/characters/ai-draft", json={"text": "a"}).status_code == 422
