"""Tests for security pattern detection (Task 3).

Verifies that planloop suggest can integrate with bandit/semgrep
to identify security vulnerabilities and suggest fixes.
"""

import json
from pathlib import Path

import pytest


def test_security_analyzer_parses_bandit_output():
    """Security analyzer should parse bandit JSON output."""
    from planloop.core.security_analyzer import SecurityAnalyzer
    
    bandit_output = {
        "results": [
            {
                "filename": "src/api/auth.py",
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "issue_text": "Use of assert detected. Assert is removed in optimized code.",
                "line_number": 42,
                "code": "assert user_authenticated(token)"
            },
            {
                "filename": "src/utils/crypto.py",
                "issue_severity": "MEDIUM",
                "issue_confidence": "HIGH",
                "issue_text": "Use of weak cryptographic key",
                "line_number": 15,
                "code": "key = hashlib.md5(password)"
            }
        ]
    }
    
    analyzer = SecurityAnalyzer()
    issues = analyzer.parse_bandit_results(bandit_output)
    
    assert len(issues) == 2
    assert issues[0].file_path == "src/api/auth.py"
    assert issues[0].severity == "HIGH"
    assert issues[0].line_number == 42


def test_security_analyzer_generates_task_suggestions():
    """Security analyzer should generate fix task suggestions."""
    from planloop.core.security_analyzer import SecurityAnalyzer, SecurityIssue
    
    issue = SecurityIssue(
        file_path="src/api/auth.py",
        severity="HIGH",
        confidence="HIGH",
        description="Use of assert detected",
        line_number=42,
        code="assert user_authenticated(token)"
    )
    
    analyzer = SecurityAnalyzer()
    suggestions = analyzer.generate_security_tasks([issue])
    
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert "security" in suggestion.title.lower() or "auth.py" in suggestion.title.lower()
    assert suggestion.type == "fix"
    assert suggestion.priority == "high"


def test_security_analyzer_filters_by_severity():
    """Security analyzer should filter issues by severity."""
    from planloop.core.security_analyzer import SecurityAnalyzer, SecurityIssue
    
    issues = [
        SecurityIssue(
            file_path="file1.py",
            severity="HIGH",
            confidence="HIGH",
            description="Critical issue",
            line_number=10,
            code="bad_code()"
        ),
        SecurityIssue(
            file_path="file2.py",
            severity="LOW",
            confidence="MEDIUM",
            description="Minor issue",
            line_number=20,
            code="less_bad_code()"
        )
    ]
    
    analyzer = SecurityAnalyzer()
    
    # Should only return high severity
    high_only = analyzer.filter_by_severity(issues, min_severity="HIGH")
    assert len(high_only) == 1
    assert high_only[0].severity == "HIGH"
    
    # Should return all
    all_issues = analyzer.filter_by_severity(issues, min_severity="LOW")
    assert len(all_issues) == 2


def test_suggest_config_includes_security_analysis():
    """SuggestConfig should support security analysis options."""
    from planloop.config import SuggestConfig
    
    config = SuggestConfig(
        include_security_analysis=True,
        security_min_severity="MEDIUM"
    )
    
    assert config.include_security_analysis is True
    assert config.security_min_severity == "MEDIUM"


def test_security_analyzer_handles_empty_results():
    """Security analyzer should handle empty results gracefully."""
    from planloop.core.security_analyzer import SecurityAnalyzer
    
    analyzer = SecurityAnalyzer()
    issues = analyzer.parse_bandit_results({"results": []})
    
    assert issues == []
    
    suggestions = analyzer.generate_security_tasks([])
    assert suggestions == []
