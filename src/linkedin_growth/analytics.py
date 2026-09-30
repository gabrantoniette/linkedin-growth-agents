"""Post metrics: import LinkedIn's per-post analytics export and summarize it.

LinkedIn closes self-serve API access to post metrics, but every post's
analytics page has an export button that downloads an .xlsx. This module turns
those files into two tables and computes what the Performance Analyst reads:

- `content/metrics.csv`, one row per post, keyed by the post's id;
- `content/metrics_audience.csv`, who saw each post (job title, seniority...).

The arithmetic lives here and not in a prompt. A model asked to divide 18 by
467 is right most of the time, and a wrong ratio in a report reads exactly like
a right one, so the agent receives the ratios already computed and only reads
them.

Nothing here calls a model or the network.
"""

from __future__ import annotations

import csv
import re
import shutil
import statistics
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

import yaml

from linkedin_growth.config import (
    MEDIA_DIR,
    METRICS_AUDIENCE_CSV,
    METRICS_CSV,
    METRICS_EXPORTS_DIR,
    POSTS_DIR,
)
from linkedin_growth.indexing import front_matter

POST_COLUMNS = [
    "post_id",
    "date",
    "time",
    "url",
    "file",
    "pillar",
    "format",
    "impressions",
    "members_reached",
    "profile_views",
    "followers_gained",
    "engagements",
    "reactions",
    "comments",
    "reposts",
    "saves",
    "sends",
    "link_clicks",
    "relevant_comments",
    "recruiter_contacts",
    "note",
    "imported_on",
]

AUDIENCE_COLUMNS = ["post_id", "category", "value", "percent"]

# What the user fills or corrects by hand. A later import of the same post
# refreshes the numbers and keeps these, so a correction is never undone.
MANUAL_COLUMNS = ("file", "pillar", "format", "relevant_comments", "recruiter_contacts", "note")

# Export label -> column. LinkedIn renamed a few labels between years ("from
# this post" and "from post" both appear), so labels are normalized first.
EXPORT_LABELS = {
    "post url": "url",
    "post date": "date",
    "post publish time": "time",
    "impressions": "impressions",
    "members reached": "members_reached",
    "profile viewers from post": "profile_views",
    "followers gained from post": "followers_gained",
    "social engagements": "engagements",
    "reactions": "reactions",
    "comments": "comments",
    "reposts": "reposts",
    "saves": "saves",
    "sends on linkedin": "sends",
    "link engagements": "link_clicks",
}

PILLAR_NAMES = {
    "built": "Built",
    "construi": "Built",
    "broke": "Broke",
    "quebrei": "Broke",
    "quebrou": "Broke",
    "understood": "Understood",
    "entendi": "Understood",
    "read": "Read",
    "li": "Read",
    "compared": "Compared",
    "comparei": "Compared",
}

# Below this a post's numbers are still moving, so it stays out of comparisons.
PROVISIONAL_DAYS = 7
# Below this a group is an anecdote, and the summary marks it as one.
MIN_GROUP = 3
# How far a post file's date may sit from the publish date and still match.
MATCH_WINDOW_DAYS = 7
MATCH_THRESHOLD = 0.6

_POST_ID = re.compile(r"(?:ugcPost|share|activity)-(\d+)")
_FILE_ID = re.compile(r"_(\d{15,})\.xlsx$", re.IGNORECASE)


@dataclass
class PostExport:
    """One post's analytics export, parsed."""

    row: dict[str, str]
    audience: list[dict[str, str]] = field(default_factory=list)


# ==============================================================================
# Reading the export
# ==============================================================================


def _plain(text: str) -> str:
    """Lowercase ASCII, so 'Decisão' and 'decisao' compare equal."""
    decomposed = unicodedata.normalize("NFKD", text)
    return decomposed.encode("ascii", "ignore").decode("ascii").lower()


def _label(text: str) -> str:
    return " ".join(str(text).lower().replace("from this post", "from post").split())


