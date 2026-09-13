"""The studio as tools: the Post Designer's hands, and its eyes.

Every tool follows the two conventions of `tools/`:

1. **It never raises.** A failure comes back as text the agent can read and act
   on: a slide that overflows, a URL that is refused, a browser that is not
   installed. An exception would end the run and throw away the work so far.
2. **It writes only inside `content/media/<slug>/`.** The slug is validated, and
   every path a spec points at resolves inside `content/`.

The render and capture tools return images next to the report: the contact
sheet, the slides, the capture. That is the reason to render inside the run at
all. "The headline wraps badly" is plain in a picture and invisible in a text
report, and the agent is instructed to look before it calls an asset finished.

The images reach the model as downscaled JPEGs. A full-page capture at 2x can
pass the size an image may have in a request, and the model reads at most about
1568px on the long edge anyway.
"""

from __future__ import annotations

import io
import re
from collections.abc import Callable
from pathlib import Path

from agno.media import Image
from agno.tools import tool
from agno.tools.function import ToolResult
from PIL import Image as PILImage

from linkedin_growth.config import CONTENT_DIR, MEDIA_DIR, ROOT, MissingConfiguration
from linkedin_growth.studio.brand import default_author
from linkedin_growth.studio.capture import capture_url
from linkedin_growth.studio.carousel import render_carousel as draw_carousel
from linkedin_growth.studio.convert import convert_file, supported_extensions
from linkedin_growth.studio.safety import confine, slugify, valid_slug
from linkedin_growth.studio.spec import parse_spec
from linkedin_growth.studio.themes import THEMES
from linkedin_growth.studio.video import render_video as draw_video

PREVIEW_EDGE = 1568
MAX_INSPECT = 4


def _report(text: str, *images: Image) -> ToolResult:
    return ToolResult(content=text, images=list(images) or None)


def preview(path: Path | None) -> list[Image]:
    """A picture on disk as a JPEG the model can look at, or nothing."""
    if not path or not path.is_file():
        return []
    with PILImage.open(path) as source:
        picture = source.convert("RGB")
    picture.thumbnail((PREVIEW_EDGE, PREVIEW_EDGE))
    buffer = io.BytesIO()
    picture.save(buffer, format="JPEG", quality=88)
    return [Image(content=buffer.getvalue(), format="jpeg", mime_type="image/jpeg")]


def _media_folder(slug: str) -> Path | None:
    return MEDIA_DIR / slug if valid_slug(slug) else None


def _bad_slug(slug: str) -> ToolResult:
    return _report(
        f"ERROR: '{slug}' is not a valid media folder name. Use the post file name "
        "without '.md': lowercase letters, digits and hyphens, for example "
        "'2026-09-04-rag-chunking'."
    )


def _invalid(problems: list[str]) -> ToolResult:
    listed = "\n".join(f"- {problem}" for problem in problems)
    return _report(f"ERROR: the spec is invalid. Fix these and call again:\n{listed}")


def _safely(work: Callable[[], ToolResult]) -> ToolResult:
    try:
        return work()
    except MissingConfiguration as error:
        return _report(f"ERROR: {error}")
    except Exception as error:  # noqa: BLE001 - a tool reports, it never raises
        return _report(
            f"ERROR: the studio failed unexpectedly ({type(error).__name__}: {error})."
        )


@tool
def render_carousel(slug: str, spec: str) -> ToolResult:
    """Render a carousel spec into a PDF, one PNG per slide and a contact sheet.

    Write the spec in YAML following the 'carousel-design' skill. The render
    refuses a spec with a [PREENCHER] marker, a dash in prose, a missing image or
    a slide whose text cannot fit, and the report names the slide and what to
    change. Warnings do not block, but read them.

    The contact sheet comes back as an image: look at it before calling the
    carousel done.

    Args:
        slug: The media folder, which is the post file name without '.md'.
        spec: The carousel spec, in YAML or JSON.

    Returns:
        The report, with paths from the project root, and the contact sheet.
    """

    def work() -> ToolResult:
        folder = _media_folder(slug)
        if folder is None:
            return _bad_slug(slug)
        parsed, problems = parse_spec(spec, "carousel")
        if parsed is None:
            return _invalid(problems)
        result = draw_carousel(parsed, folder, author=default_author())
        return _report(result.summary(ROOT), *preview(result.contact_sheet))

    return _safely(work)


