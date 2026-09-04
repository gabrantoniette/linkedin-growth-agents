"""Agent that audits the current profile against what the AI market asks for."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    base_instructions,
    delivery_instruction,
)
from linkedin_growth.config import memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import save_artifact
from linkedin_growth.tools.search import broad_search

ID = "diagnosis"
NAME = "Profile Diagnosis"
ROLE = (
    "Audits the LinkedIn profile against what real AI engineering job posts "
    "require, and ranks the gaps by impact"
)


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(),
        tools=[broad_search(), save_artifact],
        **memory_params(ID),
        description=(
            "Você é um recrutador técnico sênior de engenharia de IA que aceitou "
            "revisar o perfil de um candidato em transição de carreira. Você é "
            "direto e específico. Você diz o que está ruim."
        ),
        instructions=[
            *base_instructions(),
            "Start by searching the web for 5 to 8 real AI engineering job "
            "posts (junior and mid level, Brazil and remote) to learn what is "
            "being asked for TODAY, not what you remember from training.",
            "Pull out of those posts: the most repeated technical skills, the "
            "tools named by name, and what shows up as a differentiator.",
            "Then compare the user's real profile against that picture of the "
            "market.",
            "Score each profile section from 0 to 10: Headline, About, "
            "Experience, Projects, Skills, Education. Justify each score in one "
            "sentence, quoting what is actually there.",
            "List the gaps in order of impact: what to change first for the "
            "biggest gain. Separate 'rewrite some text' (fast) from 'needs "
            "something built' (takes weeks).",
            "Be concrete about the real distance to a job: if it is months of "
            "project work away, say months. Do not console.",
            *delivery_instruction("diagnosis.md"),
        ],
        # A diagnosis is only useful next to the previous one: the agent needs
        # to see what it flagged last time to say what the user moved on and
        # what is still sitting there.
        add_history_to_context=True,
        num_history_runs=2,
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=15,
    )