def _number(value: object) -> str:
    """'1,234' or 1234 -> '1234'. Empty stays empty: absent is not zero."""
    if value is None:
        return ""
    digits = str(value).replace(",", "").strip()
    return digits if digits.isdigit() else ""


def _iso_date(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return datetime.strptime(str(value).strip(), "%m/%d/%Y").date().isoformat()


def _clock(value: object) -> str:
    if value is None or str(value).strip() == "":
        return ""
    return datetime.strptime(str(value).strip(), "%I:%M %p").strftime("%H:%M")


def post_id(url: str, source: Path | None = None) -> str:
    """The post's id, from its URL, or from the export's file name as a fallback."""
    found = _POST_ID.search(url or "")
    if found:
        return found.group(1)
    if source is not None:
        found = _FILE_ID.search(source.name)
        if found:
            return found.group(1)
    return ""


def read_export(path: Path) -> PostExport:
    """Parse a LinkedIn 'Post analytics' .xlsx.

    Raises `ValueError` with a readable message when the file is not one:
    the CLI shows it and moves on to the next file.
    """
    import warnings

    import openpyxl

    try:
        with warnings.catch_warnings():
            # LinkedIn's files carry no default style, and openpyxl says so on
            # every load. Nothing is wrong with the data.
            warnings.simplefilter("ignore")
            book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as error:  # noqa: BLE001 - any failure means "not an export"
        raise ValueError(f"{path.name} is not a readable .xlsx: {error}") from error

    try:
        rows = [tuple(row) for row in book.worksheets[0].iter_rows(values_only=True)]
    finally:
        book.close()

    fields: dict[str, str] = {}
    audience: list[dict[str, str]] = []
    in_demographics = False
    for row in rows:
        name, value, share = (list(row) + [None, None, None])[:3]
        if name is None:
            continue
        label = _label(name)
        if label == "category" and _label(value or "") == "value":
            in_demographics = True
            continue
        if in_demographics:
            percent = str(share or "").strip().rstrip("%").strip()
            audience.append(
                {"category": str(name).strip(), "value": str(value or "").strip(), "percent": percent}
            )
            continue
        column = EXPORT_LABELS.get(label)
        if column:
            fields[column] = value

    if "url" not in fields or "impressions" not in fields:
        raise ValueError(
            f"{path.name} does not look like a LinkedIn post analytics export: "
            "it has no 'Post URL' or 'Impressions' line."
        )

    row = {column: "" for column in POST_COLUMNS}
    row["url"] = str(fields["url"]).strip()
    row["post_id"] = post_id(row["url"], path)
    try:
        row["date"] = _iso_date(fields.get("date"))
        row["time"] = _clock(fields.get("time"))
    except ValueError as error:
        raise ValueError(f"{path.name}: unexpected date or time format ({error}).") from error
    for column in EXPORT_LABELS.values():
        if column not in ("url", "date", "time"):
            row[column] = _number(fields.get(column))

    for entry in audience:
        entry["post_id"] = row["post_id"]
    return PostExport(row=row, audience=audience)


# ==============================================================================
# Matching an export to the post file it came from
# ==============================================================================


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", _plain(text)) if len(token) >= 3}


def _slug(url: str) -> str:
    """The URL slug as words, without the author and the id.

    LinkedIn builds the slug from the document title, the first words of the
    text, or the hashtags, which is what `_handles` collects on the other side.
    """
    path = unquote(url or "").split("/posts/", 1)[-1]
    slug = path.split("_", 1)[-1]
    # The id marker is followed by digits: 'im-happy-to-share-that' is not one.
    return re.split(r"-(?:ugcPost|share|activity)-\d", slug)[0].replace("-", " ")


def _pt_body(post_file: Path) -> str:
    """The pt-BR section of a post file, or empty."""
    # Imported here: `agents/__init__` builds every agent module, and the
    # Performance Analyst imports this module, so a top-level import is a cycle.
    from linkedin_growth.agents.principles import POST_HEADING

    try:
        text = post_file.read_text(encoding="utf-8")
    except OSError:
        return ""
    _, found, rest = text.partition(POST_HEADING["pt"])
    if not found:
        return ""
    return re.split(r"^## ", rest, maxsplit=1, flags=re.MULTILINE)[0]


def first_line(post_file: Path) -> str:
    """The first line of the pt-BR post: the hook the reader saw."""
    return next((line.strip() for line in _pt_body(post_file).splitlines() if line.strip()), "")


def _handles(post_file: Path) -> list[str]:
    """The texts LinkedIn may have built the slug from."""
    lines = [line.strip() for line in _pt_body(post_file).splitlines() if line.strip()]
    handles = lines[:1] + [line for line in lines if re.match(r"#\w", line)]
    for spec in sorted((MEDIA_DIR / post_file.stem).glob("*.yaml")):
        try:
            data = yaml.safe_load(spec.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        if isinstance(data, dict) and data.get("title"):
            handles.append(str(data["title"]))
    return [handle for handle in handles if handle]


def _file_date(post_file: Path) -> date | None:
    try:
        return date.fromisoformat(post_file.name[:10])
    except ValueError:
        return None


def match_post(url: str, published: str) -> Path | None:
    """The post file an export belongs to, or None when nothing fits well.

    A wrong match is worse than none: it pins one post's numbers on another
    post's pillar and hook. So it takes a file dated near the publish date
    whose title, first line or hashtags cover most of the slug, and returns
    None otherwise, leaving the user to fill `file` by hand.
    """
    wanted = _tokens(_slug(url))
    if not wanted or not POSTS_DIR.exists():
        return None
    day = date.fromisoformat(published)

    best: tuple[float, int, str] | None = None
    chosen: Path | None = None
    for candidate in sorted(POSTS_DIR.glob("*.md")):
        dated = _file_date(candidate)
        if dated is None or abs((day - dated).days) > MATCH_WINDOW_DAYS:
            continue
        score = max(
            (len(wanted & _tokens(handle)) / len(wanted) for handle in _handles(candidate)),
            default=0.0,
        )
        rank = (score, -abs((day - dated).days), candidate.name)
        if score >= MATCH_THRESHOLD and (best is None or rank > best):
            best, chosen = rank, candidate
    return chosen


def pillar_of(post_file: Path) -> str:
    """The post's pillar, in the five canonical names, from its front matter."""
    meta = front_matter(post_file)
    # Old posts were labelled in Portuguese, some with a second pillar in
    # parentheses ('Entendi (com prova de Construí)'): the first one counts.
    words = re.findall(r"[a-z]+", _plain(meta.get("pillar") or meta.get("pilar") or ""))
    return next((PILLAR_NAMES[word] for word in words if word in PILLAR_NAMES), "")


def format_of(post_file: Path) -> str:
    """'carousel', 'image' or 'video' as the Designer recorded it, else 'text'."""
    caption = MEDIA_DIR / post_file.stem / "post.md"
    if not caption.exists():
        return "text"
    return front_matter(caption).get("format", "") or "text"


# ==============================================================================
# The CSV files
# ==============================================================================


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, columns: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) or "" for column in columns})


