"""Feeds the knowledge bases from the files on disk.

Without this module the knowledge layer is furniture: the agents get a
`search_knowledge_base` tool, call it, and get nothing back, which is worse
than not having the tool at all. Indexing is what makes it real.

Two bases, fed from two places:

- `content/posts/` -> the `posts` base, for "have I written about this?"
- `profile/voice.md` -> the `voice` base, for "how do I sound?"

`references/` is deliberately NOT indexed, `kb-linkedin-publicacao.md` included.
Five files the agent can list and read by name do not need embeddings, and
`tools/references.py` already gives progressive disclosure over them. The big one
has a stronger reason: its section 0 is usage rules and its section 9 is a list of
claims the agent must not make. Retrieval returns the chunks nearest the question,
and "what time should I post on Tuesday?" is near the timing grid and far from
"never present timing as settled fact". A rules document read in halves is worse
than one not read at all.

`profile.yaml` is not indexed either: it goes into every prompt whole through
`profile/context.py`, where nothing can fail to retrieve it.

Re-running is safe and cheap, but not incremental: every file is re-embedded on
each run (about 17 seconds for three files). `upsert=True` is what buys the
safety, because it makes the indexed state match the file even when a post was
edited in place, which happens whenever the Editor rewrites a rejected draft.

Agno does offer `skip_if_exists=True`, which skips by content hash. It is not
used here: `upsert` is documented as "only used when skip_if_exists=False", so
skipping would take the non-upsert path for a file that DID change, and the old
chunks of that post would likely survive next to the new ones. A stale index is a
worse failure than a slow one. Worth revisiting with a test that proves the old
chunks are replaced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from linkedin_growth.config import (
    POSTS_DIR,
    VOICE_MD,
    posts_knowledge,
    posts_vector_db,
    voice_knowledge,
    voice_vector_db,
)

if TYPE_CHECKING:
    from agno.knowledge.reader.markdown_reader import MarkdownReader

# Chunk sizes are bounded by the embedder, not by taste. The multilingual model
# truncates at 512 tokens, and Portuguese runs about 4 characters per token, so
# anything past ~2000 characters is embedded silently incomplete. 1500 leaves
# room for the tokenizer to disagree with that estimate.
POST_CHUNK_SIZE = 1500

# Voice chunks are smaller because the unit that matters is one past post, and
# in `voice.md` those run 500 to 900 characters under their own `##` heading. A
# bigger chunk would glue two unrelated posts into one tone sample.
VOICE_CHUNK_SIZE = 1000


@dataclass
class IndexReport:
    """What one indexing run did, for the CLI to print."""

    posts: int = 0
    voice: int = 0
    skipped: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.posts + self.voice


def _reader(chunk_size: int) -> MarkdownReader:
    """A markdown reader that chunks on document structure, not on byte counts.

    `MarkdownChunking` splits on headings, so a chunk tends to be a whole
    section instead of a sentence cut in half at character 1500.
    """
    from agno.knowledge.reader.markdown_reader import MarkdownReader

    return MarkdownReader(chunk_size=chunk_size)


def _front_matter(path: Path) -> dict[str, str]:
    """Pull the YAML front matter out of a post, or return empty.

    The metadata is worth carrying: it lands in the indexed payload, so the
    Planner sees a hit's `pilar` and `status` without opening the file. A post
    that was rejected still occupies its topic, but the Planner should know it
    can be rewritten rather than treated as published.

    Never raises. A malformed post should not stop the whole index.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---")
    raw, sep, _ = rest.partition("---")
    if not sep:
        return {}
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    # Vector metadata has to survive a JSON round-trip, and dates come back
    # from YAML as `datetime.date`.
    return {str(k): str(v) for k, v in data.items()}


def index_posts(recreate: bool = False) -> tuple[int, list[str]]:
    """Index `content/posts/*.md`. Returns how many were indexed and what failed."""
    if recreate:
        posts_vector_db().drop()

    knowledge = posts_knowledge()
    reader = _reader(POST_CHUNK_SIZE)

    indexed = 0
    skipped: list[str] = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        metadata = _front_matter(path)
        metadata["source"] = "post"
        metadata["file"] = f"posts/{path.name}"
        try:
            knowledge.insert(
                name=path.stem,
                path=str(path),
                metadata=metadata,
                reader=reader,
                upsert=True,
            )
            indexed += 1
        except Exception as error:  # noqa: BLE001 - one bad file must not stop the run
            skipped.append(f"{path.name}: {error}")
    return indexed, skipped


def index_voice(recreate: bool = False) -> tuple[int, list[str]]:
    """Index `profile/voice.md`. Returns how many files were indexed and what failed."""
    if recreate:
        voice_vector_db().drop()

    if not VOICE_MD.exists():
        return 0, ["profile/voice.md does not exist yet. Run `linkedin import` first."]

    try:
        voice_knowledge().insert(
            name="voice",
            path=str(VOICE_MD),
            metadata={"source": "voice"},
            reader=_reader(VOICE_CHUNK_SIZE),
            upsert=True,
        )
    except Exception as error:  # noqa: BLE001
        return 0, [f"voice.md: {error}"]
    return 1, []


def index_all(recreate: bool = False) -> IndexReport:
    """Index everything. `recreate` drops the tables first, for a clean rebuild.

    Use `recreate` when the embedder changes: vectors from two different models
    are not comparable, and mixing them returns nonsense instead of an error.
    """
    report = IndexReport()
    report.posts, posts_skipped = index_posts(recreate=recreate)
    report.voice, voice_skipped = index_voice(recreate=recreate)
    report.skipped = [*posts_skipped, *voice_skipped]
    return report
