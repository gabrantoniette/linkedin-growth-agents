"""The agents' memory: what the system keeps, what it re-reads, what it forgets.

The question these tests answer is literal: **does an agent in this project
reuse what it learned in earlier conversations?** Today the answer is yes, and
each layer below proves a piece of it.

1. **Configuration**: which of Agno's memory switches each agent turns on.
   Cheap to check, and it is where the system's policy becomes visible.
2. **Behaviour**: what actually reaches the model. A spy in place of `Claude`
   records the messages of every call; history and memory either show up there,
   or they do not exist. No test touches the network.
3. **Isolation**: what memory must NOT cross - another named conversation,
   another user. Memory that leaks is worse than no memory at all.

The policy these tests protect, in one sentence: **the agents read memory, the
team writes it.** It is explained in `config.memory_params`.
"""

from __future__ import annotations

import pytest
from agno.agent import Agent
from agno.db.schemas.memory import UserMemory
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager

from linkedin_growth import agents, config, team
from linkedin_growth.agents import diagnosis, planner, strategist, writer
from linkedin_growth.agents.principles import memory_instructions

from .conftest import (
    NoteTakingModel,
    SpyModel,
    stored_memories,
    stored_sessions,
)

# A fact planted in the first conversation. Specific on purpose: if it shows up
# in a later call, that was memory, not coincidence.
SECRET = "o post sobre chunking rendeu quatro mensagens de recrutador"

# The three agents whose previous run matters to the next one. The other five
# always receive the same canned request: re-reading history would be cost with
# no gain and, for the writer, a risk of repeating last week's post.
WITH_HISTORY = {
    "Profile Diagnosis",
    "Content Strategist",
    "Editorial Planner",
}


# ==============================================================================
# Layer 1 - configuration: the memory policy, written in code
# ==============================================================================


def test_every_agent_knows_whose_conversation_it_is(temp_db, no_api):
    """Without `user_id` the memory would have no owner and nothing would be retrievable.

    Agno indexes memory by user. With the field blank everything lands in the
    "default" bucket, which is where it was before this implementation.
    """
    for entity in [*agents.all_agents(), team.build()]:
        assert entity.user_id == config.USER_ID, entity.name


def test_every_agent_reads_memory(temp_db, no_api):
    """Reading is the minimum: memory written and never read is just a growing database."""
    for entity in [*agents.all_agents(), team.build()]:
        assert entity.add_memories_to_context is True, entity.name
        assert entity.memory_manager is not None, entity.name


def test_only_the_team_writes_memory(temp_db, no_api):
    """The system's division of labour, asserted as an invariant.

    The team writes because it is in conversation that the user says what they
    prefer and what they built. The CLI agents do not write because they always
    receive the same canned command: extracting memory at the end of each one
    would be an extra model call to store nothing.
    """
    assert team.build().update_memory_on_run is True

    for agent in agents.all_agents():
        assert agent.update_memory_on_run is False, agent.name
        assert agent.enable_agentic_memory is False, agent.name


def test_the_memory_manager_is_shared_and_runs_on_the_fast_model(temp_db, no_api):
    """One manager, on the cheap model, unable to delete anything on its own.

    Distilling one sentence out of what was just said is mechanical work, and
    that call happens at the end of every conversation: paying Opus for it would
    be waste. And erasing memory is the user's decision, through the
    `linkedin memory` command, not a model's mid-turn.
    """
    manager = config.memory()

    assert config.memory() is manager, "the manager is shared, not rebuilt"
    assert manager.model.id == config.FAST_MODEL
    assert manager.add_memories is True
    assert manager.update_memories is True
    assert manager.delete_memories is False
    assert manager.clear_memories is False


def test_the_filter_of_what_to_keep_reaches_the_manager(temp_db, no_api):
    """The capture instructions are what keeps memory from turning into landfill.

    Without them the extractor stores the text of the posts, what is already in
    profile.yaml and the small talk, and context bloats with no gain in signal.
    """
    capture_filter = config.memory().memory_capture_instructions

    assert capture_filter == memory_instructions()
    assert "Do NOT keep the text of the posts" in capture_filter
    assert "profile.yaml" in capture_filter
    assert "HONESTY" in capture_filter, (
        "the rule no agent may break applies to memory too"
    )


