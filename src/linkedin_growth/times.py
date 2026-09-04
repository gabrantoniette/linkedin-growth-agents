"""O time coordenador — a superfície de conversa do sistema.

É este objeto que aparece no chat da `agent_ui` e no comando `linkedin chat`.
O líder recebe o pedido em linguagem natural, escolhe o especialista certo e
junta as respostas.

Modo `coordinate`: o líder delega e sintetiza. Alternativas do Agno são `route`
(devolve a resposta do membro sem sintetizar), `broadcast` (manda para todos) e
`tasks` (decompõe em lista de tarefas). Para um assistente de conversa,
`coordinate` é o que dá a experiência mais natural.

O modo vai como `TeamMode.coordinate`, o enum, e não como a string
`"coordinate"`. As duas funcionam em execução — `TeamMode` herda de `str` —, mas
o AgentOS serializa o time com `team.mode.value`, e uma string crua não tem
`.value`: o `GET /teams` responde 500 e a `agent_ui` mostra "No teams
Available", como se o time não existisse.

É também aqui que mora a memória de longo prazo do sistema. A regra: **os
agentes leem, o time escreve.** É na conversa que o usuário conta o que
prefere, o que construiu e o que deu certo; os comandos da CLI recebem sempre o
mesmo pedido enlatado e raramente aprendem algo novo.
"""

from __future__ import annotations

from agno.team import Team
from agno.team.mode import TeamMode

from linkedin_growth import agentes
from linkedin_growth.agentes.principios import instrucoes_base
from linkedin_growth.config import SESSAO_PADRAO, USUARIO_ID, db, memoria, modelo
from linkedin_growth.perfil.contexto import contexto_do_perfil

ID = "time-linkedin"
NOME = "Time de Presença no LinkedIn"


def construir(sessao: str | None = None) -> Team:
    """Monta o time. `sessao` escolhe qual conversa continuar.

    O id da sessão é o que separa "continuar conversando" de "começar do zero".
    Sem ele o Agno sorteia um novo a cada processo, e todo `linkedin chat`
    entraria na sala sem lembrar do anterior.
    """
    return Team(
        agentes.todos(),
        id=ID,
        name=NOME,
        model=modelo(),
        mode=TeamMode.coordinate,
        db=db(),
        user_id=USUARIO_ID,
        session_id=sessao or SESSAO_PADRAO,
        description=(
            "Você coordena um time que cuida da presença de um engenheiro em "
            "formação no LinkedIn, com foco em engenharia de IA."
        ),
        instructions=[
            *instrucoes_base(),
            "Escolha o membro pelo tipo de pedido:",
            "- auditar / avaliar o perfil -> Diagnóstico de Perfil",
            "- reescrever headline, Sobre, experiências, projetos -> Redator de Perfil",
            "- posicionamento, pilares, cadência -> Estrategista de Conteúdo",
            "- o que está acontecendo em IA, buscar pauta -> Pesquisador",
            "- calendário, planejar a semana -> Planejador Editorial",
            "- escrever um post -> Redator",
            "- revisar, criticar, melhorar um rascunho -> Editor",
            "- publicar no LinkedIn, checar a conexão -> Publicador",
            "Para escrever um post do zero, encadeie: Pesquisador (se o tema "
            "depende de novidade) -> Redator -> Editor. Não pule o Editor.",
            "Não delegue publicação sem o usuário ter pedido explicitamente. "
            "Publicar é irreversível e público.",
            "Se o perfil ainda não foi importado, oriente a rodar "
            "`uv run linkedin importar` antes de qualquer outra coisa.",
            "Responda de forma direta. Quando um membro produzir um arquivo, "
            "diga o caminho dele.",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        # Memória curta: os últimos turnos desta conversa, na íntegra.
        add_history_to_context=True,
        num_history_runs=5,
        # Memória longa: ao fim de cada execução o gerente destila o que vale a
        # pena guardar (o filtro está em `principios.instrucoes_de_memoria`) e
        # grava preso ao `user_id`. Da próxima vez isso volta pelo prompt de
        # sistema — inclusive para os agentes, numa conversa diferente.
        memory_manager=memoria(),
        update_memory_on_run=True,
        add_memories_to_context=True,
        # E quando a memória destilada não bastar, o líder ainda pode ir ler as
        # conversas antigas inteiras.
        search_past_sessions=True,
        num_past_sessions_to_search=3,
        show_members_responses=True,
    )
