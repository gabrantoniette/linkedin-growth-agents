"""Spec -> HTML: every layout renders, nothing reaches the network, nothing injects.

No browser here. These tests read the HTML the templates produce, which is
where a template typo, an external URL or an unescaped string would show up.
The renders themselves are covered in `test_studio_render.py`.
"""

from __future__ import annotations

import re

import pytest
from PIL import Image as PILImage

from linkedin_growth.studio.html import ORIGIN, build_document, scale_svg
from linkedin_growth.studio.spec import LAYOUTS, Author, parse_spec

MINIMAL_BY_LAYOUT = {
    "cover": {"headline": "Capa"},
    "statement": {"text": "Uma frase"},
    "points": {"headline": "Pontos", "items": ["um", "dois"]},
    "steps": {"headline": "Etapas", "steps": [{"title": "a"}, {"title": "b", "detail": "d"}]},
    "code": {"code": "print('oi')", "language": "python", "filename": "oi.py"},
    "compare": {
        "headline": "A ou B",
        "left": {"title": "A", "items": ["x"]},
        "right": {"title": "B", "items": ["y"]},
        "favored": "right",
    },
    "metric": {"value": "42", "unit": "ms", "label": "de latência", "source": "bench"},
    "quote": {"quote": "Citação", "author": "Alguém"},
    "image": {"image": "shot.png", "frame": "browser", "url": "https://example.org/page"},
    "diagram": {"headline": "Fluxo", "nodes": [{"label": "a"}, {"label": "b"}]},
    "closing": {"headline": "Fim", "question": "E aí?", "cta": "Link no comentário"},
}


@pytest.fixture
def content(tmp_path):
    PILImage.new("RGB", (8, 8), "white").save(tmp_path / "shot.png")
    return tmp_path


def document_for(slides, content, **deck):
    spec, problems = parse_spec({"title": "T", **deck, "slides": slides}, "carousel")
    assert spec is not None and problems == [], problems
    return build_document(
        spec,
        width=1080,
        height=1350,
        content_root=content,
        author=Author(name="Pessoa Autora", tagline="engenharia"),
    )


def test_this_file_has_an_example_for_every_layout():
    assert set(MINIMAL_BY_LAYOUT) == set(LAYOUTS)


@pytest.mark.parametrize("theme", ["drafting", "blueprint"])
@pytest.mark.parametrize("layout", LAYOUTS)
def test_every_layout_renders_in_every_theme(layout, theme, content):
    """StrictUndefined turns a template typo into an error here, not into a blank slide."""
    slides = [{"layout": layout, **MINIMAL_BY_LAYOUT[layout]}, {"layout": "closing", "headline": "Fim"}]

    document = document_for(slides, content, theme=theme)

    assert document.html.count('<section class="slide') == 2
    assert f"layout-{layout}" in document.html
    assert document.missing == []


def test_the_page_reaches_nothing_outside_the_studio_origin(content):
    slides = [{"layout": layout, **example} for layout, example in MINIMAL_BY_LAYOUT.items()]

    html = document_for(slides, content).html

    urls = set(re.findall(r"(?:src|href)=[\"']([^\"']+)", html)) | set(re.findall(r"url\('([^']+)'\)", html))
    assert urls, "the document should at least reference its fonts and its image"
    assert all(url.startswith(ORIGIN) for url in urls), urls


def test_slide_text_cannot_inject_markup(content):
    html = document_for([{"layout": "statement", "text": "<img src=x onerror=alert(1)>"}], content).html

    assert "<img src=x" not in html
    assert "&lt;img src=x" in html


def test_a_missing_image_is_reported_instead_of_rendering_blank(content):
    document = document_for([{"layout": "image", "image": "nao-existe.png"}], content)

    assert document.missing
    assert "nao-existe.png" in document.missing[0]


def test_a_contained_capture_gets_a_frame_with_its_own_proportions(content):
    """Regression: a contained capture sat in a tall frame with empty bands around it."""
    PILImage.new("RGB", (1280, 640), "white").save(content / "wide.png")

    html = document_for([{"layout": "image", "image": "wide.png", "fit": "contain"}], content).html

    assert "aspect-ratio: 1280 / 640" in html


def test_an_image_outside_content_is_refused(content):
    document = document_for([{"layout": "image", "image": "../../etc/passwd"}], content)

    assert document.missing


def test_secrets_in_code_are_masked_and_reported(content):
    document = document_for([{"layout": "code", "code": 'KEY = "sk-ant-api03-abcdefghijklmnop"'}], content)

    assert document.redactions
    assert "sk-ant" not in document.html


def test_the_scale_marks_the_current_page_and_shows_when_the_deck_continues():
    middle = str(scale_svg(3, 8))
    last = str(scale_svg(8, 8))

    assert ">3/8<" in middle
    assert 'class="scale-more"' in middle
    assert ">8/8<" in last
    assert 'class="scale-more"' not in last


def test_a_single_slide_has_no_scale(content):
    html = document_for([{"layout": "statement", "text": "Só uma"}], content).html

    assert 'class="scale"' not in html
