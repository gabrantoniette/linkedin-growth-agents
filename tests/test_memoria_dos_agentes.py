"""A memória dos agentes: o que o sistema guarda, o que ele relê e o que esquece.

A pergunta que estes testes respondem é literal: **um agente deste projeto
reaproveita o que aprendeu em conversas anteriores?** Hoje a resposta é sim, e
cada camada abaixo prova um pedaço dela.

1. **Configuração** — quais interruptores de memória do Agno cada agente liga.
   Barato de verificar, e é onde a política do sistema fica visível.
2. **Comportamento** — o que de fato chega ao modelo. Um espião no lugar do
   `Claude` grava as mensagens de cada chamada; história e memória ou aparecem
   ali, ou não existem. Nenhum teste toca a rede.
3. **Isolamento** — o que a memória NÃO deve atravessar: outra conversa
   nomeada, outro usuário. Uma memória que vaza é pior que memória nenhuma.

A política que estes testes protegem, em uma frase: **os agentes leem a
memória, o time escreve.** Está explicada em `config.parametros_de_memoria`.
"""

from __future__ import annotations

import pytest
from agno.agent import Agent
from agno.db.schemas.memory import UserMemory
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager

from linkedin_growth import agentes, config, times
from linkedin_growth.agentes import diagnostico, estrategista, planejador, redator
from linkedin_growth.agentes.principios import instrucoes_de_memoria

from .conftest import (
    ModeloEspiao,
    ModeloQueAnota,
    memorias_gravadas,
    sessoes_gravadas,
)

# Frase plantada na primeira conversa. É específica de propósito: se ela
# reaparecer numa chamada posterior, foi memória, não coincidência.
SEGREDO = "o post sobre chunking rendeu quatro mensagens de recrutador"

# Os três agentes cuja execução anterior importa para a próxima. Os outros
# cinco recebem sempre o mesmo pedido enlatado: reler o histórico seria custo
# sem ganho e, no caso do redator, risco de repetir o post da semana passada.
COM_HISTORICO = {
    "Diagnóstico de Perfil",
    "Estrategista de Conteúdo",
    "Planejador Editorial",
}


# ==============================================================================
# Camada 1 — configuração: a política de memória, escrita em código
# ==============================================================================


def test_todo_agente_sabe_de_quem_e_a_conversa(banco_temp, sem_api):
    """Sem `user_id` a memória não teria dono e nada seria recuperável.

    O Agno indexa memória por usuário. Com o campo em branco tudo cairia no
    balde "default" — que é onde estava antes desta implementação.
    """
    for entidade in [*agentes.todos(), times.construir()]:
        assert entidade.user_id == config.USUARIO_ID, entidade.name


def test_todo_agente_le_a_memoria(banco_temp, sem_api):
    """Ler é o mínimo: memória escrita e nunca lida é só um banco crescendo."""
    for entidade in [*agentes.todos(), times.construir()]:
        assert entidade.add_memories_to_context is True, entidade.name
        assert entidade.memory_manager is not None, entidade.name


def test_so_o_time_escreve_memoria(banco_temp, sem_api):
    """A divisão de trabalho do sistema, afirmada como invariante.

    O time escreve porque é na conversa que o usuário conta o que prefere e o
    que construiu. Os agentes da CLI não escrevem porque recebem sempre o mesmo
    comando enlatado: extrair memória ao fim de cada um seria uma chamada de
    modelo a mais para não guardar nada.
    """
    assert times.construir().update_memory_on_run is True

    for agente in agentes.todos():
        assert agente.update_memory_on_run is False, agente.name
        assert agente.enable_agentic_memory is False, agente.name


def test_o_gerente_de_memoria_e_unico_e_roda_no_modelo_rapido(banco_temp, sem_api):
    """Um gerente só, no modelo barato, sem poder apagar nada por conta própria.

    Destilar uma frase do que acabou de ser dito é trabalho mecânico, e essa
    chamada acontece ao fim de toda conversa — pagar Opus por ela seria
    desperdício. E apagar memória é decisão do usuário, pelo comando
    `linkedin memoria`, não de um modelo no meio de um turno.
    """
    gerente = config.memoria()

    assert config.memoria() is gerente, "o gerente é compartilhado, não recriado"
    assert gerente.model.id == config.MODELO_RAPIDO
    assert gerente.add_memories is True
    assert gerente.update_memories is True
    assert gerente.delete_memories is False
    assert gerente.clear_memories is False


def test_o_filtro_do_que_guardar_chega_ao_gerente(banco_temp, sem_api):
    """As instruções de captura são o que impede a memória de virar lixo.

    Sem elas o extrator guarda o texto dos posts, o que já está no perfil.yaml
    e o "bom dia" — e aí o contexto incha sem o sinal melhorar.
    """
    filtro = config.memoria().memory_capture_instructions

    assert filtro == instrucoes_de_memoria()
    assert "NÃO guarde o texto dos posts" in filtro
    assert "perfil.yaml" in filtro
    assert "HONESTIDADE" in filtro, (
        "a regra que nenhum agente pode quebrar vale para a memória também"
    )


