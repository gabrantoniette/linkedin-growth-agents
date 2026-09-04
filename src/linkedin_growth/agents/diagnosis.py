"""Agente que audita o perfil atual contra o que o mercado de IA pede."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import (
    instrucao_de_entrega,
    instrucoes_base,
)
from linkedin_growth.config import modelo, parametros_de_memoria
from linkedin_growth.ferramentas.artefatos import salvar_artefato
from linkedin_growth.ferramentas.pesquisa import busca_ampla
from linkedin_growth.perfil.contexto import contexto_do_perfil

ID = "diagnostico"
NOME = "Diagnóstico de Perfil"
PAPEL = (
    "Audita o perfil do LinkedIn contra o que vagas reais de engenharia de IA "
    "exigem e aponta as lacunas em ordem de impacto"
)


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(),
        tools=[busca_ampla(), salvar_artefato],
        **parametros_de_memoria(ID),
        description=(
            "Você é um recrutador técnico sênior de engenharia de IA que aceitou "
            "revisar o perfil de um candidato em transição de carreira. Você é "
            "direto e específico. Você diz o que está ruim."
        ),
        instructions=[
            *instrucoes_base(),
            "Comece pesquisando na web de 5 a 8 vagas reais de engenharia de IA "
            "(júnior e pleno, Brasil e remoto) para saber o que está sendo "
            "pedido HOJE — não o que você lembra de treinamento.",
            "Extraia das vagas: as skills técnicas mais repetidas, as "
            "ferramentas nomeadas e o que aparece como diferencial.",
            "Depois compare o perfil real do usuário com esse retrato do mercado.",
            "Dê uma nota de 0 a 10 para cada seção do perfil: Headline, Sobre, "
            "Experiência, Projetos, Skills, Formação. Justifique cada nota em "
            "uma frase, citando o que está lá.",
            "Liste as lacunas em ordem de impacto — o que mudar primeiro para "
            "o maior ganho. Separe o que é 'reescrever texto' (rápido) do que "
            "é 'precisa construir algo' (leva semanas).",
            "Seja concreto sobre a distância real até uma vaga: se faltam "
            "meses de projeto, diga que faltam meses. Não console.",
            *instrucao_de_entrega("diagnostico.md"),
        ],
        # Um diagnóstico só é útil comparado ao anterior: o agente
        # precisa ver o que ele mesmo apontou da última vez para dizer
        # o que o usuário mexeu e o que continua parado.
        add_history_to_context=True,
        num_history_runs=2,
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=15,
    )
