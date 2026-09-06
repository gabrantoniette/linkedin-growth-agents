"""The `linkedin memory` command: the user's window into what the system keeps.

Memory you cannot inspect is memory you cannot trust. If an agent starts
repeating nonsense, this command is how you find out where it came from and how
you delete it, so it has to work in the annoying cases too: empty database,
abbreviated id, ambiguous prefix, id that does not exist.
"""

from __future__ import annotations

import pytest
from agno.db.schemas.memory import UserMemory
from typer.testing import CliRunner

from linkedin_growth import config
from linkedin_growth.cli import app


@pytest.fixture
def run(temp_db, no_api):
    """Run a CLI command and return the result."""
    runner = CliRunner()

    def invoke(*arguments: str, answer: str = ""):
        return runner.invoke(app, ["memory", *arguments], input=answer)

    return invoke


def text_of(result) -> str:
    """The output with whitespace normalized.

    Rich's table wraps to fit 80 columns, so comparing against the original
    sentence would fail because of the frame, not the content.
    """
    return " ".join(result.output.split())


def store(*memories: str, ids: list[str] | None = None) -> list[str]:
    """Plant memories in the test database and return their ids."""
    manager = config.memory()
    return [
        manager.add_user_memory(
            UserMemory(
                memory=memory,
                topics=["voice"],
                memory_id=ids[index] if ids else None,
            ),
            user_id=config.USER_ID,
        )
        for index, memory in enumerate(memories)
    ]


def test_an_empty_database_explains_how_to_fill_it(run):
    """This is everyone's first day: nothing stored, and the command shows the way."""
    result = run()

    assert result.exit_code == 0
    assert "does not remember anything yet" in text_of(result)
    assert "linkedin chat" in text_of(result)


def test_it_lists_what_the_system_remembers(run):
    # Short sentence on purpose: in a four-column table at 80 characters, a long
    # memory wraps onto two lines and the frame lands in the middle of it. What
    # is under test is that the row shows up, not how Rich lays it out.
    (identifier,) = store("hates the word 'jornada'")

    result = run()

    assert result.exit_code == 0
    assert "hates the word 'jornada'" in text_of(result)
    assert identifier[:8] in text_of(result), "the abbreviated id is what gets copied"
    assert "voice" in text_of(result)


def test_forget_accepts_the_abbreviated_id_the_table_shows(run):
    """The table cuts the id at eight characters; the command has to accept that.

    Without this the user would copy what they see on screen and get "does not
    exist", the worst way for a tool to fail.
    """
    (identifier,) = store("hates the word 'jornada'")

    result = run("--forget", identifier[:8])

    assert result.exit_code == 0
    assert "Forgotten" in result.output
    assert config.memory().get_user_memories(user_id=config.USER_ID) == []


def test_an_ambiguous_prefix_deletes_nothing(run):
    """Faced with two candidates, the command stops instead of choosing."""
    store("first memory", "second memory", ids=["abc-1", "abc-2"])

    result = run("--forget", "abc")

    assert result.exit_code == 1
    assert "Use more" in result.output
    assert len(config.memory().get_user_memories(user_id=config.USER_ID)) == 2


def test_a_missing_id_says_so_instead_of_failing_quietly(run):
    store("some memory")

    result = run("--forget", "does-not-exist")

    assert result.exit_code == 1
    assert "No memory starts with" in result.output
    assert len(config.memory().get_user_memories(user_id=config.USER_ID)) == 1


def test_clear_requires_confirmation_and_declining_deletes_nothing(run):
    """Deleting everything is irreversible: the prompt defaults to no."""
    store("some memory")

    result = run("--clear", answer="n\n")

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    assert len(config.memory().get_user_memories(user_id=config.USER_ID)) == 1
