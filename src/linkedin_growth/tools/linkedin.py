"""Publishing to LinkedIn through the official API.

Only the sanctioned path: OAuth plus the `Share on LinkedIn` product (the
`w_member_social` scope), publishing to your own profile, with your consent. No
scraping, no `li_at` cookie, no browser automation. Those are forbidden by the
Terms of Use and get accounts banned.

Two API subtleties this module handles:

1. **Two endpoints.** `/rest/posts` is the current one, but the documentation
   never states that an app holding only `Share on LinkedIn` may call it.
   `/v2/ugcPosts` is the legacy one, and it is what the self-serve page itself
   documents. We try the first and fall back to the second on a 403.

2. **`commentary` is not plain text.** It uses the "little text format", where
   fifteen characters are reserved and need a backslash, parentheses included,
   which show up constantly in text written by an AI. Without escaping, the post
   fails or comes out mangled. `/v2/ugcPosts` takes plain text, no escaping.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from agno.tools import tool

from linkedin_growth.config import (
    LINKEDIN_VERSION,
    MissingConfiguration,
    require_linkedin,
)

USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
UGC_URL = "https://api.linkedin.com/v2/ugcPosts"

TIMEOUT = httpx.Timeout(30.0)

# Reserved characters of the "little text format". The documentation is
# explicit: "All reserved characters need to be escaped with a backslash, even
# if those characters are not used in one of the supported elements or
# templates."
LITTLE_RESERVED = set(r"\|{}@[]()<>#*_~")

# Hashtag: '#' followed by letters or digits. No underscore: LinkedIn does not
# accept it in a hashtag, and it is a reserved character of the format.
_HASHTAG = re.compile(r"(?<![\w#])#([0-9A-Za-zÀ-ÖØ-öø-ÿ]+)")


# ==============================================================================
# Text formatting
# ==============================================================================


def escape_little(text: str) -> str:
    """Escape every reserved character of the little text format."""
    return "".join("\\" + c if c in LITTLE_RESERVED else c for c in text)


def to_little(text: str) -> str:
    """Convert plain text to little text format, preserving hashtags.

    Hashtags become the `{hashtag|\\#|value}` template, which is what makes
    LinkedIn render a clickable link. Everything else is escaped.
    """
    parts: list[str] = []
    last = 0
    for match in _HASHTAG.finditer(text):
        parts.append(escape_little(text[last : match.start()]))
        parts.append("{hashtag|\\#|" + match.group(1) + "}")
        last = match.end()
    parts.append(escape_little(text[last:]))
    return "".join(parts)


# ==============================================================================
# HTTP client
# ==============================================================================


def _headers(*, versioned: bool) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {require_linkedin()}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    if versioned:
        headers["LinkedIn-Version"] = LINKEDIN_VERSION
    return headers


def token_profile() -> dict[str, Any]:
    """Identity of the token's owner, via the OIDC `userinfo` endpoint.

    It is the only self-serve way to know who the user is. Note that `sub` is
    specific to your app: the same member has a different `sub` in another app.
    """
    response = httpx.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {require_linkedin()}"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def member_urn() -> str:
    """The author URN, in the form `urn:li:person:{sub}`."""
    data = token_profile()
    sub = data.get("sub")
    if not sub:
        raise RuntimeError(
            "The /v2/userinfo response did not include the 'sub' field. Check "
            "that the token carries the 'openid' and 'profile' scopes."
        )
    return f"urn:li:person:{sub}"


# ==============================================================================
# Payload assembly
# ==============================================================================


def rest_payload(text: str, author: str, visibility: str = "PUBLIC") -> dict[str, Any]:
    """Body for `POST /rest/posts` (current endpoint, little text format)."""
    return {
        "author": author,
        "commentary": to_little(text),
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


def ugc_payload(text: str, author: str, visibility: str = "PUBLIC") -> dict[str, Any]:
    """Body for `POST /v2/ugcPosts` (legacy endpoint, plain text)."""
    return {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
    }


def preview(text: str, visibility: str = "PUBLIC") -> str:
    """Show what would be sent, without sending. Used by the CLI's `--dry-run`."""
    try:
        author = member_urn()
    except (httpx.HTTPError, MissingConfiguration, RuntimeError) as error:
        author = f"urn:li:person:<could not resolve: {error}>"

    return (
        f"POST {POSTS_URL}\n"
        f"LinkedIn-Version: {LINKEDIN_VERSION}\n\n"
        + json.dumps(rest_payload(text, author, visibility), indent=2, ensure_ascii=False)
        + f"\n\n--- fallback if 403 ---\nPOST {UGC_URL}\n\n"
        + json.dumps(ugc_payload(text, author, visibility), indent=2, ensure_ascii=False)
    )


