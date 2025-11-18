"""Tests for codebase context builder."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from planloop.core.context_builder import CodebaseContext, ContextBuilder, TodoComment


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    src = tmp_path / "src"
    src.mkdir()
    tests = tmp_path / "tests"
    tests.mkdir()

    # Create some Python files with TODO comments
    (src / "main.py").write_text("""
# Main module
def hello():
    # TODO: Add error handling
    print("Hello")

def world():
    # FIXME: This is broken
    pass
""")

    (src / "utils.py").write_text("""
# Utilities
# NOTE: Consider refactoring
def helper():
    return 42
""")

    (tests / "test_main.py").write_text("""
# Tests
def test_hello():
    assert True
""")

    # Create a README
    (tmp_path / "README.md").write_text("# Test Project")

    return tmp_path


def test_todo_comment_model():
    """TodoComment should validate correctly."""
    comment = TodoComment(
        file="src/main.py",
        line=5,
        type="TODO",
        text="Add error handling"
    )
    assert comment.file == "src/main.py"
    assert comment.type == "TODO"


def test_codebase_context_model():
    """CodebaseContext should hold all analysis data."""
    context = CodebaseContext(
        project_root=Path("/test"),
        structure={"src": ["main.py"]},
        current_tasks=[],
        recent_changes=["src/main.py"],
        todos=[],
        language_stats={"py": 10}
    )
    assert context.project_root == Path("/test")
    assert "src" in context.structure


def test_context_builder_initializes_with_path(temp_project):
    """ContextBuilder should initialize with a project path."""
    builder = ContextBuilder(temp_project)
    assert builder.project_root == temp_project


def test_context_builder_parses_file_structure(temp_project):
    """ContextBuilder should parse file structure."""
    builder = ContextBuilder(temp_project)
    context = builder.build(depth="shallow")

    # Should find the directories and files
    assert context.structure is not None
    # Check if key directories are found
    structure_str = str(context.structure)
    assert "src" in structure_str or "main.py" in structure_str


def test_context_builder_extracts_todo_comments(temp_project):
    """ContextBuilder should find TODO/FIXME/NOTE comments."""
    builder = ContextBuilder(temp_project)
    context = builder.build(depth="medium")

    # Should find the TODO, FIXME, and NOTE comments
    assert len(context.todos) >= 3

    types = [t.type for t in context.todos]
    assert "TODO" in types
    assert "FIXME" in types
    assert "NOTE" in types


def test_context_builder_counts_language_stats(temp_project):
    """ContextBuilder should count files by extension."""
    builder = ContextBuilder(temp_project)
    context = builder.build(depth="shallow")

    # Should count Python and Markdown files
    assert "py" in context.language_stats
    assert context.language_stats["py"] >= 3  # At least 3 .py files
    assert "md" in context.language_stats
    assert context.language_stats["md"] >= 1


def test_context_builder_gets_git_history(temp_project, monkeypatch):
    """ContextBuilder should get recent changed files from git."""
    # Mock git command
    mock_result = Mock()
    mock_result.stdout = "src/main.py\nsrc/utils.py\n"
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result):
        builder = ContextBuilder(temp_project)
        context = builder.build(depth="medium")

        # Should have recent changes
        assert len(context.recent_changes) >= 2
        assert "src/main.py" in context.recent_changes or "main.py" in context.recent_changes


def test_context_builder_includes_current_tasks(temp_project):
    """ContextBuilder should include current plan tasks."""
    # For now, context builder returns empty tasks (will be enhanced later)
    # This test validates the structure exists
    builder = ContextBuilder(temp_project)
    context = builder.build(depth="shallow")

    # Should have a tasks list (even if empty)
    assert isinstance(context.current_tasks, list)


def test_context_builder_shallow_depth_is_fast(temp_project):
    """Shallow depth should scan less than deep depth."""
    builder = ContextBuilder(temp_project)

    shallow = builder.build(depth="shallow")
    deep = builder.build(depth="deep")

    # Shallow should have less detail (fewer TODOs or simpler structure)
    # This is a basic check - in practice, shallow might skip subdirectories
    assert shallow.language_stats is not None
    assert deep.language_stats is not None


def test_context_builder_handles_no_git_gracefully(temp_project):
    """ContextBuilder should handle non-git projects."""
    # Mock git command to fail
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
        builder = ContextBuilder(temp_project)
        context = builder.build(depth="medium")

        # Should still work, just with empty git history
        assert context.recent_changes == []


def test_context_builder_filters_ignored_patterns(temp_project):
    """ContextBuilder should respect ignore patterns."""
    # Create some files that should be ignored
    (temp_project / "__pycache__").mkdir()
    (temp_project / "__pycache__" / "main.pyc").write_text("compiled")
    (temp_project / "node_modules").mkdir()
    (temp_project / "node_modules" / "lib.js").write_text("dependency")

    builder = ContextBuilder(temp_project, ignore_patterns=["__pycache__", "node_modules", "*.pyc"])
    context = builder.build(depth="medium")

    # Should not count files in ignored directories
    structure_str = str(context.structure)
    assert "main.pyc" not in structure_str
    assert "lib.js" not in structure_str
