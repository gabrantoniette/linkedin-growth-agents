"""Who signs the assets: the footer identity and the default theme.

Every slide carries the same small footer (initials or photo, name, one line of
what the person does). That footer is what turns a screenshot of a carousel,
reshared out of context, back into a pointer to the profile.

It comes from two places, in order:

1. `profile/brand.yaml`, optional and hand-written, out of git like the rest of
   `profile/`:

       name: Gabriel Antoniette
       tagline: Engenharia de IA em público
       avatar: profile/avatar.jpg
       theme: graphite

2. `profile/profile.yaml`, for the name, when brand.yaml does not say.

A spec can still override all of it with its own `author` block.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from linkedin_growth.config import BRAND_YAML, CONTENT_DIR, PROFILE_DIR, ROOT
from linkedin_growth.studio.safety import confine
from linkedin_growth.studio.spec import Author
from linkedin_growth.studio.themes import DEFAULT_THEME, THEMES

_AVATAR_NAMES = ("avatar.jpg", "avatar.jpeg", "avatar.png", "avatar.webp")


def load_brand() -> dict[str, Any]:
    """The contents of profile/brand.yaml, or an empty dict."""
    if not BRAND_YAML.exists():
        return {}
    try:
        data = yaml.safe_load(BRAND_YAML.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _profile_name() -> str | None:
    # Late import: the profile module reads config at import, and the studio is
    # imported by tools that must not fail when no profile exists yet.
    from linkedin_growth.profile.context import ProfileMissing, load_profile

    try:
        return load_profile().name
    except (ProfileMissing, ValueError, OSError):
        return None


def resolve_asset_path(relative: str | None) -> Path | None:
    """A file a spec points at, only if it lives under profile/ or content/.

    The footer photo is the one path in a spec relative to the project root
    rather than to content/, because it belongs to the profile. Everything
    else in the root (.env, the source) is refused.
    """
    if not relative:
        return None
    target = confine(ROOT, relative)
    if target is None:
        return None
    allowed = (PROFILE_DIR.resolve(), CONTENT_DIR.resolve())
    if not any(base in target.parents for base in allowed):
        return None
    return target if target.is_file() else None


def default_author() -> Author | None:
    brand = load_brand()
    name = brand.get("name") or _profile_name()
    if not name:
        return None
    avatar = brand.get("avatar")
    if not avatar:
        found = next((PROFILE_DIR / n for n in _AVATAR_NAMES if (PROFILE_DIR / n).is_file()), None)
        avatar = found.relative_to(ROOT).as_posix() if found else None
    return Author(
        name=str(name)[:60],
        tagline=str(brand["tagline"])[:80] if brand.get("tagline") else None,
        avatar=avatar,
    )


def default_theme() -> str:
    theme = load_brand().get("theme")
    return theme if theme in THEMES else DEFAULT_THEME
