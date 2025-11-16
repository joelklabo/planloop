"""Integration tests for planloop status command."""
from __future__ import annotations

import json
import time
from pathlib import Path

import yaml
from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session
from planloop.config import reset_config_cache


runner = CliRunner()


def bootstrap_session(tmp_path: Path) -> str:
    home = tmp_path / "home"
    home.mkdir()
    (home / "sessions").mkdir()
    return str(home)


def set_safe_mode(home: Path, **kwargs) -> None:
    config_path = home / "config.yml"
    cfg = yaml.safe_load(config_path.read_text()) or {}
    update_cfg = cfg.setdefault("safe_modes", {}).setdefault("update", {})
    update_cfg.update(kwargs)
    config_path.write_text(yaml.safe_dump(cfg))
    reset_config_cache()


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


def test_status_includes_safe_mode_defaults(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "title", project_root=Path("/repo"))
    set_safe_mode(home, dry_run=True)
    result = runner.invoke(cli.app, ["status", "--session", state.session])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["safe_mode_defaults"]["dry_run"] is True
    reset_config_cache()


def test_status_includes_lock_queue(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "title", project_root=Path("/repo"))
    result = runner.invoke(cli.app, ["status", "--session", state.session])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    queue = data["lock_queue"]
    assert queue["pending"] == []
    assert queue["position"] is None


def test_status_reports_queue_position(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "title", project_root=Path("/repo"))
    queue_dir = home / "sessions" / state.session / ".lock_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    entry = queue_dir / "entry.json"
    entry.write_text(
        json.dumps(
            {
                "id": "entry",
                "agent": "agent-test",
                "operation": "update",
                "requested_at": time.time(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PLANLOOP_AGENT_NAME", "agent-test")
    result = runner.invoke(cli.app, ["status", "--session", state.session])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["lock_queue"]["position"] == 1
