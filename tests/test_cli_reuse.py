"""Tests for planloop reuse command."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session, save_session_state
from planloop.core.state import Task, TaskType

runner = CliRunner()


def setup_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def mark_session_done(home: Path, session_id: str) -> None:
    state_path = home / "sessions" / session_id / "state.json"
    from planloop.core.state import SessionState

    state = SessionState.model_validate_json(state_path.read_text())
    state.done = True
    state.final_summary = "Template summary"
    state.tasks = [Task(id=1, title="Existing", type=TaskType.CHORE)]
    save_session_state(home / "sessions" / state.session, state, message="mark-done")


def test_reuse_outputs_template(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Template", "Template Work", project_root=Path("/repo"))
    mark_session_done(home, state.session)

    result = runner.invoke(cli.app, ["reuse", state.session, "--goal", "New goal"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["template_session"] == state.session
    assert data["goal"] == "New goal"
    assert data["template_tasks"][0]["title"] == "Existing"


def test_reuse_requires_done_session(monkeypatch, tmp_path):
    home = setup_home(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Template", "Template Work", project_root=Path("/repo"))

    result = runner.invoke(cli.app, ["reuse", state.session])
    assert result.exit_code != 0
