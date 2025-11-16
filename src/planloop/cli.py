"""Typer CLI skeleton for planloop.

Task A3 requires stubbing primary commands (`status`, `update`, `alert`,
`describe`, `selftest`) so agents can discover the interface even before the
implementation lands.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from .core import describe, registry, selftest as selftest_module
from . import guide as guide_utils
from .cli_utils import format_log_tail
from .history import create_snapshot, restore_snapshot
from .logging_utils import log_event, log_session_event
from .tui import TEXTUAL_AVAILABLE, PlanloopViewApp, SessionViewModel
from .core.lock import acquire_lock, get_lock_queue_status, get_lock_status
from .core.session import refresh_registry, save_session_state
from .core.session_pointer import get_current_session
from .core.signals import close_signal, open_signal
from .core.state import SessionState, Signal, SignalLevel, SignalType, validate_state
from .core.update import UpdateError, apply_update, validate_update_payload
from .core.diff import state_diff
from .config import safe_mode_defaults
from .core.update_payload import UpdatePayload
from .home import SESSIONS_DIR, initialize_home

app = typer.Typer(help="planloop CLI")
sessions_app = typer.Typer(help="Manage sessions")
app.add_typer(sessions_app, name="sessions")


TRACE_RESULTS_ENV = "PLANLOOP_LAB_RESULTS"
TRACE_AGENT_ENV = "PLANLOOP_LAB_AGENT_NAME"


def _log_trace_event(step: str, detail: str) -> None:
    results_path = os.environ.get(TRACE_RESULTS_ENV)
    agent_name = os.environ.get(TRACE_AGENT_ENV)
    if not results_path or not agent_name:
        return
    trace_dir = Path(results_path) / agent_name
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / "trace.log"
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with trace_path.open("a", encoding="utf-8") as fp:
        fp.write(f"{timestamp}\t{step}\t{detail}\n")


class PlanloopError(RuntimeError):
    """Base error for CLI failures."""


def _emit_selftest_result(payload: dict, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
        return
    typer.echo(f"Self-test status: {payload['status']}")
    for scenario in payload.get("scenarios", []):
        typer.echo(
            f"- {scenario['name']}: {scenario['status']} ({scenario['detail']})"
        )


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
        queue_status = get_lock_queue_status(session_dir, agent=os.environ.get("PLANLOOP_AGENT_NAME"))
        payload = {
            "session": state.session,
            "now": state.now.model_dump(),
            "tasks": [task.model_dump(mode="json") for task in state.tasks],
            "signals": [signal.model_dump(mode="json") for signal in state.signals],
            "lock_info": lock_status.info.to_dict() if lock_status.info else None,
            "lock_queue": queue_status.to_dict(),
            "safe_mode_defaults": safe_mode_defaults(),
        }
        log_session_event(session_dir, "Status command executed")
        _log_trace_event("status", f"reason={state.now.reason.value}")
        typer.echo(json.dumps(payload, indent=2))
    except PlanloopError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def update(
    session: Optional[str] = typer.Option(None, help="Session ID"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to payload JSON"),
    dry_run: Optional[bool] = typer.Option(None, "--dry-run/--no-dry-run", help="Preview changes without writing"),
    no_plan_edit: Optional[bool] = typer.Option(None, "--no-plan-edit/--allow-plan-edit", help="Reject structural edits"),
    strict: Optional[bool] = typer.Option(None, "--strict/--allow-extra-fields", help="Reject payloads with unknown fields"),
) -> None:
    """Apply a structured update to the session."""
    data = file.read_text(encoding="utf-8") if file else typer.get_text_stream("stdin").read()
    if not data.strip():
        raise typer.Exit(code=1)
    try:
        raw_payload = json.loads(data)
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: Invalid JSON: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    try:
        payload = UpdatePayload.model_validate(raw_payload)
    except Exception as exc:  # ValidationError
        typer.echo(f"Error: Invalid update payload: {exc}", err=True)
        typer.echo("Hint: Use 'planloop describe' to see the expected schema", err=True)
        raise typer.Exit(code=1) from exc
    target_session = session or payload.session
    try:
        state, session_dir = _load_session(target_session)
    except PlanloopError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    defaults = safe_mode_defaults()
    dry_run_enabled = defaults["dry_run"] if dry_run is None else dry_run
    no_plan_edit_enabled = defaults["no_plan_edit"] if no_plan_edit is None else no_plan_edit
    strict_enabled = defaults["strict"] if strict is None else strict
    try:
        if strict_enabled:
            allowed = {
                "session",
                "last_seen_version",
                "tasks",
                "add_tasks",
                "update_tasks",
                "context_notes",
                "next_steps",
                "artifacts",
                "agent",
                "final_summary",
            }
            unknown = set(raw_payload.keys()) - allowed
            if unknown:
                raise UpdateError(f"Unknown fields in payload: {', '.join(sorted(unknown))}")
        if no_plan_edit_enabled and (payload.add_tasks or payload.update_tasks or payload.context_notes or payload.next_steps or payload.artifacts):
            raise UpdateError("Structural edits are disabled by --no-plan-edit")
        validate_update_payload(state, payload)
        if dry_run_enabled:
            state_copy = state.model_copy(deep=True)
            apply_update(state_copy, payload)
            diff = state_diff(state, state_copy)
            typer.echo(json.dumps({"dry_run": diff}, indent=2))
            return
        with acquire_lock(session_dir, operation="update"):
            state = apply_update(state, payload)
            validate_state(state)
            save_session_state(session_dir, state, message="Update command")
            log_session_event(
                session_dir,
                f"Update applied (add_tasks={len(payload.add_tasks)}, patches={len(payload.tasks)})",
            )
            _log_trace_event(
                "update",
                f"version={state.version} tasks={len(payload.tasks)} add={len(payload.add_tasks)} update_tasks={len(payload.update_tasks)} reason={state.now.reason.value}",
            )
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
                log_session_event(session_dir, f"Signal {id} closed")
                _log_trace_event("signal-close", f"id={id}")
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
                log_session_event(session_dir, f"Signal {id} opened ({level.value})")
                _log_trace_event("signal-open", f"id={id}")
            validate_state(state)
            save_session_state(session_dir, state, message="Signal update")
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
def debug(
    session: Optional[str] = typer.Option(None, help="Session ID"),
    logs: bool = typer.Option(True, "--logs/--no-logs", help="Include recent logs"),
) -> None:
    """Print debug information for a session."""
    try:
        state, session_dir = _load_session(session)
        log_path = session_dir / "logs" / "planloop.log"
        log_tail = ""
        if logs and log_path.exists():
            lines = log_path.read_text(encoding="utf-8").splitlines()
            log_tail = format_log_tail(lines)
        lock_status = get_lock_status(session_dir)
        payload = {
            "session": state.session,
            "path": str(session_dir),
            "state_json": str(session_dir / "state.json"),
            "plan_md": str(session_dir / "PLAN.md"),
            "lock_info": lock_status.info.to_dict() if lock_status.info else None,
            "now": state.now.model_dump(),
            "open_signals": [signal.model_dump(mode="json") for signal in state.signals if signal.open],
            "logs": log_tail,
        }
        log_session_event(session_dir, "Debug command inspected session")
        typer.echo(json.dumps(payload, indent=2))
    except PlanloopError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


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
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    if not state.done:
        typer.echo(f"Error: Session {template_session} is not marked as done", err=True)
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
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    model = SessionViewModel.from_state(state)
    PlanloopViewApp(model).run()


@app.command()
def guide(
    prompt_set: str = typer.Option("core-v1", help="Prompt set"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to file"),
    apply: bool = typer.Option(False, "--apply", help="Insert into docs/agents.md"),
    target: Optional[Path] = typer.Option(None, "--target", help="Target file"),
) -> None:
    content = guide_utils.render_guide(prompt_set)
    if apply:
        path = target or Path("docs/agents.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        guide_utils.insert_guide(path, content)
        typer.echo(f"Guide inserted into {path}")
    else:
        if output:
            output.write_text(content, encoding="utf-8")
            typer.echo(f"Guide written to {output}")
        else:
            typer.echo(content)


@app.command()
def web(session: Optional[str] = typer.Option(None, help="Session ID")) -> None:
    try:
        from .web import server as web_server
    except ImportError as exc:  # pragma: no cover
        typer.echo("planloop web server module is unavailable.")
        raise typer.Exit(code=1) from exc
    if not getattr(web_server, "FASTAPI_AVAILABLE", False):  # pragma: no cover
        typer.echo("fastapi is not installed. Run `pip install fastapi fastapi[standard]`.")
        raise typer.Exit(code=1)
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        typer.echo("uvicorn not installed. Run `pip install uvicorn` to use planloop web.")
        raise typer.Exit(code=1) from exc

    app = web_server.get_app()
    uvicorn.run(app, host="127.0.0.1", port=8765)


@app.command()
def snapshot(
    session: Optional[str] = typer.Option(None, help="Session ID"),
    note: str = typer.Option("Manual snapshot", "--note"),
) -> None:
    try:
        _, session_dir = _load_session(session)
        sha = create_snapshot(session_dir, note)
        log_session_event(session_dir, f"Snapshot created: {sha}")
    except (PlanloopError, RuntimeError) as exc:
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps({"snapshot": sha}, indent=2))


@app.command()
def restore(
    snapshot_ref: str = typer.Argument(..., help="Snapshot commit"),
    session: Optional[str] = typer.Option(None, help="Session ID"),
) -> None:
    try:
        _, session_dir = _load_session(session)
        restore_snapshot(session_dir, snapshot_ref)
        restored_state = refresh_registry(session_dir)
        validate_state(restored_state)
        log_session_event(session_dir, f"Restored snapshot {snapshot_ref}")
    except (PlanloopError, RuntimeError, ValueError) as exc:
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps({"restored": snapshot_ref}, indent=2))


@app.command()
def selftest(json_output: bool = typer.Option(True, "--json/--no-json", help="JSON output")) -> None:
    """Run planloop's self-test harness."""
    try:
        results = selftest_module.run_selftest()
    except selftest_module.SelfTestFailure as exc:
        payload = {
            "status": "failed",
            "scenarios": [result.to_dict() for result in exc.results],
        }
        log_event("Self-test failed", level=logging.ERROR)
        _emit_selftest_result(payload, json_output)
        raise typer.Exit(code=1) from exc
    payload = {
        "status": "ok",
        "scenarios": [result.to_dict() for result in results],
    }
    log_event("Self-test completed successfully")
    _emit_selftest_result(payload, json_output)


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
