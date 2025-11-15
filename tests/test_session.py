"""Tests for session creation helpers."""
from __future__ import annotations

from pathlib import Path

from planloop.core.session import create_session, new_session_id


def test_new_session_id_formats_slug(monkeypatch):
    monkeypatch.setattr("planloop.core.session.datetime", __import__("datetime").datetime)
    session_id = new_session_id("My Cool Feature")
    assert "my-cool-feature" in session_id
    assert len(session_id.split("-")) >= 3


def test_create_session(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(fake_home))

    state = create_session(name="Foo", title="Fix Bug", project_root=Path("/repo"))

    sessions_dir = fake_home / "sessions"
    assert sessions_dir.exists()
    session_dirs = list(sessions_dir.iterdir())
    assert len(session_dirs) == 1
    session_dir = session_dirs[0]
    assert (session_dir / "state.json").is_file()
    assert (session_dir / "PLAN.md").is_file()
    assert state.session in session_dir.name
