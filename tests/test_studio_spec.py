"""The spec contract: what a carousel or video spec must be before anything renders.

A spec is written by a model and edited by hand, so the checks that matter are
the ones that stop a public asset from carrying what it must not: a
`[PREENCHER]` marker, the banned dashes, a number with no source, a misspelled
field that would silently never render.
"""

from __future__ import annotations

import pytest

from linkedin_growth.studio.spec import CarouselSpec, dump_spec, parse_spec

MINIMAL = """
title: Um título
slides:
  - layout: cover
    headline: Uma frase que prende.
  - layout: closing
    headline: Fechamento.
    question: Qual foi a sua experiência com isso?
"""


def slide(body: str) -> str:
    return f"title: T\nslides:\n  - {body}\n"


def test_a_minimal_spec_parses_with_the_defaults():
    spec, problems = parse_spec(MINIMAL, "carousel")

    assert problems == []
    assert isinstance(spec, CarouselSpec)
    assert spec.theme == "jornal"
    assert spec.accent == "yellow"
    assert spec.language == "pt-BR"
    assert [item.layout for item in spec.slides] == ["cover", "closing"]


def test_json_is_accepted_too():
    spec, problems = parse_spec(
        '{"title": "T", "slides": [{"layout": "statement", "text": "Uma frase."}]}', "carousel"
    )

    assert spec is not None
    assert problems == []


def test_an_unknown_layout_is_reported_with_the_slide_number():
    spec, problems = parse_spec(slide("layout: hero\n    headline: X"), "carousel")

    assert spec is None
    assert any(problem.startswith("slides[1]") for problem in problems)


def test_a_misspelled_field_is_an_error_instead_of_text_that_never_renders():
    spec, problems = parse_spec(
        slide("layout: cover\n    headline: X\n    subtitel: typo"), "carousel"
    )

    assert spec is None
    assert any("subtitel" in problem for problem in problems)


def test_a_metric_without_a_source_is_refused():
    """A number on a slide is a claim, and HONESTY needs to know where it came from."""
    spec, problems = parse_spec(slide("layout: metric\n    value: 40\n    label: de redução"), "carousel")

    assert spec is None
    assert any("source" in problem for problem in problems)


def test_a_numeric_value_is_kept_as_written():
    spec, _ = parse_spec(
        slide("layout: metric\n    value: 100\n    label: testes\n    source: CI do repositório"),
        "carousel",
    )

    assert spec.slides[0].value == "100"


def test_a_placeholder_marker_blocks_the_render_and_names_the_slide():
    # Quoted, because an unquoted ': ' inside a YAML value is a syntax error
    # before it is a placeholder.
    spec, problems = parse_spec(
        slide('layout: statement\n    text: "Reduzi a latência em [PREENCHER: número]"'), "carousel"
    )

    assert spec is not None, "the shape is fine; the text is what blocks"
    assert any("[PREENCHER]" in problem and "slides[1]" in problem for problem in problems)


@pytest.mark.parametrize("dash", ["—", "–", "--"])
def test_the_banned_dashes_block_prose(dash):
    _, problems = parse_spec(slide(f"layout: statement\n    text: Uma coisa {dash} outra"), "carousel")

    assert any("dash" in problem for problem in problems)


def test_code_and_inline_code_are_exempt_from_the_dash_rule():
    """`--dry-run` is a flag, not a dash."""
    spec, problems = parse_spec(
        slide(
            "layout: code\n    code: uv run linkedin publish post.md --dry-run\n"
            "    caption: Rode com `--dry-run` primeiro."
        ),
        "carousel",
    )

    assert spec is not None
    assert problems == []


def test_a_placeholder_inside_code_still_blocks():
    _, problems = parse_spec(slide("layout: code\n    code: 'latency = [PREENCHER]'"), "carousel")

    assert problems


def test_language_aliases_are_normalized():
    spec, _ = parse_spec("title: T\nlanguage: pt\nslides:\n  - layout: statement\n    text: X\n", "carousel")

    assert spec.language == "pt-BR"


