"""CLI tests for planloop update."""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from planloop import cli
from planloop.config import reset_config_cache
from planloop.home import initialize_home
from planloop.core.session import create_session, save_session_state
from planloop.core.state import Task, TaskStatus, TaskType

runner = CliRunner()


def setup_session(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    (home / "sessions").mkdir()
    return home


def configure_safe_mode(home: Path, **kwargs) -> None:
    initialize_home()
    config_path = home / "config.yml"
    cfg = yaml.safe_load(config_path.read_text()) or {}
    update_cfg = cfg.setdefault("safe_modes", {}).setdefault("update", {})
    update_cfg.update(kwargs)
    config_path.write_text(yaml.safe_dump(cfg))
    reset_config_cache()


def test_update_changes_task_status(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    state.tasks = [Task(id=1, title="Do work", type=TaskType.CHORE)]
    save_session_state(home / "sessions" / state.session, state, message="setup")

    payload = {
        "session": state.session,
        "tasks": [{"id": 1, "status": "DONE"}]
    }
    result = runner.invoke(cli.app, ["update"], input=json.dumps(payload))

    assert result.exit_code == 0
    data = json.loads((home / "sessions" / state.session / "state.json").read_text())
    assert data["tasks"][0]["status"] == "DONE"
    log_path = home / "sessions" / state.session / "logs" / "planloop.log"
    assert log_path.exists()
    assert "Update command" in log_path.read_text()


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


def test_config_default_no_plan_edit(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    configure_safe_mode(home, no_plan_edit=True)
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    payload = {
        "session": state.session,
        "add_tasks": [{"title": "Task", "type": "feature"}],
    }
    result = runner.invoke(cli.app, ["update"], input=json.dumps(payload))
    assert result.exit_code != 0

    result = runner.invoke(cli.app, ["update", "--allow-plan-edit"], input=json.dumps(payload))
    assert result.exit_code == 0
    reset_config_cache()


def test_update_dry_run(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    payload = {
        "session": state.session,
        "add_tasks": [{"title": "Task", "type": "feature"}],
    }
    result = runner.invoke(cli.app, ["update", "--dry-run"], input=json.dumps(payload))
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["dry_run"]["tasks"]["added"]
    # ensure original state unchanged
    saved = json.loads((home / "sessions" / state.session / "state.json").read_text())
    assert saved["tasks"] == []


def test_update_no_plan_edit_blocks_structural(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    payload = {
        "session": state.session,
        "add_tasks": [{"title": "Task", "type": "feature"}],
    }
    result = runner.invoke(cli.app, ["update", "--no-plan-edit"], input=json.dumps(payload))
    assert result.exit_code != 0


def test_update_strict_rejects_unknown(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    state.tasks = [Task(id=1, title="Existing", type=TaskType.CHORE)]
    save_session_state(home / "sessions" / state.session, state, message="setup")
    payload = {
        "session": state.session,
        "tasks": [{"id": 1, "status": "DONE"}],
        "extra_field": True,
    }
    result = runner.invoke(cli.app, ["update"], input=json.dumps(payload))
    assert result.exit_code == 0

    result = runner.invoke(cli.app, ["update", "--strict"], input=json.dumps(payload))
    assert result.exit_code != 0


def test_config_default_strict(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    configure_safe_mode(home, strict=True)
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    state.tasks = [Task(id=1, title="Existing", type=TaskType.CHORE)]
    save_session_state(home / "sessions" / state.session, state, message="setup")
    payload = {
        "session": state.session,
        "tasks": [{"id": 1, "status": "DONE"}],
        "extra": True,
    }
    result = runner.invoke(cli.app, ["update"], input=json.dumps(payload))
    assert result.exit_code != 0

    result = runner.invoke(cli.app, ["update", "--allow-extra-fields"], input=json.dumps(payload))
    assert result.exit_code == 0
    reset_config_cache()
