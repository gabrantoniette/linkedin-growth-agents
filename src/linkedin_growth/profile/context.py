"""Turns the `Profile` into text to inject into the agents' context.

Design decision: **no vector store and no RAG here.** One person's profile fits
in a few thousand tokens, and Agno's default embedder would need an OpenAI key
this project does not have. Injecting the whole profile through
`additional_context` is simpler, cheaper to maintain and more reliable: the
agent never "fails to find" a fact that is right there.

The rendered block is in Portuguese on purpose. It is prompt content read by a
model that writes Portuguese posts, and the section titles line up with the
LinkedIn UI the user copies into.
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
    return f" ({start or '?'} a {end or 'atual'})"


def render(profile: Profile) -> str:
    """Profile -> compact markdown for the agents' `additional_context`."""
    parts: list[str] = [
        "## DADOS REAIS DO USUÁRIO",
        "",
        "Tudo abaixo é verdade verificável. Use só isto como base factual.",
        "Se algo que você precisa não está aqui, pergunte. Não invente.",
        "",
    ]

    identity = []
    if profile.name:
        identity.append(f"- Nome: {profile.name}")
    if profile.headline:
        identity.append(f"- Headline atual: {profile.headline}")
    if profile.industry:
        identity.append(f"- Setor: {profile.industry}")
    if profile.location:
        identity.append(f"- Localização: {profile.location}")
    for website in profile.websites:
        identity.append(f"- Site: {website}")
    parts += _block("Identidade", identity)

    if profile.about:
        parts += _block("Seção 'Sobre' atual", [profile.about])

    parts += _block("Objetivo de carreira", [profile.goal])

    if profile.topics_of_interest:
        parts += _block(
            "Temas de interesse", [", ".join(profile.topics_of_interest)]
        )

    experiences = []
    for exp in profile.experiences:
        heading = f"- **{exp.title or 'Cargo não informado'}**"
        if exp.company:
            heading += f", {exp.company}"
        heading += _period(exp.start, exp.end)
        experiences.append(heading)
        if exp.description:
            experiences.append(f"  {exp.description}")
    parts += _block("Experiência profissional", experiences)

    education = []
    for item in profile.education:
        line = f"- {item.degree or 'Formação'}"
        if item.course:
            line += f" em {item.course}"
        if item.school:
            line += f", {item.school}"
        line += _period(item.start, item.end)
        education.append(line)
    parts += _block("Formação", education)

    certifications = [
        f"- {c.name or 'Certificação'}"
        + (f", {c.issuer}" if c.issuer else "")
        + (f" ({c.url})" if c.url else "")
        for c in profile.certifications
    ]
    parts += _block("Certificações", certifications)

    projects = []
    for project in profile.projects:
        projects.append(
            f"- **{project.title or 'Projeto'}**"
            + (f", {project.url}" if project.url else "")
        )
        if project.description:
            projects.append(f"  {project.description}")
    parts += _block("Projetos", projects)

    if profile.skills:
        parts += _block("Skills declaradas", [", ".join(profile.skills)])

    languages = [
        f"- {language.name}"
        + (f" ({language.proficiency})" if language.proficiency else "")
        for language in profile.languages
        if language.name
    ]
    parts += _block("Idiomas", languages)

    return "\n".join(parts).strip()


def voice_sample() -> str:
    """An excerpt of `profile/voice.md`, so the agent can mirror the user's tone."""
    if not VOICE_MD.exists():
        return ""
    text = VOICE_MD.read_text(encoding="utf-8")
    if len(text) > MAX_VOICE_CHARACTERS:
        text = text[:MAX_VOICE_CHARACTERS] + "\n\n[...amostra truncada]"
    return (
        "\n\n## COMO O USUÁRIO ESCREVE\n\n"
        "Posts que ele já publicou. Imite o ritmo e o vocabulário, não o assunto.\n"
        "Se estiver vazio, use um tom direto e sem jargão de marketing.\n\n"
        + text
    )


NO_PROFILE = """## DADOS REAIS DO USUÁRIO

O perfil ainda não foi importado, então você não sabe nada de concreto sobre
este usuário.

Não invente nada. Se a tarefa depender de dados do perfil, responda dizendo que
é preciso rodar primeiro:

    uv run linkedin import

depois de colocar os CSVs do export do LinkedIn em `profile/linkedin_export/`.
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
