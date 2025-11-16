"""Tests for snapshot and restore commands."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from planloop import cli
from planloop.config import reset_config_cache
from planloop.core.session import create_session
from planloop.home import initialize_home


pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git is required for history snapshots",
)

runner = CliRunner()


def enable_history(home: Path) -> None:
    config_path = home / "config.yml"
    cfg = yaml.safe_load(config_path.read_text())
    cfg.setdefault("history", {})["enabled"] = True
    config_path.write_text(yaml.safe_dump(cfg))
    reset_config_cache()


def test_snapshot_and_restore(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    initialize_home()
    enable_history(home)

    state = create_session("Snap", "Snapshot Test", project_root=Path("/repo"))
    session_dir = home / "sessions" / state.session
    gitignore = session_dir / ".gitignore"
    assert gitignore.exists()

    result = runner.invoke(cli.app, ["snapshot", "--session", state.session])
    assert result.exit_code == 0
    sha = json.loads(result.stdout)["snapshot"]

    state_path = session_dir / "state.json"
    content = state_path.read_text().replace("Snapshot Test", "Changed")
    state_path.write_text(content)

    result = runner.invoke(cli.app, ["restore", sha, "--session", state.session])
    assert result.exit_code == 0
    assert "restored" in result.stdout
    restored = state_path.read_text()
    assert "Snapshot Test" in restored