def test_each_agent_has_its_own_stable_session(temp_db, no_api):
    """A fixed session per command: an agent's runs accumulate in its own.

    Without `session_id` Agno draws a new one per instance, and since `build()`
    runs on every CLI command, each run used to become an orphan conversation.
    Fixed, and separated by agent, each command's history stays coherent.
    """
    sessions = {agent.name: agent.session_id for agent in agents.all_agents()}

    assert sessions["Writer"] == config.agent_session("writer")
    assert all(session.startswith("cli-") for session in sessions.values())
    assert len(set(sessions.values())) == len(sessions), (
        "two agents in the same session would mix their histories"
    )


def test_the_team_continues_the_conversation_it_was_asked_for(temp_db, no_api):
    """The session id is what separates 'continue' from 'start over'."""
    assert team.build().session_id == config.DEFAULT_SESSION
    assert team.build("experiment").session_id == "experiment"


def test_history_only_where_continuity_matters(temp_db, no_api):
    """Not every agent gets history, and that is a choice, not an oversight."""
    with_history = {
        agent.name for agent in agents.all_agents() if agent.add_history_to_context
    }

    assert with_history == WITH_HISTORY
    assert team.build().add_history_to_context is True

    for agent in agents.all_agents():
        if agent.name in WITH_HISTORY:
            assert agent.num_history_runs == 2, agent.name


def test_only_the_strategist_and_the_team_search_old_conversations(temp_db, no_api):
    """`search_past_sessions` is expensive in context: it goes where it pays.

    The strategist is the one that needs what the user said in chat about what
    worked, which is worth more than any guess the model makes about LinkedIn's
    algorithm.
    """
    searching = {
        agent.name for agent in agents.all_agents() if agent.search_past_sessions
    }

    assert searching == {"Content Strategist"}
    assert strategist.build().num_past_sessions_to_search == 3
    assert team.build().search_past_sessions is True


# ==============================================================================
# Layer 2 - behaviour: what actually reaches the model
# ==============================================================================


def test_the_team_continues_the_conversation_across_processes(temp_db, no_api):
    """**The central test.** Same database, new process: the conversation continues.

    This reproduces what really happens: `uv run linkedin chat` today,
    `uv run linkedin chat` tomorrow. Before, each build opened a randomly drawn
    session and the second team walked into the room knowing nothing.
    """
    first = team.build()
    first.run(f"Anote isto: {SECRET}")

    second = team.build()
    spy: SpyModel = second.model  # type: ignore[assignment]
    second.run("O que eu te contei da última vez?")

    assert first.session_id == second.session_id
    assert SECRET in spy.call_text(0), (
        "the previous conversation's turn comes back into context"
    )
    assert "assistant" in spy.call_roles(0)


def test_the_stored_conversation_has_an_owner(temp_db, no_api):
    """One session, with a `user_id`, not one anonymous session per run."""
    team.build().run(f"Anote isto: {SECRET}")
    team.build().run("E agora?")

    sessions = stored_sessions(temp_db)
    assert len(sessions) == 1, "the two runs are the same conversation"
    assert sessions[0][2] == config.USER_ID


def test_a_cli_agent_sees_its_own_earlier_runs(temp_db, no_api):
    """Two `linkedin diagnose` in a row: the second one sees the first."""
    diagnosis.build().run("first diagnosis")

    second = diagnosis.build()
    spy: SpyModel = second.model  # type: ignore[assignment]
    second.run("second diagnosis")

    assert "first diagnosis" in spy.call_text(0)
    assert len({session[0] for session in stored_sessions(temp_db)}) == 1


