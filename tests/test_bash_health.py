"""Tests for bash health monitoring module.

Following TDD approach - tests written first to define expected behavior.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestBashHealthMonitor:
    """Test suite for BashHealthMonitor class."""

    def test_calculate_health_score_healthy_session(self):
        """Test health score calculation for healthy session (80-100)."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        # Healthy session: low command count, few PTYs, recent
        metrics = {
            "command_count": 10,
            "pty_count": 2,
            "age_minutes": 15,
            "last_error": None
        }
        
        score = monitor.calculate_health_score(metrics)
        
        assert 80 <= score <= 100, f"Healthy session should score 80-100, got {score}"

    def test_calculate_health_score_degraded_session(self):
        """Test health score calculation for degraded session (40-59)."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        # Degraded session: high command count, elevated PTYs
        metrics = {
            "command_count": 38,
            "pty_count": 7,
            "age_minutes": 35,
            "last_error": None
        }
        
        score = monitor.calculate_health_score(metrics)
        
        assert 40 <= score <= 59, f"Degraded session should score 40-59, got {score}"

    def test_calculate_health_score_critical_session(self):
        """Test health score calculation for critical session (20-39)."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        # Critical session: high command count, many PTYs, old
        # Penalties: 30 (command) + 40 (pty) + 10 (age) = 80 total
        # Score: 100 - 80 = 20 (bottom of critical range)
        metrics = {
            "command_count": 52,  # Above 50 threshold = 30 penalty
            "pty_count": 11,      # Above 10 threshold = 40 penalty
            "age_minutes": 50,    # Above 40 threshold = 10 penalty
            "last_error": None
        }
        
        score = monitor.calculate_health_score(metrics)
        
        assert 20 <= score <= 39, f"Critical session should score 20-39, got {score}"

    def test_calculate_health_score_with_recent_error(self):
        """Test that recent errors reduce health score."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        # Session with recent error should score lower
        metrics_no_error = {
            "command_count": 25,
            "pty_count": 4,
            "age_minutes": 30,
            "last_error": None
        }
        
        metrics_with_error = {
            "command_count": 25,
            "pty_count": 4,
            "age_minutes": 30,
            "last_error": {
                "timestamp": datetime.now(),
                "error": "posix_spawnp failed"
            }
        }
        
        score_no_error = monitor.calculate_health_score(metrics_no_error)
        score_with_error = monitor.calculate_health_score(metrics_with_error)
        
        assert score_with_error < score_no_error, "Recent error should reduce score"
        assert score_no_error - score_with_error >= 10, "Error penalty should be at least 10 points"

    @patch('subprocess.run')
    def test_count_ptys_using_lsof(self, mock_run):
        """Test PTY counting using lsof command."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        # Mock lsof output
        mock_run.return_value = Mock(
            stdout="/dev/pts/0\n/dev/pts/1\n/dev/pts/2\n",
            returncode=0
        )
        
        monitor = BashHealthMonitor()
        pty_count = monitor.count_ptys(pid=12345)
        
        assert pty_count == 3, f"Should count 3 PTYs, got {pty_count}"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_count_ptys_handles_missing_lsof(self, mock_run):
        """Test graceful handling when lsof is not available."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        # Mock lsof not found
        mock_run.side_effect = FileNotFoundError("lsof not found")
        
        monitor = BashHealthMonitor()
        pty_count = monitor.count_ptys(pid=12345)
        
        assert pty_count == 0, "Should return 0 when lsof not available"

    @patch('os.listdir')
    def test_count_fds_from_proc(self, mock_listdir):
        """Test file descriptor counting from /proc."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        # Mock /proc/<pid>/fd directory listing
        mock_listdir.return_value = ['0', '1', '2', '3', '4', '5']
        
        monitor = BashHealthMonitor()
        fd_count = monitor.count_fds(pid=12345)
        
        assert fd_count == 6, f"Should count 6 FDs, got {fd_count}"

    @patch('os.listdir')
    def test_count_fds_handles_missing_proc(self, mock_listdir):
        """Test graceful handling when /proc is not available (macOS)."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        # Mock /proc not available
        mock_listdir.side_effect = FileNotFoundError("/proc not found")
        
        monitor = BashHealthMonitor()
        fd_count = monitor.count_fds(pid=12345)
        
        assert fd_count == 0, "Should return 0 when /proc not available"

    def test_get_recommendations_for_healthy_session(self):
        """Test recommendations for healthy session."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        recommendations = monitor.get_recommendations(
            health_score=90,
            metrics={
                "command_count": 10,
                "pty_count": 2,
                "age_minutes": 15
            }
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("healthy" in rec.lower() or "good" in rec.lower() 
                  for rec in recommendations), "Should acknowledge healthy state"

    def test_get_recommendations_for_degraded_session(self):
        """Test recommendations for degraded session."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        recommendations = monitor.get_recommendations(
            health_score=50,
            metrics={
                "command_count": 38,
                "pty_count": 7,
                "age_minutes": 35
            }
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 2, "Should provide multiple recommendations"
        assert any("rotate" in rec.lower() for rec in recommendations), \
            "Should recommend rotation for degraded session"

    def test_get_recommendations_for_critical_session(self):
        """Test recommendations for critical session."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        recommendations = monitor.get_recommendations(
            health_score=30,
            metrics={
                "command_count": 55,
                "pty_count": 11,
                "age_minutes": 65
            }
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 3, "Should provide urgent recommendations"
        assert any("immediately" in rec.lower() or "urgent" in rec.lower() 
                  for rec in recommendations), \
            "Should indicate urgency for critical session"
        assert any("rotate" in rec.lower() for rec in recommendations), \
            "Should definitely recommend rotation"

    def test_status_classification_healthy(self):
        """Test status classification for healthy score."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        assert monitor.classify_status(85) == "healthy"
        assert monitor.classify_status(100) == "healthy"
        assert monitor.classify_status(80) == "healthy"

    def test_status_classification_watch(self):
        """Test status classification for watch score."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        assert monitor.classify_status(70) == "watch"
        assert monitor.classify_status(79) == "watch"
        assert monitor.classify_status(60) == "watch"

    def test_status_classification_degraded(self):
        """Test status classification for degraded score."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        assert monitor.classify_status(50) == "degraded"
        assert monitor.classify_status(59) == "degraded"
        assert monitor.classify_status(40) == "degraded"

    def test_status_classification_critical(self):
        """Test status classification for critical score."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        assert monitor.classify_status(30) == "critical"
        assert monitor.classify_status(39) == "critical"
        assert monitor.classify_status(20) == "critical"

    def test_status_classification_failed(self):
        """Test status classification for failed score."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        assert monitor.classify_status(10) == "failed"
        assert monitor.classify_status(19) == "failed"
        assert monitor.classify_status(0) == "failed"


class TestHealthMetricsIntegration:
    """Integration tests for health metrics collection."""

    def test_check_health_returns_complete_report(self):
        """Test that check_health returns all required fields."""
        from planloop.diagnostics.bash_health import BashHealthMonitor
        
        monitor = BashHealthMonitor()
        
        # Mock environment
        with patch.object(monitor, 'get_current_session_pid', return_value=12345), \
             patch.object(monitor, 'count_ptys', return_value=3), \
             patch.object(monitor, 'count_fds', return_value=50), \
             patch.object(monitor, 'get_command_count', return_value=15):
            
            health_report = monitor.check_health()
            
            # Verify all required fields present
            assert "session_id" in health_report
            assert "pid" in health_report
            assert "health_score" in health_report
            assert "status" in health_report
            assert "metrics" in health_report
            assert "warnings" in health_report
            assert "recommendations" in health_report
            assert "thresholds" in health_report
            
            # Verify metrics structure
            metrics = health_report["metrics"]
            assert "command_count" in metrics
            assert "pty_count" in metrics
            assert "fd_count" in metrics
            assert "age_minutes" in metrics
