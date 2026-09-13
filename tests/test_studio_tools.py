"""The studio tools the Post Designer calls: they report, they never raise.

The conventions of `tools/` hold here too. A failure comes back as text the
agent can act on, and nothing is written outside `content/media/<slug>/`.
"""

from __future__ import annotations

import pytest

from linkedin_growth.tools import studio
from tests.conftest import call


@pytest.fixture
def media(tmp_path, monkeypatch):
    content = tmp_path / "content"
    media_dir = content / "media"
    media_dir.mkdir(parents=True)
    monkeypatch.setattr(studio, "CONTENT_DIR", content)
    monkeypatch.setattr(studio, "MEDIA_DIR", media_dir)
    monkeypatch.setattr(studio, "ROOT", tmp_path)
    return media_dir


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("render_carousel", {"spec": "title: T"}),
        ("render_image_post", {"spec": "title: T"}),
        ("render_video", {"spec": "title: T"}),
        ("inspect_slides", {}),
        ("capture_screenshot", {"url": "https://example.org", "name": "x"}),
    ],
)
def test_a_bad_slug_is_reported_without_touching_disk(media, tool_name, arguments):
    result = call(getattr(studio, tool_name), slug="../fora", **arguments)

    assert result.content.startswith("ERROR")
    assert list(media.iterdir()) == []


def test_an_invalid_spec_comes_back_as_a_list_of_fixes(media):
    result = call(studio.render_carousel, slug="post", spec="title: T\nslides:\n  - layout: hero\n")

    assert result.content.startswith("ERROR: the spec is invalid")
    assert "slides[1]" in result.content


def test_a_linkedin_capture_is_refused_before_a_browser_starts(media):
    result = call(studio.capture_screenshot, slug="post", url="https://www.linkedin.com/feed/", name="feed")

    assert "LinkedIn" in result.content
    assert not (media / "post" / "screens").exists()


def test_convert_refuses_a_path_outside_content(media):
    assert call(studio.convert_to_pdf, source="../../.env").content.startswith("ERROR")


def test_inspecting_before_rendering_says_what_to_do_first(media):
    result = call(studio.inspect_slides, slug="post", slides="1")

    assert "render_carousel first" in result.content


def test_listing_with_nothing_there_says_so(media):
    assert call(studio.list_media).content == "No media yet."


def test_a_preview_image_can_be_formatted_for_claude(tmp_path):
    """Regression: every tool that returns an image needs `filetype` on Python 3.13.

    Agno's Claude formatter detects the image type with `imghdr`, which Python
    3.13 removed, and falls back to `filetype`. Without it the formatter raises
    for any image, file or bytes. No unit test with the spy model could see it:
    the first real design run died at the model call right after its first
    screenshot. This runs the real formatter, with no request.
    """
    from agno.utils.models.claude import _format_image_for_message
    from PIL import Image as PILImage

    picture = tmp_path / "slide.png"
    PILImage.new("RGB", (40, 50), "white").save(picture)
    [image] = studio.preview(picture)

    block = _format_image_for_message(image)

    assert block is not None
    assert "image/jpeg" in str(block)


def test_an_unexpected_failure_becomes_a_report(media, monkeypatch):
    def explode(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(studio, "draw_carousel", explode)

    result = call(
        studio.render_carousel,
        slug="post",
        spec="title: T\nslides:\n  - layout: statement\n    text: Oi\n",
    )

    assert result.content.startswith("ERROR: the studio failed unexpectedly")
