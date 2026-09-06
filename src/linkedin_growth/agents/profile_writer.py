"""Agent that writes the profile copy, ready to copy and paste.

The reminder that justifies the output format: **there is no API for editing a
LinkedIn profile.** Nothing here is applied automatically. This agent's product
is a document where every block comes with an instruction saying where to paste
it.
"""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    base_instructions,
    delivery_instruction,
    voice_instructions,
)
from linkedin_growth.config import memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import read_artifact, save_artifact
from linkedin_growth.tools.references import read_reference

ID = "profile-writer"
NAME = "Profile Writer"
ROLE = (
    "Writes the headline, About section, experience and project descriptions, "
    "ready to paste into LinkedIn"
)


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(),
        tools=[read_artifact, save_artifact, read_reference],
        **memory_params(ID),
        description=(
            "Você escreve o texto de perfis do LinkedIn para profissionais "
            "técnicos. Você escreve como gente, não como consultoria."
        ),
        instructions=[
            *base_instructions(),
            *voice_instructions(),
            "If 'diagnosis.md' exists, read it first with `read_artifact`: it "
            "says where the gaps are.",
            "Produce, in this order:",
            "1. HEADLINE: before writing, call `read_reference` with "
            "'headline-formulas.md' for the formula and the antipatterns. Three "
            "options, each at most 220 characters. Explain in one line what "
            "each option prioritizes, and recommend one.",
            "2. ABOUT: 900 to 1500 characters. Open with the strongest sentence "
            "(LinkedIn truncates at about 270). Structure: where they come "
            "from, what they are building now, what they want to do, how to "
            "reach them.",
            "3. EXPERIENCE: rewrite every REAL job that exists in the data. Two "
            "to four lines per job, focused on what transfers to AI engineering "
            "(data, automation, logic, product, communication). Do not invent a "
            "responsibility that is not described.",
            "4. PROJECTS: a description for each real project. If they have "
            "few, say so and suggest two or three concrete projects they could "
            "build to fill the gap, scoped to one or two weeks.",
            "5. SKILLS: the exact list to tick on LinkedIn, ordered by "
            "priority, separating 'already have' from 'will have once X is "
            "done'.",
            "Every block starts with an instruction line in this format: "
            "'>> Cole em: Perfil > Sobre > Editar'.",
            "Write the copy in Portuguese. After each piece, give the English "
            "version: an international recruiter reads the profile in English.",
            *delivery_instruction("optimized_profile.md"),
        ],
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=10,
    )
