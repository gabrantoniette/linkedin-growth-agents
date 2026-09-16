"""The studio's commands, and the gates that stop before a model or a browser runs."""

from __future__ import annotations

from typer.testing import CliRunner

from linkedin_growth import cli


def invoke(*arguments: str):
    return CliRunner().invoke(cli.app, list(arguments))


def test_publish_refuses_a_media_caption(tmp_path):
    """A carousel caption sent through the API would go out without its PDF."""
    caption = tmp_path / "post.md"
    caption.write_text("---\nformat: carousel\n---\n\n## Caption (pt-BR)\n\nTexto.\n", encoding="utf-8")

    result = invoke("publish", str(caption), "--dry-run")

    assert result.exit_code == 1
    assert "caption for a carousel" in result.output


def test_design_refuses_a_rejected_post_before_building_the_agent(tmp_path, monkeypatch):
    from linkedin_growth.agents import designer

    def forbidden():
        raise AssertionError("the agent must not be built for a rejected post")

    monkeypatch.setattr(designer, "build", forbidden)
    post = tmp_path / "2026-09-04-topic.md"
    post.write_text("---\nstatus: rejected\n---\n\n## Evaluation\n", encoding="utf-8")

    result = invoke("design", str(post))

    assert result.exit_code == 1
    assert "rejected by the Editor" in result.output


def test_design_refuses_a_post_with_placeholders(tmp_path):
    post = tmp_path / "2026-09-04-topic.md"
    post.write_text("## Post (pt-BR)\n\nReduzi em [PREENCHER: número].\n", encoding="utf-8")

    result = invoke("design", str(post))

    assert result.exit_code == 1
    assert "PREENCHER" in result.output


def test_design_validates_the_format(tmp_path):
    post = tmp_path / "2026-09-04-topic.md"
    post.write_text("## Post (pt-BR)\n\nTexto.\n", encoding="utf-8")

    result = invoke("design", str(post), "--format", "gif")

    assert result.exit_code == 1
    assert "--format must be one of" in result.output


def test_render_explains_an_invalid_spec(tmp_path):
    spec = tmp_path / "carousel.yaml"
    spec.write_text("title: T\nslides:\n  - layout: hero\n", encoding="utf-8")

    result = invoke("render", str(spec))

    assert result.exit_code == 1
    assert "invalid" in result.output
