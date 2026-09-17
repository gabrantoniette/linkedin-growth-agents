"""The contract a spec meets before anything is drawn.

A spec is what the Post Designer writes and what a person edits by hand: YAML
(JSON is valid YAML, so either works), one entry per slide, each slide naming
its layout. Pydantic checks the shape. `text_errors` blocks two things that
would otherwise ship inside a public asset: a `[PREENCHER: ...]` placeholder,
and a dash VOICE_RULES bans in prose (code is exempt). Both are hard errors,
not warnings, so the agent gets pointed at the exact slide and field. Soft
limits (words per slide, slide count) are warnings and live in `lint.py`.

Each layout is a single idea with its evidence (kb-visual-formats.md §4):

    cover      the hook; it is the thumbnail in the feed
    statement  one sentence, large
    points     an assertion and two to six supporting items
    steps      a process, in order
    code       real code or real terminal output
    compare    two options against the same criteria
    metric     one number, with its source
    quote      someone else's words, attributed
    image      a real screenshot, framed
    diagram    a flow of two to six nodes
    closing    the question the post ends on
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Annotated, Any, Literal, Union

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)


class _Model(BaseModel):
    # `extra="forbid"` turns a misspelled field into an error instead of text
    # that silently never renders. Numbers become strings because a YAML
    # `value: 100` is an int, and a metric slide shows it as written.
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, coerce_numbers_to_str=True
    )


class Author(_Model):
    name: str = Field(min_length=1, max_length=60)
    tagline: str | None = Field(default=None, max_length=80)
    # A photo for the footer, relative to the project root. Only files under
    # profile/ or content/ are read.
    avatar: str | None = None


class _Slide(_Model):
    # Small print under the content: a source, a caveat, a date.
    note: str | None = Field(default=None, max_length=160)
    # Video only; a carousel ignores both.
    duration: float | None = Field(default=None, gt=0, le=20)
    narration: str | None = Field(default=None, max_length=700)


class CoverSlide(_Slide):
    layout: Literal["cover"]
    headline: str = Field(min_length=1, max_length=140)
    subtitle: str | None = Field(default=None, max_length=200)


class StatementSlide(_Slide):
    layout: Literal["statement"]
    text: str = Field(min_length=1, max_length=260)
    support: str | None = Field(default=None, max_length=200)


class PointsSlide(_Slide):
    layout: Literal["points"]
    headline: str = Field(min_length=1, max_length=140)
    items: list[str] = Field(min_length=2, max_length=6)
    # Numbers only when the items are a sequence or a ranking. A list of
    # reasons numbered 1, 2, 3 claims an order that is not there.
    numbered: bool = False


class Step(_Model):
    title: str = Field(min_length=1, max_length=90)
    detail: str | None = Field(default=None, max_length=180)


class StepsSlide(_Slide):
    layout: Literal["steps"]
    headline: str = Field(min_length=1, max_length=140)
    steps: list[Step] = Field(min_length=2, max_length=5)


class CodeSlide(_Slide):
    layout: Literal["code"]
    headline: str | None = Field(default=None, max_length=140)
    code: str = Field(min_length=1, max_length=2400)
    # A Pygments lexer name ('python', 'typescript', 'console'). Guessed from
    # the filename when missing.
    language: str | None = Field(default=None, max_length=30)
    filename: str | None = Field(default=None, max_length=60)
    # 'listing' prints code with line numbers; 'terminal' drops them and reads
    # the text as a shell session, prompts marked.
    frame: Literal["listing", "terminal"] = "listing"
    # 1-based line numbers to highlight. Three at most is what a reader tracks.
    highlight: list[int] = Field(default_factory=list, max_length=6)
    caption: str | None = Field(default=None, max_length=200)


class Column(_Model):
    title: str = Field(min_length=1, max_length=40)
    items: list[str] = Field(min_length=1, max_length=5)


class CompareSlide(_Slide):
    layout: Literal["compare"]
    headline: str = Field(min_length=1, max_length=140)
    left: Column
    right: Column
    # Which side the post argues for. 'none' draws them as equals.
    favored: Literal["left", "right", "none"] = "none"
    verdict: str | None = Field(default=None, max_length=200)


class MetricSlide(_Slide):
    layout: Literal["metric"]
    value: str = Field(min_length=1, max_length=14)
    unit: str | None = Field(default=None, max_length=24)
    label: str = Field(min_length=1, max_length=120)
    detail: str | None = Field(default=None, max_length=200)
    # Required, and not a formality: a number on a slide is a claim, and the
    # HONESTY rule needs to know where it came from.
    source: str = Field(min_length=3, max_length=140)


class QuoteSlide(_Slide):
    layout: Literal["quote"]
    quote: str = Field(min_length=1, max_length=320)
    # Required for the same reason as a metric's source.
    author: str = Field(min_length=1, max_length=80)
    source: str | None = Field(default=None, max_length=140)


class ImageSlide(_Slide):
    layout: Literal["image"]
    headline: str | None = Field(default=None, max_length=140)
    # Path relative to content/, usually a capture in media/<slug>/screens/.
    image: str = Field(min_length=1, max_length=260)
    # 'browser' prints the page address above the capture, which is the proof
    # of where it came from; 'plain' shows the image alone.
    frame: Literal["browser", "plain"] = "plain"
    # 'cover' fills the frame and crops from the top, which is what a web page
    # screenshot wants; 'contain' shows the whole image, for a chart or a photo.
    fit: Literal["cover", "contain"] = "cover"
    # Shown in the browser frame's address bar. Host only is fine.
    url: str | None = Field(default=None, max_length=200)
    caption: str | None = Field(default=None, max_length=200)
    source: str | None = Field(default=None, max_length=140)
    # LinkedIn caps image alt text at 300 characters.
    alt: str | None = Field(default=None, max_length=300)


class Node(_Model):
    label: str = Field(min_length=1, max_length=40)
    detail: str | None = Field(default=None, max_length=90)


class DiagramSlide(_Slide):
    layout: Literal["diagram"]
    headline: str = Field(min_length=1, max_length=140)
    nodes: list[Node] = Field(min_length=2, max_length=6)
    caption: str | None = Field(default=None, max_length=200)


class ClosingSlide(_Slide):
    layout: Literal["closing"]
    headline: str = Field(min_length=1, max_length=140)
    question: str | None = Field(default=None, max_length=220)
    # Where the link is, typically. Never "comment X" or "tag a friend".
    cta: str | None = Field(default=None, max_length=90)


Slide = Annotated[
    Union[
        CoverSlide,
        StatementSlide,
        PointsSlide,
        StepsSlide,
        CodeSlide,
        CompareSlide,
        MetricSlide,
        QuoteSlide,
        ImageSlide,
        DiagramSlide,
        ClosingSlide,
    ],
    Field(discriminator="layout"),
]

LAYOUTS = (
    "cover",
    "statement",
    "points",
    "steps",
    "code",
    "compare",
    "metric",
    "quote",
    "image",
    "diagram",
    "closing",
)


class _Deck(_Model):
    # For a carousel, the document title LinkedIn asks for at upload and shows
    # at the top of the viewer.
    title: str = Field(min_length=1, max_length=120)
    language: Literal["pt-BR", "en"] = "pt-BR"
    # 'drafting' (computation paper) by default; 'blueprint' when the evidence
    # is dark: terminal output, dark-mode screenshots. See `themes.py`.
    theme: Literal["drafting", "blueprint"] = "drafting"
    pillar: str | None = Field(default=None, max_length=80)
    author: Author | None = None

    @field_validator("language", mode="before")
    @classmethod
    def _language_alias(cls, value: Any) -> Any:
        aliases = {"pt": "pt-BR", "pt-br": "pt-BR", "en-us": "en", "en-gb": "en"}
        if isinstance(value, str):
            return aliases.get(value.strip().lower(), value)
        return value


class CarouselSpec(_Deck):
    kind: Literal["carousel"] = "carousel"
    # LinkedIn accepts 300 pages and Instagram 20; past 20 nobody swipes.
    slides: list[Slide] = Field(min_length=1, max_length=20)


class VideoSpec(_Deck):
    kind: Literal["video"] = "video"
    aspect: Literal["4:5", "9:16", "1:1"] = "4:5"
    fps: int = Field(default=30, ge=24, le=60)
    # A recording of the user's own voice, relative to content/. Optional: most
    # feed video is watched muted, so the text on screen has to carry it anyway.
    voiceover: str | None = Field(default=None, max_length=260)
    # Burn the narration into the frame as captions. The .srt is written either
    # way, for the platforms that take a caption file.
    burn_captions: bool = True
    scenes: list[Slide] = Field(min_length=1, max_length=20)


Spec = Union[CarouselSpec, VideoSpec]


# Loading


def _location(loc: tuple[Any, ...]) -> str:
    """('slides', 3, 'headline') -> 'slides[4].headline' (1-based, as a reader counts)."""
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part + 1}]"
        elif part in LAYOUTS or part in {"function-after", "function-before"}:
            # Pydantic names the union member it tried; the reader does not care.
            continue
        else:
            out += f".{part}" if out else str(part)
    return out or "spec"


def validation_messages(error: ValidationError) -> list[str]:
    return [f"{_location(item['loc'])}: {item['msg']}" for item in error.errors()]


def parse_spec(
    source: str | dict[str, Any], kind: Literal["carousel", "video"]
) -> tuple[Spec | None, list[str]]:
    """Parse and validate a spec. Returns the spec and every blocking problem.

    The spec comes back even when there are text errors, so the caller can
    still report warnings in the same pass; it only comes back None when the
    shape itself is wrong.
    """
    if isinstance(source, str):
        try:
            data = yaml.safe_load(source)
        except yaml.YAMLError as error:
            return None, [f"The spec is not valid YAML or JSON: {error}"]
    else:
        data = source

    if not isinstance(data, dict):
        return None, [
            "The spec must be a mapping with 'title' and "
            f"'{'slides' if kind == 'carousel' else 'scenes'}'."
        ]

    model = CarouselSpec if kind == "carousel" else VideoSpec
    try:
        spec = model.model_validate(data)
    except ValidationError as error:
        return None, validation_messages(error)

    return spec, text_errors(spec)


def slides_of(spec: Spec) -> list[Any]:
    return spec.slides if isinstance(spec, CarouselSpec) else spec.scenes


def dump_spec(spec: Spec) -> str:
    """The spec as the YAML a person edits: no nulls, no defaults, accents kept."""
    data = spec.model_dump(mode="json", exclude_none=True, exclude_defaults=True)
    # `kind` and `layout` are defaults/discriminators that the file needs anyway.
    data = {"kind": spec.kind, **data}
    return yaml.safe_dump(
        data, allow_unicode=True, sort_keys=False, width=88, default_flow_style=False
    )


# Rules from principles.py

# Fields that hold a path, a lexer name or code: none of them is prose.
_NOT_PROSE = {
    "code",
    "image",
    "avatar",
    "voiceover",
    "url",
    "language",
    "layout",
    "frame",
    "theme",
    "aspect",
    "kind",
    "filename",
    "favored",
}

_DASHES = (("—", "an em dash (—)"), ("–", "an en dash (–)"), ("--", "'--' used as a dash"))
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def _strings(value: Any, path: str) -> Iterator[tuple[str, str, str]]:
    """Every string in a slide: (path, field name, text)."""
    if isinstance(value, str):
        yield path, path.rsplit(".", 1)[-1].split("[")[0], value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _strings(item, f"{path}[{index + 1}]")


def text_errors(spec: Spec) -> list[str]:
    """The blocking text problems: placeholders anywhere, dashes in prose."""
    problems: list[str] = []
    collection = "slides" if isinstance(spec, CarouselSpec) else "scenes"
    header = spec.model_dump(include={"title", "pillar", "author"}, exclude_none=True)
    body = [slide.model_dump(exclude_none=True) for slide in slides_of(spec)]

    candidates = list(_strings(header, "spec"))
    for index, slide in enumerate(body):
        candidates.extend(_strings(slide, f"{collection}[{index + 1}]"))

    for path, field, text in candidates:
        location = path.removeprefix("spec.")
        if "[PREENCHER" in text.upper():
            problems.append(
                f"{location}: still has a [PREENCHER] marker. A slide cannot "
                "carry a missing fact: get the real value or cut the claim."
            )
        if field in _NOT_PROSE:
            continue
        prose = _INLINE_CODE.sub("", text)
        for mark, name in _DASHES:
            if mark in prose:
                problems.append(
                    f"{location}: contains {name}. The voice rules ban it; use a "
                    "period, a comma or a colon."
                )
                break
    return problems
