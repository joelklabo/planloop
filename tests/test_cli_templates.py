"""Tests for planloop templates command."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session, save_session_state

runner = CliRunner()


def setup_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def mark_template(home: Path, session_id: str, tag: str | None = None) -> None:
    session_dir = home / "sessions" / session_id
    state_path = session_dir / "state.json"
    from planloop.core.state import SessionState

    state = SessionState.model_validate_json(state_path.read_text())
    state.done = True
    if tag:
        state.tags.append(tag)
    save_session_state(session_dir, state)


def test_templates_lists_done_sessions(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Template", "Template Work", project_root=Path("/repo"))
    mark_template(home, state.session)

    result = runner.invoke(cli.app, ["templates"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["templates"]) == 1


def test_templates_filters_by_tag(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    good = create_session("Good", "Done good", project_root=Path("/repo"))
    mark_template(home, good.session, tag="good_template")
    bad = create_session("Bad", "Done but not tagged", project_root=Path("/repo"))
    mark_template(home, bad.session)

    result = runner.invoke(cli.app, ["templates", "--tag", "good_template"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["templates"]) == 1
    assert data["templates"][0]["session"] == good.session
