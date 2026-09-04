"""Central configuration: secrets, paths, models and the shared database.

Every module in the system imports from here. If something needs a key, a path
or a model, this is where that gets decided, not scattered around.
"""

from __future__ import annotations

import os
from pathlib import Path

from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.models.anthropic import Claude
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# Paths
# ==============================================================================
# config.py lives in src/linkedin_growth/, so the project root is two levels
# above the package.
ROOT = Path(__file__).resolve().parents[2]

PROFILE_DIR = ROOT / "profile"
EXPORT_DIR = PROFILE_DIR / "linkedin_export"
PROFILE_YAML = PROFILE_DIR / "profile.yaml"
VOICE_MD = PROFILE_DIR / "voice.md"

CONTENT_DIR = ROOT / "content"
CALENDAR_DIR = CONTENT_DIR / "calendar"
POSTS_DIR = CONTENT_DIR / "posts"
METRICS_CSV = CONTENT_DIR / "metrics.csv"

REFERENCES_DIR = ROOT / "references"

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
        REFERENCES_DIR,
        TMP_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# Secrets
# ==============================================================================
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


# ==============================================================================
# Models
# ==============================================================================
# Opus 5 for work that needs judgement (strategy, diagnosis, editing).
# Sonnet 5 for high-volume, more mechanical work (research, first drafts).
MAIN_MODEL = os.getenv("MAIN_MODEL", "claude-opus-5")
FAST_MODEL = os.getenv("FAST_MODEL", "claude-sonnet-5")

# Agno defaults to 8192, and that is too little for this system. These agents
# write a long document and then call `save_artifact` with the whole document
# as an argument. At 8192 the text alone eats the budget: the response is cut
# mid-sentence, the tool call never happens, and the file is never created,
# while the model has already written "report saved". An expensive, silent
# failure.
#
# 16000 is the recommended value for a non-streaming request, which is what
# happens here (`agent.run()`). Opus 5 and Sonnet 5 accept up to 128000, but
# going past this without streaming runs into the SDK's HTTP timeout.
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "16000"))


def model(model_id: str | None = None) -> Claude:
    """Instantiate the Claude model the agents use."""
    return Claude(
        id=model_id or MAIN_MODEL,
        api_key=require_anthropic(),
        max_tokens=MAX_TOKENS,
    )


# ==============================================================================
# Shared database (agent sessions, history and memory)
# ==============================================================================
_db: SqliteDb | None = None


def db() -> SqliteDb:
    """The system's single database. Created on demand so importing touches no disk."""
    global _db
    if _db is None:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        _db = SqliteDb(db_file=str(DB_FILE))
    return _db


# ==============================================================================
# Memory
# ==============================================================================
# The system serves one person, but Agno indexes memory by `user_id`. Without a
# fixed id everything would land in an anonymous bucket and nothing would be
# retrievable, so it exists, and it is configurable for anyone who clones the
# project.
USER_ID = os.getenv("USER_ID", "user")

# The CLI's default conversation. A stable id is what makes today's
# `linkedin chat` continue yesterday's: without it Agno draws a fresh session
# every process and the history starts from zero.
DEFAULT_SESSION = os.getenv("DEFAULT_SESSION", "main")


def agent_session(agent_id: str) -> str:
    """The stable session of a CLI agent.

    Each command (`diagnose`, `strategy`, ...) gets its own, so an agent sees
    its own earlier runs without mixing them with the other agents' or with the
    team's conversation.
    """
    return f"cli-{agent_id}"


_memory: MemoryManager | None = None


def memory() -> MemoryManager:
    """The long-term memory manager, shared by the whole system.

    It runs on the fast model on purpose: distilling one sentence out of what
    was just said is mechanical work, and that call happens at the end of every
    conversation.

    `delete_memories` and `clear_memories` stay off: erasing memory is the
    user's decision, through the `linkedin memory` command, not a model's in the
    middle of a conversation.
    """
    # Late import: `principles` lives inside the `agents` package, whose
    # `__init__` imports the agents, which import this module. At the top of the
    # file this would be a cycle.
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
    """The memory parameters every agent receives, in one place.

    They live here rather than repeated across eight files for the same reason
    the principles live in `principles.py`: when the policy changes, it changes
    in one place.

    The division of labour is deliberate: **the agents read memory, the team
    writes it.** A CLI agent always receives the same canned command, so it
    almost never learns anything new about the user. Extracting memory at the
    end of every run would be one more model call to store nothing. It is in
    conversation, in the `Team`, that the user tells you things.
    """
    return {
        "db": db(),
        "user_id": USER_ID,
        "session_id": agent_session(agent_id),
        "memory_manager": memory(),
        "add_memories_to_context": True,
    }
