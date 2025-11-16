"""End-to-end CLI loop integration test."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session, load_session_state_from_disk
from planloop.home import SESSIONS_DIR

runner = CliRunner()


def _set_planloop_home(monkeypatch, tmp_path) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    return home


def _run_status(session_id: str) -> dict:
    result = runner.invoke(cli.app, ["status", "--session", session_id])
    assert result.exit_code == 0, result.stdout
    return json.loads(result.stdout)


def _run_update(payload: dict) -> int:
    result = runner.invoke(cli.app, ["update"], input=json.dumps(payload))
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    return data["version"]


def test_cli_loop_status_update_alert(monkeypatch, tmp_path):
    home = _set_planloop_home(monkeypatch, tmp_path)
    state = create_session("Loop", "Integration", project_root=Path("/repo"))
    session_id = state.session
    session_dir = home / SESSIONS_DIR / session_id

    status = _run_status(session_id)
    assert status["session"] == session_id
    assert status["tasks"] == []

    payload_add = {
        "session": session_id,
        "last_seen_version": str(state.version),
        "add_tasks": [
            {"title": "Bootstrap CLI", "type": "feature"},
            {"title": "Write tests", "type": "test"},
        ],
        "context_notes": ["Initial plan"],
        "next_steps": ["Run status before coding"],
    }
    version = _run_update(payload_add)

    saved = load_session_state_from_disk(session_dir)
    assert len(saved.tasks) == 2
    assert saved.context_notes == ["Initial plan"]

    status = _run_status(session_id)
    assert status["now"]["reason"] == "task"
    assert status["now"]["task_id"] == 1

    payload_progress = {
        "session": session_id,
        "last_seen_version": str(version),
        "tasks": [
            {"id": 1, "status": "DONE"},
            {"id": 2, "status": "IN_PROGRESS"},
        ],
        "context_notes": ["Task 1 done"],
    }
    version = _run_update(payload_progress)

    status = _run_status(session_id)
    assert status["tasks"][0]["status"] == "DONE"
    assert status["now"]["task_id"] == 2

    result = runner.invoke(
        cli.app,
        [
            "alert",
            "--session",
            session_id,
            "--id",
            "ci-loop",
            "--kind",
            "build",
            "--title",
            "CI failing",
            "--message",
            "Fix tests",
        ],
    )
    assert result.exit_code == 0

    blocked = _run_status(session_id)
    assert blocked["now"]["reason"] == "ci_blocker"
    assert any(sig["open"] for sig in blocked["signals"])

    result = runner.invoke(
        cli.app,
        [
            "alert",
            "--session",
            session_id,
            "--id",
            "ci-loop",
            "--kind",
            "build",
            "--title",
            "CI failing",
            "--message",
            "Fix tests",
            "--close",
        ],
    )
    assert result.exit_code == 0

    status = _run_status(session_id)
    assert status["now"]["reason"] == "task"

    payload_complete = {
        "session": session_id,
        "last_seen_version": str(version),
        "tasks": [
            {"id": 2, "status": "DONE"},
        ],
        "final_summary": "Loop wrapped",
    }
    _ = _run_update(payload_complete)

    final_status = _run_status(session_id)
    assert final_status["now"]["reason"] == "completed"

    final_state = load_session_state_from_disk(session_dir)
    assert final_state.final_summary == "Loop wrapped"
