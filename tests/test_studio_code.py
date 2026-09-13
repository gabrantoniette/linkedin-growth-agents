"""Syntax highlighting for code slides and converted source files."""

from __future__ import annotations

from linkedin_growth.studio.code import highlight, normalize


def html_of(code) -> str:
    return "".join(str(line.html) for line in code.lines)


def test_a_terminal_session_keeps_its_last_line():
    """Regression: the shell-session lexer silently dropped a last line with no newline.

    It was the line with the result, on a slide whose whole point was the result.
    """
    session = "$ uv run bench.py\nembedding  38 ms\ngeneration 1840 ms"

    code = highlight(session, terminal=True)

    assert len(code.lines) == 3
    assert "generation" in str(code.lines[-1].html)


def test_highlighted_lines_are_flagged_by_their_number():
    code = highlight("a = 1\nb = 2\nc = 3", language="python", highlight_lines=[2])

    assert [line.highlighted for line in code.lines] == [False, True, False]


def test_secrets_are_masked_before_lexing():
    """Masking the HTML afterwards would miss a key split across token spans."""
    code = highlight('API_KEY = "sk-ant-api03-abcdefghijklmnop"', language="python")

    assert "sk-ant" not in html_of(code)
    assert code.redacted


def test_the_language_is_guessed_from_the_filename():
    assert highlight("def f():\n    return 1", filename="tools.py").language == "Python"


def test_an_unknown_language_falls_back_to_plain_text():
    code = highlight("qualquer coisa", language="linguagem-que-nao-existe")

    assert "qualquer coisa" in html_of(code)


def test_normalize_expands_tabs_dedents_and_trims_blank_edges():
    assert normalize("\n\t\tx = 1\n\t\ty = 2\n\n") == "x = 1\ny = 2"
