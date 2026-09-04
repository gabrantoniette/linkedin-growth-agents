"""Shared fixtures.

Three decisions that hold for the whole suite:

1. **No test calls the Anthropic API or the LinkedIn API.** Everything here is
   pure logic or I/O on a throwaway disk. A test that spends credit does not get
   run, and a test that does not get run is worth nothing.

2. **The agent tools are decorated with Agno's `@tool`**, so they are not
   directly callable: the object is a `Function`, and the original Python code
   lives in `.entrypoint`. The `call` helper centralizes that detail. If Agno
   changes the API, it changes here and not in thirty tests.

3. **The memory tests run real agents**, with a `SpyModel` in place of `Claude`
   and a throwaway database. It is the only way to answer "does the agent
   remember?": the answer is in the messages that reach the model, and only
   running them lets you see it.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from agno.models.anthropic import Claude
from agno.models.message import Message
from agno.models.response import ModelResponse

from linkedin_growth import config, team
from linkedin_growth.agents import (
    diagnosis,
    editor,
    planner,
    profile_writer,
    publisher,
    researcher,
    strategist,
    writer,
)
from linkedin_growth.tools import artifacts, references


def call(agent_tool: Any, *args: Any, **kwargs: Any) -> Any:
    """Run an Agno `@tool` as an ordinary Python function."""
    return agent_tool.entrypoint(*args, **kwargs)


@pytest.fixture
def temp_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `content/` at a throwaway folder.

    Without this a write test would dirty the user's real folder, and a path
    traversal test could genuinely write outside it.
    """
    root = tmp_path / "content"
    root.mkdir()
    monkeypatch.setattr(artifacts, "CONTENT_DIR", root)
    return root


@pytest.fixture
def temp_references(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `references/` at a throwaway folder."""
    root = tmp_path / "references"
    root.mkdir()
    monkeypatch.setattr(references, "REFERENCES_DIR", root)
    return root


# ==============================================================================
# Infrastructure for testing memory
# ==============================================================================
# The memory tests need two things the others do not: a model that never calls
# the API, and a throwaway database. Both live here.


class SpyModel(Claude):
    """A `Claude` that never talks to Anthropic and records what it received.

    The question "does the agent remember?" is only answered by looking at the
    messages that reach the model: that is where history, memories and summaries
    show up, or do not. This spy records every message list in `calls` and
    always returns the same answer, with no tool call, so the run is
    deterministic.

    It inherits from `Claude` on purpose: that way the object passes every check
    Agno runs against the real model (tool formatting, structured-output flags),
    and what is under test stays the real path rather than a mock-up of it.
    """

    def __init__(
        self,
        answer: str = "spy answer",
        model_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        # The model id is preserved because the system picks different models
        # for different work (Opus judges, Sonnet distills), and there is a test
        # that checks that choice.
        super().__init__(
            id=model_id or config.MAIN_MODEL,
            api_key="test-key",
            **kwargs,
        )
        self.answer = answer
        self.calls: list[list[Message]] = []

    # -- the model's only network point, replaced ---------------------------
    def invoke(  # type: ignore[override]
        self, messages: list[Message], assistant_message: Message, **kwargs: Any
    ) -> ModelResponse:
        self.calls.append(list(messages))
        assistant_message.metrics.start_timer()
        assistant_message.metrics.stop_timer()
        return ModelResponse(role="assistant", content=self.answer)

    # No test uses async or streaming. If one gets here it is a bug in the test,
    # and blowing up beats trying to reach the real API.
    async def ainvoke(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise AssertionError("a test tried to call the model in async mode")

    def invoke_stream(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("a test tried to call the model in streaming mode")

    async def ainvoke_stream(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("a test tried to call the model in streaming mode")

    # -- reading the captured messages --------------------------------------
    def call_text(self, index: int = -1) -> str:
        """Every message of one call, concatenated, for simple searching."""
        return "\n".join(str(m.content) for m in self.calls[index])

    def call_roles(self, index: int = -1) -> list[str]:
        return [str(m.role) for m in self.calls[index]]


class NoteTakingModel(SpyModel):
    """A spy that asks to store a memory on its first call.

    Agno's `MemoryManager` does not write memory from text: it hands the model
    an `add_memory` tool and stores whatever the model tells it to store. To
    test the write end to end, and not just the read, the fake model has to
    return that tool call.

    From the second call on it returns text, otherwise Agno's tool loop would
    never terminate.

    A warning for anyone extending this: Agno copies the model when assembling a
    run, so this object's `calls` can stay empty even when it worked. The
    reliable check is the database.
    """

    def __init__(self, memory: str, topics: list[str] | None = None) -> None:
        super().__init__()
        self.memory = memory
        self.topics = topics or []
        self.requests = 0

    def invoke(  # type: ignore[override]
        self, messages: list[Message], assistant_message: Message, **kwargs: Any
    ) -> ModelResponse:
        self.calls.append(list(messages))
        assistant_message.metrics.start_timer()
        assistant_message.metrics.stop_timer()
        self.requests += 1
        if self.requests > 1:
            return ModelResponse(role="assistant", content="done")
        return ModelResponse(
            role="assistant",
            tool_calls=[
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "add_memory",
                        "arguments": json.dumps(
                            {"memory": self.memory, "topics": self.topics}
                        ),
                    },
                }
            ],
        )


def stored_sessions(db_file: Path) -> list[tuple]:
    """Read `agno_sessions` straight from SQLite, bypassing Agno.

    On purpose: if the test asked Agno what it had stored, it would be trusting
    the very piece under test.
    """
    connection = sqlite3.connect(db_file)
    try:
        return connection.execute(
            "SELECT session_id, session_type, user_id FROM agno_sessions"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        connection.close()


def stored_memories(db_file: Path) -> list[tuple]:
    """Read `agno_memories` straight from SQLite. A missing table counts as empty."""
    connection = sqlite3.connect(db_file)
    try:
        return connection.execute("SELECT memory, user_id FROM agno_memories").fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        connection.close()


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the system's database at a throwaway file.

    Without this, running the suite would pollute the user's real history in
    `tmp/linkedin_growth.db`, and the tests would start depending on whatever
    was already there.
    """
    db_file = tmp_path / "memory_test.db"
    monkeypatch.setattr(config, "TMP_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_FILE", db_file)
    monkeypatch.setattr(config, "_db", None)
    # The memory manager is cached too, and it holds a reference to the
    # database. Without resetting it, the session's second test would write into
    # the first one's database.
    monkeypatch.setattr(config, "_memory", None)
    return db_file


@pytest.fixture
def no_api(monkeypatch: pytest.MonkeyPatch) -> Callable[..., SpyModel]:
    """Swap the real model for the spy in every module that builds agents.

    The modules do `from ...config import model`, so the function is already in
    each one's namespace: replacing it in `config` alone would not be enough.

    Returns a factory that also records every spy it creates, so a test can
    inspect any of them.
    """
    created: list[SpyModel] = []

    def factory(model_id: str | None = None) -> SpyModel:
        spy = SpyModel(model_id=model_id)
        created.append(spy)
        return spy

    factory.created = created  # type: ignore[attr-defined]

    monkeypatch.setattr(config, "model", factory)
    monkeypatch.setattr(team, "model", factory)
    for module in (
        diagnosis,
        editor,
        planner,
        profile_writer,
        publisher,
        researcher,
        strategist,
        writer,
    ):
        monkeypatch.setattr(module, "model", factory)

    return factory
