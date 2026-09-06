"""The deterministic flows, and what each step actually reads.

The defect these tests pin down was found by running the system for real:
`linkedin post --topic "cost and latency of an LLM pipeline"` produced a post
about a leaked API key. And `linkedin calendar --weeks 4` ignored the number of
weeks.

The cause was the same in both cases. Agno's `Step(agent=...)` builds the
message with `_prepare_message`, which **replaces** the workflow input with the
previous step's content. From the second step onward the user's request simply
does not exist any more: the writer only saw the list of news the researcher had
pulled, and wrote about the most eye-catching one.

None of that surfaces as an error. The flow finishes, the file is written, and
the user gets a well-written post about the wrong subject. So these tests look
at the text that reaches each agent, not at the final result.
"""

from __future__ import annotations

import pytest
from agno.workflow import StepInput

from linkedin_growth import flows

from .conftest import SpyModel

TOPIC = "o que eu aprendi medindo custo e latência de um pipeline com LLM"
RESEARCH = "1. LLMjacking: a leaked API key turns into token mining."


def _used_spies(no_api) -> list[SpyModel]:
    """Only the models that were actually called.

    Building an agent creates more than one model: the agent's own and the
    memory manager's, which runs at the end of a conversation and is never
    triggered in these tests.
    """
    return [spy for spy in no_api.created if spy.calls]


def messages_received(no_api) -> str:
    """Everything that reached a model during the test, system prompt included."""
    return "\n".join(spy.call_text(0) for spy in _used_spies(no_api))


def requests_received(no_api) -> str:
    """Only what the flow wrote as the request, without the agent's fixed instructions.

    The distinction matters: the researcher's instructions *mention* both working
    modes, so searching the whole prompt for 'TOPIC ALREADY DECIDED' would find
    the phrase even when the flow did not send it. What decides the behaviour is
    the user message.
    """
    parts = [
        str(message.content)
        for spy in _used_spies(no_api)
        for message in spy.calls[0]
        if message.role == "user"
    ]
    return "\n".join(parts)


# ==============================================================================
# The requested topic has to reach every step
# ==============================================================================


@pytest.mark.parametrize("index", [0, 1, 2])
def test_the_requested_topic_reaches_the_step(index, temp_db, no_api):
    """Researcher, writer and editor all need to know what the post is about.

    The research step got the topic because it is first; the other two saw only
    the text of whoever came before, and that is where the subject got lost.
    """
    workflow_step = flows.post_flow().steps[index]

    output = workflow_step.executor(
        StepInput(input=TOPIC, previous_step_content=RESEARCH)
    )

    assert output.content, f"step '{workflow_step.name}' produced nothing"
    assert TOPIC in requests_received(no_api), (
        f"step '{workflow_step.name}' did not receive the requested topic"
    )


def test_every_post_step_reads_both_the_topic_and_the_previous_step(temp_db, no_api):
    """The real check: what was written into the agent's message.

    Builds each step's message with the same function the flow uses and confirms
    the topic is there. If any step goes back to receiving only the previous
    content, this fails.
    """
    workflow = flows.post_flow()

    for workflow_step in workflow.steps[:3]:
        step_input = StepInput(input=TOPIC, previous_step_content=RESEARCH)
        output = workflow_step.executor(step_input)
        assert output.content

    messages = requests_received(no_api)
    assert messages.count(TOPIC) >= 3, (
        "the requested topic has to reach all three agents in the flow"
    )
    assert RESEARCH in messages, (
        "the previous step's work also has to keep arriving"
    )


def test_the_week_count_reaches_the_planner(temp_db, no_api):
    """`--weeks 4` only works if the planner knows there are four.

    It is the second step of the week flow, so it used to receive only the
    researcher's topics and planned whatever number it felt like.
    """
    request = "Levante as pautas desta semana e monte o calendário das próximas 4 semanas."
    workflow = flows.week_flow()

    output = workflow.steps[1].executor(
        StepInput(input=request, previous_step_content=RESEARCH)
    )

    assert output.content
    message = requests_received(no_api)
    assert "4 semanas" in message
    assert RESEARCH in message


# ==============================================================================
# The researcher has two modes, and the flow picks which
# ==============================================================================


def test_with_a_decided_topic_the_researcher_suggests_no_other_topics(temp_db, no_api):
    """The post flow settles the subject before the researcher starts.

    Without that the researcher does what it does by default, weekly curation,
    and returns 8 topics, of which the writer picks the flashiest instead of the
    one that was asked for.
    """
    flows.post_flow().steps[0].executor(StepInput(input=TOPIC))

    message = requests_received(no_api)
    assert "TOPIC ALREADY DECIDED" in message
    assert "do not suggest other topics" in message.lower()


