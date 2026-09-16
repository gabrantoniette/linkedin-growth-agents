"""Agent that writes the post, in Portuguese and in English."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    POST_HEADING,
    base_instructions,
    content_instructions,
)
from linkedin_growth.config import memory_params, model, voice_knowledge
from linkedin_growth.profile.context import profile_context
from linkedin_growth.retrieval import build_retriever
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
        # Passed as the factory, not the instance: building a `Knowledge` creates
        # the LanceDB table, and agents are built at import time in `agentos.py`.
        # Agno resolves and caches the factory on the first run instead.
        knowledge=voice_knowledge,
        # Same retriever as the Planner, for the same two reasons: no floor on
        # relevance, and one chunk per sample. See `retrieval.py`.
        knowledge_retriever=build_retriever(voice_knowledge),
        description=(
            "You write LinkedIn posts for an engineer still in training. You "
            "write the way they would on a good day, not the way a content "
            "generator would."
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
            "Call `search_knowledge_base` with the post's topic to pull the "
            "past posts closest to it, and mirror their rhythm and vocabulary. "
            "It returns how the user writes, not what to write about: take the "
            "voice, never the subject.",
            "The English version is NOT a literal translation. It is the same "
            "post rewritten for an international reader: different references, "
            "different rhythm, hashtags from the English-speaking ecosystem.",
            "If real information is missing to support the post (a number, a "
            "detail of what they built), do NOT invent it: write the post with "
            "an explicit `[PREENCHER: ...]` marker and list at the end what the "
            "user has to fill in.",
            "Deliver in exactly this format, with no text around it:",
            "## Metadata\npillar, core idea, proof, suggested format",
            f"{POST_HEADING['pt']}\nthe text, ready to paste",
            f"{POST_HEADING['en']}\nthe text, ready to paste",
            "## To fill in\nthe list of `[PREENCHER]`, or 'nada' if there is none",
        ],
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=8,
    )
