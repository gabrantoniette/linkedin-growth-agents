"""Read-only tool: the recorded post metrics, with every ratio already computed.

The Performance Analyst interprets numbers; it does not produce them. Handing
it the raw CSV would invite it to divide, average and round on its own, and a
wrong division in a report reads exactly like a right one.
"""

from __future__ import annotations

from agno.tools import tool

from linkedin_growth import analytics


@tool
def metrics_summary() -> str:
    """Summarize the metrics of every published post the user imported.

    Use it before saying anything about how the posts performed. It returns,
    as markdown: one line per post (impressions, reach, engagement rate,
    comments per 1k impressions, profile views, followers), medians by origin,
    pillar, format and weekday, totals per ISO week, the hook of each post, the
    audience's job titles and seniority, and the gaps in the data.

    Returns:
        The summary, a note that nothing was imported yet, or an error.
    """
    try:
        return analytics.summarize(analytics.load_rows(), analytics.load_audience())
    except Exception as error:  # noqa: BLE001 - a tool never raises
        return f"ERROR while reading content/metrics.csv: {error}"
