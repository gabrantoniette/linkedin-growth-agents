"""O time coordenador — a superfície de conversa do sistema.

É este objeto que aparece no chat da `agent_ui` e no comando `linkedin chat`.
O líder recebe o pedido em linguagem natural, escolhe o especialista certo e
junta as respostas.

Modo `coordinate`: o líder delega e sintetiza. Alternativas do Agno são `route`
(devolve a resposta do membro sem sintetizar), `broadcast` (manda para todos) e
`tasks` (decompõe em lista de tarefas). Para um assistente de conversa,
`coordinate` é o que dá a experiência mais natural.
"""

from __future__ import annotations

from agno.team import Team

from linkedin_growth import agentes
from linkedin_growth.agentes.principios import instrucoes_base
from linkedin_growth.config import db, modelo
from linkedin_growth.perfil.contexto import contexto_do_perfil

ID = "time-linkedin"
NOME = "Time de Presença no LinkedIn"


def construir() -> Team:
    return Team(
        agentes.todos(),
        id=ID,
        name=NOME,
        model=modelo(),
        mode="coordinate",
        db=db(),
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
        add_history_to_context=True,
        num_history_runs=5,
        show_members_responses=True,
    )