def test_without_a_decided_topic_the_researcher_curates_the_week(temp_db, no_api):
    """The week flow settles nothing: there, curation is the service."""
    request = "Levante as pautas de engenharia de IA desta semana."

    flows.week_flow().steps[0].executor(StepInput(input=request))

    message = requests_received(no_api)
    assert "TOPIC ALREADY DECIDED" not in message
    assert request in message


def test_the_researcher_knows_how_to_tell_the_two_modes_apart(temp_db, no_api):
    """The agent's instructions have to cover both cases, not just one."""
    from linkedin_growth.agents import researcher

    instructions = " ".join(str(i) for i in (researcher.build().instructions or []))

    assert "TOPIC ALREADY DECIDED" in instructions
    assert "curat" in instructions


# ==============================================================================
# The contract between the Editor and the `publish` command
# ==============================================================================
# The Editor writes the file; `publish` cuts the body out of it by the version
# heading. While each side defined the format on its own, the Editor wrote
# '# Versão final (pt-BR)' and the command looked for '## Post (pt-BR)'. Result:
# three agents run, a nice file on disk, and `publish` dying with "could not
# find the 'pt' section".


def test_the_editor_gets_the_exact_headings_publish_looks_for(temp_db, no_api):
    """The agent's instruction comes from the same constant the cutter uses."""
    from linkedin_growth.agents import editor
    from linkedin_growth.agents.principles import POST_HEADING

    instructions = " ".join(str(i) for i in (editor.build().instructions or []))

    for heading in POST_HEADING.values():
        assert heading in instructions


@pytest.mark.parametrize("language", ["pt", "en"])
def test_publish_cuts_the_file_in_the_documented_format(language):
    """A file written the way the Editor is told to write it has to be readable."""
    from linkedin_growth.agents.principles import POST_HEADING
    from linkedin_growth.cli import _extract_section

    document = (
        "---\ndate: 2026-09-04\npillar: Understood\n---\n\n"
        f"{POST_HEADING['pt']}\n\nCorpo em português.\n\n"
        f"{POST_HEADING['en']}\n\nBody in English.\n\n"
        "## Avaliação\n\nscore 8/10\n"
    )

    body = _extract_section(document, language)

    expected = "Corpo em português." if language == "pt" else "Body in English."
    assert body == expected


def test_publish_does_not_swallow_the_evaluation_along_with_the_post():
    """The cut stops at the next heading. Without that, the rubric score tagged along."""
    from linkedin_growth.agents.principles import POST_HEADING
    from linkedin_growth.cli import _extract_section

    document = f"{POST_HEADING['en']}\n\nBody.\n\n## Avaliação\n\nscore 8/10\n"

    assert _extract_section(document, "en") == "Body."


def test_publish_says_so_when_the_heading_is_missing():
    """If the Editor invents another heading, the cut returns nothing and the CLI errors.

    That is the right behaviour: better to fail saying what is missing than to
    publish half a file to LinkedIn.
    """
    from linkedin_growth.cli import _extract_section

    assert _extract_section("# Versão final (pt-BR)\n\nCorpo.\n", "pt") is None


def test_a_post_rejected_by_the_editor_never_reaches_publish(tmp_path, monkeypatch):
    """Rejected by the Editor means rejected, and the command says so in those words.

    When the Editor zeroes the TRUTH criterion it deliberately omits the
    publishable headings so the cut finds no text. Without an explicit check the
    user got "could not find the 'pt' section" and went hunting for a format bug
    that does not exist.
    """
    from typer.testing import CliRunner

    from linkedin_growth import cli

    path = tmp_path / "2026-09-04-topic.md"
    path.write_text(
        "---\ndate: 2026-09-04\nstatus: rejected\nscore: 4.7/10\n---\n\n"
        "## Evaluation\n\nTruth: 0. The post claims a measurement that never happened.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "POSTS_DIR", tmp_path)

    result = CliRunner().invoke(cli.app, ["publish", str(path), "--dry-run"])

    assert result.exit_code == 1
    assert "rejected by the Editor" in result.output


def test_an_approved_post_passes_the_rejection_check(tmp_path):
    """The check must not block a normal post: it looks for the status, not the word."""
    import re

    from linkedin_growth.agents.principles import POST_HEADING
    from linkedin_growth.cli import _extract_section

    document = (
        "---\ndate: 2026-09-04\nstatus: draft\nscore: 8.1/10\n---\n\n"
        f"{POST_HEADING['pt']}\n\nCorpo aprovado.\n"
    )

    assert not re.search(r"^status:\s*rejected\s*$", document, re.MULTILINE)
    assert _extract_section(document, "pt") == "Corpo aprovado."