def _chronological(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: (row.get("date") or "", row.get("time") or ""))


def load_rows() -> list[dict[str, str]]:
    """Every post row, oldest first. Rows from before this schema survive."""
    return _chronological(_read_csv(METRICS_CSV))


def load_audience() -> list[dict[str, str]]:
    return _read_csv(METRICS_AUDIENCE_CSV)


def upsert(rows: list[dict[str, str]], new: dict[str, str]) -> list[dict[str, str]]:
    """Insert a post, or refresh its numbers while keeping what the user typed."""
    merged = []
    replaced = False
    for row in rows:
        if new["post_id"] and row.get("post_id") == new["post_id"]:
            fresh = dict(new)
            for column in MANUAL_COLUMNS:
                if row.get(column):
                    fresh[column] = row[column]
            merged.append(fresh)
            replaced = True
        else:
            merged.append(row)
    if not replaced:
        merged.append(new)
    return merged


def import_export(path: Path, today: date | None = None) -> dict[str, str]:
    """Parse one export, match it to its post, and store it. Returns the row.

    The .xlsx is copied into `content/metrics_exports/`: the CSV keeps what
    this schema knows how to read, and the original keeps everything else.
    """
    export = read_export(path)
    row = export.row
    row["imported_on"] = (today or date.today()).isoformat()

    post_file = match_post(row["url"], row["date"])
    if post_file is not None:
        row["file"] = f"posts/{post_file.name}"
        row["pillar"] = pillar_of(post_file)
        row["format"] = format_of(post_file)

    rows = upsert(load_rows(), row)
    _write_csv(METRICS_CSV, POST_COLUMNS, _chronological(rows))

    audience = [entry for entry in load_audience() if entry.get("post_id") != row["post_id"]]
    _write_csv(METRICS_AUDIENCE_CSV, AUDIENCE_COLUMNS, audience + export.audience)

    METRICS_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    archived = METRICS_EXPORTS_DIR / path.name
    if path.resolve() != archived.resolve():
        shutil.copy2(path, archived)

    return next(stored for stored in rows if stored.get("post_id") == row["post_id"])


