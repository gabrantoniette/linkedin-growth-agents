"""Central configuration: secrets, paths, models and the shared database.

Every module in the system imports from here. If something needs a key, a path
or a model, this is where that gets decided, not scattered around.
"""

from __future__ import annotations

import os
from pathlib import Path

from typing import TYPE_CHECKING

from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.models.anthropic import Claude
from dotenv import load_dotenv

if TYPE_CHECKING:
    from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
    from agno.knowledge.knowledge import Knowledge
    from agno.vectordb.lancedb import LanceDb

load_dotenv()

# Paths
ROOT = Path(__file__).resolve().parents[2]  # two levels above this package

PROFILE_DIR = ROOT / "profile"
EXPORT_DIR = PROFILE_DIR / "linkedin_export"
PROFILE_YAML = PROFILE_DIR / "profile.yaml"
VOICE_MD = PROFILE_DIR / "voice.md"
BRAND_YAML = PROFILE_DIR / "brand.yaml"  # optional: name, tagline, photo, theme

CONTENT_DIR = ROOT / "content"
CALENDAR_DIR = CONTENT_DIR / "calendar"
POSTS_DIR = CONTENT_DIR / "posts"
METRICS_CSV = CONTENT_DIR / "metrics.csv"
MEDIA_DIR = CONTENT_DIR / "media"  # Post Designer output: PDF, PNGs, video, caption

REFERENCES_DIR = ROOT / "references"
SKILLS_DIR = ROOT / "skills"  # SKILL.md folders, loaded by Agno's `LocalSkills`

TMP_DIR = ROOT / "tmp"
DB_FILE = TMP_DIR / "linkedin_growth.db"


def ensure_directories() -> None:
    """Create the folder tree the system uses. Idempotent."""
    for directory in (
        PROFILE_DIR,
        EXPORT_DIR,
        CONTENT_DIR,
        CALENDAR_DIR,
        POSTS_DIR,
        MEDIA_DIR,
        REFERENCES_DIR,
        TMP_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


# Secrets
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_VERSION = os.getenv("LINKEDIN_VERSION", "202609")


class MissingConfiguration(RuntimeError):
    """A configuration error that comes with instructions for fixing it."""


def require_anthropic() -> str:
    """Return the Anthropic key, or explain how to set it up."""
    if not ANTHROPIC_API_KEY:
        raise MissingConfiguration(
            "ANTHROPIC_API_KEY not found.\n"
            "Create a .env file at the project root with:\n"
            "    ANTHROPIC_API_KEY=sk-ant-...\n"
            "Use .env.example as a starting point."
        )
    return ANTHROPIC_API_KEY


def require_linkedin() -> str:
    """Return the LinkedIn token, or explain how to get one."""
    if not LINKEDIN_ACCESS_TOKEN:
        raise MissingConfiguration(
            "LINKEDIN_ACCESS_TOKEN not found.\n"
            "Generate a token at:\n"
            "    https://www.linkedin.com/developers/tools/oauth/token-generator\n"
            "with the 'w_member_social' scope (the 'Share on LinkedIn' product) "
            "and the 'openid profile' scope.\n"
            "Then put it in .env:\n"
            "    LINKEDIN_ACCESS_TOKEN=...\n"
            "The full walkthrough is in the README, 'Connecting LinkedIn'."
        )
    return LINKEDIN_ACCESS_TOKEN


# Models
# Opus 5: judgement work (strategy, diagnosis, editing). Sonnet 5: mechanical
# work (research, first drafts).
MAIN_MODEL = os.getenv("MAIN_MODEL", "claude-opus-5")
FAST_MODEL = os.getenv("FAST_MODEL", "claude-sonnet-5")

# Agno's 8192 default is too low: agents write a long document, then pass the
# whole thing to `save_artifact`, and get cut off mid-sentence before the tool
# call happens. 16000 is the max recommended for a non-streaming `agent.run()`.
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "16000"))


def model(model_id: str | None = None) -> Claude:
    """Instantiate the Claude model the agents use, with prompt caching on."""
    return Claude(
        id=model_id or MAIN_MODEL,
        api_key=require_anthropic(),
        max_tokens=MAX_TOKENS,
        cache_system_prompt=True,
        request_params={"cache_control": {"type": "ephemeral"}},
    )


# Shared database (agent sessions, history and memory)
# `BaseDb`, not `VectorDb`: this keeps conversation state, the vector db below
# keeps documents for similarity search. Disjoint interfaces, not interchangeable.
_db: SqliteDb | None = None


def db() -> SqliteDb:
    """The system's single database. Created on demand so importing touches no disk."""
    global _db
    if _db is None:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        _db = SqliteDb(db_file=str(DB_FILE))
    return _db


