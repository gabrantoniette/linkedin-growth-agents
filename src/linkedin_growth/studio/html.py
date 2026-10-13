"""Spec -> HTML, through the Jinja templates in `templates/`.

The document a render loads is self-contained except for two kinds of URL,
both on the studio's virtual origin and both served from disk by `browser.py`:

- `/fonts/<file>`: the bundled faces from `themes.FONTS`;
- `/files/<token>`: the images a spec points at (screenshots, photos, the
  footer portrait) and the theme's textures, registered here by token, so the
  page can never ask for an arbitrary path on disk.

Nothing else resolves. A template that referenced a CDN font would render
without it rather than reach the network, and slide text cannot inject a tag in
the first place (see `text.py`).

A theme with its own template folder (`templates/themes/<name>/`) replaces the
shared templates it names there and uses the shared ones for the rest. That is
how the jornal theme draws a different page around the same layouts.
"""

from __future__ import annotations

import math
import random
import zlib
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
from linkedin_growth.studio.spec import (
    Author,
    CodeSlide,
    CoverSlide,
    ImageSlide,
    Mark,
    Spec,
    slides_of,
)
from linkedin_growth.studio.text import inline
from linkedin_growth.studio.themes import FONTS, TEXTURES_DIR, get_theme

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
    # Jornal: the swipe cue next to the page number, drawn instead of written.
    "arrow": Markup(
        '<svg viewBox="0 0 64 40" fill="none" stroke="currentColor" stroke-width="6" '
        'stroke-linecap="square" aria-hidden="true"><path d="M4 20h50"/><path d="M38 5l16 15-16 15"/></svg>'
    ),
    # Jornal: what the closing call to action points at.
    "link": Markup(
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6"/>'
        '<path d="M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>'
    ),
    # Jornal: the box a reviewer draws around the proof, twice, slightly off.
    "box": Markup(
        '<svg viewBox="0 0 400 200" preserveAspectRatio="none" fill="none" stroke="currentColor" '
        'aria-hidden="true"><rect x="8" y="10" width="384" height="180" rx="26" '
        'transform="rotate(-0.8 200 100)" stroke-width="5" vector-effect="non-scaling-stroke"/>'
        '<rect x="3" y="5" width="392" height="190" rx="30" transform="rotate(1 200 100)" '
        'stroke-width="3" stroke-dasharray="520 3000" stroke-dashoffset="-60" stroke-linecap="round" '
        'vector-effect="non-scaling-stroke"/></svg>'
    ),
}


def torn(seed: int, sides: str = "trbl", amp: float = 9.0, n: int = 64) -> str:
    """A CSS clip-path polygon whose named sides ('t', 'r', 'b', 'l') look torn.

    A slow wave plus fine noise and the odd deeper bite, which is what paper
    torn by hand looks like at slide size. The seed comes from the deck, so a
    re-render tears the same way and two posts tear differently.
    """
    rnd = random.Random(seed)
    phase = rnd.uniform(0, 6)

    def depth(i: int, shift: float) -> float:
        wave = (0.5 + 0.5 * math.sin(i * 0.5 + phase + shift)) * amp * 0.55
        bite = amp * 0.7 if rnd.random() < 0.06 else 0.0
        return wave + rnd.uniform(0, amp * 0.55) + bite

    points: list[str] = []
    if "t" in sides:
        points += [f"{i * 100 / n:.2f}% {depth(i, 0):.1f}px" for i in range(n + 1)]
    else:
        points += ["0% 0%", "100% 0%"]
    if "r" in sides:
        points += [f"calc(100% - {depth(i, 1):.1f}px) {i * 100 / n:.2f}%" for i in range(1, n)]
    if "b" in sides:
        points += [f"{i * 100 / n:.2f}% calc(100% - {depth(i, 2):.1f}px)" for i in range(n, -1, -1)]
    else:
        points += ["100% 100%", "0% 100%"]
    if "l" in sides:
        points += [f"{depth(i, 3):.1f}px {i * 100 / n:.2f}%" for i in range(n - 1, 0, -1)]
    return "polygon(" + ", ".join(points) + ")"

# Canvas name by size, for the CSS that moves the foot into a safe zone.
CANVAS = {(1080, 1350): "portrait", (1080, 1920): "tall", (1080, 1080): "square"}

# The width the foot's scale is drawn at: the canvas minus two 108px margins.
SCALE_WIDTH = 864
SCALE_HEIGHT = 58

_environments: dict[str | None, Environment] = {}


