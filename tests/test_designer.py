"""The Post Designer: what it is told, what it can reach, what it refuses.

Like the other agent tests, these read what reaches the model rather than the
source of the agent file: an instruction that is written but never assembled
into the prompt does not exist.
"""

from __future__ import annotations

import re
import textwrap

from agno.skills.validator import validate_skill_directory

from linkedin_growth import config, team
from linkedin_growth.agents import designer
from linkedin_growth.agents.principles import DESIGN_RULES, HONESTY, PLATFORM_LIMITS
from linkedin_growth.studio.spec import LAYOUTS, parse_spec

from .conftest import SpyModel

LAYOUTS_REFERENCE = config.SKILLS_DIR / "carousel-design" / "references" / "layouts.md"


def instructions_of(agent) -> str:
    return " ".join(str(item) for item in (agent.instructions or []))


# ==============================================================================
# Skills
# ==============================================================================


def test_every_skill_the_designer_names_exists_and_passes_the_spec():
    """An invalid SKILL.md raises when the agent is built, which takes the server down."""
    for name in designer.SKILL_NAMES:
        folder = config.SKILLS_DIR / name
        assert (folder / "SKILL.md").is_file(), name
        assert validate_skill_directory(folder) == [], name


def test_the_skills_on_disk_are_exactly_the_ones_the_designer_names():
    on_disk = {path.name for path in config.SKILLS_DIR.iterdir() if (path / "SKILL.md").is_file()}

    assert on_disk == set(designer.SKILL_NAMES)


def test_the_instructions_name_every_skill(temp_db, no_api):
    text = instructions_of(designer.build())

    for name in designer.SKILL_NAMES:
        assert f"'{name}'" in text, name


def test_skills_are_passed_natively_and_reach_the_system_prompt(temp_db, no_api):
    """Agno puts the skill summaries in the prompt and adds the skill tools itself.

    Checked on the messages the model receives: that is where a hand-wired copy
    of the skill tools would collide with Agno's, and where a missing wiring
    would show up as an agent that never heard of its skills.
    """
    agent = designer.build()
    assert set(agent.skills.get_skill_names()) == set(designer.SKILL_NAMES)

    spy: SpyModel = agent.model  # type: ignore[assignment]
    agent.run("Desenhe o post posts/exemplo.md")

    prompt = spy.call_text(0)
    assert "<skills_system>" in prompt
    assert "carousel-design" in prompt


def test_every_layout_the_skill_documents_is_one_the_studio_renders():
    documented = set(re.findall(r"^## (\w+)$", LAYOUTS_REFERENCE.read_text(encoding="utf-8"), re.MULTILINE))

    assert documented == set(LAYOUTS)


def test_the_examples_in_the_layout_reference_are_valid_specs():
    """The agent copies these shapes; an invalid example teaches an invalid spec."""
    blocks = re.findall(r"```yaml\n(.*?)```", LAYOUTS_REFERENCE.read_text(encoding="utf-8"), re.DOTALL)
    assert len(blocks) == len(LAYOUTS)

    for block in blocks:
        spec, problems = parse_spec("title: Exemplo\nslides:\n" + textwrap.indent(block, "  "), "carousel")
        assert spec is not None and problems == [], (block, problems)


def test_the_references_the_designer_and_its_skills_cite_exist():
    assert (config.REFERENCES_DIR / "kb-visual-formats.md").is_file()
    assert (LAYOUTS_REFERENCE.parent / "review-checklist.md").is_file()
    assert (config.SKILLS_DIR / "post-copy" / "references" / "cross-platform.md").is_file()


# ==============================================================================
# Rules
# ==============================================================================


def test_the_designer_receives_the_honesty_design_and_voice_rules(temp_db, no_api):
    text = instructions_of(designer.build())

    for rule in (*HONESTY, *DESIGN_RULES):
        assert rule in text
    assert "NEVER use an em dash" in text


def test_the_honesty_rule_covers_visual_proof():
    """A screenshot of output that never ran is the visual version of an invented number."""
    assert any("Never fabricate visual proof" in rule for rule in HONESTY)


def test_the_designer_never_writes_a_publishable_heading_into_a_caption(temp_db, no_api):
    """`linkedin publish` sends what is under '## Post (pt-BR)', without the PDF."""
    assert "Never use the heading '## Post (pt-BR)'" in instructions_of(designer.build())


def test_the_platform_rule_says_media_is_produced_but_published_by_hand():
    rule = next(item for item in PLATFORM_LIMITS if "Post Designer" in item)

    assert "by hand" in rule
    assert "`linkedin publish`" in rule


def test_contact_sheets_stay_out_of_the_session_database(temp_db, no_api):
    assert designer.build().store_media is False


def test_the_team_routes_visual_work_to_the_designer(temp_db, no_api):
    assert "Post Designer" in instructions_of(team.build())
