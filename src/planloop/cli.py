"""Typer CLI skeleton for planloop.

Task A3 requires stubbing primary commands (`status`, `update`, `alert`,
`describe`, `selftest`) so agents can discover the interface even before the
implementation lands.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .core.lock import acquire_lock, get_lock_status
from .core.session import save_session_state
from .core.session_pointer import get_current_session
from .core.state import SessionState, validate_state
from .core.update import UpdateError, apply_update
from .core.update_payload import UpdatePayload
from .home import SESSIONS_DIR, initialize_home

app = typer.Typer(help="planloop CLI")


class PlanloopError(RuntimeError):
    """Base error for CLI failures."""


def _load_session(session_id: Optional[str]) -> tuple[SessionState, Path]:
    home = initialize_home()
    if not session_id:
        session_id = get_current_session()
        if not session_id:
            raise PlanloopError("No session specified and no current session set")
    session_dir = home / SESSIONS_DIR / session_id
    if not session_dir.exists():
        raise PlanloopError(f"Session {session_id} not found")
    state_path = session_dir / "state.json"
    if not state_path.exists():
        raise PlanloopError("state.json missing for session")
    state = SessionState.model_validate_json(state_path.read_text(encoding="utf-8"))
    return state, session_dir


@app.command()
def status(session: Optional[str] = typer.Option(None, help="Session ID"), json_output: bool = typer.Option(True, "--json/--no-json", help="JSON output")) -> None:
    """Show the current planloop session status."""
    try:
        state, session_dir = _load_session(session)
        validate_state(state)
        lock_status = get_lock_status(session_dir)
        payload = {
            "session": state.session,
            "now": state.now.model_dump(),
            "tasks": [task.model_dump() for task in state.tasks],
            "signals": [signal.model_dump() for signal in state.signals],
            "lock_info": lock_status.info.to_dict() if lock_status.info else None,
        }
        typer.echo(json.dumps(payload, indent=2))
    except PlanloopError as exc:
        raise typer.Exit(code=1) from exc


@app.command()
def update(
    session: Optional[str] = typer.Option(None, help="Session ID"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to payload JSON"),
) -> None:
    """Apply a structured update to the session."""
    data = file.read_text(encoding="utf-8") if file else typer.get_text_stream("stdin").read()
    if not data.strip():
        raise typer.Exit(code=1)
    try:
        payload = UpdatePayload.model_validate_json(data)
    except Exception as exc:  # ValidationError
        raise typer.Exit(code=1) from exc
    target_session = session or payload.session
    try:
        state, session_dir = _load_session(target_session)
    except PlanloopError as exc:
        raise typer.Exit(code=1) from exc
    try:
        with acquire_lock(session_dir, operation="update"):
            state = apply_update(state, payload)
            validate_state(state)
            save_session_state(session_dir, state)
    except UpdateError as exc:
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps({"status": "ok", "version": state.version}, indent=2))


@app.command()
def alert() -> None:
    """Manage planloop signals (stub)."""
    raise NotImplementedCLIError(_stub_message("alert"))


@app.command()
def describe(json_output: bool = typer.Option(True, "--json")) -> None:
    """Emit planloop schema information (stub)."""
    if json_output:
        typer.echo(json.dumps({"error": _stub_message("describe")}, indent=2))
    raise NotImplementedCLIError(_stub_message("describe"))


@app.command()
def selftest() -> None:
    """Run planloop's self-test harness (stub)."""
    raise NotImplementedCLIError(_stub_message("selftest"))


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