def _environment_for(folder: str | None) -> Environment:
    """The template environment for a theme folder; None is the shared templates alone."""
    if folder not in _environments:
        paths = [str(TEMPLATES_DIR / "themes" / folder)] if folder else []
        environment = Environment(
            loader=FileSystemLoader([*paths, str(TEMPLATES_DIR)]),
            autoescape=True,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        environment.filters["inline"] = inline
        environment.globals["torn"] = torn
        _environments[folder] = environment
    return _environments[folder]


_environment = _environment_for(None)


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


def _mark(mark: Mark, size: tuple[int, int]) -> dict[str, Any] | None:
    """A mark's box as percentages of the image, and the side its label fits on.

    None when the box runs past the image: a box drawn in the wrong place is
    worse than none, because it points the reader at the wrong proof.
    """
    width, height = size
    left, top, right, bottom = mark.box
    if right > width or bottom > height:
        return None

    def percent(value: int, whole: int) -> float:
        return round(value / whole * 100, 3)

    # The label goes where there is room: right of the box, else left, else under.
    side = "right" if right / width <= 0.62 else "left" if left / width >= 0.38 else "below"
    return {
        "left": percent(left, width),
        "top": percent(top, height),
        "right": percent(right, width),
        "bottom": percent(bottom, height),
        "width": percent(right - left, width),
        "height": percent(bottom - top, height),
        "label": mark.label,
        "side": side,
    }


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
    jornal = theme.marker is not None
    # Torn edges are random, seeded by the title: the same deck tears the same
    # way on every render, and two decks tear differently.
    seed = zlib.crc32(spec.title.encode("utf-8")) % 10_000

    def register(relative: str, token: str, where: str) -> dict[str, Any] | None:
        """An image under content/ as a URL on the studio origin, with its size."""
        target = confine(content_root, relative)
        if target is None or not target.is_file():
            missing.append(
                f"{where}: image '{relative}' was not found under content/. "
                "Capture or fetch it first, or fix the path."
            )
            return None
        try:
            with PILImage.open(target) as picture:
                size = picture.size
        except OSError:
            missing.append(f"{where}: '{relative}' is not an image the studio can read.")
            return None
        name = f"{token}{target.suffix.lower()}"
        files[name] = target
        return {
            "src": f"{ORIGIN}/files/{name}",
            "size": size,
            "ratio": f"{size[0]} / {size[1]}",
        }

    if jornal:
        files["marker.svg"] = TEXTURES_DIR / f"marker-{spec.accent}.svg"
        files["grain.png"] = TEXTURES_DIR / "grain.png"

    contexts: list[dict[str, Any]] = []
    for index, slide in enumerate(slides, start=1):
        where = f"{noun} {index}"
        context: dict[str, Any] = {
            "slide": slide,
            "index": index,
            "scale": scale_svg(index, total) if total > 1 else Markup(""),
            "show_sources": spec.show_sources,
            "seed": seed + index * 97,
            "photo": None,
            "collage": None,
            "mark": None,
            "mono": False,
        }

        photo = getattr(slide, "photo", None)
        if photo:
            found = register(photo.image, f"photo-{index}", where)
            if found:
                context["photo"] = {**found, "kind": photo.kind, "caption": photo.caption}

        if isinstance(slide, CoverSlide) and slide.collage:
            collage: dict[str, Any] = {"capture": None, "cutout": None, "print": None}
            for item in slide.collage:
                found = register(item.image, f"collage-{index}-{item.kind}", where)
                if found:
                    collage[item.kind] = found
            context["collage"] = collage if any(collage.values()) else None

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
            found = register(slide.image, f"image-{index}", where)
            context["image_src"] = found["src"] if found else ""
            # The capture's own proportions, so a contained frame hugs the image
            # instead of leaving empty bands above and below it.
            context["image_ratio"] = found["ratio"] if found else ""
            context["host"] = _address(slide.url)
            context["mono"] = slide.tone == "mono" or (slide.tone == "auto" and jornal)
            if slide.mark and found:
                context["mark"] = _mark(slide.mark, found["size"])
                if context["mark"] is None:
                    width_px, height_px = found["size"]
                    missing.append(
                        f"{where}: the mark's box {slide.mark.box} runs past the image, "
                        f"which is {width_px}x{height_px} pixels. Measure it on the capture."
                    )

        contexts.append(context)

    masthead = None
    if spec.masthead:
        masthead = {"label": spec.masthead.label, "detail": spec.masthead.detail}
    elif jornal:
        masthead = {"label": spec.title, "detail": None}

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

    html = _environment_for(theme.templates).get_template("deck.html.j2").render(
        language=spec.language,
        title=spec.title,
        font_faces=font_faces(),
        theme_vars=Markup(theme.css_variables(accent=spec.accent)),
        theme_id=theme.id,
        stylesheet=theme.stylesheet,
        origin=ORIGIN,
        width=width,
        height=height,
        mode=mode,
        canvas=CANVAS.get((width, height), "portrait"),
        captions=captions,
        slides=contexts,
        total=total,
        author=author_context,
        masthead=masthead,
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