@tool
def render_image_post(slug: str, spec: str) -> ToolResult:
    """Render a one-slide spec into a single 1080x1350 image post.

    The same spec format as a carousel, with exactly one slide. Layouts that
    work alone: metric, code, image, statement, compare.

    Args:
        slug: The media folder, which is the post file name without '.md'.
        spec: The spec, in YAML or JSON, with exactly one slide.

    Returns:
        The report and the image.
    """

    def work() -> ToolResult:
        folder = _media_folder(slug)
        if folder is None:
            return _bad_slug(slug)
        parsed, problems = parse_spec(spec, "carousel")
        if parsed is None:
            return _invalid(problems)
        result = draw_carousel(parsed, folder, author=default_author(), single_image=True)
        return _report(result.summary(ROOT), *preview(result.image or result.contact_sheet))

    return _safely(work)


@tool
def inspect_slides(slug: str, slides: str = "1") -> ToolResult:
    """Look at rendered slides at full size, up to four per call.

    Use it on the cover and on any slide that looks dense in the contact sheet.
    It shows the latest render: the finished slides, or the draft in preview/
    when the last render failed.

    Args:
        slug: The media folder of the carousel.
        slides: Slide numbers, comma-separated, for example '1' or '1,4,7'.

    Returns:
        The slides as images.
    """

    def work() -> ToolResult:
        folder = _media_folder(slug)
        if folder is None:
            return _bad_slug(slug)
        numbers = sorted({int(n) for n in re.findall(r"\d+", slides) if int(n) > 0})[:MAX_INSPECT]
        if not numbers:
            return _report("ERROR: say which slides to look at, for example '1' or '1,4'.")
        renders = [path for path in (folder / "slides", folder / "preview" / "slides") if path.is_dir()]
        if not renders:
            return _report(
                f"ERROR: nothing has been rendered in content/media/{slug}/ yet. "
                "Call render_carousel first."
            )
        latest = max(renders, key=lambda path: path.stat().st_mtime)
        found = [latest / f"{number:02d}.png" for number in numbers]
        found = [path for path in found if path.is_file()]
        if not found:
            return _report(f"ERROR: the last render has no slide {', '.join(map(str, numbers))}.")
        images = [image for path in found for image in preview(path)]
        shown = latest.relative_to(ROOT).as_posix()
        return _report(f"Slides {', '.join(p.stem for p in found)} from {shown}/, at full size.", *images)

    return _safely(work)


@tool
def render_video(slug: str, spec: str) -> ToolResult:
    """Render a video spec into an MP4, an SRT caption file and a cover frame.

    Scenes use the carousel layouts. Timing comes from reading speed, or from
    the user's own voiceover recording when the spec points at one. Follow the
    'short-video' skill. Rendering takes a minute or so.

    Args:
        slug: The media folder, which is the post file name without '.md'.
        spec: The video spec, in YAML or JSON.

    Returns:
        The report and the contact sheet of the scenes.
    """

    def work() -> ToolResult:
        folder = _media_folder(slug)
        if folder is None:
            return _bad_slug(slug)
        parsed, problems = parse_spec(spec, "video")
        if parsed is None:
            return _invalid(problems)
        result = draw_video(parsed, folder, author=default_author())
        return _report(result.summary(ROOT), *preview(result.contact_sheet))

    return _safely(work)


