## Codebase Overview

Nine Agno agents backed by Claude that diagnose a LinkedIn profile, plan and write posts in Brazilian Portuguese, render them as carousels, images or videos, and publish text through LinkedIn's official API. The system runs from a Typer CLI (`uv run linkedin ...`) or through AgentOS with the Next.js chat UI in `agent_ui/`. Behavior rules shared by every agent live in `src/linkedin_growth/agents/principles.py`.

**Stack**: Python 3.13 with uv, Agno 3 (agents, team, workflows, AgentOS on FastAPI), Anthropic Claude, SQLite + LanceDB + local FastEmbed, Playwright/Chromium + Jinja2 + ffmpeg for rendering, Next.js 15 + pnpm for the UI, pytest.

**Structure**: `src/linkedin_growth/` holds config, the CLI, the AgentOS app, the team and workflows, retrieval, and the `agents/`, `profile/`, `tools/` and `studio/` packages. `references/` and `skills/` are knowledge the agents read on demand. Also `tests/`, `agent_ui/` and `docs/`. Personal data and generated output stay in the gitignored `profile/`, `content/` and `tmp/`.

For detailed architecture, see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).
