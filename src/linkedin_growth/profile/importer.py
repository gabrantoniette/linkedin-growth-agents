"""Imports the LinkedIn data export into a structured `Profile`.

Why this file is forgiving rather than direct: LinkedIn **does not publicly
document** the column names in the export, and they change over time and with
the account's language. A parser that demanded an exact `"Company Name"` would
break silently.

So the strategy is:

1. sweep every `.csv` in the folder and match the *file* by normalized name;
2. match each *column* against a list of synonyms, ignoring case and
   punctuation;
3. skip the warning lines LinkedIn puts before the real header;
4. return a report of what was recognized and what was ignored.

The generated `profile.yaml` is meant to be read and corrected by hand. That
file, not the CSV, is the agents' source of truth.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

from linkedin_growth.config import EXPORT_DIR, PROFILE_DIR, PROFILE_YAML, VOICE_MD
from linkedin_growth.profile.schema import (
    Certification,
    Education,
    Experience,
    Language,
    PastPost,
    Profile,
    Project,
)

# How many past posts to keep as a voice sample. Enough for the model to pick up
# the tone without bloating every agent's context.
MAX_VOICE_POSTS = 25


# ==============================================================================
# Normalization
# ==============================================================================


def _normalize(text: str) -> str:
    """'Company Name' -> 'companyname'. The basis of every comparison here."""
    return re.sub(r"[^a-z0-9]", "", text.strip().lower())


def _value(row: dict[str, str], *synonyms: str) -> str | None:
    """First non-empty value among columns whose name matches a synonym."""
    targets = {_normalize(s) for s in synonyms}
    for key, value in row.items():
        if key is None:
            continue
        if _normalize(key) in targets:
            cleaned = (value or "").strip()
            if cleaned:
                return cleaned
    return None


# ==============================================================================
# CSV reading
# ==============================================================================


def _csv_rows(path: Path, expected_columns: Iterable[str]) -> list[dict[str, str]]:
    """Read an export CSV, skipping the preamble LinkedIn sometimes inserts.

    Some files (Connections.csv is the classic case) start with warning lines
    before the header. We look for the first line containing one of the expected
    columns and treat that as the header.

    The text goes into `csv.reader` whole, inside a `StringIO`, rather than
    split with `splitlines()`. The difference matters: the profile's 'About',
    each experience's description and the post text are multiline quoted fields,
    and `splitlines()` cuts right through them. The reader then treats every
    paragraph as a new CSV row and the text arrives scrambled, full of stray
    quotes and missing its original paragraphs.
    """
    expected = {_normalize(c) for c in expected_columns}

    try:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return []

    all_rows = list(csv.reader(io.StringIO(raw)))
    if not all_rows:
        return []

    header_index = 0
    for i, row in enumerate(all_rows[:10]):
        if any(_normalize(cell) in expected for cell in row):
            header_index = i
            break

    header = all_rows[header_index]
    records: list[dict[str, str]] = []
    for row in all_rows[header_index + 1 :]:
        if not any(cell.strip() for cell in row):
            continue
        records.append(dict(zip(header, row)))
    return records


@dataclass
class Report:
    """What the importer understood from the export. Printed for the user."""

    files_found: list[str] = field(default_factory=list)
    files_ignored: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# Normalized file name -> internal label. The export comes in English even when
# the account is in another language, but we accept both spellings to be safe.
KNOWN_FILES: dict[str, str] = {
    "profile": "profile",
    "positions": "experiences",
    "education": "education",
    "skills": "skills",
    "certifications": "certifications",
    "projects": "projects",
    "languages": "languages",
    "shares": "posts",
    "richmediashares": "posts",
}


def _file_key(name: str) -> str:
    """'Shares_1234567890' -> 'shares'.

    LinkedIn suffixes some export files with the member's numeric id (Shares,
    Comments, Reactions, Votes...). Without stripping the suffix,
    `Shares_1234567890.csv` does not match 'shares' and the past posts are
    ignored **silently**: `voice.md` is never generated and the whole system
    starts writing in generic LLM tone, with nothing to indicate what was
    missing.

    The cut happens before normalizing because `_normalize` eats the underscore
    and would leave 'shares1234567890', indistinguishable from a real file name.
    """
    return _normalize(re.sub(r"_\d{4,}$", "", name.strip()))


def _map_files(folder: Path) -> tuple[dict[str, Path], list[Path]]:
    """Match every CSV in the folder against a known label."""
    recognized: dict[str, Path] = {}
    ignored: list[Path] = []
    for path in sorted(folder.rglob("*.csv")):
        label = KNOWN_FILES.get(_file_key(path.stem))
        if label and label not in recognized:
            recognized[label] = path
        else:
            ignored.append(path)
    return recognized, ignored


# ==============================================================================
# Extractors, one per section
# ==============================================================================


def _extract_identity(rows: list[dict[str, str]], profile: Profile) -> None:
    if not rows:
        return
    row = rows[0]
    name = " ".join(
        part
        for part in (
            _value(row, "First Name", "Nome"),
            _value(row, "Last Name", "Sobrenome"),
        )
        if part
    )
    profile.name = name or None
    profile.headline = _value(row, "Headline", "Titulo", "Título")
    profile.about = _value(row, "Summary", "Resumo", "About", "Sobre")
    profile.industry = _value(row, "Industry", "Setor")
    profile.location = _value(
        row, "Geo Location", "Location", "Localizacao", "Localização"
    )
    websites = _value(row, "Websites", "Sites")
    if websites:
        profile.websites = [s.strip() for s in re.split(r"[,;]", websites) if s.strip()]


def _extract_experiences(rows: list[dict[str, str]]) -> list[Experience]:
    return [
        Experience(
            company=_value(row, "Company Name", "Company", "Empresa"),
            title=_value(row, "Title", "Position", "Cargo"),
            description=_value(row, "Description", "Descricao", "Descrição"),
            location=_value(row, "Location", "Localizacao", "Localização"),
            start=_value(row, "Started On", "Start Date", "Data de inicio"),
            end=_value(row, "Finished On", "End Date", "Data de termino"),
        )
        for row in rows
    ]


def _extract_education(rows: list[dict[str, str]]) -> list[Education]:
    return [
        Education(
            school=_value(row, "School Name", "School", "Instituicao", "Instituição"),
            course=_value(row, "Activities", "Field Of Study", "Curso"),
            degree=_value(row, "Degree Name", "Degree", "Grau"),
            description=_value(row, "Notes", "Description", "Descricao", "Descrição"),
            start=_value(row, "Start Date", "Started On"),
            end=_value(row, "End Date", "Finished On"),
        )
        for row in rows
    ]


def _extract_certifications(rows: list[dict[str, str]]) -> list[Certification]:
    return [
        Certification(
            name=_value(row, "Name", "Nome"),
            issuer=_value(row, "Authority", "Issuer", "Emissor"),
            url=_value(row, "Url", "URL"),
            start=_value(row, "Started On", "Start Date"),
            end=_value(row, "Finished On", "End Date"),
        )
        for row in rows
    ]


def _extract_projects(rows: list[dict[str, str]]) -> list[Project]:
    return [
        Project(
            title=_value(row, "Title", "Name", "Titulo", "Título"),
            description=_value(row, "Description", "Descricao", "Descrição"),
            url=_value(row, "Url", "URL"),
            start=_value(row, "Started On", "Start Date"),
            end=_value(row, "Finished On", "End Date"),
        )
        for row in rows
    ]


def _extract_languages(rows: list[dict[str, str]]) -> list[Language]:
    return [
        Language(
            name=_value(row, "Name", "Language", "Idioma"),
            proficiency=_value(row, "Proficiency", "Proficiencia", "Proficiência"),
        )
        for row in rows
    ]


def _extract_skills(rows: list[dict[str, str]]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        name = _value(row, "Name", "Skill", "Nome")
        if name and name not in seen:
            seen.append(name)
    return seen


def _clean_commentary(text: str) -> str:
    """Undo the line-break encoding of the LinkedIn export.

    In `Shares.csv` every paragraph break in the post becomes quote + newline +
    quote. Once the CSV reader has done its job, the text arrives like this:

        ...to the same question:"\\n""How many do we still have?""\\n""\\n"Probably...

    Without undoing that, `voice.md` is unreadable and the agents read the
    user's voice sample as a wall of quotes, which is precisely the file that
    was supposed to teach them to write like the user.

    The pattern requires the newline between the quotes, so real quotation marks
    inside the post survive.
    """
    cleaned = re.sub(r'"[ \t]*\n[ \t]*"', "\n\n", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip().strip('"').strip()


def _extract_posts(rows: list[dict[str, str]]) -> list[PastPost]:
    posts: list[PastPost] = []
    for row in rows:
        text = _value(row, "ShareCommentary", "Commentary", "Texto")
        if not text:
            continue
        posts.append(
            PastPost(
                date=_value(row, "Date", "Data"),
                text=_clean_commentary(text),
                link=_value(row, "ShareLink", "Link"),
            )
        )
    # Most recent first: the export comes in ascending chronological order.
    posts.reverse()
    return posts[:MAX_VOICE_POSTS]


# ==============================================================================
# Entry point
# ==============================================================================


def import_profile(folder: Path | None = None) -> tuple[Profile, Report]:
    """Read the export and return the assembled profile plus a report."""
    folder = folder or EXPORT_DIR
    report = Report()
    profile = Profile()

    if not folder.exists():
        report.warnings.append(f"The folder {folder} does not exist.")
        return profile, report

    recognized, ignored = _map_files(folder)
    report.files_ignored = [p.name for p in ignored]

    if not recognized:
        report.warnings.append(
            f"No known CSV in {folder}. Unzip the LinkedIn export archive into "
            "that folder."
        )
        return profile, report

    readers: dict[str, tuple[list[str], Any]] = {
        "profile": (["First Name", "Headline", "Summary"], None),
        "experiences": (["Company Name", "Title"], None),
        "education": (["School Name", "Degree Name"], None),
        "certifications": (["Name", "Authority"], None),
        "projects": (["Title", "Description"], None),
        "languages": (["Name", "Proficiency"], None),
        "skills": (["Name"], None),
        "posts": (["ShareCommentary", "Date"], None),
    }

    for label, path in recognized.items():
        columns, _ = readers.get(label, ([], None))
        rows = _csv_rows(path, columns)
        report.files_found.append(f"{path.name} ({label})")

        # The count key is always the label, so the report can line up
        # file -> quantity with no translation in between.
        if label == "profile":
            _extract_identity(rows, profile)
            report.counts["profile"] = 1 if profile.name else 0
        elif label == "experiences":
            profile.experiences = _extract_experiences(rows)
            report.counts["experiences"] = len(profile.experiences)
        elif label == "education":
            profile.education = _extract_education(rows)
            report.counts["education"] = len(profile.education)
        elif label == "certifications":
            profile.certifications = _extract_certifications(rows)
            report.counts["certifications"] = len(profile.certifications)
        elif label == "projects":
            profile.projects = _extract_projects(rows)
            report.counts["projects"] = len(profile.projects)
        elif label == "languages":
            profile.languages = _extract_languages(rows)
            report.counts["languages"] = len(profile.languages)
        elif label == "skills":
            profile.skills = _extract_skills(rows)
            report.counts["skills"] = len(profile.skills)
        elif label == "posts":
            profile.past_posts = _extract_posts(rows)
            report.counts["posts"] = len(profile.past_posts)

    if not profile.name:
        report.warnings.append(
            "Could not read your name from Profile.csv. Fill it in by hand in "
            "profile.yaml."
        )
    if not profile.experiences:
        report.warnings.append(
            "No experience imported. If you have a work history, check that "
            "Positions.csv came in the export."
        )

    return profile, report


def save(profile: Profile, *, preserve_edits: bool = True) -> Path:
    """Write the profile to `profile/profile.yaml`.

    If a hand-edited YAML already exists, the fields the export does not supply
    (`goal`, `topics_of_interest`) are preserved. Those are the part the user
    writes, and re-importing must not erase them.
    """
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    if preserve_edits and PROFILE_YAML.exists():
        try:
            previous = yaml.safe_load(PROFILE_YAML.read_text(encoding="utf-8")) or {}
            if isinstance(previous, dict):
                if previous.get("goal"):
                    profile.goal = previous["goal"]
                if previous.get("topics_of_interest"):
                    profile.topics_of_interest = previous["topics_of_interest"]
        except yaml.YAMLError:
            pass  # A corrupt YAML must not block re-importing.

    data = profile.model_dump(mode="json", exclude={"past_posts"})
    header = (
        "# Profile generated from the LinkedIn export.\n"
        "# This file is the agents' SOURCE OF TRUTH. Read it and fix it by hand.\n"
        "# 'goal' and 'topics_of_interest' are yours: re-importing keeps them.\n\n"
    )
    PROFILE_YAML.write_text(
        header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return PROFILE_YAML


def save_voice(profile: Profile) -> Path | None:
    """Write the writing samples to `profile/voice.md`.

    The agents read this file to write in the user's tone instead of generic LLM
    tone. With no past posts, the file is not created.
    """
    if not profile.past_posts:
        return None

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    parts = [
        "# Amostras da minha escrita",
        "",
        "Posts que eu já publiquei, extraídos do export do LinkedIn.",
        "Servem de referência de tom, não de conteúdo.",
        "",
    ]
    for post in profile.past_posts:
        if post.date:
            parts.append(f"## {post.date}")
        parts.append("")
        parts.append(post.text or "")
        parts.append("")
        parts.append("---")
        parts.append("")

    VOICE_MD.write_text("\n".join(parts), encoding="utf-8")
    return VOICE_MD
