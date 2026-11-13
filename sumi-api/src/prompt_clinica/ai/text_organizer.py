"""
"Organizar" um texto livre (muitas vezes ditado): só pontua, corrige e
divide em parágrafos. Não acrescenta conteúdo.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from prompt_clinica.ai.registry import build_chat_model, get_active

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class TextOrganizer(Protocol):
    def organize(self, text: str) -> str: ...


_SYSTEM = """\
Você é um revisor. Reorganize o texto do usuário sem mudar o conteúdo:
- corrija pontuação, ortografia, acentuação e maiúsculas;
- divida em frases e parágrafos coerentes, na ordem lógica das ideias;
- remova repetições e vícios de fala de ditado ("é…", "tipo", "né", "aí");
- mantenha o idioma, as palavras e o estilo do autor.
Proibido: acrescentar ideias, nomes, fatos, detalhes ou conclusões; resumir; comentar.
Responda apenas com o texto organizado, sem aspas nem explicações.\
"""


class LangChainTextOrganizer:
    def __init__(self, model: BaseChatModel) -> None:
        self._model = model

    def organize(self, text: str) -> str:
        reply = self._model.invoke([("system", _SYSTEM), ("human", text)])
        content = reply.content
        if isinstance(content, list):
            content = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
        return str(content).strip()


def build_text_organizer() -> TextOrganizer:
    return LangChainTextOrganizer(build_chat_model(get_active("text")))
