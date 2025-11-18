"""Security analysis for identifying vulnerabilities and generating fix tasks."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from .suggest import TaskSuggestion
from .state import TaskType


class SecurityIssue(BaseModel):
    """Represents a security issue found by analysis tools."""
    
    file_path: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    description: str
    line_number: int
    code: str


class SecurityAnalyzer:
    """Analyzes code for security vulnerabilities using bandit/semgrep."""
    
    def parse_bandit_results(self, bandit_output: dict[str, Any]) -> list[SecurityIssue]:
        """Parse bandit JSON output into security issues.
        
        Args:
            bandit_output: Parsed bandit JSON report
            
        Returns:
            List of security issues
        """
        issues = []
        results = bandit_output.get("results", [])
        
        for result in results:
            issues.append(SecurityIssue(
                file_path=result["filename"],
                severity=result["issue_severity"],
                confidence=result["issue_confidence"],
                description=result["issue_text"],
                line_number=result["line_number"],
                code=result["code"]
            ))
        
        return issues
    
    def filter_by_severity(
        self, 
        issues: list[SecurityIssue], 
        min_severity: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    ) -> list[SecurityIssue]:
        """Filter security issues by minimum severity level.
        
        Args:
            issues: List of security issues
            min_severity: Minimum severity to include
            
        Returns:
            Filtered list of issues
        """
        severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        min_level = severity_order[min_severity]
        
        return [
            issue for issue in issues 
            if severity_order[issue.severity] >= min_level
        ]
    
    def generate_security_tasks(self, issues: list[SecurityIssue]) -> list[TaskSuggestion]:
        """Generate task suggestions for security issues.
        
        Args:
            issues: List of security issues
            
        Returns:
            List of fix task suggestions
        """
        suggestions = []
        
        for issue in issues:
            # Map severity to priority
            priority_map = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
            priority = priority_map[issue.severity]
            
            # Extract filename
            from pathlib import Path
            filename = Path(issue.file_path).name
            
            suggestions.append(TaskSuggestion(
                title=f"Fix security issue in {filename} (line {issue.line_number})",
                type=TaskType.FIX,
                priority=priority,
                rationale=f"{issue.severity} severity: {issue.description}",
                implementation_notes=f"Review and fix code at line {issue.line_number}:\n{issue.code}",
                affected_files=[issue.file_path]
            ))
        
        return suggestions
