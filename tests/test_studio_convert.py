"""Converting files: which converter takes which file, and the failures that must read well.

No browser here; the real conversions are in `test_studio_render.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_growth.studio import convert
from linkedin_growth.studio.convert import convert_file, kind_of


@pytest.mark.parametrize(
    ("name", "kind"),
    [
        ("notas.md", "markdown"),
        ("log.txt", "text"),
        ("page.html", "html"),
        ("shot.PNG", "image"),
        ("deck.pdf", "pdf"),
        ("cv.docx", "docx"),
        ("bench.csv", "table"),
        ("slides.pptx", "office"),
        ("agent.py", "code"),
        ("query.sql", "code"),
        ("mystery.xyz123", None),
    ],
)
def test_each_extension_goes_to_its_converter(name, kind):
    assert kind_of(Path(name)) == kind


def test_an_unsupported_file_says_what_is_supported(tmp_path):
    source = tmp_path / "mystery.xyz123"
    source.write_text("?", encoding="utf-8")

    result = convert_file(source, tmp_path / "out.pdf")

    assert not result.ok
    assert "Supported" in result.errors[0]


def test_a_missing_file_is_an_error_not_an_exception(tmp_path):
    result = convert_file(tmp_path / "nope.md", tmp_path / "out.pdf")

    assert not result.ok
    assert "does not exist" in result.errors[0]


def test_office_files_without_libreoffice_explain_the_way_out(tmp_path, monkeypatch):
    monkeypatch.setattr(convert, "find_libreoffice", lambda: None)
    source = tmp_path / "deck.pptx"
    source.write_bytes(b"not really a pptx")

    result = convert_file(source, tmp_path / "deck.pdf")

    assert not result.ok
    assert "LibreOffice" in result.errors[0]
    assert "export the file to PDF" in result.errors[0]
