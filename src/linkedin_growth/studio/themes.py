"""The visual identity: palettes, fonts, and the contrast math that guards them.

The identity comes from the material of the user's trade, not from what social
graphics usually look like. The user is an engineer whose positioning is "a
measured number instead of an opinion", so the slides are drawn like a page of
engineering work:

- the ground is **computation paper**, the pale green pad with a 5x5 grid
  printed on it that engineers do calculations on;
- text is **graphite**, structure (scales, borders, connectors) is drawn in
  **non-photo blue**, the color drafters use for construction lines;
- anything that is a measurement, and only that, is in **red**: the current
  page on the dimension line, a measured value, a highlighted line of code.

`blueprint` is the same drawing inverted, for decks whose evidence is dark
(terminal output, dark-mode screenshots): blueprint blue, white lines, and the
reviewer's yellow for measurements.

Why this is code and not a stylesheet tuned by eye: every color pair is checked
against the WCAG contrast formula in the tests. A carousel is read on a phone,
often outdoors, and a pale line that looks fine on a calibrated monitor
disappears on a cheap screen. Text needs 4.5:1 (WCAG 2.2 §1.4.3); lines that
carry structure need 3:1 (§1.4.11).

One accent per theme, never one per pillar: the identity is what has to be
recognizable across a year of posts, and a color that changes every post is
the opposite of that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

# Canvas: 4:5 is the tallest ratio LinkedIn/Instagram show uncropped in the
# mobile feed (kb-visual-formats.md §3).
CAROUSEL_SIZE = (1080, 1350)

# 9:16 for vertical surfaces, where UI covers the top 14%/bottom 35% (Meta's
# safe zone, kb-visual-formats.md §6).
VIDEO_SIZES = {
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
}

# WCAG 2.2 §1.4.3 (text) and §1.4.11 (graphical objects).
MIN_TEXT_CONTRAST = 4.5
MIN_LARGE_CONTRAST = 3.0
MIN_GRAPHIC_CONTRAST = 3.0


# Fonts: bundled (SIL OFL, subset to Latin, WOFF2 ~200KB) rather than fetched,
# so a render can't silently fall back to Arial offline or on CI.


@dataclass(frozen=True)
class Font:
    family: str
    file: str
    weight: str = "400"
    style: str = "normal"
    # The width axis range, for variable fonts that have one.
    stretch: str | None = None


FONTS = (
    # Language text: variable width lets condensed headlines fit long
    # Portuguese words ("requisição", "aplicações") without shrinking type.
    Font("Archivo", "Archivo-Variable.woff2", "100 900", "normal", "62% 125%"),
    Font("Archivo", "Archivo-Italic-Variable.woff2", "100 900", "italic", "62% 125%"),
    # Machine text only: code, terminal output, paths, URLs. Never labels.
    Font("IBM Plex Mono", "IBMPlexMono-Regular.woff2", "400"),
    Font("IBM Plex Mono", "IBMPlexMono-SemiBold.woff2", "600"),
)


# Themes


@dataclass(frozen=True)
class Theme:
    id: str
    paper: str  # the ground
    panel: str  # one step off the ground, for listings/figures/diagram nodes
    band: str  # alternate band inside a code listing, like green-bar paper
    ink: str
    pencil: str
    construction: str  # lines that carry structure: scale, borders, connectors
    grid: str  # printed grid texture
    grid_major: str  # heavier grid line every five modules
    measure: str  # the one accent, for measurements only
    on_measure: str
    code: dict[str, str] = field(default_factory=dict)

    def css_variables(self) -> str:
        """The theme as CSS custom properties, for the `:root` of a render."""
        values = {
            "--paper": self.paper,
            "--panel": self.panel,
            "--band": self.band,
            "--ink": self.ink,
            "--pencil": self.pencil,
            "--construction": self.construction,
            "--grid": self.grid,
            "--grid-major": self.grid_major,
            "--measure": self.measure,
            "--on-measure": self.on_measure,
            **{f"--code-{name}": color for name, color in self.code.items()},
        }
        return "; ".join(f"{name}: {value}" for name, value in values.items())

    def text_pairs(self) -> dict[str, tuple[str, str]]:
        """Every (foreground, background) pair that carries text, by name.
        The tests walk this, so a new text color must be added here."""
        pairs = {
            "ink on paper": (self.ink, self.paper),
            "pencil on paper": (self.pencil, self.paper),
            "measure on paper": (self.measure, self.paper),
            "ink on panel": (self.ink, self.panel),
            "pencil on panel": (self.pencil, self.panel),
            "on-measure on measure": (self.on_measure, self.measure),
        }
        for name in ("text", "keyword", "function", "class", "string", "number",
                     "comment", "operator", "builtin", "tag", "attribute", "prompt"):
            pairs[f"code {name} on panel"] = (self.code[name], self.panel)
            pairs[f"code {name} on band"] = (self.code[name], self.band)
        return pairs

    def graphic_pairs(self) -> dict[str, tuple[str, str]]:
        """Lines a reader has to see: the scale, borders, line numbers."""
        return {
            "construction on paper": (self.construction, self.paper),
            "construction on panel": (self.construction, self.panel),
            "code gutter on panel": (self.code["gutter"], self.panel),
        }


DRAFTING = Theme(
    id="drafting",
    paper="#DFEAD8",
    panel="#EDF4E8",
    band="#E2ECDB",
    ink="#1B221E",
    pencil="#46564C",
    construction="#52799B",
    grid="rgba(82, 121, 155, 0.1)",
    grid_major="rgba(82, 121, 155, 0.17)",
    measure="#B3261E",
    on_measure="#FFF8F4",
    code={
        "text": "#1B221E",
        "gutter": "#52799B",
        "keyword": "#1F4E80",
        "function": "#1B221E",
        "class": "#1F4E80",
        "string": "#7A4A0C",
        "number": "#A62B1F",
        "comment": "#54655B",
        "operator": "#3A4841",
        "builtin": "#1F4E80",
        "tag": "#1F4E80",
        "attribute": "#7A4A0C",
        "prompt": "#B3261E",
    },
)

BLUEPRINT = Theme(
    id="blueprint",
    paper="#143A5C",
    panel="#10314E",
    band="#153B5A",
    ink="#EAF3FA",
    pencil="#A9C4DA",
    construction="#6FA3CC",
    grid="rgba(111, 163, 204, 0.11)",
    grid_major="rgba(111, 163, 204, 0.22)",
    measure="#FFD34E",
    on_measure="#143A5C",
    code={
        "text": "#EAF3FA",
        "gutter": "#7DAED4",
        "keyword": "#9CC8F0",
        "function": "#EAF3FA",
        "class": "#FFD34E",
        "string": "#F5C97A",
        "number": "#FFD34E",
        "comment": "#9BB9D1",
        "operator": "#C2D8EA",
        "builtin": "#9CC8F0",
        "tag": "#9CC8F0",
        "attribute": "#F5C97A",
        "prompt": "#FFD34E",
    },
)

THEMES = {theme.id: theme for theme in (DRAFTING, BLUEPRINT)}
DEFAULT_THEME = DRAFTING.id


def get_theme(theme_id: str | None) -> Theme:
    return THEMES.get(theme_id or DEFAULT_THEME, DRAFTING)


# Contrast


def _channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """WCAG relative luminance of a '#RRGGBB' color."""
    hex_value = color.lstrip("#")
    if len(hex_value) != 6:
        raise ValueError(f"expected #RRGGBB, got {color!r}")
    red, green, blue = (int(hex_value[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG contrast ratio between two colors, from 1.0 to 21.0."""
    lighter, darker = sorted(
        (relative_luminance(first), relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)
