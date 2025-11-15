"""Tests for planloop search command."""
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


def test_search_matches_titles(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    create_session("Crash fix", "Fix crash in login", project_root=Path("/repo"))
    create_session("UI polish", "Polish home screen", project_root=Path("/repo"))

    result = runner.invoke(cli.app, ["search", "crash"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["sessions"]) == 1
    assert "crash" in data["sessions"][0]["title"].lower()


def test_search_empty_query_returns_all(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    create_session("One", "First", project_root=Path("/repo1"))
    create_session("Two", "Second", project_root=Path("/repo2"))

    result = runner.invoke(cli.app, ["search", " "])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["sessions"]) == 2
