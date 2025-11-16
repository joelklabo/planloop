"""Tests for planloop guide command."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from planloop import cli

runner = CliRunner()


def test_guide_prints_content(tmp_path):
    result = runner.invoke(cli.app, ["guide"])
    assert result.exit_code == 0
    assert "planloop Agent Instructions" in result.stdout


def test_guide_apply_inserts_marker(tmp_path):
    target = tmp_path / "docs" / "agents.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(cli.app, ["guide", "--apply", "--target", str(target)])
    assert result.exit_code == 0
    content = target.read_text()
    assert "<!-- PLANLOOP-INSTALLED -->" in content
    # Running again should not duplicate content
    runner.invoke(cli.app, ["guide", "--apply", "--target", str(target)])
    content2 = target.read_text()
    assert content == content2
