"""
Mapeamento de intenção para o "Gerar cenário por IA".

Mesmo fluxo do character_agent: o texto livre (digitado ou ditado) é
classificado e, quando descreve um cenário, quebrado nos campos da tabela
`scenarios`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import BaseModel, Field

from prompt_clinica.ai.registry import build_chat_model, get_active
from prompt_clinica.scenario_options import GROUPS

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

ScenarioIntent = Literal["preencher_cenario", "fora_do_escopo"]

_CLOSED_FIELDS = {
    "location_type": "location",
    "time_of_day": "time_of_day",
    "weather": "weather",
    "atmosphere": "atmosphere",
}


class ScenarioDraft(BaseModel):
    name: str | None = Field(None, description="Nome curto do cenário, se citado ou sugerido pelo texto.")
    kind: str | None = Field(None, description="Tipo do lugar em uma ou duas palavras: Sala de aula, Rua, Quarto…")
    summary: str | None = Field(None, description="Resumo do lugar e do que ele representa na história.")
    details: str | None = Field(None, description="Detalhes visuais: objetos, materiais, luz, cores, texturas.")
    location_type: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    atmosphere: str | None = None


class ScenarioIntentResult(BaseModel):
    intent: ScenarioIntent
    message: str = Field("", description="Só em fora_do_escopo: o que falta para descrever um cenário.")
    scenario: ScenarioDraft | None = None


class ScenarioIntentRouter(Protocol):
    def route(self, text: str) -> ScenarioIntentResult: ...


def _options(group_id: str) -> str:
    return ", ".join(o.id for o in GROUPS[group_id].options)


_SYSTEM = f"""\
Você classifica o pedido de um escritor de HQ e extrai dados estruturados.

Intenções:
- preencher_cenario: o texto descreve um lugar ou ambiente (local, hora, clima, clima emocional, objetos…).
  Preencha `scenario` com o que o texto disser. Não invente o que não dá para deduzir: deixe nulo.
  Escreva os textos em português.
- fora_do_escopo: o texto não descreve um cenário. Explique em `message`, numa frase, o que descrever.

Campos de valor fechado (use exatamente um destes valores ou nulo):
- location_type: {_options("location")}
- time_of_day: {_options("time_of_day")}
- weather: {_options("weather")}
- atmosphere: {_options("atmosphere")}\
"""


def sanitize(result: ScenarioIntentResult) -> ScenarioIntentResult:
    """Descarta valores fora do catálogo nos campos fechados."""
    if result.scenario is None:
        return result
    draft = result.scenario
    for field, group_id in _CLOSED_FIELDS.items():
        value = getattr(draft, field)
        if value is not None and GROUPS[group_id].option(value) is None:
            setattr(draft, field, None)
    return result


class LangChainScenarioRouter:
    def __init__(self, model: BaseChatModel) -> None:
        # function_calling: ver LangChainIntentRouter em character_agent.
        self._chain = model.with_structured_output(ScenarioIntentResult, method="function_calling")

    def route(self, text: str) -> ScenarioIntentResult:
        result = self._chain.invoke([("system", _SYSTEM), ("human", text)])
        return sanitize(ScenarioIntentResult.model_validate(result))


def build_scenario_router() -> ScenarioIntentRouter:
    return LangChainScenarioRouter(build_chat_model(get_active("text")))
