"""Importing LinkedIn's post analytics export, and the numbers computed from it.

The exports here are built in the test, in the layout LinkedIn downloads. The
user's real files never enter the repository: they are personal data, and a
test that depends on them breaks on anyone else's machine.

What matters most:

- absent is not zero. Old exports have no 'Members reached'; recording 0 would
  tell the analyst the post reached nobody;
- a correction the user typed survives the next import of the same post;
- a wrong match is worse than none, since it pins one post's numbers on another
  post's pillar and hook;
- every ratio the analyst cites is computed here, so it is tested here.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import openpyxl
import pytest

from linkedin_growth import analytics
from linkedin_growth.indexing import front_matter
from linkedin_growth.tools.analytics import metrics_summary
from tests.conftest import call

URL = (
    "https://www.linkedin.com/posts/someone_escolher-o-%C3%ADndice-ou-o-pre%C3%A7o-"
    "ugcPost-7000000000000000001-AbCd"
)


def make_export(
    path: Path,
    *,
    url: str = URL,
    posted: str = "9/16/2026",
    clock: str = "12:52 PM",
    impressions: str = "182",
    reached: str | None = "95",
    comments: str = "1",
    engagements: str = "3",
    profile_label: str = "Profile viewers from this post",
    demographics: list[tuple[str, str, str]] | None = None,
) -> Path:
    """Write an .xlsx in the layout of LinkedIn's 'Post analytics' export."""
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Post analytics"
    lines: list[tuple] = [
        ("Post URL", url),
        ("Post Date", posted),
        ("Post Publish Time", clock),
        ("Discovery", None),
        ("Impressions", impressions),
    ]
    if reached is not None:
        lines.append(("Members reached", reached))
    lines += [
        ("Profile activity", None),
        (profile_label, "2"),
        ("Followers gained from this post", "0"),
        ("Engagement", None),
        ("Social engagements", engagements),
        ("Reactions", "2"),
        ("Comments", comments),
        ("Reposts", "0"),
        ("Saves", "0"),
        ("Sends on LinkedIn", "0"),
        ("Link engagements", "0"),
        ("Premium custom button engagements", "0"),
        ("Post viewer demographics", None),
        ("Category", "Value", "%"),
        *(demographics or []),
    ]
    for line in lines:
        sheet.append(list(line))
    book.save(path)
    return path


def write_post(content: Path, name: str, *, pillar: str = "Broke", first: str = "Primeira linha.", hashtags: str = "#IA #RAG") -> Path:
    post = content / "posts" / name
    post.write_text(
        f"---\ndate: {name[:10]}\npillar: {pillar}\n---\n\n"
        f"## Post (pt-BR)\n\n{first}\n\nCorpo.\n\n{hashtags}\n\n## Post (en)\n\nFirst.\n",
        encoding="utf-8",
    )
    return post


def write_media(content: Path, stem: str, *, fmt: str = "carousel", title: str | None = None) -> None:
    folder = content / "media" / stem
    folder.mkdir(parents=True)
    (folder / "post.md").write_text(f"---\nformat: {fmt}\n---\n\n## Caption (pt-BR)\n\nTexto.\n", encoding="utf-8")
    if title:
        (folder / f"{fmt}.yaml").write_text(f"title: {title}\nslides: []\n", encoding="utf-8")


# ==============================================================================
# Reading the export
# ==============================================================================


def test_read_export_turns_the_sheet_into_one_row(tmp_path):
    export = analytics.read_export(make_export(tmp_path / "a.xlsx"))

    row = export.row
    assert row["post_id"] == "7000000000000000001"
    assert row["date"] == "2026-09-16"
    assert row["time"] == "12:52"
    assert row["impressions"] == "182"
    assert row["members_reached"] == "95"
    assert row["profile_views"] == "2"
    assert row["engagements"] == "3"


def test_an_old_export_without_reach_records_it_as_absent_not_zero(tmp_path):
    """2023 exports have no 'Members reached'. Zero would mean 'reached nobody'."""
    export = analytics.read_export(make_export(tmp_path / "old.xlsx", reached=None))

    assert export.row["members_reached"] == ""


