"""Photos from the open web: only free licenses, only public hosts, only pixels.

No network here. Openverse and the image hosts are an `httpx.MockTransport`,
and the URL guard is replaced by one that knows which made-up hosts are
"private", because the real one resolves names through DNS.
"""

from __future__ import annotations

import io
import json

import httpx
import pytest
from PIL import Image as PILImage

from linkedin_growth.studio import photos

PHOTO_ID = "8a9ab3e9-cb3c-4fb6-a5b9-0ca2845d06ac"
BY_ID = "11111111-2222-3333-4444-555555555555"


def png(background: str = "white") -> bytes:
    """An object (a black square) on a background, as PNG bytes."""
    picture = PILImage.new("RGB", (200, 120), background)
    picture.paste((10, 10, 10), (60, 30, 140, 90))
    buffer = io.BytesIO()
    picture.save(buffer, format="PNG")
    return buffer.getvalue()


def item(photo_id: str = PHOTO_ID, license_: str = "cc0", url: str = "https://images.example.org/fones.png") -> dict:
    return {
        "id": photo_id,
        "title": "Black headphones",
        "creator": "Someone",
        "provider": "rawpixel",
        "license": license_,
        "license_version": "1.0",
        "width": 200,
        "height": 120,
        "url": url,
        "thumbnail": url,
        "foreign_landing_url": "https://www.rawpixel.com/image/1",
    }


@pytest.fixture
def web(monkeypatch):
    """A fake web: Openverse, an image host, and a host that counts as private."""
    state = {"image": png(), "item": item(), "requests": []}

    def handler(request: httpx.Request) -> httpx.Response:
        state["requests"].append(str(request.url))
        if request.url.host == "api.openverse.org":
            if request.url.path == "/v1/images/":
                results = [item(), item(BY_ID, license_="by")]
                return httpx.Response(200, json={"results": results})
            return httpx.Response(200, json=state["item"])
        if request.url.host == "images.example.org":
            if request.url.path == "/hop":
                return httpx.Response(302, headers={"location": "https://intranet.example.org/secret.png"})
            return httpx.Response(200, content=state["image"])
        return httpx.Response(404)

    def fake_check(url: str) -> str | None:
        return "a private address" if "intranet" in url else None

    monkeypatch.setattr(photos, "check_url", fake_check)
    state["client"] = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    return state


def test_search_asks_for_free_licenses_and_drops_anything_else(web):
    found = photos.search("black headphones", client=web["client"])

    assert [candidate.id for candidate in found] == [PHOTO_ID]
    asked = web["requests"][0]
    assert "license=cc0%2Cpdm" in asked


def test_a_photo_with_another_license_is_refused(web, tmp_path):
    web["item"] = item(license_="by-sa")

    result = photos.fetch(PHOTO_ID, tmp_path, "fones", client=web["client"])

    assert not result.ok
    assert "public domain and CC0" in result.errors[0]
    assert list(tmp_path.iterdir()) == []


def test_an_id_that_is_not_an_openverse_id_is_refused_before_any_request(web):
    with pytest.raises(photos.PhotoError):
        photos.lookup("../../etc/passwd", client=web["client"])
    assert web["requests"] == []


def test_a_fetch_writes_the_photo_its_cutout_and_its_credit(web, tmp_path):
    result = photos.fetch(PHOTO_ID, tmp_path, "fones", cutout=True, client=web["client"])

    assert result.ok, result.errors
    assert result.photo.name == "fones.jpg"
    assert result.cutout.name == "fones-recorte.png"
    with PILImage.open(result.cutout) as shape:
        assert shape.mode == "RGBA"
        assert shape.size == (80, 60), "the cutout is cropped to the object"
    credits = json.loads((tmp_path / "credits.json").read_text(encoding="utf-8"))
    assert credits[0]["file"] == "fones.jpg"
    assert credits[0]["license"] == "CC0 1.0"
    assert credits[0]["landing"] == "https://www.rawpixel.com/image/1"


def test_fetching_again_replaces_the_credit_instead_of_adding_one(web, tmp_path):
    photos.fetch(PHOTO_ID, tmp_path, "fones", client=web["client"])
    photos.fetch(PHOTO_ID, tmp_path, "fones", client=web["client"])

    assert len(json.loads((tmp_path / "credits.json").read_text(encoding="utf-8"))) == 1


def test_no_cutout_is_written_when_the_background_is_not_white(web, tmp_path):
    web["image"] = png(background="#6A7A5A")

    result = photos.fetch(PHOTO_ID, tmp_path, "foto", cutout=True, client=web["client"])

    assert result.ok
    assert result.cutout is None
    assert any("not white" in note for note in result.notes)
    assert not (tmp_path / "foto-recorte.png").exists()


def test_bytes_that_are_not_an_image_never_reach_the_folder(web, tmp_path):
    web["image"] = b"<html>not a picture</html>"

    result = photos.fetch(PHOTO_ID, tmp_path, "fones", client=web["client"])

    assert not result.ok
    assert list(tmp_path.iterdir()) == []


def test_a_redirect_into_a_private_address_is_refused(web, tmp_path):
    web["item"] = item(url="https://images.example.org/hop")

    result = photos.fetch(PHOTO_ID, tmp_path, "fones", client=web["client"])

    assert not result.ok
    assert "private" in result.errors[0]
    assert not any("intranet" in url for url in web["requests"])


def test_plain_http_is_never_fetched(web, tmp_path):
    web["item"] = item(url="http://images.example.org/fones.png")

    result = photos.fetch(PHOTO_ID, tmp_path, "fones", client=web["client"])

    assert not result.ok
    assert "only https" in result.errors[0]


def test_a_file_name_that_could_leave_the_folder_is_refused(web, tmp_path):
    result = photos.fetch(PHOTO_ID, tmp_path, "../fora", client=web["client"])

    assert not result.ok
    assert web["requests"] == []


def test_a_network_failure_is_a_report_not_a_traceback(web, tmp_path):
    def broken(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.openverse.org":
            return httpx.Response(200, json=item())
        raise httpx.ConnectError("down", request=request)

    client = httpx.Client(transport=httpx.MockTransport(broken))

    result = photos.fetch(PHOTO_ID, tmp_path, "fones", client=client)

    assert not result.ok
    assert "ConnectError" in result.errors[0]


def test_a_credits_file_that_is_not_a_list_is_started_over(web, tmp_path):
    (tmp_path / "credits.json").write_text('{"oops": 1}', encoding="utf-8")

    result = photos.fetch(PHOTO_ID, tmp_path, "fones", client=web["client"])

    assert result.ok
    credits = json.loads((tmp_path / "credits.json").read_text(encoding="utf-8"))
    assert [entry["file"] for entry in credits] == ["fones.jpg"]


def test_the_cutout_keeps_the_object_and_drops_the_white():
    picture = PILImage.open(io.BytesIO(png()))

    shape, cleared = photos.cutout_white(picture)

    assert shape.getpixel((0, 0))[3] == 255, "the object is opaque"
    assert shape.size == (80, 60)
    assert cleared == pytest.approx(1 - (80 * 60) / (200 * 120)), "measured on the whole photo, before the crop"
    blank, all_clear = photos.cutout_white(PILImage.new("RGB", (10, 10), "white"))
    assert blank.getchannel("A").getextrema() == (0, 0)
    assert all_clear == 1.0
