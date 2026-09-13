"""Soft limits: what a spec is allowed to do, but usually should not.

These are warnings, never errors. A slide with eighteen words where the limit
says sixteen can be the right slide; a slide with forty is a paragraph pasted
into a rectangle. The render always runs, and the warnings go back to whoever
wrote the spec, next to the contact sheet, so the judgement stays with them.

The numbers are not taste. Each block cites the section of
`references/kb-visual-formats.md` that justifies it, with the evidence and its
confidence. Change the number there first, then here.
"""

from __future__ import annotations

from typing import Any

from linkedin_growth.studio.spec import (
    CarouselSpec,
    CodeSlide,
    CompareSlide,
    DiagramSlide,
    ImageSlide,
    Spec,
    StepsSlide,
    VideoSpec,
    slides_of,
)
from linkedin_growth.studio.text import has_emphasis, plain, word_count

# ------------------------------------------------------------------------------
# Words per field. kb-visual-formats.md §4 (one idea per slide, the text
# overlay finding) and §5 (legibility at phone size). A cover hook is judged in
# the feed at thumbnail size, so it gets the tightest limit.
# ------------------------------------------------------------------------------
WORD_LIMITS: dict[str, dict[str, int]] = {
    "cover": {"headline": 12, "subtitle": 22},
    "statement": {"text": 25, "support": 20},
    "points": {"headline": 14, "items": 16},
    "steps": {"headline": 14, "title": 8, "detail": 18},
    "code": {"headline": 14, "caption": 22},
    "compare": {"headline": 14, "items": 10, "verdict": 22},
    "metric": {"label": 12, "detail": 24},
    "quote": {"quote": 40},
    "image": {"headline": 14, "caption": 24},
    "diagram": {"headline": 14, "label": 4, "detail": 10, "caption": 22},
    "closing": {"headline": 14, "question": 24, "cta": 10},
}

# Everything a reader has to read on one slide, prose only. Past this, the
# slide is a page of text, and a document post is not where people read pages.
MAX_WORDS_PER_SLIDE = 45

# Code at a legible size: about 14 lines and 56 columns fit a 1080px slide at
# 26px or more. Past that the renderer shrinks the type, and code shrunk to fit
# is code nobody reads. kb-visual-formats.md §7.
CODE_MAX_LINES = 14
CODE_MAX_COLUMNS = 56

# Carousel length. The practitioner consensus is 5 to 10 and no primary dataset
# settles it; 12 is where the warning starts. kb-visual-formats.md §3.2.
CAROUSEL_SLIDES = (5, 12)

# The document title LinkedIn shows at the top of the viewer.
TITLE_MAX_CHARACTERS = 60

# A feed video past this is fighting the format for a personal profile, where
# video already reaches less than a document. kb-visual-formats.md §6.
VIDEO_WARN_SECONDS = 90


def _field_words(slide: Any) -> list[tuple[str, str, int]]:
    """(field, text, words) for every prose field a limit applies to."""
    layout = slide.layout
    limits = WORD_LIMITS.get(layout, {})
    found: list[tuple[str, str, int]] = []

    def add(field: str, text: str | None) -> None:
        if text and field in limits:
            found.append((field, text, word_count(text)))

    for field in ("headline", "subtitle", "text", "support", "caption", "verdict",
                  "label", "detail", "quote", "question", "cta"):
        add(field, getattr(slide, field, None))
    for item in getattr(slide, "items", None) or []:
        add("items", item)
    if isinstance(slide, StepsSlide):
        for step in slide.steps:
            add("title", step.title)
            add("detail", step.detail)
    if isinstance(slide, CompareSlide):
        for column in (slide.left, slide.right):
            for item in column.items:
                add("items", item)
    if isinstance(slide, DiagramSlide):
        for node in slide.nodes:
            add("label", node.label)
            add("detail", node.detail)
    return found


