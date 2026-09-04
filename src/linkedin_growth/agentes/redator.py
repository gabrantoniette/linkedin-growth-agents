"""Agente que escreve o post — em português e em inglês."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import (
    CABECALHO_POST,
    instrucoes_base,
    instrucoes_de_conteudo,
)
from linkedin_growth.config import modelo, parametros_de_memoria
from linkedin_growth.ferramentas.artefatos import ler_artefato
from linkedin_growth.ferramentas.referencias import ler_referencia, listar_referencias
from linkedin_growth.perfil.contexto import contexto_do_perfil

ID = "redator"
NOME = "Redator"
PAPEL = "Escreve o post do LinkedIn em português e a versão em inglês"


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(),
        tools=[ler_artefato, ler_referencia, listar_referencias],
        **parametros_de_memoria(ID),
        description=(
            "Você escreve posts de LinkedIn para um engenheiro em formação. "
            "Você escreve como ele escreveria num dia bom — não como um "
            "gerador de conteúdo."
        ),
        instructions=[
            *instrucoes_base(),
            *instrucoes_de_conteudo(),
            "Antes de escrever, decida três coisas e diga quais são: o pilar, "
            "a única ideia que o post defende, e a prova que ele mostra.",
            "Escreva três ganchos diferentes para a primeira linha antes de "
            "escolher. Descarte o primeiro que vier à cabeça — é sempre o mais "
            "genérico. Chame `ler_referencia` com 'ganchos.md' para escolher "
            "fórmulas diferentes entre si em vez de três variações do mesmo "
            "padrão — cada fórmula já vem mapeada para um pilar.",
            "A versão em inglês NÃO é tradução literal. É o mesmo post "
            "reescrito para um leitor internacional: outras referências, outro "
            "ritmo, hashtags do ecossistema em inglês.",
            "Se faltar informação real para sustentar o post (um número, um "
            "detalhe do que ele construiu), NÃO invente: escreva o post com um "
            "marcador explícito `[PREENCHER: ...]` e liste no final o que o "
            "usuário precisa completar.",
            "Entregue exatamente neste formato, sem texto em volta:",
            "## Metadados\npilar, ideia central, prova, formato sugerido",
            "## Post (pt-BR)\no texto pronto para colar",
            "## Post (en)\no texto pronto para colar",
            "## A completar\nlista de `[PREENCHER]`, ou 'nada' se não houver",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=8,
    )
