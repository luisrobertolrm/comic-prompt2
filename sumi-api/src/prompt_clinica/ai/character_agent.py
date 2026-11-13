"""
Mapeamento de intenção para o "Gerar personagem por IA".

O usuário descreve um personagem em texto livre (digitado ou ditado). O modelo
de texto ativo, via LangChain `with_structured_output`, classifica a intenção e,
quando é um personagem, quebra a descrição nos campos da tabela `characters`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import BaseModel, Field

from prompt_clinica.ai.registry import build_chat_model, get_active
from prompt_clinica.character_options import GROUPS

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

Intent = Literal["preencher_personagem", "fora_do_escopo"]

_CLOSED_FIELDS = ("gender", "body_type", "skin_tone", "ethnicity")


class CharacterDraft(BaseModel):
    name: str | None = Field(None, description="Nome do personagem, se citado ou sugerido pelo texto.")
    role: str | None = Field(None, description="Papel na história: Protagonista, Antagonista, Coadjuvante…")
    gender: str | None = None
    body_type: str | None = None
    skin_tone: str | None = None
    ethnicity: str | None = None
    age: int | None = Field(None, description="Idade em anos. Estime pela descrição se não for explícita.")
    height: str | None = Field(None, description="Altura no formato '1.60 m'.")
    summary: str | None = Field(None, description="Descrição visual: rosto, cabelo, olhos, corpo, marcas.")
    outfit: str | None = Field(None, description="Roupa e acessórios habituais.")
    traits: list[str] = Field(default_factory=list, description="Traços de personalidade, uma ou duas palavras cada.")


class IntentResult(BaseModel):
    intent: Intent
    message: str = Field("", description="Só em fora_do_escopo: o que falta para descrever um personagem.")
    character: CharacterDraft | None = None


class IntentRouter(Protocol):
    def route(self, text: str) -> IntentResult: ...


def _options(group_id: str) -> str:
    return ", ".join(o.id for o in GROUPS[group_id].options)


_SYSTEM = f"""\
Você classifica o pedido de um escritor de HQ e extrai dados estruturados.

Intenções:
- preencher_personagem: o texto descreve um personagem (aparência, idade, roupa, personalidade…).
  Preencha `character` com o que o texto disser. Não invente o que não dá para deduzir: deixe nulo.
  Escreva os textos em português.
- fora_do_escopo: o texto não descreve um personagem. Explique em `message`, numa frase, o que descrever.

Campos de valor fechado (use exatamente um destes valores ou nulo):
- gender: {_options("gender")}
- body_type: {_options("body_type")}
- skin_tone: {_options("skin_tone")}
- ethnicity: {_options("ethnicity")}\
"""


def sanitize(result: IntentResult) -> IntentResult:
    """Descarta valores fora do catálogo nos campos fechados."""
    if result.character is None:
        return result
    draft = result.character
    for field in _CLOSED_FIELDS:
        value = getattr(draft, field)
        if value is not None and GROUPS[field].option(value) is None:
            setattr(draft, field, None)
    return result


class LangChainIntentRouter:
    def __init__(self, model: BaseChatModel) -> None:
        # function_calling é o modo de saída estruturada aceito pela maioria dos
        # provedores OpenAI-compatíveis (BytePlus, MiniMax, Groq); json_schema não.
        self._chain = model.with_structured_output(IntentResult, method="function_calling")

    def route(self, text: str) -> IntentResult:
        result = self._chain.invoke([("system", _SYSTEM), ("human", text)])
        return sanitize(IntentResult.model_validate(result))


def build_intent_router() -> IntentRouter:
    return LangChainIntentRouter(build_chat_model(get_active("text")))
