"""Performance tests for suggest feature."""
from __future__ import annotations

import time

import pytest

from planloop.config import SuggestConfig
from planloop.core.context_builder import ContextBuilder
from planloop.core.state import SessionState
from planloop.core.suggest import SuggestionEngine


@pytest.fixture
def large_project(tmp_path):
    """Create a large sample project for performance testing."""
    project = tmp_path / "large_project"
    project.mkdir()

    # Create 100 Python files in various directories
    for i in range(20):
        subdir = project / f"module_{i}"
        subdir.mkdir()

        for j in range(5):
            file_path = subdir / f"file_{j}.py"
            file_path.write_text(f"""
# Module {i}, File {j}

def function_{j}():
    # TODO: Add error handling
    pass

class Class_{j}:
    def method_a(self):
        # FIXME: Optimize this
        pass

    def method_b(self):
        return 42
""")

    # Create tests directory
    tests_dir = project / "tests"
    tests_dir.mkdir()
    for i in range(10):
        test_file = tests_dir / f"test_{i}.py"
        test_file.write_text(f"""
def test_basic_{i}():
    assert True
""")

    return project


@pytest.fixture
def session_state():
    """Create a simple session state."""
    from datetime import datetime

    from planloop.core.state import Environment, Now, NowReason, PromptMetadata

    return SessionState(
        session="test",
        name="Test",
        title="Test",
        purpose="Testing",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        project_root="/tmp/test",
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="test"),
        now=Now(reason=NowReason.IDLE),
        tasks=[]
    )


def test_context_builder_shallow_performance(large_project):
    """Shallow context build should complete in <2s."""
    builder = ContextBuilder(large_project)

    start = time.time()
    context = builder.build(depth="shallow")
    elapsed = time.time() - start

    assert context is not None
    assert elapsed < 2.0, f"Shallow build took {elapsed:.2f}s, should be <2s"


def test_context_builder_medium_performance(large_project):
    """Medium context build should complete in <5s."""
    builder = ContextBuilder(large_project)

    start = time.time()
    context = builder.build(depth="medium")
    elapsed = time.time() - start

    assert context is not None
    assert elapsed < 5.0, f"Medium build took {elapsed:.2f}s, should be <5s"


def test_context_builder_deep_performance(large_project):
    """Deep context build should complete in <15s."""
    builder = ContextBuilder(large_project)

    start = time.time()
    context = builder.build(depth="deep")
    elapsed = time.time() - start

    assert context is not None
    assert elapsed < 15.0, f"Deep build took {elapsed:.2f}s, should be <15s"


def test_context_builder_caches_structure(large_project):
    """Second call to build should be faster due to caching."""
    builder = ContextBuilder(large_project)

    # First call - cold cache
    start1 = time.time()
    context1 = builder.build(depth="medium")
    elapsed1 = time.time() - start1

    # Second call - should use cache
    start2 = time.time()
    context2 = builder.build(depth="medium")
    elapsed2 = time.time() - start2

    assert context1 is not None
    assert context2 is not None
    # Second call should be significantly faster (at least 50% faster)
    assert elapsed2 < elapsed1 * 0.5, f"Cache didn't improve performance: {elapsed1:.3f}s vs {elapsed2:.3f}s"


def test_context_builder_handles_large_codebase(tmp_path):
    """Should handle 1000+ files without crashing."""
    project = tmp_path / "huge_project"
    project.mkdir()

    # Create 1000 small Python files
    for i in range(1000):
        subdir = project / f"dir_{i // 10}"
        subdir.mkdir(exist_ok=True)

        file_path = subdir / f"file_{i}.py"
        file_path.write_text(f"# File {i}\ndef func_{i}(): pass\n")

    builder = ContextBuilder(project)

    start = time.time()
    context = builder.build(depth="shallow")
    elapsed = time.time() - start

    assert context is not None
    # Should handle large codebase in reasonable time
    assert elapsed < 10.0, f"Large codebase took {elapsed:.2f}s, should be <10s"


def test_suggest_engine_end_to_end_performance(session_state, large_project, monkeypatch):
    """Full suggest workflow should complete in reasonable time."""
    from unittest.mock import Mock, patch

    # Clear API keys to avoid accessing real LLM
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = SuggestConfig(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        context_depth="medium",
        max_suggestions=5
    )

    # Mock the entire LLM client initialization
    mock_llm = Mock()
    mock_response = [
        {
            "title": "Add error handling",
            "type": "fix",
            "priority": "high",
            "rationale": "Improve robustness",
            "implementation_notes": "Add try-catch blocks",
            "affected_files": ["main.py"],
        }
    ]
    mock_llm.generate_json.return_value = mock_response

    with patch("planloop.core.suggest.LLMClient", return_value=mock_llm):
        engine = SuggestionEngine(session_state, config)

        start = time.time()
        suggestions = engine.generate_suggestions(project_root=large_project, depth="medium")
        elapsed = time.time() - start

        # Should complete quickly with mocked LLM
        assert elapsed < 5.0, f"End-to-end took {elapsed:.2f}s, should be <5s"
        assert len(suggestions) > 0
        assert suggestions[0].title == "Add error handling"
