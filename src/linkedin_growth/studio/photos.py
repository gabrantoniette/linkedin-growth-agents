"""Photos from the open web for the jornal collage, and the record of where each came from.

Every jornal deck carries at least one real photo of the post's subject
(DESIGN_RULES). This module finds them and brings them in, under three rules:

1. **Public domain or CC0 only.** The search asks Openverse, the open catalog
   of openly licensed images, for `cc0` and `pdm` alone, and the fetch refuses
   anything else. A photo then needs no permission and no credit line on the
   slide. The credit is written down anyway, in `photos/credits.json` next to
   the photo, because "where did this come from" must always have an answer.
2. **A photo illustrates, it never proves.** That rule lives in HONESTY and
   DESIGN_RULES; here it only explains why a photo is never a capture.
3. **Downloaded bytes are untrusted.** Every request goes to a public https
   host (the same guard screenshots use, redirects included), the download is
   capped, and Pillow decodes the file and writes it again as a fresh JPEG or
   PNG, so nothing but pixels reaches content/.

The cutout: most CC0 product shots stand on white. Turning near-white into
transparency, with a soft ramp so the edges do not look cut with scissors,
gives the object the jornal cover pastes over its highlighter. It works on a
white background and nowhere else, so it is offered, never assumed.
"""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from PIL import Image, ImageChops, ImageDraw, ImageOps

from linkedin_growth.studio.safety import check_url

OPENVERSE = "https://api.openverse.org/v1/images/"
LICENSES = ("cc0", "pdm")
LICENSE_NAMES = {"cc0": "CC0", "pdm": "Public Domain Mark"}

TIMEOUT = 30.0
MAX_BYTES = 25 * 1024 * 1024
MAX_REDIRECTS = 5
# Big enough for a full-bleed slide at 2x; past that the file only grows.
MAX_EDGE = 2400
CUTOUT_EDGE = 1600
# A file that decodes to more pixels than this is refused before decoding: a
# small download can expand into gigabytes (a decompression bomb).
MAX_PIXELS = 60_000_000

USER_AGENT = "linkedin-growth-agents studio (https://github.com/gabrantoniette/linkedin-growth-agents)"
_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_NAME = re.compile(r"^[a-z0-9][a-z0-9\-]{0,59}$")

SHEET_COLUMNS = 4
SHEET_CELL = (360, 300)

# Below this share of transparent pixels, the background was not white and the
# "cutout" is the whole photo with ragged holes in it.
MIN_CUTOUT_CLEARED = 0.2


class PhotoError(Exception):
    """A search or a fetch that cannot go on, with a reason a person can act on."""


@dataclass
class Candidate:
    id: str
    title: str
    creator: str | None
    provider: str
    license: str
    license_version: str | None
    width: int | None
    height: int | None
    url: str
    thumbnail: str | None
    landing: str | None

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> Candidate | None:
        """One Openverse result, or None when it is not usable here."""
        license_ = str(item.get("license") or "").lower()
        if license_ not in LICENSES or not item.get("url") or not item.get("id"):
            return None
        return cls(
            id=str(item["id"]),
            title=str(item.get("title") or "untitled").strip()[:120],
            creator=(str(item["creator"]).strip()[:80] or None) if item.get("creator") else None,
            provider=str(item.get("provider") or item.get("source") or "unknown"),
            license=license_,
            license_version=str(item["license_version"]) if item.get("license_version") else None,
            width=item.get("width"),
            height=item.get("height"),
            url=str(item["url"]),
            thumbnail=str(item["thumbnail"]) if item.get("thumbnail") else None,
            landing=str(item["foreign_landing_url"]) if item.get("foreign_landing_url") else None,
        )

    def license_name(self) -> str:
        name = LICENSE_NAMES.get(self.license, self.license.upper())
        return f"{name} {self.license_version}" if self.license_version else name

    def line(self, number: int) -> str:
        size = f"{self.width}x{self.height}" if self.width and self.height else "size unknown"
        by = f", by {self.creator}" if self.creator else ""
        return f"{number}. {self.id}  {self.title}{by} ({self.provider}, {self.license_name()}, {size})"


@dataclass
class FetchResult:
    ok: bool = False
    photo: Path | None = None
    cutout: Path | None = None
    credit: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def summary(self, root: Path) -> str:
        def show(path: Path) -> str:
            try:
                return path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                return str(path)

        if not self.ok:
            return "NOT FETCHED. " + " ".join(self.errors)
        lines = [f"Photo: {show(self.photo)}" if self.photo else ""]
        if self.cutout:
            lines.append(f"Cutout: {show(self.cutout)}")
        lines.append(
            f"Credit: {self.credit['title']}, {self.credit.get('creator') or 'creator unknown'}, "
            f"{self.credit['license']}, {self.credit.get('landing') or self.credit['source']}"
        )
        lines.extend(f"Note: {note}" for note in self.notes)
        return "\n".join(line for line in lines if line)


