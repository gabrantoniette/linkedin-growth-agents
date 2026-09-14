"""Syntax highlighting for code slides, in the studio's own palette.

Pygments does the lexing; the colors come from `themes.CODE_COLORS` through CSS
classes, so a code slide matches the rest of the deck instead of looking like a
screenshot pasted from a different editor.

The code is redacted before it is lexed (see `safety.py`): a key would
otherwise be split across tokens and survive a mask applied to the HTML.
"""

from __future__ import annotations

import html
import textwrap
from dataclasses import dataclass, field

from markupsafe import Markup
from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
from pygments.lexers.special import TextLexer
from pygments.token import Token, _TokenType
from pygments.util import ClassNotFound

from linkedin_growth.studio.safety import redact_secrets

# Most specific first: `Token.Name.Function in Token.Name` is true, so the
# order decides which class a token gets.
_CLASSES: list[tuple[_TokenType, str]] = [
    (Token.Comment, "comment"),
    (Token.Literal.String, "string"),
    (Token.Literal.Number, "number"),
    (Token.Keyword, "keyword"),
    (Token.Name.Function, "function"),
    (Token.Name.Class, "class"),
    (Token.Name.Builtin, "builtin"),
    (Token.Name.Decorator, "operator"),
    (Token.Name.Tag, "tag"),
    (Token.Name.Attribute, "attribute"),
    (Token.Operator, "operator"),
    (Token.Generic.Prompt, "prompt"),
    (Token.Generic.Output, "output"),
]

TAB_WIDTH = 4


@dataclass
class CodeLine:
    number: int
    html: Markup
    highlighted: bool


@dataclass
class HighlightedCode:
    lines: list[CodeLine]
    language: str
    redacted: list[str] = field(default_factory=list)
    plain_lines: list[str] = field(default_factory=list)

    @property
    def widest(self) -> int:
        return max((len(line) for line in self.plain_lines), default=0)


def _css_class(token_type: _TokenType) -> str | None:
    for parent, name in _CLASSES:
        if token_type in parent:
            return name
    return None


def _lexer(code: str, language: str | None, filename: str | None, terminal: bool) -> Lexer:
    # `ensurenl` stays on: the shell-session lexers read line by line and
    # silently drop a last line with no newline, which is how a terminal slide
    # once lost the one line of output that carried the result. The extra empty
    # row it adds is trimmed in `highlight`.
    options = {"stripnl": False, "ensurenl": True}
    if terminal and not language:
        language = "console"
    if language:
        try:
            return get_lexer_by_name(language, **options)
        except ClassNotFound:
            pass
    if filename:
        try:
            return guess_lexer_for_filename(filename, code, **options)
        except ClassNotFound:
            pass
    return TextLexer(**options)


def normalize(code: str) -> str:
    """Tabs to spaces, the shared indentation removed, blank edges trimmed."""
    code = code.expandtabs(TAB_WIDTH)
    code = textwrap.dedent(code)
    return code.strip("\n").rstrip()


def highlight(
    code: str,
    language: str | None = None,
    filename: str | None = None,
    highlight_lines: list[int] | None = None,
    terminal: bool = False,
) -> HighlightedCode:
    """Code -> one entry per line, with token spans and the highlight flags."""
    code, redacted = redact_secrets(normalize(code))
    lexer = _lexer(code, language, filename, terminal)
    marked = set(highlight_lines or [])

    rows: list[list[str]] = [[]]
    for token_type, value in lexer.get_tokens(code):
        css = _css_class(token_type)
        for index, piece in enumerate(value.split("\n")):
            if index > 0:
                rows.append([])
            if not piece:
                continue
            escaped = html.escape(piece, quote=False)
            rows[-1].append(f'<span class="t-{css}">{escaped}</span>' if css else escaped)

    plain_lines = code.split("\n")
    # A lexer may add a final newline; the source decides how many lines exist.
    rows = rows[: len(plain_lines)]
    lines = [
        CodeLine(
            number=number,
            html=Markup("".join(row) or "&#8203;"),
            highlighted=number in marked,
        )
        for number, row in enumerate(rows, start=1)
    ]
    return HighlightedCode(
        lines=lines,
        language=lexer.name,
        redacted=redacted,
        plain_lines=plain_lines,
    )
