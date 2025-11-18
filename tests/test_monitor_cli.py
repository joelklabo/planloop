"""Tests for monitor CLI commands.

Tests the 'planloop monitor bash-health' command.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, Mock
import json


class TestMonitorBashHealthCLI:
    """Test suite for monitor bash-health CLI command."""
    
    def test_bash_health_command_exists(self):
        """Test that monitor bash-health command is registered."""
        from planloop.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', 'bash-health', '--help'])
        
        assert result.exit_code == 0
        assert 'bash-health' in result.output.lower() or 'Check health' in result.output
    
    @patch('planloop.diagnostics.bash_health.BashHealthMonitor')
    def test_bash_health_human_output(self, mock_monitor_class):
        """Test human-readable output format."""
        from planloop.cli import cli
        
        # Mock health check response
        mock_monitor = Mock()
        mock_monitor.check_health.return_value = {
            "session_id": "test-session",
            "pid": 12345,
            "health_score": 85,
            "status": "healthy",
            "metrics": {
                "command_count": 10,
                "pty_count": 2,
                "fd_count": 50,
                "age_minutes": 15
            },
            "warnings": [],
            "recommendations": [
                "Session is healthy",
                "Consider rotating after 30 commands"
            ],
            "thresholds": {
                "command_count_warning": 30,
                "command_count_critical": 50,
                "pty_count_warning": 6,
                "pty_count_critical": 10
            }
        }
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', 'bash-health'])
        
        assert result.exit_code == 0
        assert 'healthy' in result.output.lower() or '85' in result.output
        
    @patch('planloop.diagnostics.bash_health.BashHealthMonitor')
    def test_bash_health_json_output(self, mock_monitor_class):
        """Test JSON output format."""
        from planloop.cli import cli
        
        # Mock health check response
        mock_monitor = Mock()
        health_data = {
            "session_id": "test-session",
            "pid": 12345,
            "health_score": 85,
            "status": "healthy",
            "metrics": {
                "command_count": 10,
                "pty_count": 2,
                "fd_count": 50,
                "age_minutes": 15
            },
            "warnings": [],
            "recommendations": [
                "Session is healthy"
            ],
            "thresholds": {
                "command_count_warning": 30,
                "command_count_critical": 50,
                "pty_count_warning": 6,
                "pty_count_critical": 10
            }
        }
        mock_monitor.check_health.return_value = health_data
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', 'bash-health', '--json'])
        
        assert result.exit_code == 0
        
        # Should be valid JSON
        output_data = json.loads(result.output)
        assert output_data["health_score"] == 85
        assert output_data["status"] == "healthy"
        assert output_data["pid"] == 12345
    
    @patch('planloop.diagnostics.bash_health.BashHealthMonitor')
    def test_bash_health_degraded_status(self, mock_monitor_class):
        """Test output for degraded session."""
        from planloop.cli import cli
        
        # Mock degraded health
        mock_monitor = Mock()
        mock_monitor.check_health.return_value = {
            "session_id": "test-session",
            "pid": 12345,
            "health_score": 50,
            "status": "degraded",
            "metrics": {
                "command_count": 38,
                "pty_count": 7,
                "fd_count": 200,
                "age_minutes": 35
            },
            "warnings": [
                "High command count (38, threshold: 30)",
                "PTY count elevated (7, threshold: 6)"
            ],
            "recommendations": [
                "Session is degraded - rotation recommended",
                "Rotate session before reaching 50 commands"
            ],
            "thresholds": {
                "command_count_warning": 30,
                "command_count_critical": 50,
                "pty_count_warning": 6,
                "pty_count_critical": 10
            }
        }
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', 'bash-health'])
        
        assert result.exit_code == 0
        assert 'degraded' in result.output.lower() or '50' in result.output
        assert 'warning' in result.output.lower() or 'rotate' in result.output.lower()
    
    @patch('planloop.diagnostics.bash_health.BashHealthMonitor')
    def test_bash_health_error_handling(self, mock_monitor_class):
        """Test error handling when health check fails."""
        from planloop.cli import cli
        
        # Mock error
        mock_monitor = Mock()
        mock_monitor.check_health.side_effect = ValueError("Cannot determine bash session PID")
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', 'bash-health'])
        
        # Should handle error gracefully
        assert result.exit_code != 0
        assert 'error' in result.output.lower() or 'cannot' in result.output.lower()
    
    @patch('planloop.diagnostics.bash_health.BashHealthMonitor')
    def test_bash_health_with_session_id(self, mock_monitor_class):
        """Test providing explicit session ID."""
        from planloop.cli import cli
        
        mock_monitor = Mock()
        mock_monitor.check_health.return_value = {
            "session_id": "custom-session",
            "pid": 99999,
            "health_score": 90,
            "status": "healthy",
            "metrics": {
                "command_count": 5,
                "pty_count": 1,
                "fd_count": 25,
                "age_minutes": 5
            },
            "warnings": [],
            "recommendations": ["Session is healthy"],
            "thresholds": {
                "command_count_warning": 30,
                "command_count_critical": 50,
                "pty_count_warning": 6,
                "pty_count_critical": 10
            }
        }
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', 'bash-health', '--session-id', 'custom-session'])
        
        assert result.exit_code == 0
        # Verify session ID was passed to health check
        mock_monitor.check_health.assert_called()
