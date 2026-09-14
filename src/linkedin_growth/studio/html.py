"""Spec -> HTML, through the Jinja templates in `templates/`.

The document a render loads is self-contained except for two kinds of URL,
both on the studio's virtual origin and both served from disk by `browser.py`:

- `/fonts/<file>`: the bundled faces from `themes.FONTS`;
- `/files/<token>`: the images a spec points at (screenshots, the footer
  photo), registered here by token, so the page can never ask for an arbitrary
  path on disk.

Nothing else resolves. A template that referenced a CDN font would render
without it rather than reach the network, and slide text cannot inject a tag in
the first place (see `text.py`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup
from PIL import Image as PILImage

from linkedin_growth.studio.code import highlight
from linkedin_growth.studio.safety import confine
from linkedin_growth.studio.spec import Author, CodeSlide, ImageSlide, Spec, slides_of
from linkedin_growth.studio.text import inline
from linkedin_growth.studio.themes import FONTS, get_theme

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
ORIGIN = "https://studio.local"

# The in-page script that fits text and reports overflow. Kept as a file so it
# can be read and edited as JavaScript, not as a string inside Python.
FIT_SCRIPT = (TEMPLATES_DIR / "fit.js").read_text(encoding="utf-8")

# The only words the templates print on their own. Everything else on a slide
# comes from the spec, in the spec's language.
STRINGS = {
    "pt-BR": {"source": "Fonte", "terminal": "terminal"},
    "en": {"source": "Source", "terminal": "terminal"},
}

ICONS = {
    # The connector between two diagram nodes: a construction line and its head.
    "down": Markup(
        '<svg viewBox="0 0 20 24" fill="none" stroke="currentColor" stroke-width="2.5" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v19"/>'
        '<path d="m4 15 6 6 6-6"/></svg>'
    ),
}

# Canvas name by size, for the CSS that moves the foot into a safe zone.
CANVAS = {(1080, 1350): "portrait", (1080, 1920): "tall", (1080, 1080): "square"}

# The width the foot's scale is drawn at: the canvas minus two 108px margins.
SCALE_WIDTH = 864
SCALE_HEIGHT = 58

_environment = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)
_environment.filters["inline"] = inline


@dataclass
class Document:
    html: str
    files: dict[str, Path]
    width: int
    height: int
    count: int
    # Content problems found while assembling: an image that does not exist.
    missing: list[str] = field(default_factory=list)
    # What `safety.redact_secrets` masked in code slides.
    redactions: list[str] = field(default_factory=list)
    # For a converted HTML file: the folder its relative assets resolve against.
    base_dir: Path | None = None


def render_template(name: str, **context: Any) -> str:
    """Render any template in `templates/` with the studio's environment."""
    return _environment.get_template(name).render(**context)


def font_faces() -> Markup:
    rules = []
    for font in FONTS:
        stretch = f" font-stretch: {font.stretch};" if font.stretch else ""
        rules.append(
            f"@font-face {{ font-family: '{font.family}'; "
            f"src: url('{ORIGIN}/fonts/{font.file}') format('woff2'); "
            f"font-weight: {font.weight}; font-style: {font.style};{stretch} "
            "font-display: block; }"
        )
    return Markup("\n".join(rules))


def scale_svg(index: int, total: int, width: int = SCALE_WIDTH) -> Markup:
    """The dimension line at the foot of a slide: where the reader is.

    A construction line with a tick at every page boundary. The current page is
    dimensioned in red between its two extension lines, arrowheads pointing at
    them, with its reading above. On every page but the last, an arrowhead at
    the far end says the drawing continues: the swipe cue, drawn instead of
    written.
    """
    base = 44.0
    reserve = 24.0 if index < total else 0.0
    span = width - reserve
    step = span / total
    left, right = (index - 1) * step, index * step

    parts = [
        f'<svg class="scale" viewBox="0 0 {width} {SCALE_HEIGHT}" width="{width}" '
        f'height="{SCALE_HEIGHT}" aria-hidden="true">',
        f'<line class="scale-rule" x1="1.5" y1="{base}" x2="{span:.2f}" y2="{base}"/>',
    ]
    for boundary in range(total + 1):
        x = min(max(boundary * step, 1.5), span - 1.5)
        current = boundary in (index - 1, index)
        top, bottom = (base - 20, base + 8) if current else (base - 9, base)
        css = "scale-tick is-current" if current else "scale-tick"
        parts.append(f'<line class="{css}" x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{bottom}"/>')

    line = base - 10
    head = min(12.0, step / 4)
    wing = head / 2.2
    start, end = min(max(left, 1.5), span - 1.5), min(max(right, 1.5), span - 1.5)
    parts += [
        f'<line class="scale-current" x1="{start + head:.2f}" y1="{line}" '
        f'x2="{end - head:.2f}" y2="{line}"/>',
        f'<polygon class="scale-arrow" points="{start:.2f},{line} {start + head:.2f},'
        f'{line - wing:.2f} {start + head:.2f},{line + wing:.2f}"/>',
        f'<polygon class="scale-arrow" points="{end:.2f},{line} {end - head:.2f},'
        f'{line - wing:.2f} {end - head:.2f},{line + wing:.2f}"/>',
        f'<text class="scale-label" x="{min(max((left + right) / 2, 30), span - 30):.2f}" '
        f'y="{line - 12}" text-anchor="middle">{index}/{total}</text>',
    ]
    if index < total:
        parts.append(
            f'<polygon class="scale-more" points="{width},{base} {width - 15},{base - 7} '
            f'{width - 15},{base + 7}"/>'
        )
    parts.append("</svg>")
    return Markup("".join(parts))


