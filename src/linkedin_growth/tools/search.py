"""Web search. Uses DDGS (meta-search), which needs no API key."""

from __future__ import annotations

from agno.tools.websearch import WebSearchTools


def recent_search(max_results: int = 6) -> WebSearchTools:
    """Search limited to the last week, for topics, news and trends.

    The time window is the point: LinkedIn content about AI ages in days, and
    without `timelimit` the search returns articles from 2023.
    """
    return WebSearchTools(
        enable_search=True,
        enable_news=True,
        timelimit="w",
        fixed_max_results=max_results,
    )


def broad_search(max_results: int = 8) -> WebSearchTools:
    """Search with no time window, for job posts, salaries and study material."""
    return WebSearchTools(
        enable_search=True,
        enable_news=False,
        fixed_max_results=max_results,
    )
