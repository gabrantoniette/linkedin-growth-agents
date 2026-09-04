"""O que o servidor precisa entregar para a `agent_ui` funcionar.

A UI monta o seletor de "Team" com o que `GET /teams` devolve. Quando essa rota
falha, `getTeamsAPI` engole o erro e devolve lista vazia — e o sintoma que
chega ao usuário não é "erro no servidor", é um seletor cinza escrito
"No teams Available", como se o time não existisse.

Foi o que aconteceu: `Team(mode="coordinate")` com a string crua. Funciona em
execução, porque `TeamMode` herda de `str`, mas o AgentOS serializa o time com
`team.mode.value` e uma string não tem `.value`. A rota respondia 500, a UI
mostrava só os agentes, e nada no terminal dizia que havia um erro.

Os testes batem no app de verdade, via `TestClient`, sem subir processo nem
abrir porta. É a única forma de pegar essa classe de bug: um campo que só é
lido na hora de montar a resposta HTTP e em nenhum outro lugar do sistema.
"""

from __future__ import annotations

import pytest
from agno.os import AgentOS
from agno.team.mode import TeamMode
from starlette.testclient import TestClient

from linkedin_growth import agentes, fluxos, times
from linkedin_growth.config import db


@pytest.fixture
def cliente(banco_temp, sem_api):
    """O AgentOS montado como em `agentos.py`, sobre o banco descartável."""
    agent_os = AgentOS(
        id="linkedin-growth-os-teste",
        name="LinkedIn Growth OS",
        db=db(),
        teams=[times.construir()],
        agents=agentes.todos(),
        workflows=fluxos.todos(),
    )
    with TestClient(agent_os.get_app()) as cliente:
        yield cliente


def test_o_modo_do_time_e_o_enum_e_nao_a_string(banco_temp, sem_api):
    """A string crua passa em tudo, menos na serialização. Daí o teste.

    Como `TeamMode` herda de `str`, `mode == "coordinate"` continua verdadeiro
    dos dois jeitos — o que torna o bug invisível em qualquer teste que compare
    valores. O que distingue é ter `.value`.
    """
    time = times.construir()

    assert isinstance(time.mode, TeamMode)
    assert time.mode.value == "coordinate"


def test_a_ui_encontra_o_time(cliente):
    """`GET /teams` responde 200 com o time — o seletor "Team" tem o que mostrar."""
    resposta = cliente.get("/teams")

    assert resposta.status_code == 200, resposta.text
    times_json = resposta.json()
    assert len(times_json) == 1

    time = times_json[0]
    assert time["id"] == times.ID
    assert time["name"] == times.NOME
    assert time["mode"] == "coordinate"
    # A UI lê `entity.id` para o valor do item e `entity.model` para o rótulo.
    # Qualquer um dos dois ausente quebra o seletor.
    assert time["model"]["provider"]
    assert len(time["members"]) == 8


def test_a_ui_encontra_os_agentes(cliente):
    """`GET /agents` continua respondendo — a regressão não pode ir para o outro lado."""
    resposta = cliente.get("/agents")

    assert resposta.status_code == 200, resposta.text
    lista = resposta.json()

    assert len(lista) == 8
    for agente in lista:
        assert agente["id"], agente.get("name")
        assert agente["model"]["model"]
