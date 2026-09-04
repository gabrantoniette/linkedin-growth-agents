"""Agente que escreve os textos do perfil, prontos para copiar e colar.

Lembrete que justifica o formato de saída: **não existe API para editar o
perfil do LinkedIn.** Nada aqui é aplicado automaticamente. O produto deste
agente é um documento em que cada bloco vem com a instrução de onde colar.
"""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import instrucoes_base
from linkedin_growth.config import db, modelo
from linkedin_growth.ferramentas.artefatos import ler_artefato, salvar_artefato
from linkedin_growth.ferramentas.referencias import ler_referencia
from linkedin_growth.perfil.contexto import contexto_do_perfil

NOME = "Redator de Perfil"
PAPEL = (
    "Escreve headline, seção Sobre, descrições de experiência e de projetos "
    "prontas para colar no LinkedIn"
)


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(),
        tools=[ler_artefato, salvar_artefato, ler_referencia],
        db=db(),
        description=(
            "Você escreve o texto de perfis do LinkedIn para profissionais "
            "técnicos. Você escreve como gente, não como consultoria."
        ),
        instructions=[
            *instrucoes_base(),
            "Se 'diagnostico.md' existir, leia primeiro com `ler_artefato` — "
            "ele diz onde estão as lacunas.",
            "Produza, nesta ordem:",
            "1. HEADLINE — antes de escrever, chame `ler_referencia` com "
            "'headline-formulas.md' para a fórmula e os antipadrões. Três "
            "opções, cada uma com no máximo 220 caracteres. Explique em uma "
            "linha o que cada opção prioriza e recomende uma.",
            "2. SOBRE — de 900 a 1500 caracteres. Abra com a frase mais forte "
            "(o LinkedIn corta em ~270). Estrutura: de onde ele vem, o que está "
            "construindo agora, o que quer fazer, como falar com ele.",
            "3. EXPERIÊNCIA — reescreva cada cargo REAL que existe nos dados. "
            "Duas a quatro linhas por cargo, focando no que é transferível para "
            "engenharia de IA (dados, automação, lógica, produto, comunicação). "
            "Não invente responsabilidade que não está descrita.",
            "4. PROJETOS — descrição para cada projeto real. Se ele tem poucos, "
            "diga isso e sugira dois ou três projetos concretos que ele poderia "
            "construir para preencher a lacuna, com escopo de uma a duas semanas.",
            "5. SKILLS — a lista exata a marcar no LinkedIn, ordenada por "
            "prioridade, separando 'já tenho' de 'terei quando terminar X'.",
            "Cada bloco começa com uma linha de instrução no formato: "
            "'>> Cole em: Perfil > Sobre > Editar'.",
            "Escreva os textos em português. Depois de cada um, dê a versão em "
            "inglês — recrutador internacional lê o perfil em inglês.",
            "Ao final, chame `salvar_artefato` com caminho 'perfil_otimizado.md'.",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=10,
    )
