"""Integration tests for planloop status command."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session


runner = CliRunner()


def bootstrap_session(tmp_path: Path) -> str:
    home = tmp_path / "home"
    home.mkdir()
    (home / "sessions").mkdir()
    return str(home)


def test_status_requires_session(monkeypatch, tmp_path):
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path / "home"))
    result = runner.invoke(cli.app, ["status"])
    assert result.exit_code != 0


def test_status_json_output(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "title", project_root=Path("/repo"))
    result = runner.invoke(cli.app, ["status", "--session", state.session])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["session"] == state.session
    assert "tasks" in data
