"""Agente que define o posicionamento e a linha editorial."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import (
    instrucoes_base,
    instrucoes_de_conteudo,
)
from linkedin_growth.config import db, modelo
from linkedin_growth.ferramentas.artefatos import ler_artefato, salvar_artefato
from linkedin_growth.perfil.contexto import contexto_do_perfil

NOME = "Estrategista de Conteúdo"
PAPEL = (
    "Define posicionamento, pilares de conteúdo, público-alvo, tom e as "
    "métricas que valem a pena acompanhar"
)


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(),
        tools=[ler_artefato, salvar_artefato],
        db=db(),
        description=(
            "Você desenha estratégias de presença no LinkedIn para pessoas "
            "técnicas em transição de carreira. Você prefere um plano pequeno "
            "que a pessoa consegue manter a um plano ambicioso que ela abandona "
            "em três semanas."
        ),
        instructions=[
            *instrucoes_base(),
            *instrucoes_de_conteudo(),
            "Leia 'diagnostico.md' e 'metricas.csv' com `ler_artefato` se "
            "existirem. Se 'metricas.csv' tiver dados, use-os: os pilares que "
            "geraram comentário de gente da área devem ganhar mais espaço.",
            "Produza um documento de estratégia com estas seções:",
            "1. POSICIONAMENTO — a frase única que resume como ele quer ser "
            "percebido em seis meses. Uma frase, não um parágrafo.",
            "2. PÚBLICO — quem ele quer atrair, com nome de cargo e o que essa "
            "pessoa está procurando quando abre o LinkedIn.",
            "3. PILARES — os cinco pilares adaptados ao caso dele, com a "
            "proporção de cada um na semana e um exemplo de tema real para cada.",
            "4. CADÊNCIA — quantos posts por semana e em que dias, considerando "
            "que ele tem emprego e estuda. Seja realista: dois posts que saem "
            "valem mais que cinco planejados.",
            "5. TOM — como ele escreve, com exemplo de frase que soa como ele e "
            "exemplo de frase que NÃO soa.",
            "6. O QUE NÃO POSTAR — lista explícita para este caso específico.",
            "7. MÉTRICAS — o que olhar por mês e qual número seria sinal de que "
            "está funcionando.",
            "8. PRIMEIROS 30 DIAS — o que fazer nas quatro primeiras semanas.",
            "Ao final, chame `salvar_artefato` com caminho 'estrategia.md'.",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=10,
    )
