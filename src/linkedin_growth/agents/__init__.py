"""Os agentes especialistas do sistema.

Cada módulo expõe `construir()`, que devolve um `Agent` novo. A construção é
preguiçosa de propósito: montar um agente lê o perfil do disco e instancia o
cliente do modelo, e nada disso deve acontecer só porque alguém importou o
pacote.
"""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes import (
    diagnostico,
    editor,
    estrategista,
    perfil_writer,
    pesquisador,
    planejador,
    publicador,
    redator,
)

__all__ = [
    "diagnostico",
    "editor",
    "estrategista",
    "perfil_writer",
    "pesquisador",
    "planejador",
    "publicador",
    "redator",
    "todos",
]


def todos() -> list[Agent]:
    """Todos os agentes, na ordem em que aparecem no fluxo de trabalho."""
    return [
        diagnostico.construir(),
        perfil_writer.construir(),
        estrategista.construir(),
        pesquisador.construir(),
        planejador.construir(),
        redator.construir(),
        editor.construir(),
        publicador.construir(),
    ]