# ==============================================================================
# The summary the Performance Analyst reads
# ==============================================================================


def _int(value: str | None) -> int | None:
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


def _ratio(part: int | None, whole: int | None, scale: float = 100.0) -> float | None:
    if part is None or not whole:
        return None
    return part / whole * scale


def _show(value: float | int | None, digits: int = 1, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return f"{value}{suffix}"
    return f"{value:.{digits}f}{suffix}"


def _median(values: list[float | int | None]) -> float | None:
    present = [value for value in values if value is not None]
    return statistics.median(present) if present else None


def _age(row: dict[str, str]) -> int | None:
    try:
        return (date.fromisoformat(row["imported_on"]) - date.fromisoformat(row["date"])).days
    except (KeyError, ValueError):
        return None


def _label_of(row: dict[str, str]) -> str:
    if row.get("file"):
        return Path(row["file"]).stem
    return f"(no post file) {_slug(row.get('url', ''))}".strip()


def _weekday(row: dict[str, str]) -> str:
    try:
        return date.fromisoformat(row["date"]).strftime("%a")
    except (KeyError, ValueError):
        return "?"


@dataclass
class _Post:
    row: dict[str, str]

    def get(self, column: str) -> int | None:
        return _int(self.row.get(column))

    @property
    def rate(self) -> float | None:
        return _ratio(self.get("engagements"), self.get("impressions"))

    @property
    def comments_per_k(self) -> float | None:
        return _ratio(self.get("comments"), self.get("impressions"), 1000)

    @property
    def views_per_k(self) -> float | None:
        return _ratio(self.get("profile_views"), self.get("impressions"), 1000)

    @property
    def provisional(self) -> bool:
        age = _age(self.row)
        return age is not None and age < PROVISIONAL_DAYS


def _table(header: list[str], lines: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
        *("| " + " | ".join(line) + " |" for line in lines),
    ]


def _groups(title: str, posts: list[_Post], key) -> list[str]:
    buckets: dict[str, list[_Post]] = defaultdict(list)
    for post in posts:
        buckets[key(post) or "(unknown)"].append(post)
    lines = []
    for name, members in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0])):
        mark = "" if len(members) >= MIN_GROUP else " *"
        lines.append(
            [
                f"{name}{mark}",
                str(len(members)),
                _show(_median([p.get("impressions") for p in members])),
                _show(_median([p.get("members_reached") for p in members])),
                _show(_median([p.rate for p in members]), suffix="%"),
                _show(_median([p.comments_per_k for p in members])),
                str(sum(p.get("comments") or 0 for p in members)),
                str(sum(p.get("profile_views") or 0 for p in members)),
            ]
        )
    return [
        f"### {title}",
        "",
        *_table(
            [
                "group",
                "posts",
                "median impressions",
                "median reached",
                "median eng. rate",
                "median comments / 1k",
                "comments total",
                "profile views total",
            ],
            lines,
        ),
        "",
    ]


