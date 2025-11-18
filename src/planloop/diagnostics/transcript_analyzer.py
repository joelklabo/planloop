"""Transcript analyzer for post-mortem PTY diagnostics.

Analyzes agent-transcript.jsonl files to detect PTY failure patterns,
calculate session statistics, and generate recommendations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TranscriptAnalyzer:
    """Analyze agent transcripts for PTY issues."""
    
    def parse_transcript(self, transcript_path: str) -> list[dict]:
        """Parse JSONL transcript file into list of events.
        
        Args:
            transcript_path: Path to agent-transcript.jsonl file
        
        Returns:
            List of event dictionaries
        """
        events = []
        
        with open(transcript_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        
        return events
    
    def extract_bash_commands(self, events: list[dict]) -> list[dict]:
        """Extract only bash command events from transcript.
        
        Args:
            events: List of all events
        
        Returns:
            List of bash command events only
        """
        return [e for e in events if e.get("event") == "bash_command"]
    
    def calculate_statistics(self, commands: list[dict]) -> dict:
        """Calculate session statistics from commands.
        
        Args:
            commands: List of bash command events
        
        Returns:
            Statistics dictionary
        """
        if not commands:
            return {
                "total_commands": 0,
                "duration_minutes": 0,
                "avg_command_interval_seconds": 0
            }
        
        total = len(commands)
        
        # Parse timestamps
        timestamps = []
        for cmd in commands:
            ts_str = cmd.get("timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    timestamps.append(ts)
                except (ValueError, AttributeError):
                    pass
        
        duration_minutes = 0
        avg_interval = 0
        
        if len(timestamps) >= 2:
            duration = timestamps[-1] - timestamps[0]
            duration_minutes = duration.total_seconds() / 60
            
            # Calculate average interval
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
        
        return {
            "total_commands": total,
            "duration_minutes": round(duration_minutes, 1),
            "avg_command_interval_seconds": round(avg_interval, 1),
            "first_command": commands[0].get("timestamp") if commands else None,
            "last_command": commands[-1].get("timestamp") if commands else None
        }
    
    def detect_failure_pattern(self, commands: list[dict]) -> dict:
        """Detect PTY failure patterns in command sequence.
        
        Args:
            commands: List of bash command events
        
        Returns:
            Failure analysis dictionary
        """
        failure_detected = False
        failure_type = None
        first_failure_cmd = None
        
        for cmd in commands:
            error = cmd.get("error")
            if error and ("posix_spawnp" in error or "pty" in error.lower()):
                failure_detected = True
                failure_type = "pty_exhaustion"
                first_failure_cmd = cmd.get("cmd_number")
                break
        
        return {
            "failure_detected": failure_detected,
            "failure_type": failure_type,
            "first_failure_command": first_failure_cmd
        }
    
    def analyze_command_frequency(self, commands: list[dict]) -> dict:
        """Analyze command frequency over time.
        
        Args:
            commands: List of bash command events
        
        Returns:
            Frequency analysis with phases and rate changes
        """
        if len(commands) < 10:
            return {"phases": [], "rate_increased": False}
        
        # Divide into phases (first half vs second half)
        mid = len(commands) // 2
        first_half = commands[:mid]
        second_half = commands[mid:]
        
        # Calculate rates for each phase
        def calc_rate(cmds):
            if len(cmds) < 2:
                return 0
            timestamps = []
            for cmd in cmds:
                ts_str = cmd.get("timestamp", "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        timestamps.append(ts)
                    except:
                        pass
            if len(timestamps) >= 2:
                duration = (timestamps[-1] - timestamps[0]).total_seconds() / 60
                return len(cmds) / duration if duration > 0 else 0
            return 0
        
        first_rate = calc_rate(first_half)
        second_rate = calc_rate(second_half)
        
        return {
            "phases": [
                {"commands": len(first_half), "rate_per_minute": round(first_rate, 2)},
                {"commands": len(second_half), "rate_per_minute": round(second_rate, 2)}
            ],
            "rate_increased": second_rate > first_rate * 1.5  # 50% increase threshold
        }
    
    def analyze_pty_growth(self, commands: list[dict]) -> dict:
        """Analyze PTY count growth over time.
        
        Args:
            commands: List of bash command events with pty_count
        
        Returns:
            PTY growth analysis
        """
        pty_counts = [cmd.get("pty_count") for cmd in commands if cmd.get("pty_count") is not None]
        
        if not pty_counts:
            return {"start_pty_count": 0, "end_pty_count": 0, "growth_rate": 0}
        
        start = pty_counts[0]
        end = pty_counts[-1]
        growth = end - start
        growth_rate = growth / len(pty_counts) if len(pty_counts) > 0 else 0
        
        return {
            "start_pty_count": start,
            "end_pty_count": end,
            "growth_rate": round(growth_rate, 2)
        }
    
    def identify_contributing_factors(self, commands: list[dict]) -> dict:
        """Identify factors that contributed to PTY exhaustion.
        
        Args:
            commands: List of bash command events
        
        Returns:
            Dictionary of contributing factors
        """
        factors = {
            "complex_command_chains": False,
            "subprocess_spawning": False,
            "no_session_rotation": True  # Assume true if we got this far
        }
        
        # Check for complex command chains (multiple && or ;)
        for cmd in commands:
            command_str = cmd.get("command", "")
            if command_str.count("&&") >= 2 or command_str.count(";") >= 2:
                factors["complex_command_chains"] = True
            if "source" in command_str and ("&&" in command_str or ";" in command_str):
                factors["subprocess_spawning"] = True
        
        return factors
    
    def generate_report(self, analysis: dict, format: str = "text") -> str:
        """Generate analysis report in specified format.
        
        Args:
            analysis: Complete analysis dictionary
            format: Output format (text, json, markdown)
        
        Returns:
            Formatted report string
        """
        if format == "json":
            return json.dumps(analysis, indent=2)
        
        elif format == "markdown":
            return self._generate_markdown_report(analysis)
        
        else:  # text
            return self._generate_text_report(analysis)
    
    def _generate_text_report(self, analysis: dict) -> str:
        """Generate text report."""
        session_id = analysis.get("session_id", "unknown")
        stats = analysis.get("statistics", {})
        failure = analysis.get("failure_analysis", {})
        recs = analysis.get("recommendations", [])
        
        report = []
        report.append(f"Session Analysis: {session_id}")
        report.append("=" * 60)
        report.append("")
        report.append("Summary:")
        report.append(f"  Total Commands: {stats.get('total_commands', 0)}")
        report.append(f"  Duration: {stats.get('duration_minutes', 0)} minutes")
        report.append("")
        
        if failure.get("failure_detected"):
            report.append(f"FAILURE DETECTED: {failure.get('failure_type', 'unknown')}")
            report.append(f"  First failure at command: {failure.get('first_failure_command', 'N/A')}")
            report.append("")
        
        if recs:
            report.append("Recommendations:")
            for rec in recs:
                report.append(f"  - {rec}")
        
        return "\n".join(report)
    
    def _generate_markdown_report(self, analysis: dict) -> str:
        """Generate markdown report."""
        session_id = analysis.get("session_id", "unknown")
        stats = analysis.get("statistics", {})
        failure = analysis.get("failure_analysis", {})
        recs = analysis.get("recommendations", [])
        
        report = []
        report.append(f"# Session Analysis: {session_id}")
        report.append("")
        report.append("## Summary")
        report.append(f"- **Total Commands**: {stats.get('total_commands', 0)}")
        report.append(f"- **Duration**: {stats.get('duration_minutes', 0)} minutes")
        report.append("")
        
        if failure.get("failure_detected"):
            report.append("## Failure Detected")
            report.append(f"**Type**: {failure.get('failure_type', 'unknown')}")
            report.append(f"**First Failure**: Command {failure.get('first_failure_command', 'N/A')}")
            report.append("")
        
        if recs:
            report.append("## Recommendations")
            for rec in recs:
                report.append(f"- {rec}")
        
        return "\n".join(report)
    
    def analyze_session(self, session_id: str) -> dict:
        """Perform complete analysis of session transcript.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Complete analysis dictionary
        """
        # Find transcript file
        transcript_path = Path.home() / ".planloop" / "sessions" / session_id / "logs" / "agent-transcript.jsonl"
        
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")
        
        # Parse and analyze
        events = self.parse_transcript(str(transcript_path))
        commands = self.extract_bash_commands(events)
        
        statistics = self.calculate_statistics(commands)
        failure_analysis = self.detect_failure_pattern(commands)
        frequency_analysis = self.analyze_command_frequency(commands)
        factors = self.identify_contributing_factors(commands)
        
        # Generate recommendations
        recommendations = []
        if failure_analysis.get("failure_detected"):
            recommendations.append("Implement automatic rotation at 30 commands")
            if factors.get("complex_command_chains"):
                recommendations.append("Simplify command chains")
            if factors.get("subprocess_spawning"):
                recommendations.append("Use explicit Python paths")
        
        return {
            "session_id": session_id,
            "statistics": statistics,
            "failure_analysis": failure_analysis,
            "frequency_analysis": frequency_analysis,
            "contributing_factors": factors,
            "recommendations": recommendations
        }
