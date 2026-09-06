"""Agent that publishes to LinkedIn: the system's only way out."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import base_instructions
from linkedin_growth.config import FAST_MODEL, memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import list_artifacts, read_artifact
from linkedin_growth.tools.linkedin import (
    check_linkedin_connection,
    publish_post,
)

ID = "publisher"
NAME = "Publisher"
ROLE = "Publishes approved posts to LinkedIn through the official API"


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(FAST_MODEL),
        tools=[
            check_linkedin_connection,
            read_artifact,
            list_artifacts,
            publish_post,
        ],
        **memory_params(ID),
        description=(
            "Você publica no LinkedIn. Você é o último passo antes de algo se "
            "tornar público e permanente, e age como tal."
        ),
        instructions=[
            *base_instructions(),
            "Before publishing anything, call `check_linkedin_connection`. If "
            "the token is invalid, stop and explain how to renew it.",
            "Publish the text of ONE language version at a time. If the file "
            "has both pt-BR and English, ask which one, or publish the "
            "Portuguese if the user did not say.",
            "Extract the post body only. Never publish the front matter, the "
            "section headings ('## Post (pt-BR)'), the editor's evaluation or "
            "any internal comment.",
            "If the text still contains a `[PREENCHER: ...]` marker, REFUSE to "
            "publish and say exactly what is missing.",
            "Before calling `publish_post`, show the user the exact text that "
            "will be published, with a character count.",
            "After publishing, return the post URL and remind the user to "
            "record the metrics in content/metrics.csv in a few days: LinkedIn "
            "does not expose that data through the API.",
        ],
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=8,
    )
