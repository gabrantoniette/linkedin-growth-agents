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
    "diagram": {"headline": "Fluxo", "nodes": [{"label": "a"}, {"label": "b", "key": True}]},
    "ledger": {
        "headline": "Soma",
        "rows": [{"value": "1", "label": "um"}, {"value": "2", "label": "dois"}],
        "total": {"value": "3", "label": "três"},
    },
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


def body_of(html: str) -> str:
    """The slides only: the inlined stylesheet names every class, used or not."""
    return html[html.index("<body") :]


def test_this_file_has_an_example_for_every_layout():
    assert set(MINIMAL_BY_LAYOUT) == set(LAYOUTS)


@pytest.mark.parametrize("theme", ["jornal", "drafting", "blueprint"])
@pytest.mark.parametrize("layout", LAYOUTS)
def test_every_layout_renders_in_every_theme(layout, theme, content):
    """StrictUndefined turns a template typo into an error here, not into a blank slide."""
    slides = [{"layout": layout, **MINIMAL_BY_LAYOUT[layout]}, {"layout": "closing", "headline": "Fim"}]

    document = document_for(slides, content, theme=theme)

    assert document.html.count('<section class="slide') == 2
    assert f"layout-{layout}" in document.html
    assert document.missing == []


@pytest.mark.parametrize("theme", ["jornal", "drafting"])
def test_the_page_reaches_nothing_outside_the_studio_origin(theme, content):
    slides = [{"layout": layout, **example} for layout, example in MINIMAL_BY_LAYOUT.items()]

    html = document_for(slides, content, theme=theme).html

    urls = set(re.findall(r"(?:src|href)=[\"']([^\"']+)", html)) | set(re.findall(r"url\('([^']+)'\)", html))
    assert urls, "the document should at least reference its fonts and its image"
    assert all(url.startswith(ORIGIN) for url in urls), urls


def test_the_jornal_theme_serves_its_textures_and_nothing_else(content):
    """The grain and the highlighter are files on the studio origin, registered by name."""
    document = document_for([{"layout": "statement", "text": "Uma ==frase=="}], content)

    assert set(document.files) >= {"marker.svg", "grain.png"}
    assert document.files["marker.svg"].name == "marker-yellow.svg"
    assert f"{ORIGIN}/files/marker.svg" in document.html


def test_the_accent_swaps_the_highlighter(content):
    document = document_for([{"layout": "statement", "text": "Uma ==frase=="}], content, accent="blue")

    assert document.files["marker.svg"].name == "marker-blue.svg"
    assert "--marker: #A3CDF2" in document.html


def test_the_previous_identity_has_no_jornal_textures(content):
    document = document_for([{"layout": "statement", "text": "Uma frase"}], content, theme="drafting")

    assert "marker.svg" not in document.files
    assert "masthead" not in document.html


def test_the_masthead_falls_back_to_the_title(content):
    plain = document_for([{"layout": "statement", "text": "Uma frase"}], content).html
    named = document_for(
        [{"layout": "statement", "text": "Uma frase"}],
        content,
        masthead={"label": "Loja que aprende", "detail": "products-recommendations"},
    ).html

    assert '<span class="masthead-label">T</span>' in plain
    assert '<span class="masthead-label">Loja que aprende</span>' in named
    assert '<span class="masthead-detail">products-recommendations</span>' in named


def test_the_cover_collage_puts_each_picture_in_its_slot(content):
    PILImage.new("RGBA", (40, 30), (0, 0, 0, 0)).save(content / "cut.png")
    collage = [
        {"image": "shot.png", "kind": "capture"},
        {"image": "cut.png", "kind": "cutout"},
    ]

    document = document_for([{"layout": "cover", "headline": "Capa", "collage": collage}], content)
    body = body_of(document.html)

    assert 'class="collage-pasted is-capture"' in body
    assert 'class="collage-cutout"' in body
    assert "collage-print" not in body
    assert "cover-band" in body
    assert {"collage-1-capture.png", "collage-1-cutout.png"} <= set(document.files)


def test_a_photo_that_does_not_exist_is_reported(content):
    slide = {"layout": "statement", "text": "Uma frase", "photo": {"image": "media/x/photos/nao.jpg"}}

    document = document_for([slide], content)

    assert any("nao.jpg" in problem for problem in document.missing)


def test_a_slide_photo_sits_in_the_corner_and_the_headline_makes_room(content):
    PILImage.new("RGB", (30, 40), "gray").save(content / "foto.jpg")
    slide = {
        "layout": "points",
        "headline": "Pontos",
        "items": ["um", "dois"],
        "photo": {"image": "foto.jpg", "kind": "print", "caption": "Uma foto"},
    }

    html = document_for([slide], content).html

    assert 'class="corner-photo is-print"' in html
    assert 'class="photo-room"' in html
    assert "Uma foto" in html


def test_a_mark_is_placed_in_percent_of_the_image(content):
    PILImage.new("RGB", (1000, 500), "white").save(content / "tela.png")
    slide = {
        "layout": "image",
        "image": "tela.png",
        "fit": "contain",
        "mark": {"box": [100, 50, 400, 250], "label": "aqui"},
    }

    html = document_for([slide], content).html

    assert "left: calc(10.0% - 12px)" in html
    assert "top: calc(10.0% - 12px)" in html
    assert "width: calc(30.0% + 24px)" in html
    assert 'class="mark-label is-right"' in html


def test_a_mark_outside_the_image_is_an_error_not_a_misplaced_box(content):
    PILImage.new("RGB", (200, 100), "white").save(content / "tela.png")
    slide = {"layout": "image", "image": "tela.png", "fit": "contain", "mark": {"box": [10, 10, 300, 50]}}

    document = document_for([slide], content)

    assert any("runs past the image" in problem for problem in document.missing)
    assert "mark-box" not in body_of(document.html)


def test_captures_print_in_black_and_white_in_jornal_unless_color_is_asked(content):
    def shot(**deck) -> str:
        image = {"layout": "image", "image": "shot.png", **deck.pop("slide", {})}
        return body_of(document_for([image], content, **deck).html)

    assert "is-mono" in shot()
    assert "is-mono" not in shot(slide={"tone": "color"})
    assert "is-mono" not in shot(theme="drafting")


def test_torn_edges_are_the_same_on_every_render_and_differ_between_decks(content):
    closing = [{"layout": "closing", "headline": "Fim", "cta": "Link no comentário"}]

    def clips(title: str) -> list[str]:
        html = document_for(closing, content, title=title).html
        return re.findall(r'style="clip-path: (polygon\([^"]*)"', html)

    first = clips("Um")
    assert first and first == clips("Um")
    assert first != clips("Outro")


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
