# Agno AI Agents Development

A playground project for building and testing AI agents with [agno](https://github.com/agno-agi/agno), paired with the official Agno Agent UI for chatting with them.

## Project structure

```
.
├── src/agno_ai_agents_development/   # Python backend: agno-based agents
│   └── 0.llm-call.py                 # Example agent using Claude Sonnet 4.5
├── agent-ui/                         # Next.js/React chat UI for the agents
├── pyproject.toml                    # Python project config (managed with uv)
└── uv.lock                           # Locked Python dependencies
```

## Backend (Python)

Requirements: Python 3.13+ and [uv](https://docs.astral.sh/uv/).

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create a `.env` file in the project root with your Anthropic API key:

   ```
   CLAUDE_API_KEY=your-api-key-here
   ```

3. Run an example agent:

   ```bash
   uv run src/agno_ai_agents_development/0.llm-call.py
   ```

## Agent UI (frontend)

The `agent-ui` folder contains the official Agno Agent UI, a Next.js chat interface for interacting with agno agents.

```bash
cd agent-ui
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) and point it at your running agent backend.

## Notes

- Never commit your `.env` file or API keys — they are excluded via `.gitignore`.
