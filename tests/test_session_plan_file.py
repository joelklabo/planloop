"""Tests for session initialization with PLAN.md file (Task 12).

Verifies that sessions can be created with existing PLAN.md files.
"""

from pathlib import Path

import pytest


def test_sessions_create_accepts_plan_file_flag():
    """Sessions create should accept --plan-file flag."""
    from typer.testing import CliRunner
    from planloop.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["sessions", "create", "--help"])
    
    assert result.exit_code == 0
    assert "--plan-file" in result.stdout


def test_sessions_create_loads_existing_plan(tmp_path, monkeypatch):
    """Sessions create should load tasks from existing PLAN.md."""
    import os
    
    # Set up environment
    home = tmp_path / ".planloop"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    # Create a PLAN.md with tasks
    plan_file = tmp_path / "PLAN.md"
    plan_file.write_text("""# Development Plan

## Tasks

- [ ] Task 1: Implement feature A
- [ ] Task 2: Add tests for feature A
- [x] Task 3: Document feature A
""")
    
    from typer.testing import CliRunner
    from planloop.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, [
        "sessions", "create",
        "--name", "test-session",
        "--title", "Test",
        "--plan-file", str(plan_file)
    ])
    
    assert result.exit_code == 0, f"Command failed with: {result.stdout}"
    
    # Load the session and verify tasks were imported
    import json
    output = json.loads(result.stdout)
    session_id = output["session"]
    
    # Check session state
    from planloop.core.session import load_session_state_from_disk
    session_dir = home / "sessions" / session_id
    state = load_session_state_from_disk(session_dir)
    
    # Should have loaded tasks from PLAN.md
    assert len(state.tasks) >= 2  # At least the TODO tasks


def test_plan_file_parser_extracts_tasks():
    """Plan file parser should extract tasks from markdown."""
    from planloop.core.plan_parser import parse_plan_file
    
    plan_content = """# My Plan

## Tasks

- [ ] Task 1: Build API
- [ ] Task 2: Write tests
- [x] Task 3: Deploy

## Notes
Some notes here.
"""
    
    tasks = parse_plan_file(plan_content)
    
    assert len(tasks) == 3
    assert tasks[0].title == "Task 1: Build API"
    assert tasks[0].status == "TODO"
    assert tasks[2].status == "DONE"


def test_plan_file_parser_handles_various_formats():
    """Parser should handle different markdown task formats."""
    from planloop.core.plan_parser import parse_plan_file
    
    plan_content = """
# Tasks
- [ ] Simple task
* [ ] Asterisk task
+ [ ] Plus task
- [x] Done task
- [X] Also done
"""
    
    tasks = parse_plan_file(plan_content)
    
    assert len(tasks) == 5
    assert tasks[0].title == "Simple task"
    assert tasks[1].title == "Asterisk task"
    assert tasks[3].status == "DONE"
    assert tasks[4].status == "DONE"


def test_sessions_create_with_invalid_plan_file_fails(tmp_path, monkeypatch):
    """Sessions create should fail gracefully with invalid plan file."""
    import os
    
    home = tmp_path / ".planloop"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    from typer.testing import CliRunner
    from planloop.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, [
        "sessions", "create",
        "--name", "test",
        "--plan-file", "/nonexistent/file.md"
    ])
    
    assert result.exit_code != 0
    # May output to stdout or stderr, just check it failed
    assert result.exit_code == 1