def summarize(rows: list[dict[str, str]], audience: list[dict[str, str]]) -> str:
    """Every number the analyst may cite, as markdown. Computed, not estimated."""
    if not rows:
        return (
            "No metrics recorded yet. The user downloads each post's analytics "
            "export (.xlsx) on LinkedIn and imports it with "
            "`uv run linkedin metrics <file.xlsx>`."
        )

    posts = [_Post(row) for row in rows]
    settled = [post for post in posts if not post.provisional]
    made_here = sum(1 for post in posts if post.row.get("file"))

    out = [
        "# Metrics summary",
        "",
        f"Posts: {len(posts)}, from {rows[0].get('date')} to {rows[-1].get('date')}. "
        f"{made_here} made with this system (they have a post file), "
        f"{len(posts) - made_here} without one.",
        "Numbers are as of each row's import date. Engagement rate = social "
        "engagements / impressions, as LinkedIn counts them (reactions, "
        "comments, reposts and saves). 'n/a' means LinkedIn did not report it, "
        "not zero.",
        f"Groups use only posts at least {PROVISIONAL_DAYS} days old at import. "
        f"Groups marked * have fewer than {MIN_GROUP} posts: an observation, "
        "not a pattern.",
        "",
        "## Per post",
        "",
    ]
    out += _table(
        [
            "date",
            "day",
            "time",
            "post",
            "pillar",
            "format",
            "age at import (days)",
            "impressions",
            "reached",
            "eng. rate",
            "reactions",
            "comments",
            "comments / 1k",
            "relevant comments",
            "profile views",
            "profile views / 1k",
            "followers",
            "reposts",
            "saves",
        ],
        [
            [
                post.row.get("date", ""),
                _weekday(post.row),
                post.row.get("time", ""),
                _label_of(post.row) + (" (provisional)" if post.provisional else ""),
                post.row.get("pillar") or "?",
                post.row.get("format") or "?",
                _show(_age(post.row)),
                _show(post.get("impressions")),
                _show(post.get("members_reached")),
                _show(post.rate, suffix="%"),
                _show(post.get("reactions")),
                _show(post.get("comments")),
                _show(post.comments_per_k),
                _show(post.get("relevant_comments")),
                _show(post.get("profile_views")),
                _show(post.views_per_k),
                _show(post.get("followers_gained")),
                _show(post.get("reposts")),
                _show(post.get("saves")),
            ]
            for post in posts
        ],
    )
    out += ["", "## Groups (median per post)", ""]
    out += _groups(
        "By origin",
        settled,
        lambda p: "made with this system" if p.row.get("file") else "before the system",
    )
    out += _groups("By pillar", settled, lambda p: p.row.get("pillar"))
    out += _groups("By format", settled, lambda p: p.row.get("format"))
    out += _groups("By weekday", settled, lambda p: _weekday(p.row))

    weeks: dict[str, list[_Post]] = defaultdict(list)
    for post in posts:
        try:
            year, week, _ = date.fromisoformat(post.row["date"]).isocalendar()
        except (KeyError, ValueError):
            continue
        weeks[f"{year}-W{week:02d}"].append(post)
    out += ["## Per ISO week (only weeks with a post)", ""]
    out += _table(
        ["week", "posts", "impressions", "engagements", "comments", "profile views"],
        [
            [
                week,
                str(len(members)),
                str(sum(p.get("impressions") or 0 for p in members)),
                str(sum(p.get("engagements") or 0 for p in members)),
                str(sum(p.get("comments") or 0 for p in members)),
                str(sum(p.get("profile_views") or 0 for p in members)),
            ]
            for week, members in sorted(weeks.items())
        ],
    )

    hooks = []
    for post in posts:
        stored = post.row.get("file")
        if stored:
            path = POSTS_DIR / Path(stored).name
            hooks.append([post.row.get("date", ""), Path(stored).stem, first_line(path) or "(not found)"])
    if hooks:
        out += ["", "## Hooks (first line of the pt-BR post)", ""]
        out += _table(["date", "post", "first line"], hooks)

    out += ["", *_audience(audience, {row.get("post_id"): row.get("date", "") for row in rows})]
    out += ["## Data gaps", ""]
    out += (_gaps(posts) + _unmeasured(rows)) or ["- none"]
    return "\n".join(out) + "\n"


