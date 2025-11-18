"""Tests for batch workflow support (Task 4).

Verifies that planloop suggest supports batch modes like --weekly
for regular automated audits.
"""

from pathlib import Path

import pytest


def test_suggest_cli_accepts_weekly_flag():
    """planloop suggest should accept --weekly flag."""
    from typer.testing import CliRunner
    from planloop.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["suggest", "--help"])
    
    assert result.exit_code == 0
    assert "--weekly" in result.stdout or "weekly" in result.stdout.lower()


def test_weekly_mode_generates_comprehensive_audit():
    """Weekly mode should perform comprehensive codebase audit."""
    from planloop.core.suggest import SuggestionEngine
    from planloop.config import SuggestConfig
    
    config = SuggestConfig(
        batch_mode="weekly",
        context_depth="deep",
        include_coverage_analysis=True,
        include_security_analysis=True
    )
    
    assert config.batch_mode == "weekly"
    assert config.context_depth == "deep"


def test_suggest_config_supports_batch_modes():
    """SuggestConfig should support batch mode configuration."""
    from planloop.config import SuggestConfig
    
    # Test different batch modes
    config_daily = SuggestConfig(batch_mode="daily")
    assert config_daily.batch_mode == "daily"
    
    config_weekly = SuggestConfig(batch_mode="weekly")
    assert config_weekly.batch_mode == "weekly"
    
    config_none = SuggestConfig(batch_mode=None)
    assert config_none.batch_mode is None


def test_batch_mode_adjusts_suggestion_limits():
    """Batch mode should automatically adjust suggestion limits."""
    from planloop.config import SuggestConfig
    
    # Weekly mode should allow more suggestions
    config_weekly = SuggestConfig(
        batch_mode="weekly",
        max_suggestions=5  # Default
    )
    
    # Should have batch-specific defaults
    assert hasattr(config_weekly, 'get_effective_max_suggestions')
    effective_max = config_weekly.get_effective_max_suggestions()
    
    # Weekly should suggest more items for comprehensive audit
    assert effective_max >= 10


def test_suggest_weekly_stores_audit_report(tmp_path, monkeypatch):
    """Weekly mode should store audit report for tracking."""
    import os
    from datetime import datetime
    
    # Set up temporary planloop home
    home = tmp_path / ".planloop"
    home.mkdir()
    monkeypatch.setenv("PLANLOOP_HOME", str(home))
    
    from planloop.home import initialize_home
    initialize_home()
    
    # Check audit reports directory exists
    reports_dir = home / "audit_reports"
    
    # Should be created on first weekly run
    from planloop.core.suggest import store_audit_report
    
    report_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "suggestions_count": 12,
        "mode": "weekly"
    }
    
    report_path = store_audit_report(report_data, reports_dir)
    
    assert report_path.exists()
    assert "weekly" in report_path.name or "audit" in report_path.name
