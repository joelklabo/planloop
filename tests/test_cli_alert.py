"""Tests for planloop alert command."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session, save_session_state

runner = CliRunner()


def setup_session(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    (home / "sessions").mkdir()
    return home


def test_alert_opens_signal(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    save_session_state(home / "sessions" / state.session, state)

    result = runner.invoke(
        cli.app,
        [
            "alert",
            "--session",
            state.session,
            "--id",
            "ci-1",
            "--kind",
            "build",
            "--title",
            "CI failed",
            "--message",
            "Tests failing",
        ],
    )
    assert result.exit_code == 0
    saved = (home / "sessions" / state.session / "state.json").read_text()
    assert "ci-1" in saved


def test_alert_close(monkeypatch, tmp_path):
    home = setup_session(tmp_path)
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    state = create_session("Test", "Demo", project_root=Path("/repo"))
    state.signals = []
    save_session_state(home / "sessions" / state.session, state)

    runner.invoke(
        cli.app,
        [
            "alert",
            "--session",
            state.session,
            "--id",
            "ci-1",
            "--kind",
            "build",
            "--title",
            "CI failed",
            "--message",
            "Tests failing",
        ],
    )
    result = runner.invoke(
        cli.app,
        [
            "alert",
            "--session",
            state.session,
            "--id",
            "ci-1",
            "--kind",
            "build",
            "--title",
            "CI failed",
            "--message",
            "Tests failing",
            "--close",
        ],
    )
    assert result.exit_code == 0
    saved = (home / "sessions" / state.session / "state.json").read_text()
    assert '"open": false' in saved
