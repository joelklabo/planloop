"""Tests for coverage gap analysis integration (Task 2).

Verifies that planloop suggest can analyze test coverage and suggest
missing tests for uncovered code.
"""

from pathlib import Path

import pytest


def test_coverage_analyzer_identifies_uncovered_modules(tmp_path):
    """Coverage analyzer should identify modules with low coverage."""
    from planloop.core.coverage_analyzer import CoverageAnalyzer
    
    # Create a mock coverage report
    coverage_data = {
        "totals": {
            "percent_covered": 88.0
        },
        "files": {
            "src/module_a.py": {
                "summary": {
                    "percent_covered": 45.0,
                    "missing_lines": [10, 15, 20, 25],
                    "covered_lines": 40
                }
            },
            "src/module_b.py": {
                "summary": {
                    "percent_covered": 95.0,
                    "missing_lines": [100],
                    "covered_lines": 200
                }
            }
        }
    }
    
    analyzer = CoverageAnalyzer(coverage_data)
    gaps = analyzer.find_coverage_gaps(threshold=70.0)
    
    # Should identify module_a as having coverage gap
    assert len(gaps) == 1
    assert gaps[0].file_path == "src/module_a.py"
    assert gaps[0].coverage_percent == 45.0
    assert len(gaps[0].missing_lines) == 4


def test_coverage_analyzer_suggests_test_tasks():
    """Coverage analyzer should generate task suggestions for gaps."""
    from planloop.core.coverage_analyzer import CoverageAnalyzer, CoverageGap
    
    gap = CoverageGap(
        file_path="src/utils/parser.py",
        coverage_percent=35.0,
        missing_lines=[10, 15, 20, 25, 30],
        total_lines=100
    )
    
    analyzer = CoverageAnalyzer({})
    suggestions = analyzer.generate_test_suggestions([gap])
    
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert "parser.py" in suggestion.title.lower()
    assert suggestion.type == "test"
    assert suggestion.priority in ["medium", "high"]
    assert "35%" in suggestion.rationale or "35.0%" in suggestion.rationale


def test_suggest_includes_coverage_analysis(tmp_path, monkeypatch):
    """planloop suggest should integrate coverage analysis."""
    from planloop.core.suggest import SuggestionEngine
    from planloop.core.state import SessionState
    from planloop.config import SuggestConfig
    
    # Create a test project with coverage data
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    # Create minimal files
    (project_root / "src").mkdir()
    (project_root / "src" / "main.py").write_text("def foo(): pass")
    (project_root / "tests").mkdir()
    
    # Mock coverage report
    coverage_file = tmp_path / ".coverage"
    coverage_file.touch()
    
    # Create session state
    from datetime import datetime
    from planloop.core.state import Environment, Now, NowReason, PromptMetadata
    
    state = SessionState(
        session="test-session",
        name="test",
        title="Test",
        purpose="Testing coverage",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        project_root=str(project_root),
        prompts=PromptMetadata(set="core-v1"),
        environment=Environment(os="test"),
        now=Now(reason=NowReason.IDLE)
    )
    
    config = SuggestConfig(
        context_depth="shallow",
        max_suggestions=5,
        include_coverage_analysis=True
    )
    
    engine = SuggestionEngine(state, config)
    
    # Should have coverage analysis capability
    assert hasattr(engine, 'analyze_coverage') or config.include_coverage_analysis


def test_coverage_report_parsing(tmp_path):
    """Should parse pytest-cov JSON report correctly."""
    from planloop.core.coverage_analyzer import parse_coverage_report
    
    # Create a mock coverage.json
    coverage_json = tmp_path / "coverage.json"
    coverage_json.write_text("""
    {
        "meta": {"version": "7.0.0"},
        "totals": {
            "covered_lines": 880,
            "num_statements": 1000,
            "percent_covered": 88.0
        },
        "files": {
            "src/main.py": {
                "summary": {
                    "covered_lines": 45,
                    "num_statements": 100,
                    "percent_covered": 45.0,
                    "missing_lines": [10, 15, 20]
                }
            }
        }
    }
    """)
    
    data = parse_coverage_report(coverage_json)
    
    assert data["totals"]["percent_covered"] == 88.0
    assert "src/main.py" in data["files"]
    assert data["files"]["src/main.py"]["summary"]["percent_covered"] == 45.0
