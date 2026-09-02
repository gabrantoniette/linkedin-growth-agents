"""Busca na web. Usa DDGS (meta-busca), que não exige chave de API."""

from __future__ import annotations

from agno.tools.websearch import WebSearchTools


def busca_recente(max_resultados: int = 6) -> WebSearchTools:
    """Busca limitada à última semana — para pauta, notícia e tendência.

    O recorte temporal é o ponto: conteúdo de LinkedIn sobre IA envelhece em
    dias, e sem `timelimit` a busca devolve artigo de 2023.
    """
    return WebSearchTools(
        enable_search=True,
        enable_news=True,
        timelimit="w",
        fixed_max_results=max_resultados,
    )


def busca_ampla(max_resultados: int = 8) -> WebSearchTools:
    """Busca sem recorte de tempo — para vagas, salários e material de estudo."""
    return WebSearchTools(
        enable_search=True,
        enable_news=False,
        fixed_max_results=max_resultados,
    )