def test_both_spellings_of_the_profile_viewers_label_are_read(tmp_path):
    """LinkedIn wrote 'from this post' in some years and 'from post' in others."""
    export = analytics.read_export(
        make_export(tmp_path / "a.xlsx", profile_label="Profile viewers from post")
    )

    assert export.row["profile_views"] == "2"


def test_demographics_become_audience_rows_with_the_percent_sign_stripped(tmp_path):
    export = analytics.read_export(
        make_export(
            tmp_path / "a.xlsx",
            demographics=[("Job title", "Data Engineer", "6%"), ("Seniority", "Entry", "43%")],
        )
    )

    assert export.audience == [
        {"category": "Job title", "value": "Data Engineer", "percent": "6", "post_id": "7000000000000000001"},
        {"category": "Seniority", "value": "Entry", "percent": "43", "post_id": "7000000000000000001"},
    ]


def test_a_spreadsheet_that_is_not_an_export_is_refused_with_a_reason(tmp_path):
    book = openpyxl.Workbook()
    book.active.append(["Name", "Value"])
    book.save(tmp_path / "budget.xlsx")

    with pytest.raises(ValueError, match="does not look like a LinkedIn post analytics export"):
        analytics.read_export(tmp_path / "budget.xlsx")


def test_a_file_that_is_not_a_spreadsheet_is_refused_with_a_reason(tmp_path):
    fake = tmp_path / "notes.xlsx"
    fake.write_text("not a zip", encoding="utf-8")

    with pytest.raises(ValueError, match="not a readable .xlsx"):
        analytics.read_export(fake)


def test_the_post_id_falls_back_to_the_file_name_when_the_url_has_none():
    source = Path("SinglePostAnalytics_Someone_7000000000000000005.xlsx")

    assert analytics.post_id("https://www.linkedin.com/feed/", source) == "7000000000000000005"


# ==============================================================================
# Matching an export to its post file
# ==============================================================================


def test_a_document_post_matches_the_file_whose_carousel_title_is_the_slug(temp_metrics):
    write_post(temp_metrics, "2026-09-16-escolher-o-indice.md", first="Troquei o índice do banco.")
    write_media(temp_metrics, "2026-09-16-escolher-o-indice", title="Escolher o índice ou o preço")
    write_post(temp_metrics, "2026-09-15-pedir-nao-e-garantir.md", first="Pedi um texto.")

    match = analytics.match_post(URL, "2026-09-16")

    assert match is not None and match.name == "2026-09-16-escolher-o-indice.md"


def test_hashtags_pick_the_right_draft_among_several_on_the_same_day(temp_metrics):
    """Three drafts of one workshop post, one published: its hashtags are the slug."""
    url = "https://www.linkedin.com/posts/someone_agentesdeia-engenhariadeia-ianobrasil-share-7000000000000000002-7o5K"
    write_post(temp_metrics, "2026-09-14-workshop-a.md", hashtags="#AgentesDeIA #EngenhariaDeIA #QualidadeDeDados")
    write_post(temp_metrics, "2026-09-14-workshop-b.md", hashtags="#AgentesDeIA #EngenhariaDeIA #IANoBrasil")

    match = analytics.match_post(url, "2026-09-14")

    assert match is not None and match.name == "2026-09-14-workshop-b.md"


def test_the_word_share_in_a_slug_is_not_mistaken_for_the_id_marker(temp_metrics):
    """'im-happy-to-share-that...' was cut at 'share', losing the rest of the slug."""
    url = "https://www.linkedin.com/posts/someone_im-happy-to-share-that-im-starting-a-new-ugcPost-7000000000000000004-IX2C"

    summary = analytics.summarize([row(post_id="1", date="2024-02-20", url=url)], [])

    assert "im happy to share that im starting a new" in summary


def test_a_post_file_outside_the_date_window_never_matches(temp_metrics):
    write_post(temp_metrics, "2026-07-01-escolher-o-indice.md", first="Escolher o índice ou o preço")

    assert analytics.match_post(URL, "2026-09-16") is None


