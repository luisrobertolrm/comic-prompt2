from typing import Any

import pytest
from fastapi.testclient import TestClient

from prompt_clinica.ai.scenario_agent import (
    LangChainScenarioRouter,
    ScenarioDraft,
    ScenarioIntentResult,
    build_scenario_router,
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
        "intent": "preencher_cenario",
        "scenario": {"name": "Templo na névoa", "location_type": "templo",
                     "time_of_day": "amanhecer", "weather": "neblina", "atmosphere": "misterioso"},
    })

    result = LangChainScenarioRouter(model).route("um templo antigo ao amanhecer, com neblina")  # type: ignore[arg-type]

    assert model.method == "function_calling"
    assert model.chain.messages[-1] == ("human", "um templo antigo ao amanhecer, com neblina")
    assert result.scenario is not None
    assert result.scenario.name == "Templo na névoa"
    assert result.scenario.weather == "neblina"


def test_router_drops_values_outside_catalog() -> None:
    model = _FakeModel({
        "intent": "preencher_cenario",
        "scenario": {"location_type": "lua", "time_of_day": "noite", "atmosphere": "Sombria"},
    })

    draft = LangChainScenarioRouter(model).route("…").scenario  # type: ignore[arg-type]

    assert draft is not None
    assert draft.location_type is None
    assert draft.time_of_day == "noite"
    assert draft.atmosphere is None


def test_router_out_of_scope() -> None:
    model = _FakeModel({"intent": "fora_do_escopo", "message": "Descreva o lugar."})

    result = LangChainScenarioRouter(model).route("quanto é 2+2?")  # type: ignore[arg-type]

    assert result.intent == "fora_do_escopo"
    assert result.scenario is None


class _StubRouter:
    def route(self, text: str) -> ScenarioIntentResult:
        return ScenarioIntentResult(intent="preencher_cenario", scenario=ScenarioDraft(details=text))


@pytest.fixture
def user_client(client: TestClient) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[build_scenario_router] = _StubRouter
    return client


def test_ai_draft_endpoint(user_client: TestClient) -> None:
    resp = user_client.post("/scenarios/ai-draft", json={"text": "lanternas de papel e chão de pedra"})

    assert resp.status_code == 200
    assert resp.json()["scenario"]["details"] == "lanternas de papel e chão de pedra"


def test_ai_draft_rejects_short_text(user_client: TestClient) -> None:
    assert user_client.post("/scenarios/ai-draft", json={"text": "a"}).status_code == 422
