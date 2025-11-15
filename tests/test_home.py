"""Tests for PLANLOOP_HOME resolution."""
from __future__ import annotations

from pathlib import Path

import planloop.home as home


def test_get_home_env_override(tmp_path, monkeypatch):
    custom_home = tmp_path / "custom" / "nested"
    monkeypatch.setenv(home.PLANLOOP_HOME_ENV, str(custom_home))

    result = home.get_home()

    assert result == custom_home.resolve()
    assert result.exists()


def test_get_home_default(monkeypatch, tmp_path):
    monkeypatch.delenv(home.PLANLOOP_HOME_ENV, raising=False)

    # Patch Path.home() so we do not rely on the actual user home.
    monkeypatch.setattr(
        home.Path,
        "home",
        classmethod(lambda cls: tmp_path),
    )

    result = home.get_home()
    expected = (tmp_path / home.DEFAULT_HOME_NAME).resolve()

    assert result == expected
    assert result.exists()
