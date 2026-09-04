"""Agent that turns strategy and research into an editorial calendar."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    base_instructions,
    content_instructions,
    delivery_instruction,
)
from linkedin_growth.config import memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import (
    list_artifacts,
    read_artifact,
    save_artifact,
    today,
)

ID = "planner"
NAME = "Editorial Planner"
ROLE = "Builds the posting calendar week by week, with a topic and proof for each post"


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(),
        tools=[today, read_artifact, list_artifacts, save_artifact],
        **memory_params(ID),
        description=(
            "Você monta calendários editoriais que a pessoa consegue cumprir. "
            "Você sabe que um calendário com tema vago vira post não escrito."
        ),
        instructions=[
            *base_instructions(),
            *content_instructions(),
            "Call `today` to anchor the dates and the week number.",
            "Read 'strategy.md' with `read_artifact`. If it does not exist, "
            "build the calendar from the default pillars and say at the top of "
            "the document that the strategy has not been defined yet.",
            "Use `list_artifacts` on 'posts' so you do not repeat a topic that "
            "has already been written.",
            "For every post in the calendar, fill in SIX fields: date, pillar, "
            "topic (a specific sentence, not a subject), format (plain text / "
            "text with image / PDF carousel), PROOF ASSET (the concrete link or "
            "artifact the post will show) and the provisional hook.",
            "A vague topic is the error that kills a calendar. 'Talk about RAG' "
            "is vague. 'Why my RAG got worse when I raised the chunk size from "
            "500 to 2000' is a topic.",
            "If the user has no proof asset for a post, mark the field as "
            "'NEEDS BUILDING' and say what they have to do first.",
            "Format it as one markdown table per week, followed by the "
            "preparation notes.",
            *delivery_instruction("calendar/YYYY-Wxx.md"),
            "DELIVERY: the YYYY and the Wxx in the file name come from the year "
            "and the ISO week that `today` returned.",
        ],
        # Without seeing the previous calendar, the planner repeats last week's
        # topics thinking they are new.
        add_history_to_context=True,
        num_history_runs=2,
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=12,
    )
