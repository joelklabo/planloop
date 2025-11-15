"""Tests for current session pointer helpers."""
from __future__ import annotations

from planloop.core import session_pointer


def test_set_and_get_session(monkeypatch, tmp_path):
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path / "home"))

    assert session_pointer.get_current_session() is None
    session_pointer.set_current_session("abc-123")
    assert session_pointer.get_current_session() == "abc-123"


def test_clear_session(monkeypatch, tmp_path):
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path / "home"))

    session_pointer.set_current_session("foo")
    session_pointer.clear_current_session()

    assert session_pointer.get_current_session() is None
