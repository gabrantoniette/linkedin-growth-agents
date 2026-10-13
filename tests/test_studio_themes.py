"""The visual identity's guarantees: contrast, fonts, and variables that exist.

A slide is read on a phone, often outdoors. These tests make the WCAG floors a
property of the code: a new color that carries text either passes 4.5:1 or the
suite fails, whatever it looks like on a calibrated monitor.
"""

from __future__ import annotations

import re

import pytest

from linkedin_growth.studio.html import TEMPLATES_DIR
from linkedin_growth.studio.spec import CarouselSpec
from linkedin_growth.studio.themes import (
    ACCENTS,
    DEFAULT_THEME,
    FONTS,
    FONTS_DIR,
    JORNAL,
    MIN_GRAPHIC_CONTRAST,
    MIN_TEXT_CONTRAST,
    TEXTURES_DIR,
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


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda theme: theme.id)
def test_every_variable_a_theme_stylesheet_uses_is_defined(theme):
    """The jornal stylesheet uses colors only its theme has (the sheet, the marker)."""
    folder = TEMPLATES_DIR / "themes" / theme.templates if theme.templates else TEMPLATES_DIR
    text = (folder / theme.stylesheet).read_text(encoding="utf-8")
    used = set(re.findall(r"var\((--[a-z\-]+)", text))
    declared_in_the_sheet = set(re.findall(r"(--[a-z\-]+)\s*:", text))
    defined = {part.split(":")[0].strip() for part in theme.css_variables().split(";")}

    assert used - defined - declared_in_the_sheet - {"--w", "--h"} == set()


def test_the_jornal_theme_is_the_default_for_new_specs():
    assert DEFAULT_THEME == JORNAL.id
    assert CarouselSpec.model_validate({"title": "T", "slides": [{"layout": "statement", "text": "x"}]}).theme == "jornal"


def test_every_accent_has_its_highlighter_and_swaps_the_marker_color():
    for name, color in ACCENTS.items():
        assert (TEXTURES_DIR / f"marker-{name}.svg").is_file(), name
        assert color in (TEXTURES_DIR / f"marker-{name}.svg").read_text(encoding="utf-8")
        assert f"--marker: {color}" in JORNAL.css_variables(accent=name)
    assert (TEXTURES_DIR / "grain.png").is_file()


def test_ink_reads_on_every_highlighter():
    """Highlighted words are ink on the marker; a post may pick any accent."""
    for name, color in ACCENTS.items():
        assert contrast_ratio(JORNAL.ink, color) >= MIN_TEXT_CONTRAST, name
