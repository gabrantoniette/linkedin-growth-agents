"""Servidor AgentOS — expõe o time e os agentes para a interface web.

A `agent_ui/` deste repositório aponta por padrão para `http://localhost:7777`,
que é exatamente a porta padrão do `AgentOS.serve`, e `localhost:3000` já vem
liberado no CORS do Agno. Ou seja: sobe o servidor, sobe a UI, funciona.

Para rodar:

    uv run linkedin serve          # este servidor, em :7777
    cd agent_ui && pnpm dev        # a interface, em :3000

Os Workflows são registrados aqui e ficam disponíveis por HTTP, mas a `agent_ui`
só sabe conversar com Agents e Teams — use a CLI para os fluxos.
"""

from __future__ import annotations

from agno.os import AgentOS

from linkedin_growth import agentes, fluxos, times
from linkedin_growth.config import db, garantir_diretorios

garantir_diretorios()

agent_os = AgentOS(
    id="linkedin-growth-os",
    name="LinkedIn Growth OS",
    description=(
        "Sistema multiagente para construir relevância no LinkedIn em "
        "engenharia de IA."
    ),
    db=db(),
    teams=[times.construir()],
    agents=agentes.todos(),
    workflows=fluxos.todos(),
)

app = agent_os.get_app()
