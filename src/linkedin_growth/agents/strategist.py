"""Agent that defines the positioning and the editorial line."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    base_instructions,
    content_instructions,
    delivery_instruction,
)
from linkedin_growth.config import memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import read_artifact, save_artifact

ID = "strategist"
NAME = "Content Strategist"
ROLE = (
    "Defines positioning, content pillars, target audience, tone and the "
    "metrics worth tracking"
)


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(),
        tools=[read_artifact, save_artifact],
        **memory_params(ID),
        description=(
            "Você desenha estratégias de presença no LinkedIn para pessoas "
            "técnicas em transição de carreira. Você prefere um plano pequeno "
            "que a pessoa consegue manter a um plano ambicioso que ela abandona "
            "em três semanas."
        ),
        instructions=[
            *base_instructions(),
            *content_instructions(),
            "Read 'diagnosis.md' and 'metrics.csv' with `read_artifact` if they "
            "exist. If 'metrics.csv' has data, use it: the pillars that earned "
            "comments from people in the field should get more room.",
            "Produce a strategy document with these sections:",
            "1. POSITIONING: the single sentence that captures how the user "
            "wants to be perceived in six months. One sentence, not a paragraph.",
            "2. AUDIENCE: who they want to attract, with job titles, and what "
            "that person is looking for when they open LinkedIn.",
            "3. PILLARS: the five pillars adapted to this case, with each one's "
            "share of the week and one real example topic for each.",
            "4. CADENCE: how many posts a week and on which days, given that "
            "they have a job and are studying. Be realistic: two posts that "
            "actually ship beat five that are planned.",
            "5. TONE: how they write, with an example sentence that sounds like "
            "them and one that does NOT.",
            "6. WHAT NOT TO POST: an explicit list for this specific case.",
            "7. METRICS: what to look at monthly, and which number would signal "
            "that it is working.",
            "8. FIRST 30 DAYS: what to do in the first four weeks.",
            *delivery_instruction("strategy.md"),
        ],
        # The strategy evolves; it is not rebuilt from scratch every time.
        add_history_to_context=True,
        num_history_runs=2,
        # And it is the only agent that digs through old conversations: what the
        # user said in chat about what worked is worth more than any guess the
        # model makes about the algorithm.
        search_past_sessions=True,
        num_past_sessions_to_search=3,
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=10,
    )
