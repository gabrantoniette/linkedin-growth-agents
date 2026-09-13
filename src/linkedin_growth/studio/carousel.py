"""A carousel spec becomes a PDF, one PNG per slide, and a contact sheet.

The PDF is the deliverable: LinkedIn renders an uploaded document as a
swipeable carousel, and a PDF with real text stays selectable and readable by
screen readers when someone downloads it (LinkedIn lets any viewer do that).
The PNGs are the same slides as images, for Instagram, Threads, X or a
multi-image LinkedIn post. The contact sheet is every slide on one image, for
whoever has to judge the deck at a glance, human or model.

A render that finds a problem writes nothing final. Text errors stop it before
the browser opens; overflow stops it after the fitter has tried everything. In
the second case the draft goes to `preview/`, so the problem can be seen, and
`carousel.pdf` is left exactly as it was: a clipped slide must never look like
a finished file.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image as PILImage

from linkedin_growth.config import CONTENT_DIR
from linkedin_growth.studio.brand import resolve_asset_path
from linkedin_growth.studio.browser import Studio, run_isolated
from linkedin_growth.studio.html import FIT_SCRIPT, build_document
from linkedin_growth.studio.lint import lint
from linkedin_growth.studio.spec import Author, CarouselSpec, dump_spec, text_errors
from linkedin_growth.studio.themes import CAROUSEL_SIZE

# Below this share of its designed size, fitted text reads as small print. The
# render still succeeds, with a warning that cutting words would read better.
SHRINK_WARNING = 0.86

CONTACT_SHEET_WIDTH = 1560
CONTACT_SHEET_GAP = 24
CONTACT_SHEET_BACKGROUND = "#1B1E23"


@dataclass
class RenderResult:
    out_dir: Path
    ok: bool = False
    pdf: Path | None = None
    image: Path | None = None
    slides: list[Path] = field(default_factory=list)
    contact_sheet: Path | None = None
    spec_file: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self, root: Path) -> str:
        """The result as text, with paths relative to `root`."""

        def show(path: Path) -> str:
            try:
                return path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                return str(path)

        lines: list[str] = []
        if self.ok:
            if self.pdf:
                lines.append(f"Carousel PDF: {show(self.pdf)} ({len(self.slides)} pages, 1080x1350)")
            if self.image:
                lines.append(f"Image: {show(self.image)} (1080x1350)")
            if self.slides:
                lines.append(
                    f"Slides as PNG: {show(self.slides[0].parent)}/ "
                    f"({self.slides[0].name} to {self.slides[-1].name})"
                )
            if self.contact_sheet:
                lines.append(f"Contact sheet: {show(self.contact_sheet)}")
        else:
            lines.append(f"NOT RENDERED. {len(self.errors)} problem(s) to fix first:")
            lines.extend(f"- {error}" for error in self.errors)
            if self.contact_sheet:
                lines.append(f"Draft preview, for diagnosis only: {show(self.contact_sheet)}")
        if self.spec_file:
            lines.append(f"Spec: {show(self.spec_file)}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n".join(lines)


def fit_problems(report: dict[str, Any], noun: str) -> tuple[list[str], list[str]]:
    """Turn the in-page fit report into errors and warnings."""
    errors: list[str] = []
    warnings: list[str] = []
    if not report.get("fontsOk", False):
        errors.append(
            "the bundled fonts did not load, so the render would fall back to "
            "a system face. Check src/linkedin_growth/studio/assets/fonts/."
        )
    for source in report.get("broken", []):
        errors.append(f"an image failed to load: {source}")
    for item in report.get("slides", []):
        where = f"{noun} {item['index']} ({item['layout']})"
        if item["overflow"] > 0:
            errors.append(
                f"{where}: the content does not fit even at the smallest allowed "
                f"type ({item['overflow']}px too tall). Cut words or split it into "
                f"two {noun}s."
            )
        elif item["wide"]:
            errors.append(
                f"{where}: a line of code or a number is wider than the frame even "
                "at the smallest allowed size. Shorten that line."
            )
        elif item["shrunk"] < SHRINK_WARNING:
            warnings.append(
                f"{where}: text was shrunk to {round(item['shrunk'] * 100)}% of its "
                "designed size to fit. Cutting words reads better than small type."
            )
    return errors, warnings


def make_contact_sheet(images: list[Path], target: Path) -> Path:
    """Every slide on one image, wide enough to judge and small enough to send.

    1560px wide keeps it under the 1568px a vision model reads at full
    resolution, so the sheet costs one image and shows every slide legibly.
    """
    count = len(images)
    columns = min(count, 4 if count <= 12 else 5)
    gap = CONTACT_SHEET_GAP
    thumb_width = (CONTACT_SHEET_WIDTH - gap * (columns + 1)) // columns
    with PILImage.open(images[0]) as first:
        ratio = first.height / first.width
    thumb_height = round(thumb_width * ratio)
    rows = -(-count // columns)
    sheet = PILImage.new(
        "RGB",
        (CONTACT_SHEET_WIDTH, gap + rows * (thumb_height + gap)),
        CONTACT_SHEET_BACKGROUND,
    )
    for index, path in enumerate(images):
        with PILImage.open(path) as slide:
            thumb = slide.convert("RGB").resize((thumb_width, thumb_height), PILImage.LANCZOS)
        row, column = divmod(index, columns)
        sheet.paste(thumb, (gap + column * (thumb_width + gap), gap + row * (thumb_height + gap)))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, optimize=True)
    return target


def _clear_pngs(folder: Path) -> None:
    """Old slides go before new ones are written, or a shorter deck keeps a stale tail."""
    if folder.is_dir():
        for stale in folder.glob("*.png"):
            stale.unlink()


def render_carousel(
    spec: CarouselSpec,
    out_dir: Path,
    *,
    author: Author | None = None,
    content_root: Path | None = None,
    single_image: bool = False,
    save_spec: bool = True,
) -> RenderResult:
    """Render a carousel (or, with `single_image`, a one-slide image post).

    `save_spec` writes the normalized spec next to the PDF. A re-render of a
    spec the user edited by hand passes False, so their comments survive.
    """
    content_root = content_root or CONTENT_DIR
    author = spec.author or author
    basename = "image" if single_image else "carousel"
    result = RenderResult(out_dir=out_dir)

    if single_image and len(spec.slides) != 1:
        result.errors.append(
            f"an image post has exactly one slide; this spec has {len(spec.slides)}."
        )
        return result

    out_dir.mkdir(parents=True, exist_ok=True)
    result.spec_file = out_dir / f"{basename}.yaml"
    if save_spec:
        result.spec_file.write_text(dump_spec(spec), encoding="utf-8")

    result.errors.extend(text_errors(spec))
    result.warnings.extend(lint(spec))
    width, height = CAROUSEL_SIZE
    document = build_document(
        spec,
        width=width,
        height=height,
        content_root=content_root,
        author=author,
        resolve_avatar=resolve_asset_path,
    )
    result.errors.extend(document.missing)
    result.warnings.extend(document.redactions)
    if result.errors:
        return result

    def draw() -> None:
        with Studio() as studio:
            page = studio.open_document(document)
            report = page.evaluate(FIT_SCRIPT)
            errors, warnings = fit_problems(report, "slide")
            result.errors.extend(errors)
            result.warnings.extend(warnings)
            result.ok = not result.errors

            target = out_dir if result.ok else out_dir / "preview"
            slides = page.locator(".slide")
            if single_image:
                target.mkdir(parents=True, exist_ok=True)
                image = target / "image.png"
                slides.nth(0).screenshot(path=str(image))
                if result.ok:
                    result.image = image
                else:
                    result.contact_sheet = image
                return

            slides_dir = target / "slides"
            _clear_pngs(slides_dir)
            slides_dir.mkdir(parents=True, exist_ok=True)
            pngs = []
            for index in range(document.count):
                path = slides_dir / f"{index + 1:02d}.png"
                slides.nth(index).screenshot(path=str(path))
                pngs.append(path)
            result.contact_sheet = make_contact_sheet(pngs, target / "contact-sheet.png")

            if not result.ok:
                return
            result.slides = pngs
            result.pdf = out_dir / "carousel.pdf"
            page.pdf(
                path=str(result.pdf),
                width=f"{width}px",
                height=f"{height}px",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            shutil.rmtree(out_dir / "preview", ignore_errors=True)

    run_isolated(draw)
    return result
