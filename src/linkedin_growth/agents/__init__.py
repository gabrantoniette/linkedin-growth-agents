"""The system's specialist agents.

Each module exposes `build()`, which returns a fresh `Agent`. Construction is
lazy on purpose: assembling an agent reads the profile from disk and
instantiates the model client, and none of that should happen just because
somebody imported the package.
"""

from __future__ import annotations

from agno.agent import Agent

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

__all__ = [
    "diagnosis",
    "editor",
    "planner",
    "profile_writer",
    "publisher",
    "researcher",
    "strategist",
    "writer",
    "all_agents",
]


def all_agents() -> list[Agent]:
    """Every agent, in the order they appear in the workflow."""
    return [
        diagnosis.build(),
        profile_writer.build(),
        strategist.build(),
        researcher.build(),
        planner.build(),
        writer.build(),
        editor.build(),
        publisher.build(),
    ]