def _address(url: str | None) -> str:
    """What a browser figure prints above the capture: host and path, no scheme."""
    if not url:
        return ""
    parts = urlsplit(url if "://" in url else f"https://{url}")
    host = parts.hostname or url
    path = parts.path.rstrip("/")
    return f"{host}{path}"


def build_document(
    spec: Spec,
    *,
    width: int,
    height: int,
    content_root: Path,
    author: Author | None = None,
    mode: Literal["print", "video"] = "print",
    captions: bool = False,
    resolve_avatar: Callable[[str], Path | None] | None = None,
) -> Document:
    """Assemble the HTML for every slide (or scene) of a spec."""
    theme = get_theme(spec.theme)
    strings = STRINGS[spec.language]
    noun = "slide" if spec.kind == "carousel" else "scene"
    slides = slides_of(spec)
    total = len(slides)
    files: dict[str, Path] = {}
    missing: list[str] = []
    redactions: list[str] = []

    contexts: list[dict[str, Any]] = []
    for index, slide in enumerate(slides, start=1):
        context: dict[str, Any] = {
            "slide": slide,
            "index": index,
            "scale": scale_svg(index, total) if total > 1 else Markup(""),
        }

        if isinstance(slide, CodeSlide):
            code = highlight(
                slide.code,
                language=slide.language,
                filename=slide.filename,
                highlight_lines=slide.highlight,
                terminal=slide.frame == "terminal",
            )
            context["code"] = code
            context["listing_label"] = slide.filename or (
                strings["terminal"] if slide.frame == "terminal" else code.language.lower()
            )
            redactions.extend(
                f"{noun} {index}: masked a {item} in the code before drawing it"
                for item in code.redacted
            )

        if isinstance(slide, ImageSlide):
            target = confine(content_root, slide.image)
            context["image_src"] = ""
            # The capture's own proportions, so a contained frame hugs the image
            # instead of leaving empty bands above and below it.
            context["image_ratio"] = ""
            if target is None or not target.is_file():
                missing.append(
                    f"{noun} {index}: image '{slide.image}' was not found under "
                    "content/. Capture it first, or fix the path."
                )
            else:
                try:
                    with PILImage.open(target) as picture:
                        context["image_ratio"] = f"{picture.width} / {picture.height}"
                except OSError:
                    missing.append(
                        f"{noun} {index}: '{slide.image}' is not an image the studio can read."
                    )
                token = f"image-{index}{target.suffix.lower()}"
                files[token] = target
                context["image_src"] = f"{ORIGIN}/files/{token}"
            context["host"] = _address(slide.url)

        contexts.append(context)

    author_context = None
    if author:
        avatar_src = None
        if author.avatar and resolve_avatar:
            photo = resolve_avatar(author.avatar)
            if photo:
                token = f"avatar{photo.suffix.lower()}"
                files[token] = photo
                avatar_src = f"{ORIGIN}/files/{token}"
        author_context = {
            "name": author.name,
            "tagline": author.tagline,
            "avatar_src": avatar_src,
        }

    html = _environment.get_template("deck.html.j2").render(
        language=spec.language,
        title=spec.title,
        font_faces=font_faces(),
        theme_vars=Markup(theme.css_variables()),
        theme_id=theme.id,
        width=width,
        height=height,
        mode=mode,
        canvas=CANVAS.get((width, height), "portrait"),
        captions=captions,
        slides=contexts,
        total=total,
        author=author_context,
        t=strings,
        icons=ICONS,
    )
    return Document(
        html=html,
        files=files,
        width=width,
        height=height,
        count=total,
        missing=missing,
        redactions=redactions,
    )