def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}, follow_redirects=False)


def _get(client: httpx.Client, url: str, *, limit: int = MAX_BYTES) -> bytes:
    """GET a public https URL, following redirects one hop at a time, capped in size.

    A network failure becomes a PhotoError, like every other refusal, so the
    CLI prints a sentence instead of a traceback.
    """
    try:
        return _get_unchecked(client, url, limit)
    except httpx.HTTPError as error:
        raise PhotoError(f"could not download {url} ({type(error).__name__}).") from error


def _get_unchecked(client: httpx.Client, url: str, limit: int) -> bytes:
    for _ in range(MAX_REDIRECTS + 1):
        if not url.startswith("https://"):
            raise PhotoError(f"refused {url}: only https is fetched.")
        reason = check_url(url)
        if reason:
            raise PhotoError(f"refused {url}: {reason}")
        with client.stream("GET", url) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers.get("location", ""))
                continue
            if response.status_code != 200:
                raise PhotoError(f"{url} answered HTTP {response.status_code}.")
            declared = int(response.headers.get("content-length") or 0)
            if declared > limit:
                raise PhotoError(f"{url} is {declared // 1_000_000} MB, past the {limit // 1_000_000} MB cap.")
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > limit:
                    raise PhotoError(f"{url} is past the {limit // 1_000_000} MB cap.")
                chunks.append(chunk)
            return b"".join(chunks)
    raise PhotoError(f"{url} redirects more than {MAX_REDIRECTS} times.")


def _decode(data: bytes, source: str) -> Image.Image:
    """Bytes from the web as a Pillow image, fully loaded, or a PhotoError."""
    try:
        picture = Image.open(io.BytesIO(data))
        if picture.width * picture.height > MAX_PIXELS:
            raise PhotoError(f"{source} is {picture.width}x{picture.height}, too large to decode safely.")
        picture.load()
    except (OSError, Image.DecompressionBombError) as error:
        raise PhotoError(f"{source} is not an image the studio can read ({error}).") from error
    return ImageOps.exif_transpose(picture)


def search(query: str, *, count: int = 12, client: httpx.Client | None = None) -> list[Candidate]:
    """Public-domain and CC0 photos for a query, best match first."""
    query = query.strip()
    if not query:
        raise PhotoError("say what to look for, in English: the catalog is mostly English.")
    params = {
        "q": query,
        "license": ",".join(LICENSES),
        "category": "photograph,illustration,digitized_artwork",
        "mature": "false",
        "page_size": str(max(1, min(count, 30))),
    }
    own = client is None
    client = client or _client()
    try:
        response = client.get(OPENVERSE, params=params)
        if response.status_code == 429:
            raise PhotoError("Openverse is rate limiting this address; wait a minute and try again.")
        if response.status_code != 200:
            raise PhotoError(f"Openverse answered HTTP {response.status_code}.")
        results = response.json().get("results", [])
    except httpx.HTTPError as error:
        raise PhotoError(f"could not reach Openverse ({type(error).__name__}).") from error
    finally:
        if own:
            client.close()
    found = [Candidate.from_api(item) for item in results]
    return [candidate for candidate in found if candidate][:count]


def lookup(photo_id: str, *, client: httpx.Client | None = None) -> Candidate:
    """One photo by its Openverse id, checked for a license this project uses."""
    photo_id = photo_id.strip().lower()
    if not _ID.match(photo_id):
        raise PhotoError(f"'{photo_id}' is not an Openverse id; copy it from search_photos.")
    own = client is None
    client = client or _client()
    try:
        response = client.get(f"{OPENVERSE}{photo_id}/")
        if response.status_code == 404:
            raise PhotoError(f"Openverse has no photo {photo_id}.")
        if response.status_code != 200:
            raise PhotoError(f"Openverse answered HTTP {response.status_code}.")
        item = response.json()
    except httpx.HTTPError as error:
        raise PhotoError(f"could not reach Openverse ({type(error).__name__}).") from error
    finally:
        if own:
            client.close()
    candidate = Candidate.from_api(item)
    if candidate is None:
        raise PhotoError(
            f"{photo_id} is licensed '{item.get('license')}'. Only public domain and CC0 "
            "photos are used, so a post never depends on someone's permission."
        )
    return candidate


