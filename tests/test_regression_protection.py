"""Test regression protection for agent baselines"""
import json
import subprocess
from pathlib import Path
import pytest


def test_baseline_config_file_exists():
    """Baseline configuration should be version-controlled"""
    baseline_file = Path("labs/baseline.json")
    assert baseline_file.exists(), "labs/baseline.json should exist for version control"


def test_baseline_config_structure():
    """Baseline config should have proper structure"""
    baseline_file = Path("labs/baseline.json")
    with open(baseline_file) as f:
        config = json.load(f)
    
    assert "copilot" in config, "Must have copilot baseline"
    assert "pass_rate" in config["copilot"], "Must track pass rate"
    assert "avg_score" in config["copilot"], "Must track avg score"
    assert "version" in config["copilot"], "Must track prompt version"
    assert "last_updated" in config["copilot"], "Must track when baseline was set"


def test_baseline_config_has_reasonable_values():
    """Baseline values should be realistic"""
    baseline_file = Path("labs/baseline.json")
    with open(baseline_file) as f:
        config = json.load(f)
    
    copilot = config["copilot"]
    assert 0 <= copilot["pass_rate"] <= 100, "Pass rate should be 0-100%"
    assert 0 <= copilot["avg_score"] <= 100, "Avg score should be 0-100"
    assert copilot["version"].startswith("v"), "Version should start with 'v'"


def test_check_baseline_script_uses_config():
    """check_baseline.sh should read from baseline.json"""
    script_path = Path("labs/check_baseline.sh")
    content = script_path.read_text()
    
    # Should reference baseline.json
    assert "baseline.json" in content, "Script should read baseline.json"
    # Should not have hardcoded values
    assert "BASELINE_PASS_RATE=" not in content or "baseline.json" in content, \
        "Should use baseline.json instead of hardcoded values"


def test_ci_workflow_includes_regression_check():
    """CI workflow should check for regressions when prompts change"""
    ci_file = Path(".github/workflows/ci.yml")
    content = ci_file.read_text()
    
    # Should have a regression check job or step
    assert "regression" in content.lower() or "baseline" in content.lower(), \
        "CI should include regression checking"


def test_baseline_update_script_exists():
    """There should be a script to update baselines"""
    update_script = Path("labs/update_baseline.sh")
    assert update_script.exists(), "labs/update_baseline.sh should exist"
    assert update_script.is_file(), "Should be a file"


def test_update_baseline_script_is_executable():
    """Update baseline script should be executable"""
    update_script = Path("labs/update_baseline.sh")
    import stat
    mode = update_script.stat().st_mode
    assert mode & stat.S_IXUSR, "Script should be executable"
