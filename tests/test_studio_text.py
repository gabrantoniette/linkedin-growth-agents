"""Slide text: escaping, the four inline marks and typography.

Slide text comes from a model that read web pages and is rendered in a real
browser, so the first property under test is that it cannot become markup.
"""

from __future__ import annotations

from linkedin_growth.studio.text import has_emphasis, inline, plain, typographic, word_count


def test_html_in_slide_text_is_escaped_not_rendered():
    rendered = str(inline("<script>alert(1)</script> & <b>x</b>"))

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "&amp;" in rendered


def test_the_four_marks_become_tags():
    rendered = str(inline("**forte** *ênfase* ==marca== `código`"))

    assert "<strong>forte</strong>" in rendered
    assert "<em>ênfase</em>" in rendered
    assert "<mark>marca</mark>" in rendered
    assert "<code>código</code>" in rendered


def test_marks_inside_inline_code_stay_literal():
    rendered = str(inline("use `**kwargs` aqui"))

    assert "<code>**kwargs</code>" in rendered
    assert "<strong>" not in rendered


def test_a_lone_asterisk_in_arithmetic_is_not_emphasis():
    assert "<em>" not in str(inline("5*3 e 2*4"))


def test_straight_quotes_and_dots_become_typographic():
    assert typographic('"não é só X"') == "“não é só X”"
    assert typographic("isn't") == "isn’t"
    assert typographic("espera...") == "espera…"


def test_plain_text_and_word_count_ignore_the_marks():
    assert plain("**forte** e ==marca==") == "forte e marca"
    assert word_count("**forte** e ==marca==") == 3


def test_emphasis_detection_ignores_inline_code():
    """The lint flags emphasis in headlines; code in a headline is not emphasis."""
    assert has_emphasis("um *acento* no título")
    assert has_emphasis("**negrito**")
    assert not has_emphasis("rode `**kwargs`")
    assert not has_emphasis(None)