# ==============================================================================
# Publishing
# ==============================================================================


def _post_url(response: httpx.Response) -> str:
    """Build the post link from the URN returned in the `x-restli-id` header."""
    urn = response.headers.get("x-restli-id", "")
    if not urn:
        try:
            urn = response.json().get("id", "")
        except (ValueError, json.JSONDecodeError):
            urn = ""
    if not urn:
        return "(published, but LinkedIn returned no identifier)"
    return f"https://www.linkedin.com/feed/update/{urn}/"


def publish(text: str, visibility: str = "PUBLIC") -> dict[str, Any]:
    """Publish a text post on the token owner's profile.

    Tries the versioned endpoint and falls back to the legacy one if the app
    lacks access.
    """
    author = member_urn()

    response = httpx.post(
        POSTS_URL,
        headers=_headers(versioned=True),
        json=rest_payload(text, author, visibility),
        timeout=TIMEOUT,
    )

    if response.status_code == 403:
        # The app probably only holds 'Share on LinkedIn'. The legacy endpoint
        # is the one the self-serve page documents, and it takes plain text.
        response = httpx.post(
            UGC_URL,
            headers=_headers(versioned=False),
            json=ugc_payload(text, author, visibility),
            timeout=TIMEOUT,
        )
        endpoint = "/v2/ugcPosts (legacy)"
    else:
        endpoint = "/rest/posts"

    if response.status_code not in (200, 201):
        return {
            "ok": False,
            "endpoint": endpoint,
            "status": response.status_code,
            "error": response.text[:1000],
        }

    return {
        "ok": True,
        "endpoint": endpoint,
        "status": response.status_code,
        "url": _post_url(response),
    }


# ==============================================================================
# Tools exposed to the agents
# ==============================================================================


@tool(requires_confirmation=True)
def publish_post(text: str, visibility: str = "PUBLIC") -> str:
    """Publish a text post on the user's LinkedIn profile.

    This is irreversible and public: the post shows up in the feed immediately.
    The user always approves before it runs.

    Args:
        text: Full post content, already reviewed and ready. Single line breaks
            are preserved. Hashtags written as '#word' become clickable links.
        visibility: 'PUBLIC' (anyone) or 'CONNECTIONS' (connections only).

    Returns:
        JSON with the result and the URL of the published post, or the error.
    """
    try:
        result = publish(text, visibility)
    except MissingConfiguration as error:
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)
    except httpx.HTTPError as error:
        return json.dumps(
            {"ok": False, "error": f"Network failure: {error}"}, ensure_ascii=False
        )
    except RuntimeError as error:
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)
    return json.dumps(result, indent=2, ensure_ascii=False)


@tool
def check_linkedin_connection() -> str:
    """Check whether the LinkedIn token is valid, and whose it is.

    Use it before trying to publish, or when the user asks whether the LinkedIn
    connection is working.

    Returns:
        JSON with the token owner's name, or a description of the problem.
    """
    try:
        data = token_profile()
    except MissingConfiguration as error:
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 401:
            return json.dumps(
                {
                    "ok": False,
                    "error": (
                        "Invalid or expired token. LinkedIn tokens last 60 "
                        "days. Generate another at "
                        "https://www.linkedin.com/developers/tools/oauth/token-generator"
                    ),
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "ok": False,
                "status": error.response.status_code,
                "error": error.response.text[:500],
            },
            ensure_ascii=False,
        )
    except httpx.HTTPError as error:
        return json.dumps(
            {"ok": False, "error": f"Network failure: {error}"}, ensure_ascii=False
        )

    return json.dumps(
        {
            "ok": True,
            "name": data.get("name"),
            "email": data.get("email"),
            "urn": f"urn:li:person:{data.get('sub')}",
        },
        indent=2,
        ensure_ascii=False,
    )
