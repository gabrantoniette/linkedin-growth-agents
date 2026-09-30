"""The Performance Analyst, and the commands that feed it.

No model runs here. What is under test is what the agent is given: the tools
that keep it from doing arithmetic, the rules that keep it from reading a
pattern into three posts, and the gates that stop `linkedin report` before a
model is paid to say there is nothing to read.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from typer.testing import CliRunner

from linkedin_growth import agents, cli, team
from linkedin_growth.agents import analyst, strategist
from linkedin_growth.agents.principles import HONESTY
from tests.test_analytics import make_export


def invoke(*arguments: str):
    return CliRunner().invoke(cli.app, list(arguments))


def instructions_of(agent) -> str:
    return "\n".join(agent.instructions)


@pytest.mark.parametrize(
    "module",
    ["linkedin_growth.analytics", "linkedin_growth.tools.analytics", "linkedin_growth.agents.analyst"],
)
def test_each_entry_point_imports_first_without_a_cycle(module):
    """`analytics` needs the post heading, the analyst needs `analytics`, and
    `agents/__init__` builds every agent: whichever is imported first must work.
    A fresh interpreter, since this process already has them all cached."""
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr


def test_the_analyst_is_part_of_the_team(temp_db, no_api):
    names = [agent.name for agent in agents.all_agents()]

    assert analyst.NAME in names
    assert any(analyst.NAME in line for line in team.build().instructions)


def test_the_analyst_reads_numbers_from_the_summary_tool_and_not_the_raw_csv(temp_db, no_api):
    """The raw CSV would invite it to divide and round on its own."""
    agent = analyst.build()
    tools = {tool.name for tool in agent.tools}

    assert "metrics_summary" in tools
    assert "save_artifact" in tools
    assert "Do not compute a new ratio" in instructions_of(agent)


def test_the_analyst_carries_every_honesty_rule(temp_db, no_api):
    text = instructions_of(analyst.build())

    for rule in HONESTY:
        assert rule in text


def test_the_analyst_is_told_a_small_group_is_not_a_pattern(temp_db, no_api):
    text = instructions_of(analyst.build())

    assert "SMALL SAMPLE" in text
    assert "provisional" in text
    assert "hypothesis" in text


def test_the_analyst_saves_its_report_before_answering(temp_db, no_api):
    text = instructions_of(analyst.build())

    assert "DELIVERY: call `save_artifact` with the path 'performance.md'" in text


def test_the_strategist_starts_from_the_analyst_report(temp_db, no_api):
    text = instructions_of(strategist.build())

    assert "'performance.md'" in text
    assert "CHANGES TO TEST" in text


def test_report_refuses_before_building_the_agent_when_nothing_was_imported(temp_metrics, monkeypatch):
    def forbidden():
        raise AssertionError("the agent must not be built without metrics")

    monkeypatch.setattr(analyst, "build", forbidden)

    result = invoke("report")

    assert result.exit_code == 1
    assert "no metrics to analyze" in result.output


def test_metrics_without_arguments_explains_how_to_export(temp_metrics):
    result = invoke("metrics")

    assert result.exit_code == 0
    assert "Export" in result.output


def test_metrics_imports_every_export_in_a_folder(temp_metrics, tmp_path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    make_export(downloads / "SinglePostAnalytics_a.xlsx")
    make_export(
        downloads / "SinglePostAnalytics_b.xlsx",
        url="https://www.linkedin.com/posts/someone_hello-ugcPost-7000000000000000003-XM0J",
        posted="11/6/2023",
    )

    result = invoke("metrics", str(downloads))

    assert result.exit_code == 0, result.output
    stored = (temp_metrics / "metrics.csv").read_text(encoding="utf-8")
    assert "7000000000000000001" in stored
    assert "7000000000000000003" in stored
    assert "did not match a file" in result.output


def test_metrics_reports_a_bad_file_and_still_imports_the_good_one(temp_metrics, tmp_path):
    good = make_export(tmp_path / "good.xlsx")
    bad = tmp_path / "bad.xlsx"
    bad.write_text("not a spreadsheet", encoding="utf-8")

    result = invoke("metrics", str(bad), str(good))

    assert result.exit_code == 0
    assert "Skipped" in result.output
    assert "7000000000000000001" in (temp_metrics / "metrics.csv").read_text(encoding="utf-8")
