"""Turns the `Profile` into text to inject into the agents' context.

Design decision: **no retrieval for the profile.** One person's profile fits in
a few thousand tokens, so injecting the whole thing through `additional_context`
is simpler, cheaper to maintain and more reliable: the agent never "fails to
find" a fact that is right there.

This is a decision about the profile only, not about the system. The posts you
have already written and your past writing DO go through a vector store, because
"have I covered this topic?" is a similarity question that no file listing
answers well. See `config.py` and `indexing.py`. The embedder runs locally
through FastEmbed, so none of that needs a second API key.

The scaffolding of the rendered block -- headings, labels, instructions -- is
English, like the rest of the project. The values inside it are whatever the
user wrote on LinkedIn, so a Brazilian profile renders in Portuguese. That is
data, not project language, and the agents that write posts carry their own
pt-BR instruction.
"""

from __future__ import annotations

from functools import lru_cache

import yaml

from linkedin_growth.config import PROFILE_YAML, VOICE_MD
from linkedin_growth.profile.schema import Profile

# How much of the voice sample fits in context without bloating every call.
MAX_VOICE_CHARACTERS = 4000


class ProfileMissing(RuntimeError):
    """The profile has not been imported yet."""


def load_profile() -> Profile:
    """Read `profile/profile.yaml`. Raise with instructions if it is missing."""
    if not PROFILE_YAML.exists():
        raise ProfileMissing(
            "profile/profile.yaml does not exist.\n"
            "Put the LinkedIn export CSVs in profile/linkedin_export/ and run:\n"
            "    uv run linkedin import"
        )
    data = yaml.safe_load(PROFILE_YAML.read_text(encoding="utf-8")) or {}
    return Profile.model_validate(data)


def _block(title: str, lines: list[str]) -> list[str]:
    """Emit the section only if it has content. An empty section is prompt noise."""
    if not lines:
        return []
    return [f"### {title}", *lines, ""]


def _period(start: str | None, end: str | None) -> str:
    if not start and not end:
        return ""
    return f" ({start or '?'} to {end or 'present'})"


def render(profile: Profile) -> str:
    """Profile -> compact markdown for the agents' `additional_context`."""
    parts: list[str] = [
        "## THE USER'S REAL DATA",
        "",
        "Everything below is verifiable truth. Use only this as factual ground.",
        "If something you need is not here, ask for it. Do not make it up.",
        "",
    ]

    identity = []
    if profile.name:
        identity.append(f"- Name: {profile.name}")
    if profile.headline:
        identity.append(f"- Current headline: {profile.headline}")
    if profile.industry:
        identity.append(f"- Industry: {profile.industry}")
    if profile.location:
        identity.append(f"- Location: {profile.location}")
    for website in profile.websites:
        identity.append(f"- Website: {website}")
    parts += _block("Identity", identity)

    if profile.about:
        parts += _block("Current 'About' section", [profile.about])

    parts += _block("Career goal", [profile.goal])

    if profile.topics_of_interest:
        parts += _block(
            "Topics of interest", [", ".join(profile.topics_of_interest)]
        )

    experiences = []
    for exp in profile.experiences:
        heading = f"- **{exp.title or 'Role not given'}**"
        if exp.company:
            heading += f", {exp.company}"
        heading += _period(exp.start, exp.end)
        experiences.append(heading)
        if exp.description:
            experiences.append(f"  {exp.description}")
    parts += _block("Work experience", experiences)

    education = []
    for item in profile.education:
        line = f"- {item.degree or 'Degree'}"
        if item.course:
            line += f" in {item.course}"
        if item.school:
            line += f", {item.school}"
        line += _period(item.start, item.end)
        education.append(line)
    parts += _block("Education", education)

    certifications = [
        f"- {c.name or 'Certification'}"
        + (f", {c.issuer}" if c.issuer else "")
        + (f" ({c.url})" if c.url else "")
        for c in profile.certifications
    ]
    parts += _block("Certifications", certifications)

    projects = []
    for project in profile.projects:
        projects.append(
            f"- **{project.title or 'Project'}**"
            + (f", {project.url}" if project.url else "")
        )
        if project.description:
            projects.append(f"  {project.description}")
    parts += _block("Projects", projects)

    if profile.skills:
        parts += _block("Declared skills", [", ".join(profile.skills)])

    languages = [
        f"- {language.name}"
        + (f" ({language.proficiency})" if language.proficiency else "")
        for language in profile.languages
        if language.name
    ]
    parts += _block("Languages", languages)

    return "\n".join(parts).strip()


def voice_sample() -> str:
    """An excerpt of `profile/voice.md`, so the agent can mirror the user's tone."""
    if not VOICE_MD.exists():
        return ""
    text = VOICE_MD.read_text(encoding="utf-8")
    if len(text) > MAX_VOICE_CHARACTERS:
        text = text[:MAX_VOICE_CHARACTERS] + "\n\n[...sample truncated]"
    return (
        "\n\n## HOW THE USER WRITES\n\n"
        "Posts they have already published. Mirror the rhythm and the "
        "vocabulary, not the subject.\n"
        "If this is empty, use a direct tone with no marketing jargon.\n\n"
        + text
    )


NO_PROFILE = """## THE USER'S REAL DATA

The profile has not been imported yet, so you know nothing concrete about this
user.

Do not make anything up. If the task depends on profile data, answer by saying
that this has to run first:

    uv run linkedin import

after putting the LinkedIn export CSVs in `profile/linkedin_export/`.
"""


@lru_cache(maxsize=1)
def profile_context() -> str:
    """The full context, assembled once per process.

    Cached because every agent asks for the same text: building the same
    markdown seven times would be waste, and the content does not change during
    a run.

    If the profile has not been imported yet, this returns a block that tells
    the agent to ask for the import instead of blowing up. That way the chat and
    the server start even before the first `import`.
    """
    try:
        return render(load_profile()) + voice_sample()
    except (ProfileMissing, ValueError):
        return NO_PROFILE
