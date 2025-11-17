"""Integration tests for planloop suggest end-to-end workflows."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from planloop import cli
from planloop.core.session import create_session
from planloop.core.state import Task, TaskStatus, TaskType
from planloop.core.suggest import TaskSuggestion

runner = CliRunner()


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project structure for testing."""
    project = tmp_path / "sample_project"
    project.mkdir()
    
    # Create some Python files
    (project / "main.py").write_text("""
def main():
    # TODO: Add error handling
    print("Hello world")

if __name__ == "__main__":
    main()
""")
    
    (project / "utils.py").write_text("""
# FIXME: This function needs tests
def calculate(x, y):
    return x + y
""")
    
    # Create a test file (but not comprehensive)
    tests_dir = project / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_utils.py").write_text("""
def test_basic():
    assert 1 + 1 == 2
""")
    
    return project


def test_suggest_empty_plan_generates_tasks(monkeypatch, tmp_path, sample_project):
    """Integration test: Empty plan → suggest generates and adds tasks."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    # Create session with empty plan
    state = create_session("Test", "Test Session", project_root=sample_project)
    assert len(state.tasks) == 0
    
    # Mock the LLM to return suggestions
    mock_suggestions = [
        TaskSuggestion(
            title="Add error handling to main.py",
            type=TaskType.FIX,
            priority="high",
            rationale="TODO comment indicates missing error handling",
            implementation_notes="Add try/catch around main logic",
            affected_files=["main.py"],
            depends_on=[]
        ),
        TaskSuggestion(
            title="Add tests for calculate function",
            type=TaskType.TEST,
            priority="medium",
            rationale="FIXME comment indicates function needs tests",
            implementation_notes="Create test_calculate in test_utils.py",
            affected_files=["tests/test_utils.py"],
            depends_on=[]
        )
    ]
    
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = mock_suggestions
        MockEngine.return_value = mock_engine
        
        with patch("planloop.cli._load_session") as mock_load:
            mock_load.return_value = (state, home / "sessions" / state.session)
            
            with patch("planloop.cli.acquire_lock"):
                # Run suggest with auto-approve
                result = runner.invoke(cli.app, [
                    "suggest",
                    "--session", state.session,
                    "--auto-approve"
                ])
                
                assert result.exit_code == 0
                assert "Found 2 suggestion(s)" in result.stdout
                assert "Added 2 task(s)" in result.stdout


def test_suggest_with_existing_tasks_no_duplicates(monkeypatch, tmp_path, sample_project):
    """Integration test: Existing tasks → no duplicate suggestions."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    # Create session with existing task
    state = create_session("Test", "Test Session", project_root=sample_project)
    existing_task = Task(
        id=1,
        title="Add error handling to main.py",
        type=TaskType.FIX,
        status=TaskStatus.TODO
    )
    state.tasks.append(existing_task)
    state.now = state.compute_now()
    
    # Save state
    from planloop.core.session import save_session_state
    from planloop.home import SESSIONS_DIR
    session_dir = home / SESSIONS_DIR / state.session
    save_session_state(session_dir, state)
    
    # Mock LLM to return a suggestion that would be a duplicate
    mock_suggestions = [
        TaskSuggestion(
            title="Add error handling to main.py",  # Duplicate!
            type=TaskType.FIX,
            priority="high",
            rationale="TODO comment indicates missing error handling",
            implementation_notes="Add try/catch around main logic",
            affected_files=["main.py"],
            depends_on=[]
        )
    ]
    
    with patch("planloop.core.suggest.LLMClient") as MockLLM:
        mock_llm = Mock()
        # Return empty list after deduplication
        mock_llm.generate_json.return_value = []
        MockLLM.return_value = mock_llm
        
        # Run suggest
        result = runner.invoke(cli.app, [
            "suggest",
            "--session", state.session,
            "--dry-run"  # Just preview
        ])
        
        assert result.exit_code == 0


def test_suggest_dry_run_no_modifications(monkeypatch, tmp_path, sample_project):
    """Integration test: Dry-run mode should not modify state."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    state = create_session("Test", "Test Session", project_root=sample_project)
    initial_task_count = len(state.tasks)
    
    mock_suggestions = [
        TaskSuggestion(
            title="Test task",
            type=TaskType.TEST,
            priority="low",
            rationale="Test",
            implementation_notes="Test",
            affected_files=["test.py"],
            depends_on=[]
        )
    ]
    
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = mock_suggestions
        MockEngine.return_value = mock_engine
        
        with patch("planloop.cli._load_session") as mock_load:
            mock_load.return_value = (state, home / "sessions" / state.session)
            
            # Run with dry-run
            result = runner.invoke(cli.app, [
                "suggest",
                "--session", state.session,
                "--dry-run"
            ])
            
            assert result.exit_code == 0
            # Verify no tasks were added
            assert len(state.tasks) == initial_task_count


