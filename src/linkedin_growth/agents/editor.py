"""Agente que critica o rascunho contra a rubrica e entrega a versão final."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import (
    CABECALHO_POST,
    RUBRICA,
    instrucoes_base,
    instrucoes_de_conteudo,
)
from linkedin_growth.config import modelo, parametros_de_memoria
from linkedin_growth.ferramentas.artefatos import data_de_hoje, salvar_artefato
from linkedin_growth.ferramentas.referencias import ler_referencia, listar_referencias
from linkedin_growth.perfil.contexto import contexto_do_perfil

ID = "editor"
NOME = "Editor"
PAPEL = "Critica o rascunho contra uma rubrica e entrega a versão final revisada"


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(),
        tools=[data_de_hoje, salvar_artefato, ler_referencia, listar_referencias],
        **parametros_de_memoria(ID),
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
            "ENTREGA: salve com `salvar_artefato` em "
            "'posts/AAAA-MM-DD-<slug-do-tema>.md' ANTES de escrever as versões "
            "finais na resposta. O slug tem no máximo cinco palavras, "
            "minúsculas, separadas por hífen, sem acento.",
            "ENTREGA: depois de salvar, a resposta traz só as notas da rubrica, "
            "os três cortes de maior impacto e o caminho do arquivo. As versões "
            "finais completas ficam no arquivo — repetir tudo na resposta gasta "
            "o limite de tokens duas vezes.",
            "O arquivo salvo começa com este cabeçalho:",
            "---\ndata: AAAA-MM-DD\npilar: <pilar>\ntema: <tema>\n"
            "status: rascunho\nnota: <média>/10\n---",
            "FORMATO OBRIGATÓRIO do arquivo: as duas versões finais vêm sob "
            f"estes títulos, exatamente assim, sem inventar variação — "
            f"'{CABECALHO_POST['pt']}' e '{CABECALHO_POST['en']}'. É por eles "
            "que o comando `publicar` acha o texto; com outro título ele não "
            "acha nada e a publicação falha. A avaliação vem depois, sob outro "
            "título qualquer.",
            "Se a nota de VERDADE for 0, salve mesmo assim com "
            "'status: reprovado' e explique o que precisa sair.",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=8,
    )
