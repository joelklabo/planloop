"""Coverage analysis for identifying test gaps."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .suggest import TaskSuggestion
from .state import TaskType


class CoverageGap(BaseModel):
    """Represents a coverage gap in a file."""
    
    file_path: str
    coverage_percent: float
    missing_lines: list[int]
    total_lines: int


class CoverageAnalyzer:
    """Analyzes test coverage to identify gaps and suggest tests."""
    
    def __init__(self, coverage_data: dict[str, Any]):
        """Initialize with coverage data.
        
        Args:
            coverage_data: Parsed coverage report (pytest-cov JSON format)
        """
        self.coverage_data = coverage_data
    
    def find_coverage_gaps(self, threshold: float = 70.0) -> list[CoverageGap]:
        """Find files with coverage below threshold.
        
        Args:
            threshold: Coverage percentage threshold (default: 70%)
            
        Returns:
            List of coverage gaps
        """
        gaps = []
        files = self.coverage_data.get("files", {})
        
        for file_path, file_data in files.items():
            summary = file_data.get("summary", {})
            coverage_percent = summary.get("percent_covered", 0.0)
            
            if coverage_percent < threshold:
                gaps.append(CoverageGap(
                    file_path=file_path,
                    coverage_percent=coverage_percent,
                    missing_lines=summary.get("missing_lines", []),
                    total_lines=summary.get("num_statements", 
                                          summary.get("covered_lines", 0) + len(summary.get("missing_lines", [])))
                ))
        
        return gaps
    
    def generate_test_suggestions(self, gaps: list[CoverageGap]) -> list[TaskSuggestion]:
        """Generate task suggestions for coverage gaps.
        
        Args:
            gaps: List of coverage gaps
            
        Returns:
            List of test task suggestions
        """
        suggestions = []
        
        for gap in gaps:
            # Determine priority based on coverage level
            if gap.coverage_percent < 50:
                priority = "high"
            elif gap.coverage_percent < 70:
                priority = "medium"
            else:
                priority = "low"
            
            # Extract module name
            module_name = Path(gap.file_path).stem
            
            suggestions.append(TaskSuggestion(
                title=f"Add tests for {module_name}.py ({gap.coverage_percent:.1f}% coverage)",
                type=TaskType.TEST,
                priority=priority,
                rationale=f"File has {gap.coverage_percent:.1f}% test coverage with {len(gap.missing_lines)} uncovered lines. "
                         f"Increasing coverage will improve code reliability.",
                implementation_notes=f"Focus on lines: {gap.missing_lines[:10]}{'...' if len(gap.missing_lines) > 10 else ''}",
                affected_files=[gap.file_path]
            ))
        
        return suggestions


def parse_coverage_report(report_path: Path) -> dict[str, Any]:
    """Parse pytest-cov JSON coverage report.
    
    Args:
        report_path: Path to coverage.json file
        
    Returns:
        Parsed coverage data
    """
    with report_path.open("r", encoding="utf-8") as f:
        return json.load(f)
