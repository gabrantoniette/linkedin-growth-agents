"""Reading the LinkedIn data export.

The export is hostile: it comes in English even for an account in another
language, column names change between versions, and some files carry a warning
preamble before the real header. These tests pin down the behaviour that
absorbs that mess. If it breaks, the user's profile comes in empty and every
agent starts writing about nobody.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_growth.profile.importer import (
    _clean_commentary,
    _csv_rows,
    _map_files,
    _normalize,
    _value,
)


# ==============================================================================
# Name normalization
# ==============================================================================


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("Company Name", "companyname"),
        ("First Name", "firstname"),
        ("  ESPAÇO  ", "espao"),
        ("Formação", "formao"),
        ("já-normalizado", "jnormalizado"),
    ],
)
def test_normalize_reduces_to_lowercase_letters_and_digits(given: str, expected: str):
    """Accents go too: that is what lets a column match in both languages."""
    assert _normalize(given) == expected


# ==============================================================================
# Finding a value by column synonym
# ==============================================================================


def test_value_finds_the_column_by_synonym():
    row = {"Company Name": "Acme", "Title": "Dev"}

    assert _value(row, "company name") == "Acme"


def test_value_accepts_different_spellings_of_the_same_synonym():
    """'Company Name', 'companyname' and 'COMPANY  NAME' are the same column."""
    row = {"COMPANY  NAME": "Acme"}

    assert _value(row, "Company Name") == "Acme"


def test_value_ignores_an_empty_cell_and_returns_none():
    assert _value({"Title": "   "}, "title") is None


def test_value_with_a_missing_column_returns_none():
    assert _value({"Other": "x"}, "title") is None


def test_value_uses_the_first_synonym_with_content():
    row = {"Title": "", "Position": "Engineer"}

    assert _value(row, "title", "position") == "Engineer"


# ==============================================================================
# CSV reading
# ==============================================================================


def test_csv_rows_reads_a_header_on_the_first_line(tmp_path: Path):
    path = tmp_path / "Positions.csv"
    path.write_text("Company Name,Title\nAcme,Dev\n", encoding="utf-8")

    rows = _csv_rows(path, ["Company Name"])

    assert rows == [{"Company Name": "Acme", "Title": "Dev"}]


def test_csv_rows_skips_the_linkedin_warning_preamble(tmp_path: Path):
    """Connections.csv is the classic case: warning lines before the header."""
    path = tmp_path / "Connections.csv"
    path.write_text(
        'Notes:\n"A LinkedIn notice about the data"\n\n'
        "First Name,Last Name,Company\nAlex,Rivera,Acme\n",
        encoding="utf-8",
    )

    rows = _csv_rows(path, ["First Name", "Company"])

    assert rows == [{"First Name": "Alex", "Last Name": "Rivera", "Company": "Acme"}]


def test_csv_rows_drops_completely_empty_lines(tmp_path: Path):
    path = tmp_path / "Skills.csv"
    path.write_text("Name\nPython\n\n\nAgno\n", encoding="utf-8")

    rows = _csv_rows(path, ["Name"])

    assert [row["Name"] for row in rows] == ["Python", "Agno"]


def test_csv_rows_with_a_missing_file_returns_an_empty_list(tmp_path: Path):
    """An incomplete export is normal: not everyone has certifications or projects."""
    assert _csv_rows(tmp_path / "DoesNotExist.csv", ["Name"]) == []


def test_csv_rows_reads_a_file_with_a_bom(tmp_path: Path):
    """LinkedIn ships some CSVs as UTF-8 with a BOM."""
    path = tmp_path / "Profile.csv"
    path.write_text("﻿First Name,Headline\nAlex,Engineer\n", encoding="utf-8")

    rows = _csv_rows(path, ["First Name"])

    assert rows == [{"First Name": "Alex", "Headline": "Engineer"}]


# ==============================================================================
# Mapping the export's files
# ==============================================================================


def test_map_files_recognizes_the_known_csvs(tmp_path: Path):
    for name in ("Positions.csv", "Education.csv", "Skills.csv"):
        (tmp_path / name).write_text("a,b\n1,2\n", encoding="utf-8")

    recognized, ignored = _map_files(tmp_path)

    assert set(recognized) == {"experiences", "education", "skills"}
    assert ignored == []


def test_map_files_sends_an_unknown_file_to_ignored(tmp_path: Path):
    (tmp_path / "Connections.csv").write_text("a\n1\n", encoding="utf-8")

    recognized, ignored = _map_files(tmp_path)

    assert recognized == {}
    assert [path.name for path in ignored] == ["Connections.csv"]


def test_map_files_finds_a_csv_in_a_subfolder(tmp_path: Path):
    sub = tmp_path / "Basic_LinkedInDataExport"
    sub.mkdir()
    (sub / "Positions.csv").write_text("a\n1\n", encoding="utf-8")

    recognized, _ = _map_files(tmp_path)

    assert "experiences" in recognized


# ==============================================================================
# The two defects that only showed up with a real export
# ==============================================================================
# Both failed silently: the import finished "successfully", the table of
# recognized files looked right, and the damage only showed in the text the
# agents read. That is the kind of bug a synthetic test does not catch, so this
# block exists to keep it from coming back.


def test_a_file_with_the_member_id_in_its_name_is_recognized(tmp_path: Path):
    """`Shares_1234567890.csv` is the real name; `Shares.csv` is not in the export.

    LinkedIn suffixes some files with the account's numeric id. Without cutting
    the suffix, the past posts are ignored, `voice.md` is never generated, and
    every agent that writes falls back to generic LLM tone, with no warning that
    the user's voice sample was left out.
    """
    (tmp_path / "Shares_1234567890.csv").write_text(
        "Date,ShareCommentary\n2026-01-01,text\n", encoding="utf-8"
    )

    recognized, ignored = _map_files(tmp_path)

    assert "posts" in recognized
    assert recognized["posts"].name == "Shares_1234567890.csv"
    assert ignored == []


def test_the_numeric_suffix_does_not_turn_an_unknown_file_into_a_known_one(
    tmp_path: Path,
):
    """Cutting the suffix must not become a loose match.

    `Comments_1234567890.csv` stays ignored: the cut removes the id, it does not
    bring different names closer together.
    """
    (tmp_path / "Comments_1234567890.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    recognized, ignored = _map_files(tmp_path)

    assert recognized == {}
    assert [path.name for path in ignored] == ["Comments_1234567890.csv"]


def test_a_multiline_quoted_field_arrives_whole(tmp_path: Path):
    """The 'About', each job description and the post text are multiline.

    Splitting the file with `splitlines()` before `csv.reader` cuts inside the
    field: every paragraph becomes a new CSV row and the text arrives scrambled.
    The reader has to receive the whole file.
    """
    (tmp_path / "Positions.csv").write_text(
        "Company Name,Title,Description\n"
        'Acme,Dev,"First line.\n\nSecond line.\n\nThird."\n',
        encoding="utf-8",
    )

    rows = _csv_rows(tmp_path / "Positions.csv", ["Company Name", "Title"])

    assert len(rows) == 1, "the multiline field must not become three records"
    assert rows[0]["Description"] == "First line.\n\nSecond line.\n\nThird."


def test_the_exports_paragraph_break_becomes_a_real_paragraph():
    """In `Shares.csv` each paragraph break comes as quote-newline-quote.

    Without undoing it, `voice.md` is a wall of quotes, which is exactly the
    file meant to teach the agents to write like the user.
    """
    raw = 'Três planilhas. Uma pergunta:"\n""Quantos ainda temos?""\n""\n"E ninguém sabe.'

    assert _clean_commentary(raw) == (
        "Três planilhas. Uma pergunta:\n\n"
        '"Quantos ainda temos?"\n\n'
        "E ninguém sabe."
    )


def test_real_quotes_mid_sentence_survive():
    """The pattern needs the newline between the quotes: an inline quote stands."""
    assert _clean_commentary('Ele disse "não" e saiu.') == 'Ele disse "não" e saiu.'