def cutout_white(picture: Image.Image, low: int = 24, high: int = 72) -> tuple[Image.Image, float]:
    """An object shot on white, with the white made transparent and the rest cropped away.

    A pixel's distance from white is how far its darkest channel is from 255.
    Below `low` it is background; past `high` it is the object; in between it
    fades, which keeps soft edges and contact shadows from looking cut out.

    Returns the cutout and the share of the photo that came out transparent,
    measured before the crop: after it, a clean cutout is nearly all object.
    """
    red, green, blue = picture.convert("RGB").split()
    darkest = ImageChops.darker(ImageChops.darker(red, green), blue)
    distance = ImageOps.invert(darkest)
    span = high - low
    alpha = distance.point(lambda d: 0 if d < low else 255 if d > high else int((d - low) * 255 / span))
    cleared = alpha.histogram()[0] / (alpha.width * alpha.height)
    out = picture.convert("RGBA")
    out.putalpha(alpha)
    box = alpha.getbbox()
    return (out.crop(box) if box else out), cleared


def _record(folder: Path, credit: dict[str, Any]) -> None:
    """Add or replace one entry of the folder's credits.json."""
    path = folder / "credits.json"
    try:
        entries = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    except (OSError, json.JSONDecodeError):
        entries = []
    # A file edited by hand into something else is started over, not trusted.
    if not isinstance(entries, list):
        entries = []
    entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("file") != credit["file"]]
    entries.append(credit)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch(
    photo_id: str,
    folder: Path,
    name: str,
    *,
    cutout: bool = False,
    client: httpx.Client | None = None,
) -> FetchResult:
    """Download one photo into `folder` as `<name>.jpg`, its cutout as `<name>-recorte.png`."""
    result = FetchResult()
    if not _NAME.match(name):
        result.errors.append(f"'{name}' is not a valid file name: lowercase letters, digits and hyphens.")
        return result
    own = client is None
    client = client or _client()
    try:
        candidate = lookup(photo_id, client=client)
        picture = _decode(_get(client, candidate.url), candidate.url)
    except PhotoError as error:
        result.errors.append(str(error))
        return result
    finally:
        if own:
            client.close()

    folder.mkdir(parents=True, exist_ok=True)
    flat = picture.convert("RGB")
    flat.thumbnail((MAX_EDGE, MAX_EDGE))
    result.photo = folder / f"{name}.jpg"
    flat.save(result.photo, format="JPEG", quality=90, optimize=True)
    if cutout:
        shape, cleared = cutout_white(picture)
        if cleared < MIN_CUTOUT_CLEARED:
            result.notes.append(
                f"no cutout: only {cleared:.0%} of the photo came out transparent, so its "
                "background is not white. Use the photo as a `print`."
            )
        else:
            shape.thumbnail((CUTOUT_EDGE, CUTOUT_EDGE))
            result.cutout = folder / f"{name}-recorte.png"
            shape.save(result.cutout, format="PNG", optimize=True)

    result.credit = {
        "file": result.photo.name,
        "cutout": result.cutout.name if result.cutout else None,
        "openverse_id": candidate.id,
        "title": candidate.title,
        "creator": candidate.creator,
        "provider": candidate.provider,
        "license": candidate.license_name(),
        "landing": candidate.landing,
        "source": candidate.url,
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _record(folder, result.credit)
    result.ok = True
    return result


def candidate_sheet(candidates: list[Candidate], target: Path, *, client: httpx.Client | None = None) -> Path | None:
    """Every candidate's thumbnail on one numbered image, for choosing at a glance.

    Openverse's own thumbnail first; for providers whose thumbnail fails, the
    original, shrunk here. A candidate that loads neither way gets an empty cell
    with its number, so the numbers still match the list.
    """
    if not candidates:
        return None
    own = client is None
    client = client or _client()
    width, height = SHEET_CELL
    rows = -(-len(candidates) // SHEET_COLUMNS)
    sheet = Image.new("RGB", (SHEET_COLUMNS * width, rows * height), "#26241F")
    draw = ImageDraw.Draw(sheet)
    try:
        for index, candidate in enumerate(candidates):
            picture = None
            for url in (candidate.thumbnail, candidate.url):
                if not url:
                    continue
                try:
                    picture = _decode(_get(client, url, limit=8 * 1024 * 1024), url)
                    break
                except PhotoError:
                    continue
            x, y = (index % SHEET_COLUMNS) * width, (index // SHEET_COLUMNS) * height
            if picture is not None:
                picture = picture.convert("RGB")
                picture.thumbnail((width - 12, height - 40))
                sheet.paste(picture, (x + 6, y + 6))
            draw.rectangle((x + 6, y + height - 32, x + 46, y + height - 6), fill="#FFD34E")
            draw.text((x + 14, y + height - 27), str(index + 1), fill="#171614")
            draw.text((x + 54, y + height - 27), candidate.license_name(), fill="#EEEAE2")
    finally:
        if own:
            client.close()
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, optimize=True)
    return target
