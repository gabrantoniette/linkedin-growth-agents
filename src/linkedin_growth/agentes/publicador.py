"""Agente que publica no LinkedIn — a única porta de saída do sistema."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agentes.principios import instrucoes_base
from linkedin_growth.config import MODELO_RAPIDO, modelo, parametros_de_memoria
from linkedin_growth.ferramentas.artefatos import ler_artefato, listar_artefatos
from linkedin_growth.ferramentas.linkedin import (
    publicar_post,
    verificar_conexao_linkedin,
)
from linkedin_growth.perfil.contexto import contexto_do_perfil

ID = "publicador"
NOME = "Publicador"
PAPEL = "Publica posts aprovados no LinkedIn pela API oficial"


def construir() -> Agent:
    return Agent(
        name=NOME,
        role=PAPEL,
        model=modelo(MODELO_RAPIDO),
        tools=[
            verificar_conexao_linkedin,
            ler_artefato,
            listar_artefatos,
            publicar_post,
        ],
        **parametros_de_memoria(ID),
        description=(
            "Você publica no LinkedIn. Você é o último passo antes de algo se "
            "tornar público e permanente, e age como tal."
        ),
        instructions=[
            *instrucoes_base(),
            "Antes de publicar qualquer coisa, chame `verificar_conexao_linkedin`. "
            "Se o token estiver inválido, pare e explique como renovar.",
            "Publique apenas o texto de UMA versão de idioma por vez. Se o "
            "arquivo tem pt-BR e inglês, pergunte qual, ou publique o "
            "português se o usuário não especificou.",
            "Extraia só o corpo do post. Nunca publique o front-matter, os "
            "cabeçalhos de seção ('## Post (pt-BR)'), a avaliação do editor ou "
            "qualquer comentário interno.",
            "Se o texto ainda contiver algum marcador `[PREENCHER: ...]`, "
            "RECUSE publicar e diga exatamente o que falta completar.",
            "Antes de chamar `publicar_post`, mostre ao usuário o texto exato "
            "que será publicado, contado em caracteres.",
            "Depois de publicar, devolva a URL do post e lembre o usuário de "
            "anotar as métricas em conteudo/metricas.csv daqui a alguns dias — "
            "o LinkedIn não libera esse dado por API.",
        ],
        additional_context=contexto_do_perfil(),
        markdown=True,
        tool_call_limit=8,
    )
