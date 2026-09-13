"""The headless browser every render goes through. Offline by construction.

Why a browser at all: layout. Text that wraps with balanced lines, a code window
that measures its widest line, type that shrinks until it fits, a PDF whose text
stays selectable. Chromium does all of that for free, and the same engine
produces the PDF and the PNGs, so they cannot disagree.

Three decisions worth knowing before touching this file:

1. **Which Chromium.** Playwright's bundled build first, then an installed
   Chrome, then Edge. On Windows, Edge is always there, so a fresh clone renders
   without downloading anything. `STUDIO_BROWSER_CHANNEL` forces one.

2. **No network.** The document is served from a virtual origin through
   `page.route`, and every request that is not a known font, a registered file
   or the document itself is aborted. A render is reproducible and cannot leak
   anything, because it cannot reach anything.

3. **Threads.** Playwright's sync API refuses to run inside a live asyncio loop,
   and AgentOS runs agents inside one. `run_isolated` moves the work to a
   worker thread when a loop is running and runs it inline when not (the CLI).
"""

from __future__ import annotations

import asyncio
import mimetypes
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar
from urllib.parse import unquote

from linkedin_growth.config import MissingConfiguration
from linkedin_growth.studio.html import ORIGIN, Document
from linkedin_growth.studio.safety import confine
from linkedin_growth.studio.themes import FONTS, FONTS_DIR

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page, Playwright, Route

T = TypeVar("T")

INSTALL_HINT = (
    "No Chromium browser is available to render with.\n"
    "Install Playwright's build once:\n"
    "    uv run playwright install chromium\n"
    "Or install Google Chrome or Microsoft Edge, which the studio also uses."
)


def _fulfill_file(route: Route, target: Path) -> None:
    route.fulfill(
        status=200,
        content_type=mimetypes.guess_type(target.name)[0] or "application/octet-stream",
        body=target.read_bytes(),
    )


def run_isolated(work: Callable[[], T]) -> T:
    """Run `work` where Playwright's sync API is allowed."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return work()
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="studio") as pool:
        return pool.submit(work).result()


def _launch(playwright: Playwright) -> Browser:
    forced = os.getenv("STUDIO_BROWSER_CHANNEL", "").strip()
    channels: list[str | None] = [forced] if forced else [None, "chrome", "msedge"]
    failures: list[str] = []
    for channel in channels:
        try:
            if channel:
                return playwright.chromium.launch(channel=channel)
            return playwright.chromium.launch()
        except Exception as error:  # noqa: BLE001 - Playwright raises its own Error type
            first_line = str(error).strip().splitlines()[0] if str(error).strip() else repr(error)
            failures.append(f"  {channel or 'bundled chromium'}: {first_line[:160]}")
    raise MissingConfiguration(INSTALL_HINT + "\n\nWhat was tried:\n" + "\n".join(failures))


def browser_available() -> bool:
    """Whether a render could start. Slow (it launches a browser); for tests and doctor checks."""
    try:
        with Studio():
            return True
    except Exception:  # noqa: BLE001
        return False


class Studio:
    """One browser for the duration of a render. Use as a context manager."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self.browser: Browser | None = None

    def __enter__(self) -> Studio:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:  # pragma: no cover - it is a declared dependency
            raise MissingConfiguration(
                "Playwright is not installed. Run `uv sync`."
            ) from error
        self._playwright = sync_playwright().start()
        try:
            self.browser = _launch(self._playwright)
        except BaseException:
            self._playwright.stop()
            raise
        return self

    def __exit__(self, *_: Any) -> None:
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()

    def open_document(self, document: Document, scale: float = 1) -> Page:
        """A page showing `document`, with the network closed around it."""
        assert self.browser is not None, "use Studio as a context manager"
        context = self.browser.new_context(
            viewport={"width": document.width, "height": document.height},
            device_scale_factor=scale,
        )
        page = context.new_page()
        fonts = {font.file for font in FONTS}

        def serve(route: Route) -> None:
            url = route.request.url
            if not url.startswith(ORIGIN + "/"):
                route.abort("blockedbyclient")
                return
            path = url[len(ORIGIN) + 1 :].split("?", 1)[0].split("#", 1)[0]
            if path in ("", "index.html"):
                route.fulfill(
                    status=200,
                    content_type="text/html; charset=utf-8",
                    body=document.html,
                )
            elif path.startswith("fonts/") and path[len("fonts/") :] in fonts:
                route.fulfill(
                    status=200,
                    content_type="font/woff2",
                    body=(FONTS_DIR / path[len("fonts/") :]).read_bytes(),
                )
            elif path.startswith("files/") and path[len("files/") :] in document.files:
                _fulfill_file(route, document.files[path[len("files/") :]])
            elif document.base_dir is not None:
                # A converted HTML file: its relative assets, confined to its folder.
                target = confine(document.base_dir, unquote(path))
                if target is not None and target.is_file():
                    _fulfill_file(route, target)
                else:
                    route.abort("blockedbyclient")
            else:
                route.abort("blockedbyclient")

        page.route("**/*", serve)
        page.goto(f"{ORIGIN}/index.html", wait_until="load")
        return page