def test_cada_agente_tem_a_propria_sessao_estavel(banco_temp, sem_api):
    """Sessão fixa por comando: as execuções de um agente se acumulam na dele.

    Sem `session_id` o Agno sorteia um novo a cada instância, e como
    `construir()` roda a cada comando da CLI, cada execução virava uma conversa
    órfã. Fixa, e separada por agente, o histórico de cada comando fica coeso.
    """
    sessoes = {agente.name: agente.session_id for agente in agentes.todos()}

    assert sessoes["Redator"] == config.sessao_do_agente("redator")
    assert all(sessao.startswith("cli-") for sessao in sessoes.values())
    assert len(set(sessoes.values())) == len(sessoes), (
        "dois agentes na mesma sessão misturariam os históricos"
    )


def test_o_time_continua_a_conversa_pedida(banco_temp, sem_api):
    """O id da sessão é o que separa 'continuar' de 'começar do zero'."""
    assert times.construir().session_id == config.SESSAO_PADRAO
    assert times.construir("experimento").session_id == "experimento"


def test_historico_so_onde_a_continuidade_importa(banco_temp, sem_api):
    """Nem todo agente ganha histórico — e isso é escolha, não esquecimento."""
    com_historico = {
        agente.name for agente in agentes.todos() if agente.add_history_to_context
    }

    assert com_historico == COM_HISTORICO
    assert times.construir().add_history_to_context is True

    for agente in agentes.todos():
        if agente.name in COM_HISTORICO:
            assert agente.num_history_runs == 2, agente.name


def test_so_o_estrategista_e_o_time_vasculham_conversas_antigas(banco_temp, sem_api):
    """`search_past_sessions` é caro em contexto: vai onde paga.

    O estrategista é quem precisa do que o usuário contou no chat sobre o que
    funcionou — isso vale mais que qualquer suposição do modelo sobre o
    algoritmo do LinkedIn.
    """
    buscam = {
        agente.name for agente in agentes.todos() if agente.search_past_sessions
    }

    assert buscam == {"Estrategista de Conteúdo"}
    assert estrategista.construir().num_past_sessions_to_search == 3
    assert times.construir().search_past_sessions is True


# ==============================================================================
# Camada 2 — comportamento: o que realmente chega ao modelo
# ==============================================================================


def test_o_time_continua_a_conversa_entre_processos(banco_temp, sem_api):
    """**O teste central.** Mesmo banco, processo novo: a conversa continua.

    Isto reproduz o que acontece de verdade — `uv run linkedin chat` hoje,
    `uv run linkedin chat` amanhã. Antes, cada construção abria uma sessão
    sorteada e o segundo time entrava na sala sem saber de nada.
    """
    primeiro = times.construir()
    primeiro.run(f"Anote isto: {SEGREDO}")

    segundo = times.construir()
    espiao: ModeloEspiao = segundo.model  # type: ignore[assignment]
    segundo.run("O que eu te contei da última vez?")

    assert primeiro.session_id == segundo.session_id
    assert SEGREDO in espiao.texto_da_chamada(0), (
        "o turno da conversa anterior volta ao contexto"
    )
    assert "assistant" in espiao.papeis_da_chamada(0)


def test_a_conversa_gravada_tem_dono(banco_temp, sem_api):
    """Uma sessão, com `user_id` — e não uma sessão anônima por execução."""
    times.construir().run(f"Anote isto: {SEGREDO}")
    times.construir().run("E agora?")

    sessoes = sessoes_gravadas(banco_temp)
    assert len(sessoes) == 1, "as duas execuções são a mesma conversa"
    assert sessoes[0][2] == config.USUARIO_ID


def test_o_agente_da_cli_ve_as_proprias_execucoes_anteriores(banco_temp, sem_api):
    """Dois `linkedin diagnosticar` seguidos: o segundo enxerga o primeiro."""
    diagnostico.construir().run("primeiro diagnóstico")

    segundo = diagnostico.construir()
    espiao: ModeloEspiao = segundo.model  # type: ignore[assignment]
    segundo.run("segundo diagnóstico")

    assert "primeiro diagnóstico" in espiao.texto_da_chamada(0)
    assert len({sessao[0] for sessao in sessoes_gravadas(banco_temp)}) == 1


