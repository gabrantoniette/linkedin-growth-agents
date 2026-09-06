"""Formatting and payload assembly for the LinkedIn API.

Nothing here makes a request: these are pure functions, tested against the
behaviour the API expects. It is the part of the project most likely to break
silently. A wrong escape raises no exception, it just publishes a post with a
visible `\\#` in the middle of the text.
"""

from __future__ import annotations

import httpx
import pytest

from linkedin_growth.tools.linkedin import (
    LITTLE_RESERVED,
    _post_url,
    escape_little,
    rest_payload,
    to_little,
    ugc_payload,
)

AUTHOR = "urn:li:person:abc123"


# ==============================================================================
# Escaping
# ==============================================================================


@pytest.mark.parametrize("reserved", sorted(LITTLE_RESERVED))
def test_escape_little_escapes_every_reserved_character(reserved: str):
    """LinkedIn's docs are explicit: every reserved character is escaped, always."""
    assert escape_little(reserved) == "\\" + reserved


def test_escape_little_leaves_ordinary_text_alone():
    text = "Construí um agente em Python e ele funcionou."

    assert escape_little(text) == text


def test_escape_little_preserves_accents():
    assert escape_little("programação, ação e manutenção") == "programação, ação e manutenção"


# ==============================================================================
# Hashtags
# ==============================================================================


def test_to_little_turns_a_hashtag_into_a_clickable_template():
    assert to_little("#IA") == "{hashtag|\\#|IA}"


def test_to_little_converts_several_hashtags_mid_text():
    result = to_little("texto antes #IA e #RAG fim")

    assert result == "texto antes {hashtag|\\#|IA} e {hashtag|\\#|RAG} fim"


def test_to_little_accepts_an_accented_hashtag():
    """The posts are in Portuguese: #programação has to become a real hashtag."""
    assert to_little("#programação") == "{hashtag|\\#|programação}"


def test_to_little_does_not_treat_a_hash_glued_to_a_word_as_a_hashtag():
    """'C#' is a language name, not a hashtag. It has to come out escaped."""
    assert to_little("escrevo em C# às vezes") == "escrevo em C\\# às vezes"


def test_to_little_does_not_treat_a_double_hash_as_a_hashtag():
    assert to_little("##IA") == "\\#\\#IA"


def test_to_little_ends_the_hashtag_at_the_underscore():
    """LinkedIn does not accept an underscore in a hashtag, and it is reserved.

    The correct behaviour is for the hashtag to end before the underscore and
    the rest to come out as escaped text.
    """
    assert to_little("#foo_bar") == "{hashtag|\\#|foo}\\_bar"


def test_to_little_escapes_reserved_characters_around_the_hashtag():
    result = to_little("veja (isto) #IA [aqui]")

    assert result == "veja \\(isto\\) {hashtag|\\#|IA} \\[aqui\\]"


# ==============================================================================
# Payloads
# ==============================================================================


def test_rest_payload_uses_little_text_in_commentary():
    payload = rest_payload("post com #IA", AUTHOR)

    assert payload["commentary"] == "post com {hashtag|\\#|IA}"
    assert payload["author"] == AUTHOR
    assert payload["lifecycleState"] == "PUBLISHED"


def test_ugc_payload_uses_plain_text_with_no_escaping():
    """The legacy endpoint does not understand little text: escaping would publish the backslashes."""
    payload = ugc_payload("post com #IA", AUTHOR)

    content = payload["specificContent"]["com.linkedin.ugc.ShareContent"]
    assert content["shareCommentary"]["text"] == "post com #IA"


def test_payloads_respect_the_requested_visibility():
    rest = rest_payload("text", AUTHOR, "CONNECTIONS")
    ugc = ugc_payload("text", AUTHOR, "CONNECTIONS")

    assert rest["visibility"] == "CONNECTIONS"
    assert ugc["visibility"]["com.linkedin.ugc.MemberNetworkVisibility"] == "CONNECTIONS"


# ==============================================================================
# URL of the published post
# ==============================================================================


def test_post_url_uses_the_x_restli_id_header():
    response = httpx.Response(201, headers={"x-restli-id": "urn:li:share:7000"})

    assert _post_url(response) == "https://www.linkedin.com/feed/update/urn:li:share:7000/"


def test_post_url_falls_back_to_the_body_id_when_there_is_no_header():
    response = httpx.Response(201, json={"id": "urn:li:share:8000"})

    assert _post_url(response) == "https://www.linkedin.com/feed/update/urn:li:share:8000/"


def test_post_url_with_no_identifier_says_so_instead_of_building_a_broken_link():
    response = httpx.Response(201, content=b"a response that is not json")

    result = _post_url(response)

    assert "published" in result
    assert "http" not in result
