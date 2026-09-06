"""Deterministic production flows.

When the order of the steps is known in advance, a `Workflow` beats a `Team`:
it spends no tokens deciding who does what, and the result is the same every
time.

Note: this repository's `agent_ui` only knows Agents and Teams, so Workflows do
not appear in the chat. They run from the CLI (`linkedin post`,
`linkedin calendar`).

**Why the steps are executors and not `Step(agent=...)`:** Agno builds an agent
step's message with `_prepare_message`, which *replaces* the workflow input with
the previous step's content. From the second step onward the original request is
gone. In practice that meant `linkedin post --topic "X"` produced a post about
something else (the writer only saw the list of news the researcher had pulled)
and `linkedin calendar --weeks 4` was ignored, because the planner never learned
how many weeks to plan. By composing the message by hand, every step gets both
things: the request, and the work of whoever came before.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path

from agno.agent import Agent
from agno.workflow import Step, StepInput, StepOutput, Workflow

from linkedin_growth.agents import editor, planner, researcher, writer
from linkedin_growth.config import POSTS_DIR, db

POST_ID = "post-flow"
WEEK_ID = "week-flow"

# Window for considering a file "written by this run".
RECENT_SECONDS = 300


def _slug(text: str, limit: int = 5) -> str:
    """'Por que meu RAG piorou' -> 'por-que-meu-rag-piorou'."""
    unaccented = (
        text.lower()
        .replace("ã", "a").replace("á", "a").replace("â", "a").replace("à", "a")
        .replace("é", "e").replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u").replace("ü", "u")
        .replace("ç", "c")
    )
    words = re.findall(r"[a-z0-9]+", unaccented)[:limit]
    return "-".join(words) or "post"


def step(
    name: str,
    build: Callable[[], Agent],
    message: Callable[[str, str], str],
) -> Step:
    """An agent step that decides explicitly what the agent will read.

    `message` receives the user's original request and the previous step's
    output, and returns the text the agent sees. This is the point where the
    flow guarantees the requested topic does not get lost down the line.
    """

    def run(step_input: StepInput) -> StepOutput:
        agent = build()
        output = agent.run(
            message(
                step_input.get_input_as_string() or "",
                step_input.previous_step_content or "",
            )
        )
        return StepOutput(content=str(output.content or ""), step_name=name)

    return Step(name=name, executor=run)


def _most_recent(folder: Path) -> Path | None:
    files = [p for p in folder.glob("*.md") if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def record_post(step_input: StepInput) -> StepOutput:
    """Make sure the post became a file, and report where it is.

    The Editor normally saves on its own, through the `save_artifact` tool. This
    step double-checks: if nothing was written in the last few minutes, it
    writes the file itself. A flow that runs to completion and leaves no file is
    worse than one that fails.
    """
    content = step_input.previous_step_content or ""
    topic = step_input.get_input_as_string() or "post"

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    recent = _most_recent(POSTS_DIR)

    if recent and (time.time() - recent.stat().st_mtime) < RECENT_SECONDS:
        path = recent
    else:
        path = POSTS_DIR / f"{date.today().isoformat()}-{_slug(topic)}.md"
        path.write_text(str(content), encoding="utf-8")

    return StepOutput(
        content=f"{content}\n\n---\n\nFile: {path}",
        step_name="record_post",
    )


def post_flow() -> Workflow:
    """Research -> write (pt + en) -> edit -> write the file."""
    return Workflow(
        id=POST_ID,
        name="Post Production",
        description="Researches the topic, writes it in Portuguese and English, reviews and saves.",
        db=db(),
        steps=[
            step(
                "research",
                researcher.build,
                lambda topic, _: (
                    f"TOPIC ALREADY DECIDED: {topic}\n\n"
                    "Gather supporting material for a post on THIS topic. Do "
                    "not curate the week and do not suggest other topics: the "
                    "user has already chosen."
                ),
            ),
            step(
                "writing",
                writer.build,
                lambda topic, research: (
                    f"POST TOPIC: {topic}\n\n"
                    "Write the post on that topic, and only on that topic.\n\n"
                    f"Material the research turned up:\n{research}"
                ),
            ),
            step(
                "editing",
                editor.build,
                lambda topic, draft: (
                    f"POST TOPIC: {topic}\n\n"
                    "Review the draft below. If it has drifted off topic, that "
                    "is a content problem: call it out and fix it.\n\n"
                    f"Draft:\n{draft}"
                ),
            ),
            Step(name="record", executor=record_post),
        ],
    )


def week_flow() -> Workflow:
    """Research the week -> build the editorial calendar."""
    return Workflow(
        id=WEEK_ID,
        name="Weekly Planning",
        description="Pulls the week's topics and builds the editorial calendar.",
        db=db(),
        steps=[
            step("research", researcher.build, lambda request, _: request),
            step(
                "calendar",
                planner.build,
                lambda request, topics: (
                    f"USER REQUEST: {request}\n\n"
                    "Build the calendar with exactly the number of weeks asked "
                    "for above.\n\n"
                    f"Topics the research turned up:\n{topics}"
                ),
            ),
        ],
    )


def all_flows() -> list[Workflow]:
    return [post_flow(), week_flow()]
