"""Agent that writes the post, in Portuguese and in English."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    POST_HEADING,
    base_instructions,
    content_instructions,
)
from linkedin_growth.config import memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import read_artifact
from linkedin_growth.tools.references import list_references, read_reference

ID = "writer"
NAME = "Writer"
ROLE = "Writes the LinkedIn post in Portuguese and the English version"


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(),
        tools=[read_artifact, read_reference, list_references],
        **memory_params(ID),
        description=(
            "Você escreve posts de LinkedIn para um engenheiro em formação. "
            "Você escreve como ele escreveria num dia bom, não como um "
            "gerador de conteúdo."
        ),
        instructions=[
            *base_instructions(),
            *content_instructions(),
            "Before writing, decide three things and say what they are: the "
            "pillar, the single idea the post argues, and the proof it shows.",
            "Write three different hooks for the first line before choosing. "
            "Throw away the first one that comes to mind: it is always the most "
            "generic. Call `read_reference` with 'hooks.md' to pick formulas "
            "that differ from each other, instead of three variations on the "
            "same pattern. Each formula there is already mapped to a pillar.",
            "The English version is NOT a literal translation. It is the same "
            "post rewritten for an international reader: different references, "
            "different rhythm, hashtags from the English-speaking ecosystem.",
            "If real information is missing to support the post (a number, a "
            "detail of what they built), do NOT invent it: write the post with "
            "an explicit `[PREENCHER: ...]` marker and list at the end what the "
            "user has to fill in.",
            "Deliver in exactly this format, with no text around it:",
            "## Metadados\npilar, ideia central, prova, formato sugerido",
            f"{POST_HEADING['pt']}\no texto pronto para colar",
            f"{POST_HEADING['en']}\no texto pronto para colar",
            "## A completar\nlista de `[PREENCHER]`, ou 'nada' se não houver",
        ],
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=8,
    )
