"""Agent that turns a written post into the asset that carries it.

Carousel, image or video, real screenshots as proof, and the text that goes
out with each of them. What to say is already decided when this agent starts:
the Writer and the Editor produced the post. This agent decides the format and
how it looks, on evidence (references/kb-visual-formats.md) and by procedure
(the Agent Skills in skills/), not on taste.

It is also the only agent that sees its own output. The render tools return
the contact sheet as an image, and looking at it is part of the job.

**Skills are passed natively.** Agno 3 takes `skills=` and does two things with
it: it puts each skill's name and description in the system prompt, and it
gives the agent `get_skill_instructions` and `get_skill_reference`, so a full
procedure enters the context only when the agent loads it. It is the same
progressive disclosure `read_reference` gives the other agents, packaged the
way the Agent Skills spec defines it. Do not add the skill tools by hand as
well: Agno already does, and the names would collide.
"""

from __future__ import annotations

from agno.agent import Agent
from agno.skills import LocalSkills, Skills

from linkedin_growth.agents.principles import (
    base_instructions,
    content_instructions,
    design_instructions,
)
from linkedin_growth.config import SKILLS_DIR, memory_params, model
from linkedin_growth.profile.context import profile_context
from linkedin_growth.tools.artifacts import (
    list_artifacts,
    read_artifact,
    save_artifact,
    today,
)
from linkedin_growth.tools.references import list_references, read_reference
from linkedin_growth.tools.studio import (
    capture_screenshot,
    convert_to_pdf,
    inspect_slides,
    list_media,
    render_carousel,
    render_image_post,
    render_video,
)

ID = "designer"
NAME = "Post Designer"
ROLE = (
    "Turns an approved post into its best format: a PDF carousel, an image or a "
    "short video, with real screenshots as proof and the caption for that format"
)

# The skills this agent's instructions name. A test checks each one exists and
# passes the Agent Skills validation, so renaming a folder cannot silently
# leave the instructions pointing at nothing.
SKILL_NAMES = (
    "format-selection",
    "carousel-design",
    "proof-screenshots",
    "short-video",
    "post-copy",
)


def load_skills() -> Skills:
    """The design procedures from `skills/`, validated against the Agent Skills spec."""
    return Skills(loaders=[LocalSkills(str(SKILLS_DIR))])


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
            render_carousel,
            render_image_post,
            inspect_slides,
            render_video,
            capture_screenshot,
            convert_to_pdf,
            list_media,
        ],
        skills=load_skills(),
        **memory_params(ID),
        description=(
            "Você é o diretor de arte de um engenheiro que constrói IA em público. "
            "Você transforma um post aprovado no formato que melhor carrega a "
            "prova dele, e olha o que produziu antes de entregar."
        ),
        instructions=[
            *base_instructions(),
            *content_instructions(),
            *design_instructions(),
            "WORK ORDER: (1) read the post, (2) choose the format, (3) build and "
            "render the asset, (4) look at it and fix it, (5) write the text for "
            "that format, (6) answer briefly.",
            "(1) READ. When the request names a post file, read it with "
            "`read_artifact` (the path from content/, like "
            "'posts/2026-09-04-topic.md'). Work from the section under "
            "'## Post (pt-BR)', or '## Post (en)' when the request asks for "
            "English. If the file says `status: rejected`, or a `[PREENCHER` "
            "marker is left, stop and say what is missing: nothing is designed on "
            "top of a rejected or incomplete post.",
            "The media folder, the `slug` every studio tool takes, is the post "
            "file name without '.md'. With no post file, call `today` and use "
            "'YYYY-MM-DD-' plus the topic in three to five words.",
            "(2) FORMAT. Call `get_skill_instructions` with 'format-selection' and "
            "follow it; `read_reference` on 'kb-visual-formats.md' has the numbers "
            "behind it. State the format and the reason in one sentence before "
            "building. If the request names a format, use it, and say so if the "
            "evidence points elsewhere.",
            "(3) BUILD. For a carousel or an image post, load the 'carousel-design' "
            "skill and its 'layouts.md' reference before writing the spec. For a "
            "video, load 'short-video'. For a screenshot, load 'proof-screenshots' "
            "and capture it before writing the slide that shows it.",
            "Every fact on a slide comes from the post or from the USER'S REAL "
            "DATA: the numbers, the names, the code. A metric slide needs a number "
            "the post states; a code slide needs code the user wrote or output a "
            "real run printed. When the post does not have it, the slide does not "
            "exist.",
            "(4) REVIEW. The render tools return the contact sheet as an image: "
            "look at it. Then call `inspect_slides` on the cover and on the "
            "densest slide, and go through 'review-checklist.md' from the "
            "'carousel-design' skill. Fix the spec and render again. Stop after "
            "two review rounds past the first clean render: the spec is saved, and "
            "the user can still edit it by hand.",
            "A report that says NOT RENDERED means no final file was written. Fix "
            "exactly what it lists and call again; never answer as if the asset "
            "exists.",
            "(5) TEXT. Load 'post-copy' and save 'media/<slug>/post.md' with "
            "`save_artifact` BEFORE the final answer, in the format that skill "
            "defines. Never use the heading '## Post (pt-BR)' in that file: "
            "`linkedin publish` would send the caption as a text-only post, "
            "without its PDF.",
            "(6) ANSWER in at most 15 lines: the format and why, the files (the "
            "asset, its spec, post.md), what the user uploads by hand and where, "
            "and any warning you chose not to fix, with the reason. Do not paste "
            "the caption or the spec into the answer: they are in the files.",
            "Media is published by hand. Never say the system will publish the "
            "carousel, the image or the video.",
        ],
        additional_context=profile_context(),
        markdown=True,
        # The contact sheets are for the model to look at during the run. Kept
        # out of the session database, where a few renders a day would pile up
        # megabytes of base64 that nobody reads again.
        store_media=False,
        tool_call_limit=40,
    )