def _audience(audience: list[dict[str, str]], dates: dict[str | None, str]) -> list[str]:
    entries = [entry for entry in audience if entry.get("post_id") in dates]
    listed = {entry["post_id"] for entry in entries}
    if not entries:
        return ["## Audience", "", "No demographics in the imported exports.", ""]
    out = [
        "## Audience",
        "",
        f"From the {len(listed)} posts whose export lists demographics. LinkedIn "
        "lists only the largest groups, so a value missing from a post means "
        "'not among its largest groups', not zero. 'mean %' averages only the "
        "posts that list the value.",
        "",
    ]
    by_category: dict[str, dict[str, list[tuple[str, float]]]] = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        try:
            share = float(entry.get("percent", "").replace(",", "."))
        except ValueError:
            continue
        by_category[entry["category"]][entry["value"]].append((dates[entry["post_id"]], share))
    for category, values in by_category.items():
        lines = []
        for value, seen in sorted(
            values.items(), key=lambda item: (-len(item[1]), -statistics.mean(s for _, s in item[1]))
        ):
            where = f"{len(seen)} of {len(listed)}"
            # Which posts, when not all: a value only one post reached is
            # read against that post's topic, not against the account.
            if len(seen) < len(listed):
                where += " (" + ", ".join(sorted(day for day, _ in seen)) + ")"
            lines.append([value, _show(statistics.mean(s for _, s in seen)), where])
        out += [f"### {category}", ""]
        out += _table(["value", "mean %", "posts listing it"], lines)
        out.append("")
    return out


def _unmeasured(rows: list[dict[str, str]]) -> list[str]:
    """Post files with no metrics row: not published yet, or not imported.

    Post files keep `status: draft` after publishing, so the file cannot say
    which. Only a rejected post is certainly unpublished, and it is skipped.
    """
    if not POSTS_DIR.exists():
        return []
    measured = {Path(row["file"]).name for row in rows if row.get("file")}
    gaps = []
    for post in sorted(POSTS_DIR.glob("*.md")):
        status = front_matter(post).get("status", "")
        if post.name in measured or status in ("rejected", "reprovado"):
            continue
        gaps.append(
            f"- posts/{post.name} has no metrics row: if it was published, "
            "import its export"
        )
    return gaps


def _gaps(posts: list[_Post]) -> list[str]:
    gaps = []
    for post in posts:
        label = f"{post.row.get('date')} {_label_of(post.row)}"
        missing = [column for column in ("file", "pillar", "format") if not post.row.get(column)]
        if missing:
            gaps.append(f"- {label}: no {', '.join(missing)} (fill them in content/metrics.csv)")
        if post.provisional:
            gaps.append(
                f"- {label}: only {_age(post.row)} days old at import; re-import "
                "its export later for settled numbers"
            )
    # The strategy's main signal, and no export carries it: who commented is
    # something only the user can judge.
    for column in ("relevant_comments", "recruiter_contacts"):
        empty = [post for post in posts if not post.row.get(column)]
        if empty:
            gaps.append(
                f"- {column} is empty on {len(empty)} of {len(posts)} rows: the "
                "export does not carry it, only the user knows it"
            )
    return gaps
