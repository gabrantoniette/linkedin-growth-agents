"""What must never reach a public asset.

Three guards, each for a mistake that is cheap to make and impossible to undo
once the post is out:

1. **Secrets in code.** A code slide is a screenshot of real work, and real work
   has API keys in it. A key in a PDF is a key in the download folder of every
   reader, forever: LinkedIn lets anyone download a document post. So code is
   redacted before it is drawn, and the render says what it masked.

2. **Private pages.** A screenshot tool that follows any URL will happily
   photograph `localhost:7777`, a router admin page or an internal dashboard.
   The strategy forbids posting internal systems (strategy.md, "what not to
   post"); this makes it hard to do by accident.

3. **LinkedIn itself.** The project's line is the official API and nothing
   else: no scraping, no driven browser (README, "What can and cannot be
   automated"). A headless browser pointed at linkedin.com is exactly that, so
   it is refused, with the reason.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

# ==============================================================================
# Secrets
# ==============================================================================
# Specific formats first, then generic assignments. The generic ones mask only
# the value, so `api_key = "..."` still shows the reader where the key goes.

_MASK = "••••••••"

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private key", re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    )),
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}")),
    ("OpenAI key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("GitHub token", re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Slack token", re.compile(r"xox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}")),
]

# `DB_PASSWORD=hunter22`, `"token": "abc..."`, `API_KEY: xyz`. Only the value is
# masked, so the reader still sees where the key goes. The value has to look
# like a secret: a token mixing letters and digits, or a quoted string of 12
# characters or more. Code that merely talks about secrets (`token: str`,
# `_SECRET_PATTERNS = re.compile(...)`) is not one, and masking it made
# converted source files unreadable.
_ASSIGNMENT = re.compile(
    r"(?i)(?P<key>[\w\-]*(?:api[_\-]?key|secret|token|passw(?:or)?d|pwd|access[_\-]?key|"
    r"private[_\-]?key|client[_\-]?secret)[\w\-]*)"
    r"(?P<sep>[\"']?\s*[:=]\s*)"
    r"(?P<quote>[\"']?)"
    r"(?P<value>[A-Za-z0-9+/=_\-.~]{8,})"
    r"(?P=quote)"
)

# postgres://user:PASSWORD@host
_URL_PASSWORD = re.compile(r"(?P<head>\b[a-z][a-z0-9+.\-]*://[^:/\s@]+:)(?P<value>[^@\s]+)(?P<tail>@)")


def redact_secrets(text: str) -> tuple[str, list[str]]:
    """Mask what looks like a credential. Returns the text and what was masked."""
    found: list[str] = []

    for name, pattern in _SECRET_PATTERNS:
        text, count = pattern.subn(_MASK, text)
        found.extend([name] * count)

    def mask_value(match: re.Match[str]) -> str:
        value = match.group("value")
        quote = match.group("quote")
        looks_random = any(c.isdigit() for c in value) and any(c.isalpha() for c in value)
        reads_environment = value.lower().startswith(("os.", "env", "getenv"))
        if reads_environment or not (looks_random or (quote and len(value) >= 12)):
            # Reading from the environment is the right way to do it, and it is
            # exactly what a post about configuration should show.
            return match.group(0)
        found.append(f"value of {match.group('key')}")
        return f"{match.group('key')}{match.group('sep')}{quote}{_MASK}{quote}"

    text = _ASSIGNMENT.sub(mask_value, text)

    def mask_url(match: re.Match[str]) -> str:
        found.append("password in a connection URL")
        return f"{match.group('head')}{_MASK}{match.group('tail')}"

    text = _URL_PASSWORD.sub(mask_url, text)
    return text, found


# ==============================================================================
# URLs
# ==============================================================================

BLOCKED_DOMAINS = ("linkedin.com", "lnkd.in", "licdn.com")
_PRIVATE_SUFFIXES = (".local", ".internal", ".lan", ".home", ".corp", ".localhost")


def _is_private(address: str) -> bool:
    """True for any IP that is not a public internet address."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def blocked_host_reason(host: str | None, *, resolve: bool = True) -> str | None:
    """Why a host may not be captured, or None when it may.

    `resolve` looks the name up and refuses one that points inside the network:
    a public-looking name can resolve to 192.168.x.x.
    """
    if not host:
        return "the URL has no host."
    host = host.lower().rstrip(".")

    for domain in BLOCKED_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return (
                f"{host} is LinkedIn. This project only talks to LinkedIn through "
                "the official API; driving a browser there breaks the Terms of "
                "Use. Capture the original source instead, or take the screenshot "
                "by hand."
            )

    if host == "localhost" or host.endswith(_PRIVATE_SUFFIXES):
        return f"{host} is a local or internal address, not a public page."

    if _is_private(host.strip("[]")):
        return f"{host} is a private or loopback IP, not a public page."

    if resolve:
        try:
            addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
        except OSError:
            return f"{host} does not resolve. Check the address."
        private = sorted(a for a in addresses if _is_private(a))
        if private:
            return f"{host} resolves to a private address ({private[0]})."
    return None


def check_url(url: str, *, resolve: bool = True) -> str | None:
    """Why a URL may not be captured, or None when it may."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return "the URL is malformed."
    if parts.scheme not in ("http", "https"):
        return f"only http and https pages can be captured, not '{parts.scheme or 'no scheme'}'."
    if parts.username or parts.password:
        return "the URL carries credentials; remove them."
    return blocked_host_reason(parts.hostname, resolve=resolve)


# ==============================================================================
# Paths
# ==============================================================================


def confine(root: Path, relative: str) -> Path | None:
    """Resolve `relative` inside `root`, or None if it escapes."""
    base = root.resolve()
    target = (base / relative).resolve()
    if target != base and base not in target.parents:
        return None
    return target


_SLUG = re.compile(r"^[a-z0-9][a-z0-9\-]{0,79}$")


def valid_slug(slug: str) -> bool:
    """A media folder name: lowercase, digits and hyphens, like a post file stem."""
    return bool(_SLUG.match(slug))


def slugify(text: str, limit: int = 60) -> str:
    """'Notas de Estudo (RAG).md' -> 'notas-de-estudo-rag-md'."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = "-".join(re.findall(r"[a-z0-9]+", ascii_text.lower()))[:limit].strip("-")
    return slug or "media"
