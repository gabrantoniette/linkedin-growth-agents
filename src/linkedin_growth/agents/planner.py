"""Agent that turns strategy and research into an editorial calendar."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    base_instructions,
    content_instructions,
    delivery_instruction,
)
from linkedin_growth.config import memory_params, model, posts_knowledge
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import (
    list_artifacts,
    read_artifact,
    save_artifact,
    today,
)
from linkedin_growth.retrieval import build_retriever
from linkedin_growth.tools.references import list_references, read_reference

ID = "planner"
NAME = "Editorial Planner"
ROLE = "Builds the posting calendar week by week, with a topic and proof for each post"


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(),
        tools=[
            today,
            read_artifact,
            list_artifacts,
            save_artifact,
            read_reference,
            list_references,
        ],
        **memory_params(ID),
        # The factory, not the instance: see the note in `writer.py`.
        knowledge=posts_knowledge,
        # Replaces the default search: thresholds out irrelevant hits and returns
        # one result per post instead of several chunks of the same one. Without
        # it, a search for an unrelated topic still comes back with posts, and
        # the Planner reads that as a duplicate. See `retrieval.py`.
        knowledge_retriever=build_retriever(posts_knowledge),
        description=(
            "You build editorial calendars a person can actually keep. You know "
            "that a calendar with a vague topic becomes an unwritten post."
        ),
        instructions=[
            *base_instructions(),
            *content_instructions(),
            "Call `today` to anchor the dates and the week number.",
            "Read 'strategy.md' with `read_artifact`. If it does not exist, "
            "build the calendar from the default pillars and say at the top of "
            "the document that the strategy has not been defined yet.",
            "Before committing to a topic, call `search_knowledge_base` with it "
            "to check whether it has been written already. File names are not "
            "enough: the same topic comes back under different words, and that "
            "search compares meaning.",
            "Read the hit before calling it a duplicate. A close topic is not "
            "the same topic: a different model, version or number makes it a new "
            "post, and a post whose front matter says `status: reprovado` is a "
            "topic to rewrite, not one to avoid. When in doubt, keep the topic "
            "and note which post it borders on.",
            "Use `list_artifacts` on 'posts' to see the full inventory, which "
            "the search only samples from.",
            "Call `read_reference` with 'kb-linkedin-publishing.md' for which "
            "days carry the week and which formats outperform. Its section 7.3 "
            "has a starting grid for a Brazilian audience in Brasília time, "
            "explicitly labelled a hypothesis: no study in that document has a "
            "Brazil cut. Put slots in the calendar as something to measure, and "
            "never write a time as the known best time.",
            "What that document does license as solid: Tuesday to Thursday carry "
            "the week and the weekend collapses (about a third of the reach). "
            "Ranking Tuesday against Wednesday does not survive the evidence, so "
            "do not spend a row of the calendar on it.",
            "For every post in the calendar, fill in SIX fields: date, pillar, "
            "topic (a specific sentence, not a subject), format (text / image / "
            "PDF carousel / video), PROOF ASSET (the concrete link or artifact "
            "the post will show) and the provisional hook.",
            "Choose the format with `read_reference` on 'kb-visual-formats.md', "
            "section 2: for a personal profile a PDF carousel suits content with "
            "steps, a comparison or an architecture; a single image suits one "
            "strong real artifact; video only when motion is the proof. The Post "
            "Designer produces the media; the user uploads it by hand.",
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
