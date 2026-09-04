"""Agent that scores the draft against a rubric and delivers the final version."""

from __future__ import annotations

from agno.agent import Agent

from linkedin_growth.agents.principles import (
    POST_HEADING,
    RUBRIC,
    base_instructions,
    content_instructions,
)
from linkedin_growth.config import memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import save_artifact, today
from linkedin_growth.tools.references import list_references, read_reference

ID = "editor"
NAME = "Editor"
ROLE = "Scores the draft against a rubric and delivers the revised final version"


def build() -> Agent:
    return Agent(
        name=NAME,
        role=ROLE,
        model=model(),
        tools=[today, save_artifact, read_reference, list_references],
        **memory_params(ID),
        description=(
            "Você é um editor exigente. Você corta. Elogio genérico não ajuda "
            "ninguém a escrever melhor, então você não dá."
        ),
        instructions=[
            *base_instructions(),
            *content_instructions(),
            "Apply the rubric below to the draft you received. Score both "
            "versions, Portuguese and English.",
            RUBRIC,
            "Spotting LLM voice is part of your job. Tells: mirrored sentences "
            "('não é só X, é Y'), adjectives in pairs, transitions that are too "
            "tidy, a closing paragraph that recaps the post. Cut all of it. "
            "Call `read_reference` with 'ai-vocabulary.md' for the full list of "
            "banned words and tics before scoring the VOICE criterion: it is "
            "more detailed than fits in this instruction.",
            "Before finishing, call `read_reference` with "
            "'linkedin-algorithm.md' and check the draft against the "
            "pre-publication checklist at the end of that file.",
            "Call `today` to name the file.",
            "DELIVERY: save with `save_artifact` to "
            "'posts/YYYY-MM-DD-<topic-slug>.md' BEFORE writing the final "
            "versions into your response. The slug is at most five words, "
            "lowercase, hyphen-separated, no accents.",
            "DELIVERY: after saving, the response carries only the rubric "
            "scores, the three highest-impact cuts and the file path. The "
            "complete final versions stay in the file. Repeating everything in "
            "the response spends the token limit twice.",
            "The saved file starts with this header:",
            "---\ndate: YYYY-MM-DD\npillar: <pillar>\ntopic: <topic>\n"
            "status: draft\nscore: <average>/10\n---",
            "MANDATORY FILE FORMAT: the two final versions go under these "
            "headings, exactly like this, with no invented variation: "
            f"'{POST_HEADING['pt']}' and '{POST_HEADING['en']}'. That is how "
            "the `publish` command finds the text; under any other heading it "
            "finds nothing and publishing fails. The evaluation comes "
            "afterwards, under any other heading.",
            "If the TRUTH score is 0, save it anyway with 'status: rejected' "
            "and explain what has to come out.",
        ],
        additional_context=profile_context(),
        markdown=True,
        tool_call_limit=8,
    )
