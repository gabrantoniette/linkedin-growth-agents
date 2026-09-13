"""The soft limits: warnings a render returns next to the contact sheet.

Warnings never block. What these tests pin down is that each one fires on the
case it exists for, with a message that says what to change, and that a
well-formed deck gets none: a lint that always complains gets ignored.
"""

from __future__ import annotations

from linkedin_growth.studio.lint import lint
from linkedin_growth.studio.spec import parse_spec

COVER = "  - layout: cover\n    headline: Uma frase curta.\n"
STATEMENT = "  - layout: statement\n    text: Uma frase.\n"
CLOSING = "  - layout: closing\n    headline: Fim.\n    question: Qual é a sua?\n"


def deck(*slides: str, title: str = "T") -> str:
    return f"title: {title}\nslides:\n" + "".join(slides)


def warnings_for(source: str, kind: str = "carousel") -> list[str]:
    spec, problems = parse_spec(source, kind)
    assert spec is not None, problems
    return lint(spec)


def test_a_well_formed_deck_has_no_warnings():
    assert warnings_for(deck(COVER, STATEMENT, STATEMENT, STATEMENT, CLOSING)) == []


def test_a_cover_hook_past_twelve_words_is_flagged():
    cover = "  - layout: cover\n    headline: um dois três quatro cinco seis sete oito nove dez onze doze treze\n"

    warnings = warnings_for(deck(cover, STATEMENT, STATEMENT, STATEMENT, CLOSING))

    assert any("headline has 13 words" in warning for warning in warnings)


def test_emphasis_in_a_headline_is_flagged():
    cover = "  - layout: cover\n    headline: Uma frase com *acento*.\n"

    warnings = warnings_for(deck(cover, STATEMENT, STATEMENT, STATEMENT, CLOSING))

    assert any("emphasis marks" in warning for warning in warnings)


def test_emphasis_in_body_text_is_allowed():
    points = "  - layout: points\n    headline: Três razões\n    items: ['uma **forte**', 'outra']\n"

    warnings = warnings_for(deck(COVER, points, STATEMENT, STATEMENT, CLOSING))

    assert not any("emphasis" in warning for warning in warnings)


def test_too_few_and_too_many_slides_are_flagged():
    assert any("Under 5" in warning for warning in warnings_for(deck(COVER, CLOSING)))
    assert any("Past 12" in warning for warning in warnings_for(deck(COVER, *[STATEMENT] * 12, CLOSING)))


def test_a_deck_that_does_not_open_on_a_cover_is_flagged():
    warnings = warnings_for(deck(STATEMENT, STATEMENT, STATEMENT, STATEMENT, CLOSING))

    assert any("not 'cover'" in warning for warning in warnings)


def test_long_code_is_flagged_by_lines_and_by_columns():
    lines = "".join(f"      linha_{index} = {index}\n" for index in range(16))
    code = "  - layout: code\n    code: |\n" + lines + "      " + "x" * 70 + "\n"

    warnings = warnings_for(deck(COVER, code, STATEMENT, STATEMENT, CLOSING))

    assert any("lines of code" in warning for warning in warnings)
    assert any("character line" in warning for warning in warnings)


def test_an_image_without_alt_text_is_flagged():
    image = "  - layout: image\n    image: media/x/screens/a.png\n"

    warnings = warnings_for(deck(COVER, image, STATEMENT, STATEMENT, CLOSING))

    assert any("alt text" in warning for warning in warnings)


def test_a_long_document_title_is_flagged():
    warnings = warnings_for(deck(COVER, STATEMENT, STATEMENT, STATEMENT, CLOSING, title="x" * 70))

    assert any("title: 70 characters" in warning for warning in warnings)


def test_a_scene_too_short_for_its_narration_is_flagged():
    video = (
        "title: T\nscenes:\n  - layout: statement\n    text: X\n    duration: 1\n"
        "    narration: " + "palavra " * 10 + "\n"
    )

    warnings = warnings_for(video, "video")

    assert any("17 characters per second" in warning for warning in warnings)