def test_the_conversation_writes_memory_and_a_cli_agent_reads_it(temp_db, no_api):
    """**The full cycle.** The team learns in chat; the writer uses it the next day.

    This is exactly what was missing before: knowledge acquired in one
    conversation, applied in a different run, by another agent, in another
    session.
    """
    memory_text = f"Gabriel contou que {SECRET}"
    # The manager needs a model capable of asking for `add_memory`; the ordinary
    # spy only returns text and would never store anything.
    config._memory = MemoryManager(
        db=config.db(),
        model=NoteTakingModel(memory_text, topics=["content"]),
        memory_capture_instructions=memory_instructions(),
    )

    team.build().run(f"Anote isto: {SECRET}")

    stored = stored_memories(temp_db)
    assert len(stored) == 1, "the conversation left a memory behind"
    assert SECRET in stored[0][0]
    assert stored[0][1] == config.USER_ID

    agent = writer.build()
    spy: SpyModel = agent.model  # type: ignore[assignment]
    agent.run("Sobre o que eu deveria escrever?")

    assert SECRET in spy.call_text(0), (
        "the conversation's memory reaches an agent that was not part of it"
    )
    assert spy.call_roles(0)[0] == "system", (
        "memory enters through the system prompt, before the question"
    )


def test_memory_reaches_every_agent(temp_db, no_api):
    """Not one agent's privilege: the whole system reads memory."""
    MemoryManager(db=config.db()).add_user_memory(
        UserMemory(memory=f"Gabriel contou que {SECRET}"),
        user_id=config.USER_ID,
    )

    for build in (writer.build, planner.build, strategist.build):
        agent = build()
        spy: SpyModel = agent.model  # type: ignore[assignment]
        agent.run("o que você sabe de mim?")
        assert SECRET in spy.call_text(0), agent.name


# ==============================================================================
# Layer 3 - isolation: what memory must not cross
# ==============================================================================


def test_a_named_conversation_does_not_leak_into_another(temp_db, no_api):
    """`chat --session experiment` is a separate conversation, and stays separate.

    That is what makes a named session useful: you can try a different editorial
    line without contaminating the main conversation.
    """
    team.build().run(f"Anote isto: {SECRET}")

    other = team.build("experiment")
    spy: SpyModel = other.model  # type: ignore[assignment]
    other.run("O que eu te contei da última vez?")

    assert SECRET not in spy.call_text(0)


def test_memory_does_not_leak_between_users(temp_db, no_api):
    """Memory is indexed by `user_id` and does not escape it.

    The project serves one person, but `user_id` is configurable: if two
    profiles share a database, one's content must not show up in the other's
    context.
    """
    MemoryManager(db=config.db()).add_user_memory(
        UserMemory(memory=f"Gabriel contou que {SECRET}"),
        user_id=config.USER_ID,
    )

    spy = SpyModel()
    Agent(
        name="Writer",
        model=spy,
        db=SqliteDb(db_file=str(temp_db)),
        user_id="someone-else",
        add_memories_to_context=True,
        memory_manager=MemoryManager(db=SqliteDb(db_file=str(temp_db))),
    ).run("o que você sabe de mim?")

    assert SECRET not in spy.call_text(0)


def test_the_profile_still_reaches_every_run(temp_db, no_api):
    """Memory adds to the profile; it does not replace it.

    `additional_context` injects `profile/profile.yaml` into every run. That is
    the verifiable factual data, the basis of the HONESTY rule, and nothing
    memory learns may take its place.
    """
    agent = writer.build()
    spy: SpyModel = agent.model  # type: ignore[assignment]
    agent.run("escreva um post")

    context = spy.call_text(0)
    assert "DADOS REAIS DO USUÁRIO" in context or "profile.yaml" in context
    assert agent.additional_context


@pytest.mark.parametrize("build", [writer.build, team.build])
def test_empty_memory_neither_breaks_nor_pollutes_the_prompt(build, temp_db, no_api):
    """The system's first ever run: no memory, and no error.

    Worth a test because it is the path everyone walks on day one, and because
    an empty "previous memories" block in the prompt would be pure noise.
    """
    entity = build()
    spy: SpyModel = entity.model  # type: ignore[assignment]
    output = entity.run("oi")

    assert output.content
    assert "memories_from_previous_interactions" not in spy.call_text(0)