@tool
def capture_screenshot(
    slug: str,
    url: str,
    name: str,
    full_page: bool = False,
    width: int = 1280,
    height: int = 800,
    selector: str = "",
    dark_mode: bool = False,
    hide: str = "",
) -> ToolResult:
    """Photograph a public web page, as proof for a slide.

    Only public http(s) pages. LinkedIn, local and private addresses are refused,
    and so is anything the page tries to load from them. The browser is clean:
    no cookies, no login. Look at the returned image to check that the part
    proving the point is visible. Follow the 'proof-screenshots' skill.

    Args:
        slug: The media folder of the post.
        url: The page address, starting with https://.
        name: A file name without extension, lowercase with hyphens, e.g. 'repo-readme'.
        full_page: Capture the whole page instead of one window (capped at 6000px tall).
        width: Browser window width in CSS pixels, 320 to 2560. For a page of text use
            600 to 720: a slide shows the capture about 864px wide, so a wide window
            shrinks the text below what a phone can show.
        height: Browser window height in CSS pixels, 320 to 2560.
        selector: A CSS selector to capture one element only, e.g. 'article' or '#readme'.
        dark_mode: Ask the page for its dark theme.
        hide: CSS selectors to hide before capturing, comma-separated, e.g. a cookie banner.

    Returns:
        The report, the path to use in an image slide, and the capture.
    """

    def work() -> ToolResult:
        folder = _media_folder(slug)
        if folder is None:
            return _bad_slug(slug)
        if not valid_slug(name):
            return _report(
                f"ERROR: '{name}' is not a valid file name. Use lowercase letters, "
                "digits and hyphens, like 'repo-readme'."
            )
        hidden = [part.strip() for part in hide.split(",") if part.strip()]
        result = capture_url(
            url,
            folder / "screens" / f"{name}.png",
            width=width,
            height=height,
            full_page=full_page,
            selector=selector or None,
            dark_mode=dark_mode,
            hide_selectors=hidden or None,
        )
        text = result.summary(ROOT)
        if not result.ok:
            return _report(text)
        text += (
            f"\nIn an image slide use: image: media/{slug}/screens/{name}.png"
            f"\nand url: {result.final_url}"
        )
        return _report(text, *preview(result.path))

    return _safely(work)


@tool
def convert_to_pdf(source: str, slug: str = "", theme: str = "drafting") -> ToolResult:
    """Convert a file inside content/ into a PDF LinkedIn accepts as a document post.

    Faithful, not designed: the file's own content set on 1080x1350 pages. For a
    designed carousel, write a spec instead. Files to convert go under content/,
    for example content/inbox/.

    Args:
        source: Path from content/, e.g. 'inbox/notas.md' or 'inbox/deck.pptx'.
        slug: The media folder for the PDF. Defaults to the file's name.
        theme: 'drafting' or 'blueprint'.

    Returns:
        The report: pages, page size, file size, and anything LinkedIn would refuse.
    """

    def work() -> ToolResult:
        path = confine(CONTENT_DIR, source)
        if path is None:
            return _report(f"ERROR: '{source}' leaves the content/ folder.")
        if not path.is_file():
            return _report(
                f"ERROR: content/{source} does not exist. Supported: {supported_extensions()}."
            )
        folder = _media_folder(slug or slugify(path.stem))
        if folder is None:
            return _bad_slug(slug)
        result = convert_file(
            path,
            folder / f"{slugify(path.stem)}.pdf",
            theme=theme if theme in THEMES else "drafting",
            author=default_author(),
        )
        return _report(result.summary(ROOT))

    return _safely(work)


@tool
def list_media(slug: str = "") -> ToolResult:
    """List what the studio has produced: every media folder, or the files in one.

    Args:
        slug: A media folder to list. Empty lists the folders.

    Returns:
        One entry per line, paths from content/.
    """

    def work() -> ToolResult:
        if not MEDIA_DIR.is_dir():
            return _report("No media yet.")
        if not slug:
            folders = sorted(path.name for path in MEDIA_DIR.iterdir() if path.is_dir())
            return _report("\n".join(folders) if folders else "No media yet.")
        folder = _media_folder(slug)
        if folder is None:
            return _bad_slug(slug)
        if not folder.is_dir():
            return _report(f"content/media/{slug}/ does not exist yet.")
        files = sorted(
            path.relative_to(CONTENT_DIR).as_posix() for path in folder.rglob("*") if path.is_file()
        )
        return _report("\n".join(files) if files else "The folder is empty.")

    return _safely(work)
