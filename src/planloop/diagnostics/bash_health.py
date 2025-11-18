"""Bash session health monitoring for PTY diagnostics.

This module provides health monitoring for bash sessions to detect and prevent
PTY (pseudo-terminal) resource exhaustion that leads to 'posix_spawnp failed' errors.

Based on production observability patterns using RED and USE metrics.
"""

import os
import subprocess
from datetime import datetime, timedelta
from typing import Optional


class BashHealthMonitor:
    """Monitor health of bash sessions using RED/USE metrics.
    
    Health Score Algorithm (0-100):
    - Command count penalty: 0-30 points
    - PTY count penalty: 0-40 points
    - Age penalty: 0-20 points
    - Recent error penalty: 0-10 points
    
    Status Classification:
    - 80-100: Healthy - No action needed
    - 60-79: Watch - Monitor closely
    - 40-59: Degraded - Consider rotation
    - 20-39: Critical - Rotate immediately
    - 0-19: Failed - Already corrupted
    """
    
    # Thresholds for health scoring
    COMMAND_COUNT_MEDIUM = 20
    COMMAND_COUNT_HIGH = 30
    COMMAND_COUNT_CRITICAL = 50
    
    PTY_COUNT_MEDIUM = 4
    PTY_COUNT_HIGH = 6
    PTY_COUNT_CRITICAL = 10
    
    AGE_WARNING_MINUTES = 40
    AGE_CRITICAL_MINUTES = 60
    
    # Error recency window (minutes)
    ERROR_RECENCY_MINUTES = 5
    
    def calculate_health_score(self, metrics: dict) -> int:
        """Calculate 0-100 health score for bash session.
        
        Args:
            metrics: Dictionary with keys:
                - command_count: Number of commands executed
                - pty_count: Number of PTYs in use
                - age_minutes: Age of session in minutes
                - last_error: Optional dict with 'timestamp' and 'error'
        
        Returns:
            Health score (0-100)
        """
        score = 100
        
        command_count = metrics.get("command_count", 0)
        pty_count = metrics.get("pty_count", 0)
        age_minutes = metrics.get("age_minutes", 0)
        last_error = metrics.get("last_error")
        
        # Command count penalty (0-30 points)
        if command_count > self.COMMAND_COUNT_CRITICAL:
            score -= 30  # Critical
        elif command_count > self.COMMAND_COUNT_HIGH:
            score -= 20  # High
        elif command_count > self.COMMAND_COUNT_MEDIUM:
            score -= 10  # Medium
        
        # PTY count penalty (0-40 points) - HIGHEST IMPACT
        if pty_count > self.PTY_COUNT_CRITICAL:
            score -= 40  # Critical
        elif pty_count > self.PTY_COUNT_HIGH:
            score -= 25  # High
        elif pty_count > self.PTY_COUNT_MEDIUM:
            score -= 15  # Medium
        
        # Age penalty (0-20 points)
        if age_minutes > self.AGE_CRITICAL_MINUTES:
            score -= 20  # Old session
        elif age_minutes > self.AGE_WARNING_MINUTES:
            score -= 10  # Aging
        
        # Recent error penalty (0-10 points)
        if last_error and self._is_recent_error(last_error):
            score -= 10  # Critical - already failing
        
        return max(0, score)
    
    def _is_recent_error(self, error_info: dict) -> bool:
        """Check if error occurred recently (within recency window)."""
        if not error_info or "timestamp" not in error_info:
            return False
        
        error_time = error_info["timestamp"]
        if not isinstance(error_time, datetime):
            return False
        
        time_since_error = datetime.now() - error_time
        return time_since_error < timedelta(minutes=self.ERROR_RECENCY_MINUTES)
    
    def classify_status(self, health_score: int) -> str:
        """Classify health status based on score.
        
        Args:
            health_score: Score from 0-100
        
        Returns:
            Status string: 'healthy', 'watch', 'degraded', 'critical', or 'failed'
        """
        if health_score >= 80:
            return "healthy"
        elif health_score >= 60:
            return "watch"
        elif health_score >= 40:
            return "degraded"
        elif health_score >= 20:
            return "critical"
        else:
            return "failed"
    
    def count_ptys(self, pid: int) -> int:
        """Count PTYs in use by process using lsof.
        
        Args:
            pid: Process ID
        
        Returns:
            Number of PTYs, or 0 if lsof not available
        """
        try:
            result = subprocess.run(
                ["lsof", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return 0
            
            # Count lines containing /dev/pts or /dev/tty
            pty_lines = [
                line for line in result.stdout.split('\n')
                if '/dev/pts' in line or '/dev/tty' in line
            ]
            
            return len(pty_lines)
            
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # lsof not available or timeout
            return 0
    
    def count_fds(self, pid: int) -> int:
        """Count open file descriptors from /proc.
        
        Args:
            pid: Process ID
        
        Returns:
            Number of open FDs, or 0 if /proc not available
        """
        try:
            fd_dir = f"/proc/{pid}/fd"
            fds = os.listdir(fd_dir)
            return len(fds)
        except (FileNotFoundError, PermissionError, OSError):
            # /proc not available (macOS) or permission denied
            return 0
    
    def get_current_session_pid(self) -> Optional[int]:
        """Get current bash session PID.
        
        Returns:
            Process ID or None if cannot determine
        """
        # Try to get parent PID from environment
        ppid = os.getppid()
        if ppid:
            return ppid
        
        return None
    
    def get_command_count(self, session_id: Optional[str] = None) -> int:
        """Get command count for session from planloop logs.
        
        Args:
            session_id: Optional session ID
        
        Returns:
            Command count (0 if cannot determine)
        """
        # TODO: Implement log parsing for command counting
        # For now, return 0 as placeholder
        return 0
    
    def get_recommendations(self, health_score: int, metrics: dict) -> list[str]:
        """Generate actionable recommendations based on health status.
        
        Args:
            health_score: Current health score
            metrics: Metrics dictionary
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        status = self.classify_status(health_score)
        command_count = metrics.get("command_count", 0)
        pty_count = metrics.get("pty_count", 0)
        age_minutes = metrics.get("age_minutes", 0)
        
        if status == "healthy":
            recommendations.append("Session is healthy")
            recommendations.append(f"Consider rotating after {self.COMMAND_COUNT_HIGH} commands")
            
        elif status == "watch":
            recommendations.append("Session is stable but approaching limits")
            if command_count > self.COMMAND_COUNT_MEDIUM:
                recommendations.append(
                    f"Command count elevated ({command_count}, threshold: {self.COMMAND_COUNT_MEDIUM})"
                )
            if pty_count > self.PTY_COUNT_MEDIUM:
                recommendations.append(
                    f"PTY count increasing ({pty_count}, threshold: {self.PTY_COUNT_MEDIUM})"
                )
            recommendations.append("Monitor closely and prepare to rotate")
            
        elif status == "degraded":
            recommendations.append("Session is degraded - rotation recommended")
            if command_count > self.COMMAND_COUNT_HIGH:
                recommendations.append(
                    f"High command count ({command_count}, threshold: {self.COMMAND_COUNT_HIGH})"
                )
            if pty_count > self.PTY_COUNT_HIGH:
                recommendations.append(
                    f"Elevated PTY count ({pty_count}, threshold: {self.PTY_COUNT_HIGH})"
                )
            recommendations.append("Rotate session before reaching 50 commands")
            recommendations.append("Use explicit Python paths to reduce subprocess spawning")
            
        elif status == "critical":
            recommendations.append("Session is critical - rotate immediately")
            recommendations.append("Resource exhaustion imminent")
            if command_count > self.COMMAND_COUNT_CRITICAL:
                recommendations.append(
                    f"Command count critical ({command_count}, limit: {self.COMMAND_COUNT_CRITICAL})"
                )
            if pty_count > self.PTY_COUNT_CRITICAL:
                recommendations.append(
                    f"PTY count critical ({pty_count}, limit: {self.PTY_COUNT_CRITICAL})"
                )
            recommendations.append("Create new session immediately")
            recommendations.append("Prefer alternative tools (view, create, grep) over bash")
            
        else:  # failed
            recommendations.append("Session has failed - PTY corruption detected")
            recommendations.append("Create fresh bash session with new ID")
            recommendations.append("Old session cannot be recovered")
            recommendations.append("Review transcript for failure patterns")
        
        return recommendations
    
    def check_health(self, session_id: Optional[str] = None, pid: Optional[int] = None) -> dict:
        """Perform complete health check on bash session.
        
        Args:
            session_id: Optional session ID for logging
            pid: Optional PID (uses current if not provided)
        
        Returns:
            Health report dictionary with all metrics and recommendations
        """
        # Determine PID
        if pid is None:
            pid = self.get_current_session_pid()
        
        if pid is None:
            raise ValueError("Cannot determine bash session PID")
        
        # Collect metrics
        pty_count = self.count_ptys(pid)
        fd_count = self.count_fds(pid)
        command_count = self.get_command_count(session_id)
        
        # TODO: Calculate actual age from session start time
        # For now, use 0 as placeholder
        age_minutes = 0
        
        metrics = {
            "command_count": command_count,
            "pty_count": pty_count,
            "fd_count": fd_count,
            "age_minutes": age_minutes,
            "last_error": None
        }
        
        # Calculate health score
        health_score = self.calculate_health_score(metrics)
        status = self.classify_status(health_score)
        
        # Generate recommendations
        recommendations = self.get_recommendations(health_score, metrics)
        
        # Identify warnings
        warnings = []
        if command_count > self.COMMAND_COUNT_HIGH:
            warnings.append(
                f"High command count ({command_count}, threshold: {self.COMMAND_COUNT_HIGH})"
            )
        if pty_count > self.PTY_COUNT_HIGH:
            warnings.append(
                f"PTY count elevated ({pty_count}, threshold: {self.PTY_COUNT_HIGH})"
            )
        if age_minutes > self.AGE_WARNING_MINUTES:
            warnings.append(
                f"Session age high ({age_minutes} min, threshold: {self.AGE_WARNING_MINUTES} min)"
            )
        
        # Build health report
        return {
            "session_id": session_id or "unknown",
            "pid": pid,
            "health_score": health_score,
            "status": status,
            "metrics": metrics,
            "warnings": warnings,
            "recommendations": recommendations,
            "thresholds": {
                "command_count_warning": self.COMMAND_COUNT_HIGH,
                "command_count_critical": self.COMMAND_COUNT_CRITICAL,
                "pty_count_warning": self.PTY_COUNT_HIGH,
                "pty_count_critical": self.PTY_COUNT_CRITICAL
            }
        }
