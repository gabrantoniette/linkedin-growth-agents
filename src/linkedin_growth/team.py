"""The coordinating team: the system's conversational surface.

This is the object that shows up in the `agent_ui` chat and in the
`linkedin chat` command. The leader takes the request in natural language,
picks the right specialist and stitches the answers together.

`coordinate` mode: the leader delegates and synthesizes. Agno's alternatives
are `route` (returns the member's answer without synthesizing), `broadcast`
(sends to everyone) and `tasks` (decomposes into a task list). For a
conversational assistant, `coordinate` gives the most natural experience.

The mode goes in as `TeamMode.coordinate`, the enum, not the string
"coordinate". Both work at runtime, because `TeamMode` inherits from `str`, but
AgentOS serializes the team with `team.mode.value`, and a bare string has no
`.value`: `GET /teams` answers 500 and the `agent_ui` shows "No teams
Available", as if the team did not exist.

This is also where the system's long-term memory lives. The rule: **the agents
read, the team writes.** It is in conversation that the user says what they
prefer, what they built and what worked; the CLI commands always receive the
same canned request and rarely learn anything new.
"""

from __future__ import annotations

from agno.team import Team
from agno.team.mode import TeamMode

from linkedin_growth import agents
from linkedin_growth.agents.principles import base_instructions
from linkedin_growth.config import DEFAULT_SESSION, USER_ID, db, memory, model
from linkedin_growth.profile.context import profile_context

ID = "linkedin-team"
NAME = "LinkedIn Presence Team"


def build(session: str | None = None) -> Team:
    """Assemble the team. `session` picks which conversation to continue.

    The session id is what separates "keep talking" from "start over". Without
    it Agno draws a new one every process, and every `linkedin chat` would walk
    into the room with no memory of the last one.
    """
    return Team(
        agents.all_agents(),
        id=ID,
        name=NAME,
        model=model(),
        mode=TeamMode.coordinate,
        db=db(),
        user_id=USER_ID,
        session_id=session or DEFAULT_SESSION,
        description=(
            "Você coordena um time que cuida da presença de um engenheiro em "
            "formação no LinkedIn, com foco em engenharia de IA."
        ),
        instructions=[
            *base_instructions(),
            "Pick the member by the kind of request:",
            "- audit or review the profile -> Profile Diagnosis",
            "- rewrite headline, About, experiences, projects -> Profile Writer",
            "- positioning, pillars, cadence -> Content Strategist",
            "- what is happening in AI, find a topic -> Researcher",
            "- calendar, plan the week -> Editorial Planner",
            "- write a post -> Writer",
            "- review, critique, improve a draft -> Editor",
            "- publish to LinkedIn, check the connection -> Publisher",
            "To write a post from scratch, chain them: Researcher (if the topic "
            "depends on something new) -> Writer -> Editor. Do not skip the "
            "Editor.",
            "Do not delegate publishing unless the user asked for it "
            "explicitly. Publishing is irreversible and public.",
            "If the profile has not been imported yet, tell the user to run "
            "`uv run linkedin import` before anything else.",
            "Answer directly. When a member produces a file, say where it is.",
        ],
        additional_context=profile_context(),
        markdown=True,
        # Short memory: the last turns of this conversation, verbatim.
        add_history_to_context=True,
        num_history_runs=5,
        # Long memory: at the end of each run the manager distills what is worth
        # keeping (the filter is in `principles.memory_instructions`) and stores
        # it against the `user_id`. Next time it comes back through the system
        # prompt, including for the agents, in a different conversation.
        memory_manager=memory(),
        update_memory_on_run=True,
        add_memories_to_context=True,
        # And when the distilled memory is not enough, the leader can still go
        # read the old conversations in full.
        search_past_sessions=True,
        num_past_sessions_to_search=3,
        show_members_responses=True,
    )
