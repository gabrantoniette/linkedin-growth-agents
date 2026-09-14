"""The visual identity's guarantees: contrast, fonts, and variables that exist.

A slide is read on a phone, often outdoors. These tests make the WCAG floors a
property of the code: a new color that carries text either passes 4.5:1 or the
suite fails, whatever it looks like on a calibrated monitor.
"""

from __future__ import annotations

import re

import pytest

from linkedin_growth.studio.html import TEMPLATES_DIR
from linkedin_growth.studio.themes import (
    FONTS,
    FONTS_DIR,
    MIN_GRAPHIC_CONTRAST,
    MIN_TEXT_CONTRAST,
    THEMES,
    contrast_ratio,
)


def test_the_contrast_math_matches_the_wcag_reference_points():
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast_ratio("#777777", "#FFFFFF") == pytest.approx(4.48, abs=0.01)


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda theme: theme.id)
def test_every_pair_that_carries_text_passes_wcag_aa(theme):
    failing = {
        name: round(contrast_ratio(foreground, background), 2)
        for name, (foreground, background) in theme.text_pairs().items()
        if contrast_ratio(foreground, background) < MIN_TEXT_CONTRAST
    }

    assert failing == {}


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda theme: theme.id)
def test_lines_that_carry_structure_are_visible(theme):
    failing = {
        name: round(contrast_ratio(foreground, background), 2)
        for name, (foreground, background) in theme.graphic_pairs().items()
        if contrast_ratio(foreground, background) < MIN_GRAPHIC_CONTRAST
    }

    assert failing == {}


def test_every_bundled_font_exists_next_to_its_license():
    """The fonts are redistributed under the OFL, which requires the license."""
    for font in FONTS:
        assert (FONTS_DIR / font.file).is_file(), font.file

    for family in {font.file.split("-")[0] for font in FONTS}:
        assert (FONTS_DIR / f"{family}-OFL.txt").is_file(), family


def test_every_css_variable_the_templates_use_is_defined_by_every_theme():
    """A variable the CSS uses and a theme lacks renders as nothing, silently."""
    used: set[str] = set()
    for stylesheet in ("studio.css", "document.css"):
        text = (TEMPLATES_DIR / stylesheet).read_text(encoding="utf-8")
        used |= set(re.findall(r"var\((--[a-z\-]+)", text))
    set_by_the_layout = {"--margin", "--content-top", "--content-bottom", "--foot-bottom", "--w", "--h"}

    for theme in THEMES.values():
        defined = {part.split(":")[0].strip() for part in theme.css_variables().split(";")}
        assert used - defined - set_by_the_layout == set(), theme.id