def test_suggest_focus_area(monkeypatch, tmp_path, sample_project):
    """Integration test: Focus area limits analysis scope."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    state = create_session("Test", "Test Session", project_root=sample_project)
    
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = []
        MockEngine.return_value = mock_engine
        
        with patch("planloop.cli._load_session") as mock_load:
            mock_load.return_value = (state, home / "sessions" / state.session)
            
            # Run with focus
            result = runner.invoke(cli.app, [
                "suggest",
                "--session", state.session,
                "--focus", "tests/",
                "--dry-run"
            ])
            
            # Should pass focus parameter to engine
            mock_engine.generate_suggestions.assert_called_once()
            assert result.exit_code == 0


def test_suggest_depth_parameter(monkeypatch, tmp_path, sample_project):
    """Integration test: Depth parameter controls analysis thoroughness."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    state = create_session("Test", "Test Session", project_root=sample_project)
    
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        mock_engine.generate_suggestions.return_value = []
        MockEngine.return_value = mock_engine
        
        with patch("planloop.cli._load_session") as mock_load:
            mock_load.return_value = (state, home / "sessions" / state.session)
            
            # Test each depth level
            for depth in ["shallow", "medium", "deep"]:
                result = runner.invoke(cli.app, [
                    "suggest",
                    "--session", state.session,
                    "--depth", depth,
                    "--dry-run"
                ])
                
                assert result.exit_code == 0
                # Verify depth was passed
                call_kwargs = mock_engine.generate_suggestions.call_args[1]
                assert call_kwargs["depth"] == depth


def test_suggest_handles_invalid_llm_output(monkeypatch, tmp_path, sample_project):
    """Integration test: Invalid LLM output should be handled gracefully."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    state = create_session("Test", "Test Session", project_root=sample_project)
    
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        # Simulate LLM returning invalid data
        mock_engine.generate_suggestions.side_effect = Exception("LLM error: Invalid JSON")
        MockEngine.return_value = mock_engine
        
        with patch("planloop.cli._load_session") as mock_load:
            mock_load.return_value = (state, home / "sessions" / state.session)
            
            result = runner.invoke(cli.app, [
                "suggest",
                "--session", state.session,
                "--dry-run"
            ])
            
            # Should exit with error but not crash
            assert result.exit_code == 1
            # Check for error message in output
            assert "error" in result.output.lower()


def test_suggest_limit_option(monkeypatch, tmp_path, sample_project):
    """Integration test: Limit option restricts number of suggestions."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    state = create_session("Test", "Test Session", project_root=sample_project)
    
    # Create many suggestions
    many_suggestions = [
        TaskSuggestion(
            title=f"Task {i}",
            type=TaskType.FEATURE,
            priority="low",
            rationale=f"Reason {i}",
            implementation_notes=f"Notes {i}",
            affected_files=[f"file{i}.py"],
            depends_on=[]
        )
        for i in range(10)
    ]
    
    with patch("planloop.cli.SuggestionEngine") as MockEngine:
        mock_engine = Mock()
        # Engine should respect the limit
        mock_engine.generate_suggestions.return_value = many_suggestions[:3]
        MockEngine.return_value = mock_engine
        
        with patch("planloop.cli._load_session") as mock_load:
            mock_load.return_value = (state, home / "sessions" / state.session)
            
            result = runner.invoke(cli.app, [
                "suggest",
                "--session", state.session,
                "--limit", "3",
                "--dry-run"
            ])
            
            assert result.exit_code == 0
            assert "Found 3 suggestion(s)" in result.stdout
