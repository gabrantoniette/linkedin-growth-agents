"""Profile data model.

The schema is the contract between the importer and every agent. What is tested
here is what breaks silently: a required field where the export is usually
empty, and the two places with real logic.
"""

from __future__ import annotations

from linkedin_growth.profile.schema import Experience, Profile


# ==============================================================================
# Tolerance for an incomplete export
# ==============================================================================


def test_empty_profile_is_valid():
    """Not every export has certifications, projects or languages.

    If any field became required, the import would break for anyone missing
    that section, and the user would end up with no profile at all.
    """
    profile = Profile()

    assert profile.name is None
    assert profile.experiences == []
    assert profile.skills == []


def test_profile_ships_with_a_goal_and_topics_of_interest():
    """They are the floor of the positioning: without them the agent writes for nobody."""
    profile = Profile()

    assert "AI engineering" in profile.goal
    assert profile.topics_of_interest


def test_profile_lists_are_not_shared_between_instances():
    """The classic mutable-default bug: one profile inheriting another's list."""
    first = Profile()
    second = Profile()

    first.skills.append("Python")

    assert second.skills == []


# ==============================================================================
# Logic
# ==============================================================================


def test_experience_with_no_end_date_counts_as_current():
    assert Experience(company="Acme", start="2024").current is True


def test_experience_with_an_end_date_is_not_current():
    assert Experience(company="Acme", start="2020", end="2023").current is False


def test_short_summary_joins_name_and_headline():
    profile = Profile(name="Alex", headline="Building AI agents")

    assert profile.short_summary() == "Alex - Building AI agents"


def test_short_summary_without_headline_returns_just_the_name():
    assert Profile(name="Alex").short_summary() == "Alex"


def test_short_summary_without_a_name_says_so_instead_of_returning_empty():
    """It shows up in logs and artifact headers: an empty string there confuses."""
    assert Profile().short_summary() == "(no name)"
