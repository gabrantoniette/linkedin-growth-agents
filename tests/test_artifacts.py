"""The agents' file tools.

What matters most here is the confinement: an agent may only write inside
`content/`. If that check breaks, a badly formatted post turns into an overwrite
of `.env` or of source code.

The second convention under test is the module's own: a tool never raises, it
returns the error as text, so the agent can read the failure and try another
path instead of bringing the run down.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from linkedin_growth.tools.artifacts import (
    _resolve,
    list_artifacts,
    read_artifact,
    save_artifact,
    today,
)
from tests.conftest import call


# ==============================================================================
# Confinement to content/
# ==============================================================================


def test_resolve_with_a_simple_path_returns_a_target_inside_content(temp_content: Path):
    target = _resolve("posts/2026-09-03-rag.md")

    assert target is not None
    assert temp_content.resolve() in target.parents


@pytest.mark.parametrize(
    "escape",
    [
        "../secret.md",
        "../../.env",
        "posts/../../../pyproject.toml",
        "posts/../../src/linkedin_growth/config.py",
    ],
)
def test_resolve_with_path_traversal_returns_none(temp_content: Path, escape: str):
    """Any path that leaves content/ has to be refused."""
    assert _resolve(escape) is None


def test_save_artifact_with_path_traversal_writes_nothing_and_returns_an_error(
    temp_content: Path, tmp_path: Path
):
    forbidden_target = tmp_path / "breached.md"

    result = call(save_artifact, "../breached.md", "malicious content")

    assert result.startswith("ERROR")
    assert not forbidden_target.exists()


# ==============================================================================
# Writing and reading
# ==============================================================================


def test_save_artifact_writes_the_content_and_creates_the_subfolder(temp_content: Path):
    result = call(save_artifact, "posts/2026-09-03-agents.md", "# Post\n\nbody")

    written = temp_content / "posts" / "2026-09-03-agents.md"
    assert written.read_text(encoding="utf-8") == "# Post\n\nbody"
    assert "posts/2026-09-03-agents.md" in result


def test_save_and_read_artifact_preserves_accents(temp_content: Path):
    """The posts are written in Portuguese: losing accents here loses everything."""
    original = "Construí um agente. A pergunta é: compensou?"

    call(save_artifact, "strategy.md", original)
    read_back = call(read_artifact, "strategy.md")

    assert read_back == original


def test_reading_a_missing_artifact_returns_the_error_as_text(temp_content: Path):
    """The module's convention: an error is a return value, not an exception."""
    result = call(read_artifact, "does-not-exist.md")

    assert result.startswith("ERROR")
    assert "does not exist" in result


def test_save_artifact_overwrites_an_existing_file(temp_content: Path):
    call(save_artifact, "strategy.md", "first version")
    call(save_artifact, "strategy.md", "second version")

    assert call(read_artifact, "strategy.md") == "second version"


# ==============================================================================
# Listing
# ==============================================================================


def test_listing_with_nothing_there_says_it_is_empty(temp_content: Path):
    assert call(list_artifacts) == "No files yet."


def test_listing_uses_forward_slashes_even_on_windows(temp_content: Path):
    """The agent gets paths it will hand straight back to `read_artifact`.

    If they come out with backslashes on Windows, the path comes back different
    from the one the agent asked to write.
    """
    call(save_artifact, "posts/2026-09-03-rag.md", "x")
    call(save_artifact, "calendar/2026-W36.md", "y")

    listing = call(list_artifacts)

    assert "posts/2026-09-03-rag.md" in listing
    assert "calendar/2026-W36.md" in listing
    assert "\\" not in listing


def test_listing_a_subfolder_filters_to_it(temp_content: Path):
    call(save_artifact, "posts/one.md", "x")
    call(save_artifact, "calendar/two.md", "y")

    listing = call(list_artifacts, "posts")

    assert "posts/one.md" in listing
    assert "two.md" not in listing


# ==============================================================================
# Date
# ==============================================================================


def test_today_returns_iso_date_and_iso_week():
    """The Editor uses this to name files; a wrong format breaks the name."""
    result = call(today)

    assert re.fullmatch(r"date=\d{4}-\d{2}-\d{2} iso_week=\d{4}-W\d{2}", result)