def test_more_than_twenty_slides_is_refused():
    slides = "".join("  - layout: statement\n    text: X\n" for _ in range(21))

    spec, _ = parse_spec(f"title: T\nslides:\n{slides}", "carousel")

    assert spec is None


def test_points_are_not_numbered_unless_asked():
    """Numbers claim an order; a list of reasons has none."""
    spec, _ = parse_spec(slide("layout: points\n    headline: H\n    items: [a, b]"), "carousel")

    assert spec.slides[0].numbered is False


def test_a_video_spec_needs_scenes_not_slides():
    spec, _ = parse_spec(MINIMAL, "video")

    assert spec is None


def test_the_saved_spec_parses_back_to_the_same_spec():
    """`linkedin render` reads what a render wrote; the round trip must lose nothing."""
    spec, _ = parse_spec(MINIMAL, "carousel")

    again, problems = parse_spec(dump_spec(spec), "carousel")

    assert problems == []
    assert again == spec


def test_the_saved_spec_keeps_accents_readable():
    spec, _ = parse_spec(slide("layout: statement\n    text: Não é convenção."), "carousel")

    assert "Não é convenção." in dump_spec(spec)


# ==============================================================================
# The jornal fields
# ==============================================================================


def test_a_ledger_takes_rows_and_a_total():
    spec, problems = parse_spec(
        slide(
            "layout: ledger\n    headline: Soma\n    rows:\n      - {value: 1, label: um}\n"
            "      - {value: 2, label: dois}\n    total: {value: 3, label: três}"
        ),
        "carousel",
    )

    assert problems == []
    assert [row.value for row in spec.slides[0].rows] == ["1", "2"]
    assert spec.slides[0].total.label == "três"


def test_a_mark_box_must_be_a_box():
    for box in ("[10, 10, 5, 50]", "[10, 10, 50, 10]", "[-1, 0, 5, 5]"):
        spec, problems = parse_spec(
            slide(f"layout: image\n    image: a.png\n    fit: contain\n    mark: {{box: {box}}}"), "carousel"
        )
        assert spec is None, box
        assert any("box" in problem for problem in problems), box


def test_a_mark_needs_the_whole_image():
    """With fit: cover the capture is cropped, and the box would land somewhere else."""
    spec, problems = parse_spec(slide("layout: image\n    image: a.png\n    mark: {box: [0, 0, 10, 10]}"), "carousel")

    assert spec is None
    assert any("fit: contain" in problem for problem in problems)


def test_the_collage_takes_one_picture_of_each_kind():
    twice = (
        "layout: cover\n    headline: X\n    collage:\n      - {image: a.png, kind: cutout}\n"
        "      - {image: b.png, kind: cutout}"
    )

    spec, problems = parse_spec(slide(twice), "carousel")

    assert spec is None
    assert any("one capture, one cutout and one print" in problem for problem in problems)


def test_a_diagram_has_one_key_node_at_most():
    nodes = "      - {label: a, key: true}\n      - {label: b, key: true}"

    spec, problems = parse_spec(slide(f"layout: diagram\n    headline: X\n    nodes:\n{nodes}"), "carousel")

    assert spec is None
    assert any("key" in problem for problem in problems)


def test_an_unknown_accent_is_refused():
    spec, problems = parse_spec("title: T\naccent: purple\nslides:\n  - layout: statement\n    text: x\n", "carousel")

    assert spec is None
    assert any(problem.startswith("accent") for problem in problems)


def test_banned_dashes_are_caught_in_the_masthead():
    spec, problems = parse_spec(
        "title: T\nmasthead:\n  label: Loja — que aprende\nslides:\n  - layout: statement\n    text: x\n",
        "carousel",
    )

    assert spec is not None
    assert any(problem.startswith("masthead.label") for problem in problems)


def test_a_photo_cannot_go_on_the_cover_or_a_metric():
    """The cover has its collage, and a metric slide is the number alone."""
    for body in (
        "layout: cover\n    headline: X\n    photo: {image: a.jpg}",
        "layout: metric\n    value: 1\n    label: x\n    source: y y\n    photo: {image: a.jpg}",
    ):
        spec, problems = parse_spec(slide(body), "carousel")
        assert spec is None, body
