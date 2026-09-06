"""File tools: the agents read and write inside `content/`.

Everything is confined to `content/`. An agent has no business writing anywhere
else on disk, and a path check costs three lines.

Project convention: a tool never raises, it returns the error as text. That way
the agent reads the failure, understands it and tries another path, instead of
bringing the whole run down.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from agno.tools import tool

from linkedin_growth.config import CONTENT_DIR


def _resolve(relative_path: str) -> Path | None:
    """Resolve a path inside `content/`, or None if it tries to escape."""
    target = (CONTENT_DIR / relative_path).resolve()
    root = CONTENT_DIR.resolve()
    if root not in target.parents and target != root:
        return None
    return target


@tool
def save_artifact(relative_path: str, content: str) -> str:
    """Save a text file inside the project's `content/` folder.

    Use it at the end of a task to write the result: a diagnosis, a strategy, a
    calendar, a post draft. Overwrites the file if it already exists.

    Args:
        relative_path: Path from `content/`, with extension.
            Examples: 'diagnosis.md', 'posts/2026-09-02-rag.md'.
        content: Full text of the file, in markdown.

    Returns:
        Confirmation with the written path, or a description of the error.
    """
    target = _resolve(relative_path)
    if target is None:
        return (
            f"ERROR: '{relative_path}' leaves the content/ folder. "
            "Use a simple relative path."
        )
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written to content/{relative_path} ({len(content)} characters)."
    except OSError as error:
        return f"ERROR while writing: {error}"


@tool
def read_artifact(relative_path: str) -> str:
    """Read a text file from inside the `content/` folder.

    Use it to look up something you or another agent already produced: the
    strategy before planning the calendar, the calendar before writing a post.

    Args:
        relative_path: Path from `content/`.
            Examples: 'strategy.md', 'calendar/2026-W36.md'.

    Returns:
        The file contents, or a description of the error.
    """
    target = _resolve(relative_path)
    if target is None:
        return f"ERROR: '{relative_path}' leaves the content/ folder."
    if not target.exists():
        return f"ERROR: content/{relative_path} does not exist yet."
    try:
        return target.read_text(encoding="utf-8")
    except OSError as error:
        return f"ERROR while reading: {error}"


@tool
def list_artifacts(subfolder: str = "") -> str:
    """List the files already produced inside `content/`.

    Use it to find out what already exists before creating something from
    scratch.

    Args:
        subfolder: Subfolder to list. Empty lists everything, recursively.
            Examples: '', 'posts', 'calendar'.

    Returns:
        One path per line, or a note that the folder is empty.
    """
    base = _resolve(subfolder) if subfolder else CONTENT_DIR
    if base is None:
        return f"ERROR: '{subfolder}' leaves the content/ folder."
    if not base.exists():
        return "No files yet."

    root = CONTENT_DIR.resolve()
    found = sorted(
        str(p.resolve().relative_to(root)).replace("\\", "/")
        for p in base.rglob("*")
        if p.is_file()
    )
    return "\n".join(found) if found else "No files yet."


@tool
def today() -> str:
    """Return today's date in ISO form (YYYY-MM-DD) and the week number.

    Use it when naming post or calendar files, so the date is never a guess.
    """
    now = date.today()
    year, week, _ = now.isocalendar()
    return f"date={now.isoformat()} iso_week={year}-W{week:02d}"
