"""Tests for agent transcript logging (P1.3)."""
import json

from planloop.agent_transcript import (
    TRANSCRIPT_FILENAME,
    log_agent_command,
    log_agent_note,
    log_agent_response,
    read_transcript,
)


def test_log_agent_command(tmp_path):
    """Test logging agent command invocations."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    log_agent_command(session_dir, "status", {"session": "test"}, "copilot")

    transcript_path = session_dir / "logs" / TRANSCRIPT_FILENAME
    assert transcript_path.exists()

    with transcript_path.open() as f:
        line = f.readline()
        entry = json.loads(line)

    assert entry["type"] == "command"
    assert entry["command"] == "status"
    assert entry["args"] == {"session": "test"}
    assert entry["agent"] == "copilot"
    assert "timestamp" in entry


def test_log_agent_response(tmp_path):
    """Test logging agent command responses."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    log_agent_response(session_dir, "status", True, {"reason": "task"})

    transcript_path = session_dir / "logs" / TRANSCRIPT_FILENAME
    with transcript_path.open() as f:
        entry = json.loads(f.readline())

    assert entry["type"] == "response"
    assert entry["command"] == "status"
    assert entry["success"] is True
    assert entry["data"] == {"reason": "task"}
    assert entry["error"] is None


def test_log_agent_response_error(tmp_path):
    """Test logging failed command responses."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    log_agent_response(session_dir, "update", False, error="Invalid payload")

    transcript_path = session_dir / "logs" / TRANSCRIPT_FILENAME
    with transcript_path.open() as f:
        entry = json.loads(f.readline())

    assert entry["type"] == "response"
    assert entry["success"] is False
    assert entry["error"] == "Invalid payload"


def test_log_agent_note(tmp_path):
    """Test logging free-form agent notes."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    log_agent_note(
        session_dir,
        "Starting TDD cycle for P1.3",
        "claude",
        {"task_id": "P1.3"}
    )

    transcript_path = session_dir / "logs" / TRANSCRIPT_FILENAME
    with transcript_path.open() as f:
        entry = json.loads(f.readline())

    assert entry["type"] == "note"
    assert entry["message"] == "Starting TDD cycle for P1.3"
    assert entry["agent"] == "claude"
    assert entry["metadata"] == {"task_id": "P1.3"}


def test_read_transcript(tmp_path):
    """Test reading transcript entries."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    # Log multiple entries
    log_agent_command(session_dir, "status", {}, "copilot")
    log_agent_response(session_dir, "status", True, {"reason": "task"})
    log_agent_command(session_dir, "update", {"file": "payload.json"}, "copilot")

    entries = read_transcript(session_dir)
    assert len(entries) == 3
    assert entries[0]["type"] == "command"
    assert entries[1]["type"] == "response"
    assert entries[2]["type"] == "command"


def test_read_transcript_with_limit(tmp_path):
    """Test reading transcript with entry limit."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    # Log 5 entries
    for i in range(5):
        log_agent_command(session_dir, f"cmd{i}", {}, "agent")

    # Read last 2
    entries = read_transcript(session_dir, limit=2)
    assert len(entries) == 2
    assert entries[0]["command"] == "cmd3"
    assert entries[1]["command"] == "cmd4"


def test_read_transcript_nonexistent(tmp_path):
    """Test reading transcript when file doesn't exist."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    entries = read_transcript(session_dir)
    assert entries == []


def test_logs_command_integration(tmp_path, monkeypatch):
    """Test the logs CLI command."""
    monkeypatch.setenv("PLANLOOP_HOME", str(tmp_path))

    from datetime import datetime

    from planloop.core.session import save_session_state
    from planloop.core.state import Environment, Now, NowReason, PromptMetadata, SessionState

    state = SessionState(
        session="test-logs",
        project_root=str(tmp_path),
        name="Test",
        title="Test Logs",
        purpose="Test logs",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="linux"),
        now=Now(reason=NowReason.IDLE),
    )

    session_dir = tmp_path / "sessions" / "test-logs"
    session_dir.mkdir(parents=True)
    save_session_state(session_dir, state)

    # Add some transcript entries
    log_agent_command(session_dir, "status", {}, "copilot")
    log_agent_response(session_dir, "status", True, {"reason": "idle"})

    from typer.testing import CliRunner

    from planloop.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["logs", "--session", "test-logs", "--json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert "entries" in output
    assert len(output["entries"]) == 2
