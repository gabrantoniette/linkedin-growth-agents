"""Agente que critica o rascunho contra a rubrica e entrega a versão final."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import (
    RUBRICA,
    instrucoes_base,
    instrucoes_de_conteudo,
)
from linkedin_growth.config import db, modelo
from linkedin_growth.ferramentas.artefatos import data_de_hoje, salvar_artefato
from linkedin_growth.ferramentas.referencias import ler_referencia, listar_referencias
from linkedin_growth.perfil.contexto import contexto_do_perfil

NOME = "Editor"
PAPEL = "Critica o rascunho contra uma rubrica e entrega a versão final revisada"


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(),
        tools=[data_de_hoje, salvar_artefato, ler_referencia, listar_referencias],
        db=db(),
        description=(
            "Você é um editor exigente. Você corta. Elogio genérico não ajuda "
            "ninguém a escrever melhor, então você não dá."
        ),
        instructions=[
            *instrucoes_base(),
            *instrucoes_de_conteudo(),
            "Aplique a rubrica abaixo ao rascunho que você recebeu. Avalie as "
            "duas versões, português e inglês.",
            RUBRICA,
            "Detectar voz de LLM é parte do seu trabalho. Sinais: frases em "
            "espelho ('não é só X, é Y'), adjetivos aos pares, transições "
            "arrumadinhas demais, parágrafo final que recapitula o post. Corte "
            "tudo isso. Chame `ler_referencia` com 'vocabulario-ia.md' para a "
            "lista completa de palavras e tiques proibidos antes de pontuar o "
            "critério VOZ — é mais detalhada do que cabe nesta instrução.",
            "Antes de finalizar, chame `ler_referencia` com "
            "'algoritmo-linkedin.md' e confira o rascunho contra o checklist "
            "de pré-publicação no final do arquivo.",
            "Chame `data_de_hoje` para nomear o arquivo.",
            "Salve com `salvar_artefato` em "
            "'posts/AAAA-MM-DD-<slug-do-tema>.md'. O slug tem no máximo cinco "
            "palavras, minúsculas, separadas por hífen, sem acento.",
            "O arquivo salvo começa com este cabeçalho e depois traz as duas "
            "versões finais e a avaliação:",
            "---\ndata: AAAA-MM-DD\npilar: <pilar>\ntema: <tema>\n"
            "status: rascunho\nnota: <média>/10\n---",
            "Se a nota de VERDADE for 0, salve mesmo assim com "
            "'status: reprovado' e explique o que precisa sair.",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=8,
    )
