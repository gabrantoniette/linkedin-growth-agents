"""Profile data model.

This is the contract between the importer (which reads the LinkedIn CSVs) and
every agent (which reads the structured profile). Everything is optional
because the LinkedIn export varies: not everyone has certifications, projects
or languages.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None

    @property
    def current(self) -> bool:
        return not self.end


class Education(BaseModel):
    school: Optional[str] = None
    course: Optional[str] = None
    degree: Optional[str] = None
    description: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    url: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class Project(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class Language(BaseModel):
    name: Optional[str] = None
    proficiency: Optional[str] = None


class PastPost(BaseModel):
    """A post published in the past. Teaches the system the user's voice."""

    date: Optional[str] = None
    text: Optional[str] = None
    link: Optional[str] = None


class Profile(BaseModel):
    """Full picture of the user. Source of truth for every agent."""

    # --- identity -------------------------------------------------------------
    name: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    websites: list[str] = Field(default_factory=list)

    # --- history --------------------------------------------------------------
    experiences: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    # --- content history ------------------------------------------------------
    past_posts: list[PastPost] = Field(default_factory=list)

    # --- goal (filled in by hand in the YAML, never from the export) ----------
    goal: str = Field(
        default=(
            "Moving into AI engineering. No professional experience in the "
            "field yet; learning and building projects in public."
        ),
        description="Where you want to go. Edit by hand in profile.yaml.",
    )
    topics_of_interest: list[str] = Field(
        default_factory=lambda: [
            "AI agents",
            "LLMs",
            "RAG",
            "Python",
            "prompt engineering",
        ]
    )

    def short_summary(self) -> str:
        """One line, for logs and artifact headers."""
        parts = [self.name or "(no name)"]
        if self.headline:
            parts.append(self.headline)
        return " - ".join(parts)
