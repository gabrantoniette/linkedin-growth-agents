"""Slide text: escaping, the small inline markup specs use, and typography.

A spec is written by a model and edited by a person, so its text is plain with
four marks, and nothing else is ever interpreted:

    **strong**   weight, in the text color
    *emphasis*   the italic serif accent word (one per slide, at most)
    ==marker==   the accent highlight, for the number or phrase that matters
    `code`       monospace, for identifiers inside a sentence

Everything is HTML-escaped BEFORE the marks become tags. A headline containing
`<script>` renders as those characters, not as a script: the text comes from a
model that read web pages, and a render runs in a real browser.
"""

from __future__ import annotations

import html
import re

from markupsafe import Markup

_CODE = re.compile(r"`([^`\n]+)`")
_STRONG = re.compile(r"\*\*(.+?)\*\*")
_MARK = re.compile(r"==(.+?)==")
# A single asterisk pair, not touching another asterisk or a letter on the
# outside, so '5*3' and '**' leftovers are left alone.
_EMPHASIS = re.compile(r"(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])")

# The marks, for code that needs the text without them (word counts).
_ANY_MARK = re.compile(r"\*\*|==|`|(?<![*\w])\*|\*(?![*\w])")


def typographic(text: str) -> str:
    """Straight quotes to curly ones, three dots to an ellipsis.

    Both Portuguese and English use “ ” and ‘ ’. Straight quotes are the
    typewriter version, and at 110px a typewriter quote is the first thing a
    reader notices.
    """
    text = text.replace("...", "…")
    text = re.sub(r'(^|[\s(\[{—–-])"', r"\1“", text)
    text = text.replace('"', "”")
    text = re.sub(r"(^|[\s(\[{—–-])'", r"\1‘", text)
    return text.replace("'", "’")


def _prose(chunk: str) -> str:
    escaped = html.escape(typographic(chunk), quote=False)
    escaped = _STRONG.sub(r"<strong>\1</strong>", escaped)
    escaped = _MARK.sub(r"<mark>\1</mark>", escaped)
    escaped = _EMPHASIS.sub(r"<em>\1</em>", escaped)
    return escaped.replace("\n", "<br>")


def inline(text: str | None) -> Markup:
    """Spec text -> safe HTML with the four marks applied."""
    if not text:
        return Markup("")
    parts: list[str] = []
    last = 0
    for match in _CODE.finditer(text):
        parts.append(_prose(text[last : match.start()]))
        parts.append(f"<code>{html.escape(match.group(1), quote=False)}</code>")
        last = match.end()
    parts.append(_prose(text[last:]))
    return Markup("".join(parts))


def plain(text: str | None) -> str:
    """The text a reader sees, without the marks."""
    if not text:
        return ""
    return _ANY_MARK.sub("", text)


def word_count(text: str | None) -> int:
    return len(re.findall(r"\S+", plain(text)))


# Emphasis, as opposed to inline code: the marks that change weight or color.
_EMPHASIS_MARKS = re.compile(r"\*\*|==|(?<![*\w])\*(?![\s*])")


def has_emphasis(text: str | None) -> bool:
    """Whether the text uses **strong**, *emphasis* or ==marker==."""
    return bool(text) and bool(_EMPHASIS_MARKS.search(_CODE.sub("", text or "")))
