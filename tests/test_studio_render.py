"""Real renders, in a real headless browser, and a real ffmpeg encode.

Everything else in the studio can be tested on strings. These cannot: whether
text fits, whether the PDF has one page per slide at one size, whether a video
comes out with the length it was planned to have. They are skipped when no
Chromium is available, which is the case on CI unless `playwright install`
ran; locally they take about half a minute.
"""

from __future__ import annotations

import html
import zipfile
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from PIL import Image as PILImage

from linkedin_growth.studio import browser
from linkedin_growth.studio.browser import browser_available
from linkedin_growth.studio.carousel import render_carousel
from linkedin_growth.studio.convert import convert_file, find_libreoffice
from linkedin_growth.studio.spec import parse_spec
from linkedin_growth.studio.video import media_seconds, render_video

# The smallest OpenDocument text LibreOffice opens: a zip with the mimetype
# stored first, a manifest and the content. Built at test time so the suite
# needs no binary fixture.
ODT_MANIFEST = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" '
    'manifest:version="1.3">'
    '<manifest:file-entry manifest:full-path="/" '
    'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
    '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
    "</manifest:manifest>"
)
ODT_CONTENT = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.3">'
    "<office:body><office:text>{paragraphs}</office:text></office:body>"
    "</office:document-content>"
)

DECK = [
    {"layout": "cover", "headline": "Um gancho curto."},
    {"layout": "points", "headline": "Três pontos", "items": ["um", "dois", "três"]},
    {"layout": "closing", "headline": "Fim.", "question": "E você?"},
]


@pytest.fixture(scope="module")
def chromium():
    if not browser_available():
        pytest.skip("no Chromium to render with (uv run playwright install chromium)")


@pytest.fixture(scope="module")
def libreoffice():
    if not find_libreoffice():
        pytest.skip("LibreOffice is not installed")


def write_odt(path: Path, paragraphs: list[str]) -> Path:
    body = "".join(f"<text:p>{html.escape(paragraph)}</text:p>" for paragraph in paragraphs)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.text")
        archive.writestr("META-INF/manifest.xml", ODT_MANIFEST, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr(
            "content.xml", ODT_CONTENT.format(paragraphs=body), compress_type=zipfile.ZIP_DEFLATED
        )
    return path


def carousel(slides, **deck):
    spec, problems = parse_spec({"title": "Teste", **deck, "slides": slides}, "carousel")
    assert spec is not None and problems == [], problems
    return spec


def page_sizes(pdf) -> set[tuple[int, int]]:
    document = pdfium.PdfDocument(str(pdf))
    try:
        return {tuple(round(value) for value in document[i].get_size()) for i in range(len(document))}
    finally:
        document.close()


def test_a_carousel_renders_one_uniform_page_per_slide(chromium, tmp_path):
    result = render_carousel(carousel(DECK), tmp_path / "deck", content_root=tmp_path)

    assert result.ok, result.errors
    document = pdfium.PdfDocument(str(result.pdf))
    try:
        assert len(document) == 3
    finally:
        document.close()
    # 1080x1350 CSS pixels are 810x1012.5 points; Chromium rounds the height.
    assert page_sizes(result.pdf) == {(810, 1013)}
    assert [path.name for path in result.slides] == ["01.png", "02.png", "03.png"]
    with PILImage.open(result.slides[0]) as png:
        assert png.size == (1080, 1350)
    assert result.contact_sheet.is_file()


def test_text_that_cannot_fit_writes_no_pdf(chromium, tmp_path):
    """A clipped slide must never look like a finished file."""
    crowded = [{"layout": "points", "headline": "Demais " * 18, "items": ["palavra " * 20] * 6}]

    result = render_carousel(carousel(crowded), tmp_path / "deck", content_root=tmp_path)

    assert not result.ok
    assert any("does not fit" in error for error in result.errors)
    assert not (tmp_path / "deck" / "carousel.pdf").exists()
    assert (tmp_path / "deck" / "preview" / "contact-sheet.png").is_file()


def test_a_deck_whose_bundled_fonts_do_not_load_writes_no_pdf(chromium, tmp_path, monkeypatch):
    """A deck set in a fallback system face must never look like a finished file."""
    # The page still declares every face; the browser just refuses to serve them.
    monkeypatch.setattr(browser, "FONTS", ())

    result = render_carousel(carousel(DECK), tmp_path / "deck", content_root=tmp_path)

    assert not result.ok
    assert any("fonts did not load" in error for error in result.errors)
    assert not (tmp_path / "deck" / "carousel.pdf").exists()


def test_a_single_image_post_writes_one_png_and_no_pdf(chromium, tmp_path):
    spec = carousel([{"layout": "statement", "text": "Uma frase só."}])

    result = render_carousel(spec, tmp_path / "image", content_root=tmp_path, single_image=True)

    assert result.ok, result.errors
    with PILImage.open(result.image) as png:
        assert png.size == (1080, 1350)
    assert not (tmp_path / "image" / "carousel.pdf").exists()


def test_markdown_flows_across_uniform_pages(chromium, tmp_path):
    source = tmp_path / "notas.md"
    source.write_text("# Título\n\n" + ("Um parágrafo de texto. " * 40 + "\n\n") * 8, encoding="utf-8")

    result = convert_file(source, tmp_path / "notas.pdf")

    assert result.ok, result.errors
    assert result.pages >= 2
    assert page_sizes(result.pdf) == {(810, 1013)}


def test_a_pdf_with_mixed_page_sizes_is_refit_to_one_size(chromium, tmp_path):
    source = tmp_path / "misto.pdf"
    document = pdfium.PdfDocument.new()
    document.new_page(612, 792)
    document.new_page(842, 595)
    document.save(str(source))
    document.close()

    result = convert_file(source, tmp_path / "saida.pdf")

    assert result.ok, result.errors
    assert result.pages == 2
    assert page_sizes(result.pdf) == {(810, 1013)}
    assert any("different sizes" in warning for warning in result.warnings)


def test_an_office_document_converts_through_libreoffice(libreoffice, tmp_path):
    """The path .pptx, .xlsx, .odt and .doc files take. Skipped without LibreOffice.

    LibreOffice sets its own page size; what LinkedIn requires, and what is
    checked, is that every page shares it.
    """
    source = write_odt(tmp_path / "notas.odt", ["Uma nota de estudo.", "Com acentos: ação, útil, pão."])

    result = convert_file(source, tmp_path / "notas.pdf")

    assert result.ok, result.errors
    assert result.kind == "office"
    assert result.pages >= 1
    assert len(page_sizes(result.pdf)) == 1


def test_a_short_video_encodes_to_its_planned_length_with_captions(chromium, tmp_path):
    spec, problems = parse_spec(
        {
            "title": "V",
            "scenes": [
                {"layout": "statement", "text": "Uma frase.", "duration": 1.5, "narration": "Uma frase curta."},
                {"layout": "closing", "headline": "Fim.", "duration": 1.5},
            ],
        },
        "video",
    )
    assert spec is not None, problems

    result = render_video(spec, tmp_path / "video", content_root=tmp_path)

    assert result.ok, result.errors
    assert media_seconds(result.video) == pytest.approx(3.0, abs=0.2)
    assert result.captions.read_text(encoding="utf-8").startswith("1\n")
    assert result.cover.is_file()
