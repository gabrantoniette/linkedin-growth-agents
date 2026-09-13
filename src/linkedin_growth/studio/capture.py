"""Screenshots of real web pages: the proof a post points at.

A post that says "the docs now say X" is stronger with the docs on the slide,
and a "Construí" post is stronger with the repository on it. This module takes
that picture, and only that picture: a real page, loaded now, in a clean browser
with no cookies and no logged-in session.

The guards from `safety.py` run twice. Once on the URL before anything loads,
and again on every request the page makes while loading, because a public page
can redirect to a private address or embed something from LinkedIn.

Every capture writes a small JSON next to the PNG: the URL asked for, the URL
that actually loaded, the page title and the time. That is the provenance of
the image. If someone asks "is this screenshot real?", the answer is on disk.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from linkedin_growth.studio.browser import Studio, run_isolated
from linkedin_growth.studio.safety import blocked_host_reason, check_url

if TYPE_CHECKING:
    from playwright.sync_api import Route

# A tall page captured whole becomes a 40,000px strip nobody can use on a slide.
MAX_CAPTURE_HEIGHT = 6000

NAVIGATION_TIMEOUT_MS = 45_000
IDLE_TIMEOUT_MS = 8_000


@dataclass
class Capture:
    ok: bool
    url: str
    path: Path | None = None
    final_url: str = ""
    title: str = ""
    width: int = 0
    height: int = 0
    captured_at: str = ""
    error: str | None = None
    # Hosts the page tried to reach and was refused (private, LinkedIn).
    blocked: list[str] = field(default_factory=list)

    def summary(self, root: Path) -> str:
        if not self.ok:
            return f"NOT CAPTURED: {self.error}"
        try:
            shown = self.path.resolve().relative_to(root.resolve()).as_posix()  # type: ignore[union-attr]
        except ValueError:
            shown = str(self.path)
        lines = [
            f"Screenshot: {shown} ({self.width}x{self.height})",
            f"Page: {self.title or '(no title)'}",
            f"Loaded from: {self.final_url}",
        ]
        if self.final_url.rstrip("/") != self.url.rstrip("/"):
            lines.append(f"Note: {self.url} redirected to the address above.")
        if self.blocked:
            lines.append(
                "Blocked while loading (private or LinkedIn hosts): "
                + ", ".join(sorted(set(self.blocked)))
            )
        return "\n".join(lines)


def capture_url(
    url: str,
    target: Path,
    *,
    width: int = 1280,
    height: int = 800,
    full_page: bool = False,
    selector: str | None = None,
    dark_mode: bool = False,
    hide_selectors: list[str] | None = None,
    wait_ms: int = 900,
    scale: float = 2,
) -> Capture:
    """Photograph a public page into `target` (a .png path)."""
    result = Capture(ok=False, url=url)
    problem = check_url(url)
    if problem:
        result.error = problem
        return result
    if not (320 <= width <= 2560 and 320 <= height <= 2560):
        result.error = "width and height must be between 320 and 2560 pixels."
        return result

    def shoot() -> None:
        with Studio() as studio:
            assert studio.browser is not None
            context = studio.browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=scale,
                color_scheme="dark" if dark_mode else "light",
                accept_downloads=False,
                service_workers="block",
                locale="pt-BR",
            )
            page = context.new_page()
            verdicts: dict[str, str | None] = {}

            def guard(route: Route) -> None:
                parts = urlsplit(route.request.url)
                if parts.scheme in ("data", "blob"):
                    route.continue_()
                    return
                host = (parts.hostname or "").lower()
                if host not in verdicts:
                    verdicts[host] = blocked_host_reason(host, resolve=True)
                if verdicts[host]:
                    result.blocked.append(host)
                    route.abort("blockedbyclient")
                    return
                route.continue_()

            page.route("**/*", guard)
            try:
                response = page.goto(url, wait_until="load", timeout=NAVIGATION_TIMEOUT_MS)
            except Exception as error:  # noqa: BLE001 - surfaced to the agent as text
                first = str(error).strip().splitlines()[0] if str(error).strip() else repr(error)
                if "ERR_BLOCKED_BY_CLIENT" in first:
                    result.error = (
                        "the page redirected to a private or LinkedIn address, "
                        "which is not captured."
                    )
                else:
                    result.error = f"the page did not load: {first[:200]}"
                return
            if response is not None and response.status >= 400:
                result.error = f"the page answered HTTP {response.status}."
                return

            try:
                page.wait_for_load_state("networkidle", timeout=IDLE_TIMEOUT_MS)
            except Exception:  # noqa: BLE001 - a page that never goes idle still renders
                pass
            if hide_selectors:
                rules = ", ".join(hide_selectors)
                page.add_style_tag(content=f"{rules} {{ display: none !important; }}")
            page.wait_for_timeout(wait_ms)

            target.parent.mkdir(parents=True, exist_ok=True)
            if selector:
                element = page.locator(selector).first
                if element.count() == 0:
                    result.error = f"no element matches the selector '{selector}'."
                    return
                element.screenshot(path=str(target))
                box = element.bounding_box() or {"width": 0, "height": 0}
                result.width, result.height = round(box["width"]), round(box["height"])
            elif full_page:
                page_height = page.evaluate("() => document.documentElement.scrollHeight")
                clipped = min(int(page_height), MAX_CAPTURE_HEIGHT)
                page.screenshot(
                    path=str(target),
                    full_page=True,
                    clip={"x": 0, "y": 0, "width": width, "height": clipped},
                )
                result.width, result.height = width, clipped
            else:
                page.screenshot(path=str(target))
                result.width, result.height = width, height

            result.final_url = page.url
            result.title = page.title()
            result.captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            result.path = target
            result.ok = True

    run_isolated(shoot)

    if result.ok and result.path:
        provenance = {
            key: value
            for key, value in asdict(result).items()
            if key not in {"ok", "path", "error"}
        }
        result.path.with_suffix(".json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return result
