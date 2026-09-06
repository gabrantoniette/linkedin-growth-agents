"""Read-only tools: lookups into the reference material in `references/`.

Deliberately separate from `artifacts.py`. `content/` is what the system
PRODUCES; `references/` is supporting material the system only CONSULTS: hook
formulas, algorithm heuristics, lists of vocabulary to avoid. That is why there
is no `save_reference`: an agent should not be able to rewrite its own
reference base.

The goal is to reproduce, inside Agno, the progressive disclosure of Claude
Skills: the content enters the context only when the agent decides to call the
tool, instead of sitting in the instructions all the time.
"""

from __future__ import annotations

from pathlib import Path

from agno.tools import tool

from linkedin_growth.config import REFERENCES_DIR


def _resolve(relative_path: str) -> Path | None:
    """Resolve a path inside `references/`, or None if it tries to escape."""
    target = (REFERENCES_DIR / relative_path).resolve()
    root = REFERENCES_DIR.resolve()
    if root not in target.parents and target != root:
        return None
    return target


@tool
def read_reference(relative_path: str) -> str:
    """Read a reference file from inside the `references/` folder.

    Use it when you need hook formulas, LinkedIn algorithm heuristics,
    vocabulary to avoid or headline formulas, before writing rather than after.
    Call `list_references` first if you do not know the exact file name.

    Args:
        relative_path: Path from `references/`, with extension.
            Examples: 'hooks.md', 'linkedin-algorithm.md'.

    Returns:
        The file contents, or a description of the error.
    """
    target = _resolve(relative_path)
    if target is None:
        return f"ERROR: '{relative_path}' leaves the references/ folder."
    if not target.exists():
        return f"ERROR: references/{relative_path} does not exist."
    try:
        return target.read_text(encoding="utf-8")
    except OSError as error:
        return f"ERROR while reading: {error}"


@tool
def list_references() -> str:
    """List the reference files available in `references/`.

    Use it to discover what exists before asking for a specific file with
    `read_reference`.

    Returns:
        One path per line, or a note that the folder is empty.
    """
    if not REFERENCES_DIR.exists():
        return "No references yet."

    root = REFERENCES_DIR.resolve()
    found = sorted(
        str(p.resolve().relative_to(root)).replace("\\", "/")
        for p in REFERENCES_DIR.rglob("*")
        if p.is_file()
    )
    return "\n".join(found) if found else "No references yet."
