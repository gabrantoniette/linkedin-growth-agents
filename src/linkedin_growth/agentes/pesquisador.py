"""Agente que traz matéria-prima da semana: o que está acontecendo em IA."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import instrucoes_base
from linkedin_growth.config import MODELO_RAPIDO, db, modelo
from linkedin_growth.ferramentas.artefatos import data_de_hoje
from linkedin_growth.ferramentas.pesquisa import busca_recente
from linkedin_growth.perfil.contexto import contexto_do_perfil

NOME = "Pesquisador"
PAPEL = (
    "Busca na web o que está acontecendo em engenharia de IA nesta semana e "
    "devolve material aproveitável para pauta"
)


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        # Modelo rápido: aqui o trabalho é volume de busca e triagem, não
        # julgamento fino. Opus seria dinheiro jogado fora.
        model=modelo(MODELO_RAPIDO),
        tools=[busca_recente(), data_de_hoje],
        db=db(),
        description=(
            "Você faz a curadoria semanal de engenharia de IA. Você separa o "
            "que é notícia real do que é anúncio de marketing."
        ),
        instructions=[
            *instrucoes_base(),
            "Chame `data_de_hoje` primeiro — você precisa saber a data real "
            "antes de falar em 'esta semana'.",
            "Faça de três a cinco buscas com ângulos diferentes: lançamentos de "
            "modelos e ferramentas, discussões técnicas, práticas de engenharia "
            "de LLM, e o recorte brasileiro quando houver.",
            "Priorize o que dá para o usuário ter opinião própria a partir da "
            "experiência dele. Notícia que ele só poderia repetir não serve.",
            "Descarte: anúncio de rodada de investimento, texto de hype sem "
            "conteúdo técnico, e qualquer coisa que ele não tenha como testar.",
            "Para cada item devolva: título, o link, uma frase do que é, e — o "
            "mais importante — o ÂNGULO que este usuário específico poderia "
            "usar, considerando o que ele já sabe e já construiu.",
            "Devolva de 5 a 8 itens. Não salve arquivo: seu resultado alimenta "
            "outro agente.",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=12,
    )
