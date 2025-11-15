"""Tests for session management CLI commands."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session

runner = CliRunner()


def setup_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_sessions_list(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    create_session("One", "First", project_root=Path("/repo1"))
    create_session("Two", "Second", project_root=Path("/repo2"))

    result = runner.invoke(cli.app, ["sessions", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["sessions"]) == 2


def test_sessions_info_defaults_to_current(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Info", "Details", project_root=Path("/repo"))

    result = runner.invoke(cli.app, ["sessions", "info"])
    assert result.exit_code == 0
    info = json.loads(result.stdout)
    assert info["session"] == state.session
    assert info["path"].endswith(state.session)
