"""Tests for session registry helpers."""
from __future__ import annotations

from datetime import datetime

from planloop.core.registry import SessionSummary, load_registry, upsert_session


def test_registry_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path / "home"))
    now = datetime.utcnow().isoformat()
    entry = SessionSummary(
        session="abc",
        name="foo",
        title="Foo",
        tags=["test"],
        project_root="/repo",
        created_at=now,
        last_updated_at=now,
        done=False,
    )

    upsert_session(entry)
    entries = load_registry()

    assert len(entries) == 1
    assert entries[0].session == "abc"


def test_upsert_updates_existing(monkeypatch, tmp_path):
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path / "home"))

    now = datetime.utcnow().isoformat()
    entry = SessionSummary(
        session="abc",
        name="foo",
        title="Foo",
        tags=["test"],
        project_root="/repo",
        created_at=now,
        last_updated_at=now,
        done=False,
    )

    upsert_session(entry)
    entry.title = "Bar"
    upsert_session(entry)

    entries = load_registry()
    assert len(entries) == 1
    assert entries[0].title == "Bar"