# Embedder
# FastEmbed runs locally (no second API key needed, since Anthropic has no
# embeddings API). Multilingual model on purpose: the corpus mixes pt-BR
# (`content/`, `voice.md`) and English (`references/`). Downloads on first use,
# so the first `linkedin index` takes a couple of minutes.
EMBEDDER_MODEL = os.getenv(
    "EMBEDDER_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
EMBEDDER_DIMENSIONS = int(os.getenv("EMBEDDER_DIMENSIONS", "384"))

_embedder: FastEmbedEmbedder | None = None


def embedder() -> FastEmbedEmbedder:
    """The embedder shared by every knowledge base (mixing models silently
    breaks similarity search, since embeddings are only comparable within
    the same model)."""
    from agno.knowledge.embedder.fastembed import FastEmbedEmbedder

    global _embedder
    if _embedder is None:
        _embedder = FastEmbedEmbedder(
            id=EMBEDDER_MODEL, dimensions=EMBEDDER_DIMENSIONS
        )
    return _embedder


# Vector databases (knowledge retrieval)
# Two tables because `search_type` is fixed per instance: posts use hybrid
# (dedup needs both keyword and vector matches), voice uses pure vector
# (tone matching cares about *how* something sounds, not shared keywords).
LANCEDB_URI = TMP_DIR / "lancedb"

_posts_vector_db: LanceDb | None = None
_voice_vector_db: LanceDb | None = None


def posts_vector_db() -> LanceDb:
    """Published and drafted posts, searched hybrid, for topic deduplication."""
    from agno.vectordb.lancedb import LanceDb, SearchType

    global _posts_vector_db
    if _posts_vector_db is None:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        _posts_vector_db = LanceDb(
            table_name="posts",
            uri=str(LANCEDB_URI),
            search_type=SearchType.hybrid,
            embedder=embedder(),
        )
    return _posts_vector_db


def voice_vector_db() -> LanceDb:
    """The user's past writing, searched by similarity, for tone matching."""
    from agno.vectordb.lancedb import LanceDb, SearchType

    global _voice_vector_db
    if _voice_vector_db is None:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        _voice_vector_db = LanceDb(
            table_name="voice",
            uri=str(LANCEDB_URI),
            search_type=SearchType.vector,
            embedder=embedder(),
        )
    return _voice_vector_db


# Knowledge bases
# `Knowledge` wraps a vector db plus `contents_db`, which tracks what's already
# indexed so re-running `linkedin index` doesn't re-embed everything. `name`
# scopes the `contents_db` rows so both bases can share one SQLite file.
# Built lazily: `Knowledge.__post_init__` creates tables on construction, so
# doing this at import time would create them just by importing the module.
_posts_knowledge: Knowledge | None = None
_voice_knowledge: Knowledge | None = None

POSTS_KNOWLEDGE_NAME = "posts"
VOICE_KNOWLEDGE_NAME = "voice"


def posts_knowledge() -> Knowledge:
    """What has already been written, so the Planner does not repeat a topic."""
    from agno.knowledge.knowledge import Knowledge

    global _posts_knowledge
    if _posts_knowledge is None:
        _posts_knowledge = Knowledge(
            name=POSTS_KNOWLEDGE_NAME,
            description="Posts already drafted or published, for deduplication.",
            vector_db=posts_vector_db(),
            contents_db=db(),
            max_results=5,
        )
    return _posts_knowledge


def voice_knowledge() -> Knowledge:
    """How the user writes, retrieved by topic instead of truncated blindly."""
    from agno.knowledge.knowledge import Knowledge

    global _voice_knowledge
    if _voice_knowledge is None:
        _voice_knowledge = Knowledge(
            name=VOICE_KNOWLEDGE_NAME,
            description="The user's past LinkedIn posts, as a tone sample.",
            vector_db=voice_vector_db(),
            contents_db=db(),
            max_results=5,
        )
    return _voice_knowledge


# Memory
# Single-user system, but Agno indexes memory by `user_id`, so one is fixed
# here (configurable for anyone else who clones the project).
USER_ID = os.getenv("USER_ID", "user")

# Stable id so today's `linkedin chat` continues yesterday's conversation.
DEFAULT_SESSION = os.getenv("DEFAULT_SESSION", "main")


def agent_session(agent_id: str) -> str:
    """Stable per-command session id, so each CLI agent sees its own history
    without mixing it with other agents' or the team's."""
    return f"cli-{agent_id}"


_memory: MemoryManager | None = None


def memory() -> MemoryManager:
    """The long-term memory manager, shared by the whole system. Runs on the
    fast model since distilling a sentence per turn is mechanical work.
    `delete_memories`/`clear_memories` stay off: erasing memory is the user's
    call via `linkedin memory`, not a model's mid-conversation."""
    # Late import to avoid a cycle: `agents/__init__` imports the agents,
    # which import this module.
    from linkedin_growth.agents.principles import memory_instructions

    global _memory
    if _memory is None:
        _memory = MemoryManager(
            db=db(),
            model=model(FAST_MODEL),
            memory_capture_instructions=memory_instructions(),
            add_memories=True,
            update_memories=True,
            delete_memories=False,
            clear_memories=False,
        )
    return _memory


def memory_params(agent_id: str) -> dict[str, object]:
    """Memory parameters every agent receives, in one place so the policy
    changes once instead of in eight files. Agents read memory, only the
    Team writes it: CLI agents run canned commands and rarely learn anything
    new, so extracting memory after each would just be a wasted model call."""
    return {
        "db": db(),
        "user_id": USER_ID,
        "session_id": agent_session(agent_id),
        "memory_manager": memory(),
        "add_memories_to_context": True,
    }
