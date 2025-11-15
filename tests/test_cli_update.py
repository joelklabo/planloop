"""CLI tests for planloop update."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session, save_session_state
from planloop.core.state import Task, TaskStatus, TaskType

runner = CliRunner()


def setup_session(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    (home / "sessions").mkdir()
    return home


def test_update_changes_task_status(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    state.tasks = [Task(id=1, title="Do work", type=TaskType.CHORE)]
    save_session_state(home / "sessions" / state.session, state)

    payload = {
        "session": state.session,
        "tasks": [{"id": 1, "status": "DONE"}]
    }
    result = runner.invoke(cli.app, ["update"], input=json.dumps(payload))

    assert result.exit_code == 0
    data = json.loads((home / "sessions" / state.session / "state.json").read_text())
    assert data["tasks"][0]["status"] == "DONE"


def test_update_rejects_bad_version(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    payload = {
        "session": state.session,
        "last_seen_version": "999"
    }
    result = runner.invoke(cli.app, ["update"], input=json.dumps(payload))
    assert result.exit_code != 0
