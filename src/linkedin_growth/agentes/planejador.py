"""Agente que transforma estratégia e pesquisa em calendário editorial."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import (
    instrucao_de_entrega,
    instrucoes_base,
    instrucoes_de_conteudo,
)
from linkedin_growth.config import modelo, parametros_de_memoria
from linkedin_growth.ferramentas.artefatos import (
    data_de_hoje,
    ler_artefato,
    listar_artefatos,
    salvar_artefato,
)
from linkedin_growth.perfil.contexto import contexto_do_perfil

ID = "planejador"
NOME = "Planejador Editorial"
PAPEL = "Monta o calendário de postagem semana a semana, com tema e prova para cada post"


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(),
        tools=[data_de_hoje, ler_artefato, listar_artefatos, salvar_artefato],
        **parametros_de_memoria(ID),
        description=(
            "Você monta calendários editoriais que a pessoa consegue cumprir. "
            "Você sabe que um calendário com tema vago vira post não escrito."
        ),
        instructions=[
            *instrucoes_base(),
            *instrucoes_de_conteudo(),
            "Chame `data_de_hoje` para ancorar as datas e o número da semana.",
            "Leia 'estrategia.md' com `ler_artefato`. Se não existir, monte o "
            "calendário a partir dos pilares padrão e avise no início do "
            "documento que a estratégia ainda não foi definida.",
            "Use `listar_artefatos` em 'posts' para não repetir tema já escrito.",
            "Para cada post do calendário, defina SEIS campos: data, pilar, "
            "tema (uma frase específica, não um assunto), formato (texto puro / "
            "texto com imagem / carrossel em PDF), ATIVO DE PROVA (o link ou "
            "artefato concreto que o post vai mostrar) e o gancho provisório.",
            "Tema vago é o erro que mata calendário. 'Falar sobre RAG' é vago. "
            "'Por que meu RAG piorou quando aumentei o chunk size de 500 para "
            "2000' é um tema.",
            "Se o usuário não tem ativo de prova para um post, marque o campo "
            "como 'PRECISA CONSTRUIR' e diga o que ele precisa fazer antes.",
            "Formate como uma tabela markdown por semana, seguida das notas de "
            "preparação.",
            *instrucao_de_entrega("calendario/AAAA-Wxx.md"),
            "ENTREGA: o AAAA e o Wxx do nome do arquivo vêm do ano e da "
            "semana ISO que `data_de_hoje` devolveu.",
        ],
        # Sem ver o calendário anterior, o planejador repete os temas
        # da semana passada achando que são novos.
        add_history_to_context=True,
        num_history_runs=2,
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=12,
    )
