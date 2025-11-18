"""Tests for auto-syncing agents.md guide at session creation (Task 1).

Verifies that when a new session is created, the agents.md guide is
automatically synchronized in the project root.
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from planloop.cli import app


def test_sessions_create_auto_syncs_guide(tmp_path, monkeypatch):
    """Creating a session should auto-sync agents.md guide."""
    import os

    # Change to tmp_path so relative paths work
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    # Set up PLANLOOP_HOME in tmp
    home = tmp_path / ".planloop"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))

    try:
        runner = CliRunner()
        
        # Create agents.md with old version
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        agents_md = docs_dir / "agents.md"
        agents_md.write_text("# Old Guide\n<!-- PLANLOOP-INSTALLED v1.0 -->\nOld content")
        
        # Create session
        result = runner.invoke(app, [
            "sessions", "create",
            "--name", "test-session",
            "--title", "Test Session"
        ])
        
        assert result.exit_code == 0, f"Command failed: {result.stdout}"
        
        # Check that agents.md was updated to latest version
        content = agents_md.read_text()
        assert "PLANLOOP-INSTALLED v2.0" in content
        assert "Old content" not in content
        
    finally:
        os.chdir(original_cwd)


def test_sessions_create_creates_guide_if_missing(tmp_path, monkeypatch):
    """Creating a session should create agents.md if it doesn't exist."""
    import os

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    home = tmp_path / ".planloop"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))

    try:
        runner = CliRunner()
        
        # Ensure docs directory exists but no agents.md
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        agents_md = docs_dir / "agents.md"
        
        # Create session
        result = runner.invoke(app, [
            "sessions", "create",
            "--name", "test-session",
            "--title", "Test Session"
        ])
        
        assert result.exit_code == 0
        
        # Check that agents.md was created with current version
        assert agents_md.exists()
        content = agents_md.read_text()
        assert "PLANLOOP-INSTALLED v2.0" in content
        assert "planloop Agent Instructions" in content
        
    finally:
        os.chdir(original_cwd)


def test_sessions_create_skips_sync_if_up_to_date(tmp_path, monkeypatch):
    """Creating a session should skip sync if agents.md is already up-to-date."""
    import os

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    home = tmp_path / ".planloop"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))

    try:
        runner = CliRunner()
        
        # Create agents.md with current version
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        agents_md = docs_dir / "agents.md"
        
        from planloop.guide import render_guide
        current_guide = render_guide()
        agents_md.write_text(current_guide)
        
        original_mtime = agents_md.stat().st_mtime
        
        # Create session
        result = runner.invoke(app, [
            "sessions", "create",
            "--name", "test-session",
            "--title", "Test Session"
        ])
        
        assert result.exit_code == 0
        
        # File should still be up-to-date
        content = agents_md.read_text()
        assert "PLANLOOP-INSTALLED v2.0" in content
        
    finally:
        os.chdir(original_cwd)
