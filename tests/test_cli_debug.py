"""Tests for planloop debug command."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session

runner = CliRunner()


def test_debug_outputs_session_info(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Debug", "Inspect", project_root=Path("/repo"))

    result = runner.invoke(cli.app, ["debug", "--session", state.session])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["session"] == state.session
    assert payload["path"].endswith(state.session)
