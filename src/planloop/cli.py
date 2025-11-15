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

from .core import describe, registry
from . import guide as guide_utils
from .tui import TEXTUAL_AVAILABLE, PlanloopViewApp, SessionViewModel
from .core.lock import acquire_lock, get_lock_status
from .core.session import save_session_state
from .core.session_pointer import get_current_session
from .core.signals import close_signal, open_signal
from .core.state import SessionState, Signal, SignalLevel, SignalType, validate_state
from .core.update import UpdateError, apply_update
from .core.update_payload import UpdatePayload
from .home import SESSIONS_DIR, initialize_home

app = typer.Typer(help="planloop CLI")
sessions_app = typer.Typer(help="Manage sessions")
app.add_typer(sessions_app, name="sessions")


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
def alert(
    session: Optional[str] = typer.Option(None, help="Session ID"),
    id: str = typer.Option(..., "--id", help="Signal ID"),
    level: SignalLevel = typer.Option(SignalLevel.BLOCKER, "--level", help="Signal level"),
    type_: SignalType = typer.Option(SignalType.CI, "--type", help="Signal type"),
    kind: str = typer.Option(..., "--kind", help="Signal kind"),
    title: str = typer.Option(..., "--title", help="Signal title"),
    message: str = typer.Option(..., "--message", help="Signal message"),
    link: Optional[str] = typer.Option(None, "--link", help="Link"),
    close: bool = typer.Option(False, "--close", help="Close signal"),
) -> None:
    """Manage signals within a session."""
    try:
        state, session_dir = _load_session(session)
        with acquire_lock(session_dir, operation="alert"):
            if close:
                close_signal(state, id)
            else:
                signal = Signal(
                    id=id,
                    type=type_,
                    kind=kind,
                    level=level,
                    title=title,
                    message=message,
                    link=link,
                )
                open_signal(state, signal=signal)
            validate_state(state)
            save_session_state(session_dir, state)
        typer.echo(json.dumps({"status": "ok"}, indent=2))
    except (PlanloopError, ValueError) as exc:
        raise typer.Exit(code=1) from exc


@app.command(name="describe")
def describe_command(json_output: bool = typer.Option(True, "--json")) -> None:
    """Emit planloop schema information."""
    payload = describe.describe_payload()
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo("planloop describe currently supports JSON output only.")


@sessions_app.command("list")
def sessions_list(json_output: bool = typer.Option(True, "--json")) -> None:
    entries = registry.load_registry()
    data = [entry.to_dict() for entry in entries]
    if json_output:
        typer.echo(json.dumps({"sessions": data}, indent=2))
    else:
        for entry in data:
            typer.echo(f"{entry['session']}: {entry['title']}")


@sessions_app.command("info")
def sessions_info(session: Optional[str] = typer.Argument(None)) -> None:
    home = initialize_home()
    target = session or get_current_session()
    if not target:
        raise PlanloopError("No session specified and no current session set")
    summary = registry.find_session(target)
    if not summary:
        raise PlanloopError(f"Session {target} not found in registry")
    info = summary.to_dict()
    info["path"] = str(home / SESSIONS_DIR / target)
    typer.echo(json.dumps(info, indent=2))


@app.command()
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    results = registry.search_sessions(query)
    payload = {"sessions": [entry.to_dict() for entry in results]}
    typer.echo(json.dumps(payload, indent=2))


@app.command()
def templates(tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag")) -> None:
    entries = [entry for entry in registry.load_registry() if entry.done]
    if tag:
        entries = [entry for entry in entries if tag in entry.tags]
    payload = {"templates": [entry.to_dict() for entry in entries]}
    typer.echo(json.dumps(payload, indent=2))


@app.command()
def reuse(
    template_session: str = typer.Argument(..., help="Completed session to reuse"),
    goal: Optional[str] = typer.Option(None, "--goal", help="New goal description"),
) -> None:
    try:
        state, _ = _load_session(template_session)
    except PlanloopError as exc:
        raise typer.Exit(code=1) from exc
    if not state.done:
        raise typer.Exit(code=1)
    payload = {
        "template_session": state.session,
        "template_title": state.title,
        "template_summary": state.final_summary,
        "template_tasks": [task.model_dump() for task in state.tasks],
        "goal": goal,
    }
    typer.echo(json.dumps(payload, indent=2))


@app.command()
def view(session: Optional[str] = typer.Option(None, help="Session ID")) -> None:
    if not TEXTUAL_AVAILABLE:
        typer.echo("textual is not installed. Run `pip install textual` to use planloop view.")
        raise typer.Exit(code=1)
    try:
        state, _ = _load_session(session)
    except PlanloopError as exc:
        raise typer.Exit(code=1) from exc
    model = SessionViewModel.from_state(state)
    PlanloopViewApp(model).run()


@app.command()
def guide(
    prompt_set: str = typer.Option("core-v1", help="Prompt set"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to file"),
    apply: bool = typer.Option(False, "--apply", help="Insert into AGENTS.md"),
    target: Optional[Path] = typer.Option(None, "--target", help="Target file"),
) -> None:
    content = guide_utils.render_guide(prompt_set)
    if apply:
        path = target or Path("AGENTS.md")
        guide_utils.insert_guide(path, content)
        typer.echo(f"Guide inserted into {path}")
    else:
        if output:
            output.write_text(content, encoding="utf-8")
            typer.echo(f"Guide written to {output}")
        else:
            typer.echo(content)


@app.command()
def selftest() -> None:
    """Run planloop's self-test harness (stub)."""
    raise NotImplementedCLIError(_stub_message("selftest"))


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
