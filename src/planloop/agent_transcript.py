"""Agent interaction transcript logging.

Provides structured logging of agent commands and responses for audit trails,
debugging, and learning from agent behavior.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TRANSCRIPT_FILENAME = "agent-transcript.jsonl"


def _timestamp() -> str:
    """Generate ISO 8601 timestamp in UTC."""
    return datetime.now(UTC).isoformat()


def log_agent_command(
    session_dir: Path,
    command: str,
    args: dict[str, Any] | None = None,
    agent_name: str | None = None,
) -> None:
    """Log an agent command invocation.

    Args:
        session_dir: Path to session directory
        command: Command name (e.g., "status", "update", "alert")
        args: Command arguments/options (optional)
        agent_name: Name of the agent (from PLANLOOP_AGENT_NAME env var)
    """
    logs_dir = session_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = logs_dir / TRANSCRIPT_FILENAME

    entry = {
        "timestamp": _timestamp(),
        "type": "command",
        "command": command,
        "args": args or {},
        "agent": agent_name,
    }

    with transcript_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_agent_response(
    session_dir: Path,
    command: str,
    success: bool,
    data: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Log an agent command response.

    Args:
        session_dir: Path to session directory
        command: Command that generated this response
        success: Whether the command succeeded
        data: Response data (for successful commands)
        error: Error message (for failed commands)
    """
    logs_dir = session_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = logs_dir / TRANSCRIPT_FILENAME

    entry = {
        "timestamp": _timestamp(),
        "type": "response",
        "command": command,
        "success": success,
        "data": data,
        "error": error,
    }

    with transcript_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_agent_note(
    session_dir: Path,
    message: str,
    agent_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log a free-form agent note or observation.

    Args:
        session_dir: Path to session directory
        message: Note content
        agent_name: Name of the agent (optional)
        metadata: Additional structured data (optional)
    """
    logs_dir = session_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = logs_dir / TRANSCRIPT_FILENAME

    entry = {
        "timestamp": _timestamp(),
        "type": "note",
        "message": message,
        "agent": agent_name,
        "metadata": metadata or {},
    }

    with transcript_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_transcript(session_dir: Path, limit: int | None = None) -> list[dict[str, Any]]:
    """Read agent transcript entries.

    Args:
        session_dir: Path to session directory
        limit: Maximum number of entries to return (most recent first)

    Returns:
        List of transcript entries (newest first if limit is set)
    """
    transcript_path = session_dir / "logs" / TRANSCRIPT_FILENAME
    if not transcript_path.exists():
        return []

    entries = []
    with transcript_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue

    if limit:
        entries = entries[-limit:]

    return entries


__all__ = [
    "log_agent_command",
    "log_agent_response",
    "log_agent_note",
    "read_transcript",
    "TRANSCRIPT_FILENAME",
]
