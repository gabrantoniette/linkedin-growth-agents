"""AgentOS server: exposes the team and the agents to the web interface.

This repository's `agent_ui/` points by default at http://localhost:7777, which
is exactly the default port of `AgentOS.serve`, and localhost:3000 already ships
allowed in Agno's CORS. So: start the server, start the UI, it works.

To run:

    uv run linkedin serve          # this server, on :7777
    cd agent_ui && pnpm dev        # the interface, on :3000

Workflows are registered here and available over HTTP, but `agent_ui` only
knows how to talk to Agents and Teams. Use the CLI for the flows.
"""

from __future__ import annotations

from agno.os import AgentOS

from linkedin_growth import agents, flows, team
from linkedin_growth.config import db, ensure_directories

ensure_directories()

agent_os = AgentOS(
    id="linkedin-growth-os",
    name="LinkedIn Growth OS",
    description=(
        "Multi-agent system for building LinkedIn relevance in AI engineering."
    ),
    db=db(),
    teams=[team.build()],
    agents=agents.all_agents(),
    workflows=flows.all_flows(),
)

app = agent_os.get_app()