def test_a_weak_overlap_is_not_a_match(temp_metrics):
    """Sharing one word with the slug is chance, not the same post."""
    write_post(temp_metrics, "2026-09-16-outro.md", first="Um preço justo para o banco.")

    assert analytics.match_post(URL, "2026-09-16") is None


@pytest.mark.parametrize(
    ("label", "pillar"),
    [
        ("Entendi (com prova de Construí)", "Understood"),  # the first pillar counts
        ("Quebrou", "Broke"),  # the strategy's spelling
        ("Built", "Built"),
    ],
)
def test_the_pillar_is_read_in_english_or_portuguese(temp_metrics, label, pillar):
    post = write_post(temp_metrics, "2026-09-04-halcyon.md", pillar=label)

    assert analytics.pillar_of(post) == pillar


def test_the_format_comes_from_the_designer_caption_and_defaults_to_text(temp_metrics):
    carousel = write_post(temp_metrics, "2026-09-16-a.md")
    write_media(temp_metrics, "2026-09-16-a", fmt="carousel")
    plain = write_post(temp_metrics, "2026-09-17-b.md")

    assert analytics.format_of(carousel) == "carousel"
    assert analytics.format_of(plain) == "text"


def test_front_matter_survives_an_unquoted_colon_in_a_value(tmp_path):
    """'topic: Workshop: adoção' is invalid YAML and silently dropped every field."""
    post = tmp_path / "post.md"
    post.write_text("---\ndate: 2026-09-14\npillar: Read\ntopic: Workshop: adoção\n---\n\nText.\n", encoding="utf-8")

    meta = front_matter(post)

    assert meta["pillar"] == "Read"
    assert meta["topic"] == "Workshop: adoção"


# ==============================================================================
# Storing
# ==============================================================================


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_import_fills_the_row_from_the_matched_post_and_archives_the_file(temp_metrics, tmp_path):
    write_post(temp_metrics, "2026-09-16-escolher-o-indice.md", pillar="Broke")
    write_media(temp_metrics, "2026-09-16-escolher-o-indice", title="Escolher o índice ou o preço")
    export = make_export(tmp_path / "SinglePostAnalytics_x.xlsx")

    row = analytics.import_export(export, today=date(2026, 9, 30))

    assert row["file"] == "posts/2026-09-16-escolher-o-indice.md"
    assert row["pillar"] == "Broke"
    assert row["format"] == "carousel"
    assert row["imported_on"] == "2026-09-30"
    assert (temp_metrics / "metrics_exports" / export.name).exists()
    assert read_rows(temp_metrics / "metrics.csv")[0]["impressions"] == "182"


