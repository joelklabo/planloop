"""Tests for PLANLOOP_HOME resolution and initialization."""
from __future__ import annotations

from importlib import resources

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


def test_initialize_home_creates_structure(tmp_path, monkeypatch):
    fake_home = tmp_path / "plhome"
    monkeypatch.setenv(home.PLANLOOP_HOME_ENV, str(fake_home))

    result = home.initialize_home()

    assert result == fake_home
    assert (result / home.SESSIONS_DIR).is_dir()
    assert (result / home.PROMPTS_DIR / home.DEFAULT_PROMPT_SET).is_dir()
    assert (result / home.MESSAGES_DIR).is_dir()
    config_path = result / home.CONFIG_FILE_NAME
    assert config_path.is_file()
    assert "prompt_set: core-v1" in config_path.read_text()
    assert (result / home.CURRENT_SESSION_POINTER).is_file()


def test_initialize_home_seeds_template_content(tmp_path, monkeypatch):
    fake_home = tmp_path / "plhome"
    monkeypatch.setenv(home.PLANLOOP_HOME_ENV, str(fake_home))

    home.initialize_home()

    goal_template = (
        resources.files("planloop.templates")
        / "prompts"
        / "core-v1"
        / "goal.prompt.md"
    ).read_text(encoding="utf-8")
    missing_docs_template = (
        resources.files("planloop.templates")
        / "messages"
        / "missing-docs-warning.md"
    ).read_text(encoding="utf-8")

    assert (
        (fake_home / home.PROMPTS_DIR / home.DEFAULT_PROMPT_SET / "goal.prompt.md").read_text(encoding="utf-8")
        == goal_template
    )
    assert (
        (fake_home / home.MESSAGES_DIR / "missing-docs-warning.md").read_text(encoding="utf-8")
        == missing_docs_template
    )


def test_initialize_home_is_idempotent(tmp_path, monkeypatch):
    fake_home = tmp_path / "plhome"
    monkeypatch.setenv(home.PLANLOOP_HOME_ENV, str(fake_home))

    home.initialize_home()
    config_path = fake_home / home.CONFIG_FILE_NAME
    config_path.write_text("custom: true", encoding="utf-8")

    home.initialize_home()

    assert config_path.read_text(encoding="utf-8") == "custom: true"
