"""What must never reach a public asset: secrets, private pages, LinkedIn itself.

A document post can be downloaded by anyone who sees it, so a key drawn into a
code slide is a key published. These tests pin the redaction on both sides:
real credentials are masked, and code that only talks about secrets stays
readable, because masking that made converted source files useless.
"""

from __future__ import annotations

import pytest

from linkedin_growth.studio.safety import check_url, confine, redact_secrets, slugify, valid_slug

MASK = "••••••••"


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ('ANTHROPIC_API_KEY="sk-ant-api03-abcdefghijklmnop1234"', "Anthropic key"),
        ("export OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwx", "OpenAI key"),
        ("token = ghp_" + "a1" * 18, "GitHub token"),
        ("aws_access_key_id = AKIAIOSFODNN7EXAMPLE", "AWS access key"),
        ("DB_PASSWORD=hunter22", "value of DB_PASSWORD"),
        ("postgres://app:s3cr3t@db:5432/app", "password in a connection URL"),
    ],
)
def test_credentials_are_masked_before_anything_is_drawn(text, kind):
    cleaned, found = redact_secrets(text)

    assert kind in found
    assert MASK in cleaned


@pytest.mark.parametrize(
    "text",
    [
        "token: str = Field(default=None)",
        "_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [",
        'password = os.getenv("DB_PASSWORD")',
        "author: Gabriel",
        "max_tokens = 16000",
    ],
)
def test_code_that_only_talks_about_secrets_stays_readable(text):
    assert redact_secrets(text) == (text, [])


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("https://www.linkedin.com/in/someone", "LinkedIn"),
        ("https://lnkd.in/abc", "LinkedIn"),
        ("http://localhost:7777/agents", "local"),
        ("http://127.0.0.1:8000", "private or loopback"),
        ("http://192.168.0.1", "private"),
        ("http://printer.local/status", "local"),
        ("file:///C:/Users/secret.txt", "only http and https"),
        ("https://user:pass@example.org", "credentials"),
    ],
)
def test_urls_that_must_never_be_captured_are_refused_with_the_reason(url, reason):
    problem = check_url(url, resolve=False)

    assert problem is not None
    assert reason in problem


def test_a_public_page_is_allowed():
    assert check_url("https://github.com/agno-agi/agno", resolve=False) is None


def test_confine_refuses_a_path_that_escapes(tmp_path):
    assert confine(tmp_path, "../outside.txt") is None
    assert confine(tmp_path, "inside/file.txt") == (tmp_path / "inside" / "file.txt").resolve()


@pytest.mark.parametrize(
    ("slug", "valid"),
    [
        ("2026-09-04-rag", True),
        ("Com-Maiuscula", False),
        ("../escape", False),
        ("", False),
        ("-hifen-na-frente", False),
    ],
)
def test_a_media_folder_name_is_a_plain_slug(slug, valid):
    assert valid_slug(slug) is valid


def test_slugify_strips_accents_and_punctuation():
    assert slugify("Notas de Estudo (RAG).md") == "notas-de-estudo-rag-md"
    assert slugify("Configuração") == "configuracao"
    assert slugify("???") == "media"
