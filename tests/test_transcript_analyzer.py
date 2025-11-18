"""Tests for transcript analyzer module.

Tests post-mortem analysis of agent transcripts for PTY issues.
Following TDD approach - tests written first.
"""

import pytest
from pathlib import Path
from datetime import datetime
import json
from unittest.mock import Mock, patch, mock_open


class TestTranscriptAnalyzer:
    """Test suite for TranscriptAnalyzer class."""

    def test_parse_transcript_jsonl(self):
        """Test parsing JSONL transcript file."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        # Mock JSONL content
        jsonl_content = """
{"timestamp": "2025-11-18T19:00:00Z", "event": "command", "command": "planloop status"}
{"timestamp": "2025-11-18T19:00:01Z", "event": "bash_command", "session_id": "work", "command": "pytest tests/", "cmd_number": 1}
{"timestamp": "2025-11-18T19:00:05Z", "event": "bash_output", "session_id": "work", "output": "...test results...", "cmd_number": 1}
        """.strip()
        
        analyzer = TranscriptAnalyzer()
        
        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            events = analyzer.parse_transcript("/fake/path/transcript.jsonl")
        
        assert len(events) == 3
        assert events[0]["event"] == "command"
        assert events[1]["event"] == "bash_command"
        assert events[2]["event"] == "bash_output"

    def test_extract_bash_commands(self):
        """Test extracting only bash commands from events."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        events = [
            {"event": "command", "command": "planloop status"},
            {"event": "bash_command", "session_id": "work", "command": "ls", "cmd_number": 1},
            {"event": "bash_output", "output": "file1.py"},
            {"event": "bash_command", "session_id": "work", "command": "pwd", "cmd_number": 2},
        ]
        
        bash_commands = analyzer.extract_bash_commands(events)
        
        assert len(bash_commands) == 2
        assert bash_commands[0]["command"] == "ls"
        assert bash_commands[1]["command"] == "pwd"

    def test_calculate_statistics(self):
        """Test calculating session statistics."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        commands = [
            {"timestamp": "2025-11-18T19:00:00Z", "cmd_number": 1},
            {"timestamp": "2025-11-18T19:01:00Z", "cmd_number": 2},
            {"timestamp": "2025-11-18T19:02:00Z", "cmd_number": 3},
        ]
        
        stats = analyzer.calculate_statistics(commands)
        
        assert stats["total_commands"] == 3
        assert "duration_minutes" in stats
        assert "avg_command_interval_seconds" in stats

    def test_detect_pty_failure_pattern(self):
        """Test detecting PTY failure in transcript."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        # Simulate failure after 43 commands
        commands = []
        for i in range(1, 44):
            commands.append({
                "timestamp": f"2025-11-18T19:{i:02d}:00Z",
                "cmd_number": i,
                "command": f"test_command_{i}",
                "error": "posix_spawnp failed" if i == 43 else None
            })
        
        failure_analysis = analyzer.detect_failure_pattern(commands)
        
        assert failure_analysis["failure_detected"] is True
        assert failure_analysis["failure_type"] == "pty_exhaustion"
        assert failure_analysis["first_failure_command"] == 43

    def test_detect_no_failure_healthy_session(self):
        """Test detecting no failure in healthy session."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        # Healthy session with 20 commands
        commands = [
            {"timestamp": f"2025-11-18T19:{i:02d}:00Z", "cmd_number": i, "error": None}
            for i in range(1, 21)
        ]
        
        failure_analysis = analyzer.detect_failure_pattern(commands)
        
        assert failure_analysis["failure_detected"] is False

    def test_generate_text_report(self):
        """Test generating human-readable text report."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        analysis = {
            "session_id": "test-session",
            "statistics": {
                "total_commands": 53,
                "duration_minutes": 47,
                "first_command": "2025-11-18T19:00:00Z",
                "last_command": "2025-11-18T19:47:00Z"
            },
            "failure_analysis": {
                "failure_detected": True,
                "failure_type": "pty_exhaustion",
                "first_failure_command": 43
            },
            "recommendations": [
                "Implement automatic rotation at 30 commands",
                "Use explicit Python paths"
            ]
        }
        
        report = analyzer.generate_report(analysis, format="text")
        
        assert "test-session" in report
        assert "53" in report
        assert "43" in report
        assert "pty_exhaustion" in report.lower() or "exhaustion" in report.lower()

    def test_generate_json_report(self):
        """Test generating JSON report."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        analysis = {
            "session_id": "test-session",
            "statistics": {"total_commands": 53},
            "failure_analysis": {"failure_detected": True}
        }
        
        report = analyzer.generate_report(analysis, format="json")
        
        # Should be valid JSON
        parsed = json.loads(report)
        assert parsed["session_id"] == "test-session"
        assert parsed["statistics"]["total_commands"] == 53

    def test_generate_markdown_report(self):
        """Test generating Markdown report."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        analysis = {
            "session_id": "test-session",
            "statistics": {"total_commands": 53},
            "failure_analysis": {"failure_detected": True}
        }
        
        report = analyzer.generate_report(analysis, format="markdown")
        
        assert "# Session Analysis" in report or "# " in report
        assert "test-session" in report
        assert "##" in report  # Should have markdown headers

    def test_analyze_session_integration(self):
        """Test full analysis workflow."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        # Mock transcript file with failure
        jsonl_content = ""
        for i in range(1, 44):
            error = "posix_spawnp failed" if i == 43 else None
            event = {
                "timestamp": f"2025-11-18T19:{i:02d}:00Z",
                "event": "bash_command",
                "session_id": "work",
                "command": f"cmd_{i}",
                "cmd_number": i
            }
            if error:
                event["error"] = error
            jsonl_content += json.dumps(event) + "\n"
        
        analyzer = TranscriptAnalyzer()
        
        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            with patch("pathlib.Path.exists", return_value=True):
                analysis = analyzer.analyze_session("work")
        
        assert analysis["statistics"]["total_commands"] == 43
        assert analysis["failure_analysis"]["failure_detected"] is True

    def test_command_frequency_analysis(self):
        """Test analyzing command frequency over time."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        # Simulate accelerating command rate (frantic retrying)
        commands = []
        # First 20: 1 per minute
        for i in range(20):
            commands.append({"timestamp": f"2025-11-18T19:{i:02d}:00Z", "cmd_number": i+1})
        # Next 20: 2 per minute (30 seconds apart)
        for i in range(20):
            commands.append({"timestamp": f"2025-11-18T19:{20+i//2:02d}:{30 if i%2 else 0:02d}Z", "cmd_number": 21+i})
        
        frequency_analysis = analyzer.analyze_command_frequency(commands)
        
        assert "phases" in frequency_analysis
        assert len(frequency_analysis["phases"]) > 0
        # Should detect rate increase
        assert frequency_analysis["rate_increased"] is True

    def test_pty_growth_timeline(self):
        """Test tracking PTY count growth over time."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        # Mock commands with PTY count annotations
        commands = [
            {"cmd_number": 1, "pty_count": 2},
            {"cmd_number": 10, "pty_count": 4},
            {"cmd_number": 20, "pty_count": 6},
            {"cmd_number": 30, "pty_count": 9},
            {"cmd_number": 40, "pty_count": 12}
        ]
        
        growth_analysis = analyzer.analyze_pty_growth(commands)
        
        assert growth_analysis["start_pty_count"] == 2
        assert growth_analysis["end_pty_count"] == 12
        assert growth_analysis["growth_rate"] > 0

    def test_identify_contributing_factors(self):
        """Test identifying factors that contributed to failure."""
        from planloop.diagnostics.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        commands = [
            {"cmd_number": i, "command": f"cd /path && source .venv && python script{i}.py"}
            for i in range(1, 44)
        ]
        
        factors = analyzer.identify_contributing_factors(commands)
        
        assert "complex_command_chains" in factors
        assert factors["complex_command_chains"] is True
