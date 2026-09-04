"""What the server has to deliver for the `agent_ui` to work.

The UI builds its "Team" selector from what `GET /teams` returns. When that
route fails, `getTeamsAPI` swallows the error and returns an empty list, so what
reaches the user is not "server error", it is a greyed-out selector reading
"No teams Available", as if the team did not exist.

That is what happened: `Team(mode="coordinate")` with the bare string. It works
at runtime, because `TeamMode` inherits from `str`, but AgentOS serializes the
team with `team.mode.value` and a string has no `.value`. The route answered
500, the UI showed only the agents, and nothing in the terminal said there was
an error.

The tests hit the real app through `TestClient`, with no process and no open
port. It is the only way to catch this class of bug: a field that is only read
when the HTTP response is assembled and nowhere else in the system.
"""

from __future__ import annotations

import pytest
from agno.os import AgentOS
from agno.team.mode import TeamMode
from starlette.testclient import TestClient

from linkedin_growth import agents, flows, team
from linkedin_growth.config import db


@pytest.fixture
def client(temp_db, no_api):
    """AgentOS assembled the way `agentos.py` does, over the throwaway database."""
    agent_os = AgentOS(
        id="linkedin-growth-os-test",
        name="LinkedIn Growth OS",
        db=db(),
        teams=[team.build()],
        agents=agents.all_agents(),
        workflows=flows.all_flows(),
    )
    with TestClient(agent_os.get_app()) as test_client:
        yield test_client


def test_the_team_mode_is_the_enum_and_not_the_string(temp_db, no_api):
    """The bare string passes everything except serialization. Hence the test.

    Because `TeamMode` inherits from `str`, `mode == "coordinate"` stays true
    either way, which makes the bug invisible to any test that compares values.
    What tells them apart is having `.value`.
    """
    crew = team.build()

    assert isinstance(crew.mode, TeamMode)
    assert crew.mode.value == "coordinate"


def test_the_ui_finds_the_team(client):
    """`GET /teams` answers 200 with the team, so the Team selector has content."""
    response = client.get("/teams")

    assert response.status_code == 200, response.text
    teams = response.json()
    assert len(teams) == 1

    payload = teams[0]
    assert payload["id"] == team.ID
    assert payload["name"] == team.NAME
    assert payload["mode"] == "coordinate"
    # The UI reads `entity.id` for the item value and `entity.model` for the
    # label. Either one missing breaks the selector.
    assert payload["model"]["provider"]
    assert len(payload["members"]) == 8


def test_the_ui_finds_the_agents(client):
    """`GET /agents` keeps answering: the regression must not swap sides."""
    response = client.get("/agents")

    assert response.status_code == 200, response.text
    listing = response.json()

    assert len(listing) == 8
    for agent in listing:
        assert agent["id"], agent.get("name")
        assert agent["model"]["model"]