def slide_words(slide: Any) -> int:
    """Every word a reader reads on the slide, code excluded."""
    return sum(words for _, _, words in _field_words(slide))


def reading_text(slide: Any) -> str:
    """The prose on a slide, joined: what a viewer has to read before the cut."""
    return " ".join(text for _, text, _ in _field_words(slide))


def lint(spec: Spec) -> list[str]:
    """Warnings for a spec that already passed validation."""
    warnings: list[str] = []
    slides = slides_of(spec)
    noun = "slide" if isinstance(spec, CarouselSpec) else "scene"

    if len(spec.title) > TITLE_MAX_CHARACTERS:
        warnings.append(
            f"title: {len(spec.title)} characters. The document viewer truncates "
            f"long titles; aim for {TITLE_MAX_CHARACTERS} or fewer."
        )

    if isinstance(spec, CarouselSpec):
        low, high = CAROUSEL_SLIDES
        if len(slides) < low:
            warnings.append(
                f"{len(slides)} slides. Under {low}, a carousel is rarely worth "
                "the swipe; consider a single image post instead."
            )
        elif len(slides) > high:
            warnings.append(
                f"{len(slides)} slides. Past {high}, cut: every extra slide is "
                "one more place to lose the reader before the closing question."
            )

    if slides and slides[0].layout != "cover":
        warnings.append(
            f"{noun} 1 is '{slides[0].layout}', not 'cover'. The first page is the "
            "thumbnail in the feed; it should carry the hook."
        )
    if len(slides) > 2 and slides[-1].layout != "closing":
        warnings.append(
            f"the last {noun} is '{slides[-1].layout}', not 'closing'. The post "
            "ends on a question; the asset should end on the same one."
        )

    for index, slide in enumerate(slides, start=1):
        where = f"{noun} {index} ({slide.layout})"
        limits = WORD_LIMITS.get(slide.layout, {})
        for field in ("headline", "text"):
            if has_emphasis(getattr(slide, field, None)):
                warnings.append(
                    f"{where}: the {field} has emphasis marks. One accented word in a "
                    "headline is the most common tell of a templated slide; state "
                    "the point plainly and let the evidence underneath carry it."
                )
        for field, text, words in _field_words(slide):
            limit = limits[field]
            if words > limit:
                preview = plain(text)[:60]
                warnings.append(
                    f"{where}: {field} has {words} words (aim for {limit} or "
                    f"fewer): '{preview}...'"
                )
        total = slide_words(slide)
        if total > MAX_WORDS_PER_SLIDE:
            warnings.append(
                f"{where}: {total} words on one slide. Split it in two or cut "
                f"to {MAX_WORDS_PER_SLIDE}."
            )
        if isinstance(slide, CodeSlide):
            lines = slide.code.strip("\n").splitlines()
            widest = max((len(line.expandtabs(4)) for line in lines), default=0)
            if len(lines) > CODE_MAX_LINES:
                warnings.append(
                    f"{where}: {len(lines)} lines of code. Crop to the "
                    f"{CODE_MAX_LINES} that prove the point."
                )
            if widest > CODE_MAX_COLUMNS:
                warnings.append(
                    f"{where}: a {widest}-character line. Past {CODE_MAX_COLUMNS} "
                    "the code shrinks; reflow it or cut the line."
                )
        if isinstance(slide, ImageSlide) and not slide.alt:
            warnings.append(
                f"{where}: no alt text. Write what the image shows, including "
                "any text in it that matters, in up to 300 characters."
            )

    if isinstance(spec, VideoSpec):
        for index, scene in enumerate(slides, start=1):
            if scene.narration and scene.duration:
                needed = len(scene.narration) / 17
                if needed > scene.duration:
                    warnings.append(
                        f"scene {index}: the narration needs about {needed:.1f}s "
                        f"at 17 characters per second, but the scene lasts "
                        f"{scene.duration:.1f}s."
                    )

    return warnings