def test_reimporting_refreshes_the_numbers_and_keeps_what_the_user_typed(temp_metrics, tmp_path):
    """The user fixes a pillar and adds recruiter contacts; the next export must not undo that."""
    analytics.import_export(make_export(tmp_path / "first.xlsx", impressions="182"), today=date(2026, 9, 20))
    rows = read_rows(temp_metrics / "metrics.csv")
    rows[0].update(pillar="Broke", relevant_comments="1", recruiter_contacts="1", note="shared by a recruiter")
    with (temp_metrics / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=analytics.POST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    analytics.import_export(make_export(tmp_path / "later.xlsx", impressions="240"), today=date(2026, 9, 30))

    stored = read_rows(temp_metrics / "metrics.csv")
    assert len(stored) == 1
    assert stored[0]["impressions"] == "240"
    assert stored[0]["imported_on"] == "2026-09-30"
    kept = ("pillar", "relevant_comments", "recruiter_contacts", "note")
    assert [stored[0][column] for column in kept] == ["Broke", "1", "1", "shared by a recruiter"]


def test_reimporting_replaces_the_audience_instead_of_piling_it_up(temp_metrics, tmp_path):
    first = make_export(tmp_path / "a.xlsx", demographics=[("Seniority", "Entry", "40%")])
    second = make_export(tmp_path / "b.xlsx", demographics=[("Seniority", "Entry", "43%")])

    analytics.import_export(first)
    analytics.import_export(second)

    audience = read_rows(temp_metrics / "metrics_audience.csv")
    assert [(entry["value"], entry["percent"]) for entry in audience] == [("Entry", "43")]


def test_rows_typed_under_the_old_schema_survive_an_import(temp_metrics, tmp_path):
    """Before the export import, `linkedin metrics` asked for numbers by hand."""
    (temp_metrics / "metrics.csv").write_text(
        "date,file,pillar,impressions,reactions,comments,profile_views,recruiter_contacts,note\n"
        "2026-09-01,posts/old.md,Built,300,10,2,3,0,typed by hand\n",
        encoding="utf-8",
    )

    analytics.import_export(make_export(tmp_path / "a.xlsx"))

    stored = read_rows(temp_metrics / "metrics.csv")
    assert [row["note"] for row in stored] == ["typed by hand", ""]


# ==============================================================================
# The summary the analyst reads
# ==============================================================================


def row(**values: str) -> dict[str, str]:
    base = {column: "" for column in analytics.POST_COLUMNS}
    base.update(imported_on="2026-09-30", engagements="0", comments="0", profile_views="0")
    base.update(values)
    return base


def test_the_summary_computes_the_ratios_the_analyst_cites():
    summary = analytics.summarize(
        [row(post_id="1", date="2026-09-14", impressions="467", members_reached="193", engagements="18", comments="7", profile_views="4")],
        [],
    )

    assert "| 467 | 193 | 3.9% |" in summary  # 18 / 467
    assert "| 7 | 15.0 |" in summary  # 7 comments per 467 impressions, per 1k


def test_the_summary_says_n_a_where_linkedin_reported_nothing():
    summary = analytics.summarize([row(post_id="1", date="2023-11-06", impressions="484")], [])

    assert "| 484 | n/a |" in summary


def test_a_young_post_is_flagged_and_kept_out_of_the_groups():
    summary = analytics.summarize(
        [
            row(post_id="1", date="2026-09-16", impressions="182", format="carousel"),
            row(post_id="2", date="2026-09-28", impressions="90", format="image"),
        ],
        [],
    )

    assert "(provisional)" in summary
    assert "only 2 days old at import" in summary
    by_format = summary.split("### By format", 1)[1].split("###", 1)[0]
    assert "carousel" in by_format
    assert "image" not in by_format


def test_a_group_smaller_than_the_minimum_is_marked_as_an_observation():
    summary = analytics.summarize([row(post_id="1", date="2026-09-16", impressions="182", pillar="Broke")], [])

    assert "| Broke * | 1 |" in summary


def test_the_audience_averages_only_the_posts_that_list_a_value():
    rows = [row(post_id="1", date="2026-09-14"), row(post_id="2", date="2026-09-16")]
    audience = [
        {"post_id": "1", "category": "Seniority", "value": "Entry", "percent": "36"},
        {"post_id": "2", "category": "Seniority", "value": "Entry", "percent": "44"},
        {"post_id": "2", "category": "Seniority", "value": "Manager", "percent": "8"},
    ]

    summary = analytics.summarize(rows, audience)

    assert "| Entry | 40.0 | 2 of 2 |" in summary
    assert "| Manager | 8.0 | 1 of 2 (2026-09-16) |" in summary


def test_a_post_file_without_a_metrics_row_is_listed_unless_it_was_rejected(temp_metrics):
    """A post file keeps `status: draft` after publishing, so only a row says it was measured."""
    write_post(temp_metrics, "2026-09-15-pedir.md")
    rejected = temp_metrics / "posts" / "2026-09-04-custo.md"
    rejected.write_text("---\nstatus: reprovado\n---\n\n## Avaliação\n", encoding="utf-8")

    summary = analytics.summarize([row(post_id="1", date="2026-09-16")], [])

    assert "posts/2026-09-15-pedir.md has no metrics row" in summary
    assert "2026-09-04-custo.md" not in summary


def test_the_tool_explains_how_to_import_when_nothing_was_imported(temp_metrics):
    result = call(metrics_summary)

    assert "No metrics recorded yet" in result
    assert "uv run linkedin metrics" in result