def test_a_conversa_grava_memoria_e_um_agente_da_cli_a_le(banco_temp, sem_api):
    """**O ciclo completo.** O time aprende no chat; o redator usa no dia seguinte.

    É exatamente o que faltava antes: conhecimento adquirido numa conversa,
    aplicado numa execução diferente, de outro agente, em outra sessão.
    """
    lembranca = f"Gabriel contou que {SEGREDO}"
    # O gerente precisa de um modelo capaz de pedir `add_memory`; o espião
    # comum só devolve texto e nunca gravaria nada.
    config._memoria = MemoryManager(
        db=config.db(),
        model=ModeloQueAnota(lembranca, topicos=["conteúdo"]),
        memory_capture_instructions=instrucoes_de_memoria(),
    )

    times.construir().run(f"Anote isto: {SEGREDO}")

    gravadas = memorias_gravadas(banco_temp)
    assert len(gravadas) == 1, "a conversa deixou uma memória"
    assert SEGREDO in gravadas[0][0]
    assert gravadas[0][1] == config.USUARIO_ID

    agente = redator.construir()
    espiao: ModeloEspiao = agente.model  # type: ignore[assignment]
    agente.run("Sobre o que eu deveria escrever?")

    assert SEGREDO in espiao.texto_da_chamada(0), (
        "a memória da conversa chega ao agente que não participou dela"
    )
    assert espiao.papeis_da_chamada(0)[0] == "system", (
        "a memória entra pelo prompt de sistema, antes da pergunta"
    )


def test_a_memoria_alcanca_todos_os_agentes(banco_temp, sem_api):
    """Não é privilégio de um agente: quem lê a memória é o sistema inteiro."""
    MemoryManager(db=config.db()).add_user_memory(
        UserMemory(memory=f"Gabriel contou que {SEGREDO}"),
        user_id=config.USUARIO_ID,
    )

    for construir in (redator.construir, planejador.construir, estrategista.construir):
        agente = construir()
        espiao: ModeloEspiao = agente.model  # type: ignore[assignment]
        agente.run("o que você sabe de mim?")
        assert SEGREDO in espiao.texto_da_chamada(0), agente.name


# ==============================================================================
# Camada 3 — isolamento: o que a memória não pode atravessar
# ==============================================================================


def test_conversa_nomeada_nao_vaza_para_outra(banco_temp, sem_api):
    """`chat --sessao experimento` é uma conversa separada, e continua separada.

    É o que torna a sessão nomeada útil: dá para testar uma linha editorial
    diferente sem contaminar a conversa principal.
    """
    times.construir().run(f"Anote isto: {SEGREDO}")

    outra = times.construir("experimento")
    espiao: ModeloEspiao = outra.model  # type: ignore[assignment]
    outra.run("O que eu te contei da última vez?")

    assert SEGREDO not in espiao.texto_da_chamada(0)


def test_memoria_nao_vaza_entre_usuarios(banco_temp, sem_api):
    """A memória é indexada por `user_id` e não escapa dele.

    O projeto é de uma pessoa só, mas o `user_id` é configurável: se dois
    perfis dividirem o mesmo banco, o conteúdo de um não pode aparecer no
    contexto do outro.
    """
    MemoryManager(db=config.db()).add_user_memory(
        UserMemory(memory=f"Gabriel contou que {SEGREDO}"),
        user_id=config.USUARIO_ID,
    )

    espiao = ModeloEspiao()
    Agent(
        name="Redator",
        model=espiao,
        db=SqliteDb(db_file=str(banco_temp)),
        user_id="outra-pessoa",
        add_memories_to_context=True,
        memory_manager=MemoryManager(db=SqliteDb(db_file=str(banco_temp))),
    ).run("o que você sabe de mim?")

    assert SEGREDO not in espiao.texto_da_chamada(0)


def test_o_perfil_continua_chegando_a_toda_execucao(banco_temp, sem_api):
    """A memória se soma ao perfil; não o substitui.

    `additional_context` injeta `perfil/perfil.yaml` em toda execução. É o dado
    factual verificável — a base da regra de HONESTIDADE — e nada do que a
    memória aprende pode tomar o lugar dele.
    """
    agente = redator.construir()
    espiao: ModeloEspiao = agente.model  # type: ignore[assignment]
    agente.run("escreva um post")

    contexto = espiao.texto_da_chamada(0)
    assert "DADOS REAIS DO USUÁRIO" in contexto or "perfil.yaml" in contexto
    assert agente.additional_context


@pytest.mark.parametrize("construir", [redator.construir, times.construir])
def test_memoria_vazia_nao_quebra_nem_polui_o_prompt(construir, banco_temp, sem_api):
    """Primeira execução da vida do sistema: sem memória, e sem erro.

    Vale um teste porque é o caminho que todo mundo percorre no primeiro dia, e
    porque um bloco vazio de "memórias anteriores" no prompt seria ruído puro.
    """
    entidade = construir()
    espiao: ModeloEspiao = entidade.model  # type: ignore[assignment]
    saida = entidade.run("oi")

    assert saida.content
    assert "memories_from_previous_interactions" not in espiao.texto_da_chamada(0)
