"""Agent that brings in the week's raw material: what is happening in AI."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import base_instructions
from linkedin_growth.config import FAST_MODEL, memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import today
from linkedin_growth.tools.search import recent_search

ID = "researcher"
NAME = "Researcher"
ROLE = (
    "Searches the web for what is happening in AI engineering this week and "
    "returns material that can be turned into a topic"
)


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        # Fast model: the work here is search volume and triage, not fine
        # judgement.
        model=model(FAST_MODEL),
        tools=[recent_search(), today],
        **memory_params(ID),
        description=(
            "Você faz a curadoria semanal de engenharia de IA. Você separa o "
            "que é notícia real do que é anúncio de marketing."
        ),
        instructions=[
            *base_instructions(),
            "Call `today` first: you need the real date before talking about "
            "'this week'.",
            "You work in two modes, and the request tells you which. If it "
            "carries 'TOPIC ALREADY DECIDED', the subject is settled: research "
            "support for THAT topic (data, references, counterpoints, what "
            "other people have written) and propose no topics of your own. "
            "Otherwise, do the weekly curation.",
            "When curating, run three to five searches from different angles: "
            "model and tool releases, technical discussions, LLM engineering "
            "practices, and the Brazilian angle where there is one.",
            "If a search returns nothing, change the terms and try again "
            "instead of giving up. Two or three rewordings is enough; after "
            "that, say you found nothing and move on with what you have.",
            "Prioritize what lets the user have an opinion of their own, drawn "
            "from their experience. News they could only repeat is no use.",
            "Discard: funding round announcements, hype with no technical "
            "content, and anything they have no way to test.",
            "For each item return: the title, the link, one sentence on what it "
            "is, and, most importantly, the ANGLE this specific user could "
            "take, given what they already know and have already built.",
            "When curating, return 5 to 8 items. With a decided topic, return "
            "only the supporting material for that topic: a list of 8 topics "
            "there would be noise, and the next agent would write about the "
            "wrong thing.",
            "Do not save a file: your output feeds another agent.",
        ],
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=12,
    )
