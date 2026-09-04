"""Lookups into the supporting material in `references/`.

`references/` is read-only by design: it is the agents' reference base (hook
formulas, algorithm heuristics, banned vocabulary), and an agent should not be
able to rewrite its own reference.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_growth.tools import references as references_module
from linkedin_growth.tools.references import (
    _resolve,
    list_references,
    read_reference,
)
from tests.conftest import call


# ==============================================================================
# Read-only
# ==============================================================================


def test_module_exposes_no_write_tool():
    """If somebody adds a `save_reference`, this test raises its hand."""
    names = dir(references_module)

    assert not [n for n in names if n.startswith("save") or n.startswith("write")]


# ==============================================================================
# Confinement
# ==============================================================================


@pytest.mark.parametrize(
    "escape",
    ["../.env", "../../pyproject.toml", "subfolder/../../outside.md"],
)
def test_resolve_with_path_traversal_returns_none(temp_references: Path, escape: str):
    assert _resolve(escape) is None


def test_read_reference_with_path_traversal_returns_an_error(temp_references: Path):
    result = call(read_reference, "../.env")

    assert result.startswith("ERROR")
    assert "references/" in result


# ==============================================================================
# Reading
# ==============================================================================


def test_read_reference_returns_the_file_contents(temp_references: Path):
    (temp_references / "hooks.md").write_text("# Formulas\n\nF1: test", encoding="utf-8")

    assert call(read_reference, "hooks.md") == "# Formulas\n\nF1: test"


def test_reading_a_missing_reference_returns_the_error_as_text(temp_references: Path):
    result = call(read_reference, "does-not-exist.md")

    assert result.startswith("ERROR")
    assert "does not exist" in result


def test_listing_with_nothing_there_says_it_is_empty(temp_references: Path):
    assert call(list_references) == "No references yet."


def test_listing_returns_one_per_line_with_forward_slashes(temp_references: Path):
    (temp_references / "hooks.md").write_text("x", encoding="utf-8")
    (temp_references / "linkedin-algorithm.md").write_text("y", encoding="utf-8")

    listing = call(list_references)

    assert sorted(listing.splitlines()) == ["hooks.md", "linkedin-algorithm.md"]
    assert "\\" not in listing


# ==============================================================================
# The real reference files, which the agents cite by name
# ==============================================================================


@pytest.mark.parametrize(
    "file_name",
    [
        "hooks.md",
        "linkedin-algorithm.md",
        "ai-vocabulary.md",
        "headline-formulas.md",
    ],
)
def test_a_reference_cited_in_the_instructions_exists_in_the_repo(file_name: str):
    """The agents call `read_reference` with these exact names.

    Renaming a file without updating the agent instruction would leave the agent
    asking for a file that does not exist: a silent failure, hard to notice.
    """
    path = Path(__file__).resolve().parents[1] / "references" / file_name

    assert path.is_file(), (
        f"references/{file_name} is gone, but some agent still asks for it"
    )
