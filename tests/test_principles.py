"""The codified strategy.

`principles.py` is not support code, it is the product: the behaviour of the
whole system comes from there. These tests protect invariants. Not the exact
wording of the rules, which should evolve, but the fact that certain rules keep
reaching every agent.
"""

from __future__ import annotations

from linkedin_growth.agents.principles import (
    DO_NOT,
    HONESTY,
    PILLARS,
    RUBRIC,
    VOICE_RULES,
    WRITING_RULES,
    base_instructions,
    content_instructions,
    delivery_instruction,
)


# ==============================================================================
# What every agent receives
# ==============================================================================


def test_base_instructions_carry_every_honesty_rule():
    """The rule no agent may break has to reach all of them."""
    base = "\n".join(base_instructions())

    for rule in HONESTY:
        assert rule in base


def test_base_instructions_ask_for_answers_in_portuguese():
    """The code is in English; the posts are not. This is what keeps them apart."""
    assert any(
        "Brazilian Portuguese" in instruction for instruction in base_instructions()
    )


def test_base_instructions_warn_there_is_no_profile_editing_api():
    """Without this the agent promises the user an automation that does not exist."""
    base = "\n".join(base_instructions())

    assert "There is no API for editing a LinkedIn profile" in base


def test_content_instructions_carry_the_five_pillars():
    content = "\n".join(content_instructions())

    assert len(PILLARS) == 5
    for pillar in PILLARS:
        assert pillar in content


def test_instructions_do_not_come_back_empty():
    assert len(base_instructions()) > 5
    assert len(content_instructions()) > 5


# ==============================================================================
# Regressions on specific rules
# ==============================================================================
# Each of these rules was decided for a reason. The test exists so nobody
# reverts them without noticing.


def test_the_hashtag_rule_allows_at_most_three():
    """2026 data: 5+ hashtags signals a spam account, not reach.

    The old rule asked for 'three to five'. If that comes back, this fails.
    """
    writing = "\n".join(WRITING_RULES)

    assert "Zero to three hashtags" in writing
    assert "three to five hashtags" not in writing


def test_there_is_an_explicit_ban_on_the_em_dash():
    """It is the most recognizable tell of AI-generated text."""
    voice = "\n".join(VOICE_RULES)

    assert "—" in voice and "NEVER use an em dash" in voice


def test_whoever_writes_profile_copy_gets_the_voice_rules(temp_db, no_api):
    """The 'About' and the headline go out under the user's name, same as a post.

    While the voice rules lived only inside `content_instructions`, the Profile
    Writer never received them. A real run against the user's export came out
    with 84 em dashes in the text meant to be pasted into LinkedIn, the tell
    this project bans before any other.
    """
    from linkedin_growth.agents import profile_writer, writer

    for module in (profile_writer, writer):
        agent = module.build()
        instructions = " ".join(str(i) for i in (agent.instructions or []))
        assert "NEVER use an em dash" in instructions, agent.name


def test_splitting_voice_from_post_took_nothing_away_from_post_writers():
    """Whoever wrote posts still gets the voice rules, now from the inside."""
    content = "\n".join(content_instructions())

    for rule in VOICE_RULES:
        assert rule in content


def test_there_is_a_link_in_the_first_comment_rule():
    writing = "\n".join(WRITING_RULES)

    assert "first comment" in writing


def test_asking_for_engagement_is_still_forbidden():
    """It burns credibility with a technical audience, and LinkedIn suppresses it."""
    forbidden = "\n".join(DO_NOT)

    assert "Do not ask for engagement" in forbidden


# ==============================================================================
# The editor's rubric
# ==============================================================================


def test_the_rubric_has_the_seven_criteria():
    for criterion in (
        "HOOK",
        "TRUTH",
        "PROOF",
        "SPECIFICITY",
        "READABILITY",
        "VOICE",
        "CLOSING",
    ):
        assert criterion in RUBRIC


def test_the_rubric_fails_the_whole_post_when_truth_is_zero():
    """Honesty is disqualifying, not a criterion you offset with a high score.

    The whitespace is normalized because the rubric is wrapped prose: the
    sentence under test spans two lines, and matching it raw would test the
    line breaks rather than the rule.
    """
    rubric = " ".join(RUBRIC.split())

    assert "this fails the whole post" in rubric
    assert "If TRUTH is 0, do not deliver a final version" in rubric


# ==============================================================================
# Delivery - the order that decides whether the file exists
# ==============================================================================


def test_delivery_instruction_says_save_before_writing():
    """The order is the substance of the rule, not a wording detail.

    Writing the document into the response and only then saving means emitting
    the text twice; the token ceiling arrives halfway and what gets lost is the
    tool call. The file then does not exist, with no error at all.
    """
    delivery = " ".join(delivery_instruction("strategy.md"))

    assert "strategy.md" in delivery
    assert "BEFORE" in delivery, "the order has to be explicit"
    assert "Do NOT repeat the document" in delivery


def test_every_agent_that_writes_a_file_gets_the_delivery_rule(temp_db, no_api):
    """Five agents produce a document. None of them may be left out.

    This test reads each agent's assembled instructions, not the source: what
    matters is what reaches the model. The fixtures are only there to build the
    agents without an API key or the real database.
    """
    from linkedin_growth.agents import (
        diagnosis,
        editor,
        planner,
        profile_writer,
        strategist,
    )

    for module in (diagnosis, strategist, profile_writer, planner, editor):
        agent = module.build()
        instructions = " ".join(str(i) for i in (agent.instructions or []))
        assert "DELIVERY:" in instructions, f"{agent.name} did not get the rule"
        assert "save_artifact" in instructions, agent.name
