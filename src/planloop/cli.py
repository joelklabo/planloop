# ruff: noqa: B008
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

import typer

from . import guide as guide_utils
from .cli_utils import format_log_tail
from .config import safe_mode_defaults
from .core import describe, registry
from .core import selftest as selftest_module
from .core.diff import state_diff
from .core.lock import acquire_lock, get_lock_queue_status, get_lock_status
from .core.session import refresh_registry, save_session_state
from .core.session_pointer import get_current_session, set_current_session
from .core.signals import close_signal, open_signal
from .core.state import SessionState, Signal, SignalLevel, SignalType, validate_state
from .core.update import UpdateError, apply_update, validate_update_payload
from .core.update_payload import UpdatePayload
from .history import create_snapshot, restore_snapshot
from .home import SESSIONS_DIR, initialize_home
from .logging_utils import log_event, log_session_event
from .tui import TEXTUAL_AVAILABLE, PlanloopViewApp, SessionViewModel
from .config import get_suggest_config
from .core.suggest import SuggestionEngine, TaskSuggestion

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


def _load_session(session_id: str | None) -> tuple[SessionState, Path]:
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


def _generate_agent_instructions(state: SessionState, lock_status, queue_status) -> str:
    """Generate actionable guidance for agents based on current state."""
    from .core.state import NowReason

    if state.now.reason == NowReason.CI_BLOCKER:
        signal = next((s for s in state.signals if s.id == state.now.signal_id), None)
        if signal:
            return f"Address blocker signal: {signal.title}. Use 'planloop alert' to close the signal once resolved."
        return "Address the CI blocker signal and use 'planloop alert --close' when resolved."

    elif state.now.reason == NowReason.TASK:
        task = next((t for t in state.tasks if t.id == state.now.task_id), None)
        if task:
            return f"Work on task {task.id}: {task.title}. Update with 'planloop update' to mark progress or completion."
        return "Work on the current task and update status using 'planloop update'."

    elif state.now.reason == NowReason.COMPLETED:
        return "All tasks complete! Run 'planloop suggest' to find more work, or add final_summary to close the session."

    elif state.now.reason == NowReason.IDLE:
        return "No tasks defined. Run 'planloop suggest' to discover work, or use 'planloop update' to add tasks manually."

    elif state.now.reason == NowReason.WAITING_ON_LOCK:
        if lock_status.info:
            return f"Session locked by {lock_status.info.owner}. Wait for lock release or check 'planloop debug' for details."
        return "Session is locked. Wait for lock release or use 'planloop debug' to inspect."

    elif state.now.reason == NowReason.DEADLOCKED:
        return "Deadlock detected. Review 'planloop debug' output and resolve blockers or adjust dependencies."

    elif state.now.reason == NowReason.ESCALATED:
        signal = next((s for s in state.signals if s.id == state.now.signal_id), None)
        if signal:
            return f"Escalated issue: {signal.title}. Review the signal and take appropriate action."
        return "An issue has been escalated. Review signals and take action."

    return "Check 'planloop status' for current state and next steps."


@app.command()
def status(session: str | None = typer.Option(None, help="Session ID"), json_output: bool = typer.Option(True, "--json/--no-json", help="JSON output")) -> None:
    """Show the current planloop session status."""
    try:
        state, session_dir = _load_session(session)
        validate_state(state)
        lock_status = get_lock_status(session_dir)
        queue_status = get_lock_queue_status(session_dir, agent=os.environ.get("PLANLOOP_AGENT_NAME"))
        payload = {
            "session": state.session,
            "now": state.now.model_dump(),
            "agent_instructions": _generate_agent_instructions(state, lock_status, queue_status),
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
    session: str | None = typer.Option(None, help="Session ID"),
    file: Path | None = typer.Option(None, "--file", "-f", help="Path to payload JSON"),
    dry_run: bool | None = typer.Option(None, "--dry-run/--no-dry-run", help="Preview changes without writing"),
    no_plan_edit: bool | None = typer.Option(None, "--no-plan-edit/--allow-plan-edit", help="Reject structural edits"),
    strict: bool | None = typer.Option(None, "--strict/--allow-extra-fields", help="Reject payloads with unknown fields"),
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
                "done",
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
    session: str | None = typer.Option(None, help="Session ID"),
    id: str = typer.Option(..., "--id", help="Signal ID"),
    level: SignalLevel = typer.Option(SignalLevel.BLOCKER, "--level", help="Signal level"),
    type_: SignalType = typer.Option(SignalType.CI, "--type", help="Signal type"),
    kind: str | None = typer.Option(None, "--kind", help="Signal kind"),
    title: str | None = typer.Option(None, "--title", help="Signal title"),
    message: str | None = typer.Option(None, "--message", help="Signal message"),
    link: str | None = typer.Option(None, "--link", help="Link"),
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
                # Validate required fields when opening a signal
                if not kind:
                    raise PlanloopError("--kind is required when opening a signal")
                if not title:
                    raise PlanloopError("--title is required when opening a signal")
                if not message:
                    raise PlanloopError("--message is required when opening a signal")
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
        typer.echo(f"Error: {exc}", err=True)
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
    """List all sessions."""
    entries = registry.load_registry()
    data = [entry.to_dict() for entry in entries]
    if json_output:
        typer.echo(json.dumps({"sessions": data}, indent=2))
    else:
        for entry in data:
            typer.echo(f"{entry['session']}: {entry['title']}")


@sessions_app.command("info")
def sessions_info(session: str | None = typer.Argument(None)) -> None:
    """Show detailed information about a session."""
    try:
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
    except PlanloopError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@sessions_app.command("create")
def sessions_create(
    name: str = typer.Option(..., "--name", help="Session name (used for ID generation)"),
    title: str | None = typer.Option(None, "--title", help="Human-readable title (defaults to name)"),
    project_root: Path | None = typer.Option(None, "--project-root", help="Project root path (defaults to current directory)"),
) -> None:
    """Create a new session."""
    from .core.session import create_session
    try:
        title_value = title or name
        root = project_root or Path.cwd()
        state = create_session(name=name, title=title_value, project_root=root)
        typer.echo(json.dumps({
            "session": state.session,
            "name": state.name,
            "title": state.title,
            "project_root": state.project_root,
            "status": "created"
        }, indent=2))
    except Exception as exc:
        typer.echo(f"Error: Failed to create session: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@sessions_app.command("current")
def sessions_current() -> None:
    """Show the current session."""
    session_id = get_current_session()
    if not session_id:
        typer.echo(json.dumps({"current_session": None}, indent=2))
    else:
        typer.echo(json.dumps({"current_session": session_id}, indent=2))


@sessions_app.command("switch")
def sessions_switch(session: str = typer.Argument(..., help="Session ID to switch to")) -> None:
    """Switch to a different session."""
    try:
        summary = registry.find_session(session)
        if not summary:
            raise PlanloopError(f"Session {session} not found in registry")
        set_current_session(session)
        typer.echo(json.dumps({"current_session": session, "status": "ok"}, indent=2))
    except PlanloopError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def debug(
    session: str | None = typer.Option(None, help="Session ID"),
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
def templates(tag: str | None = typer.Option(None, "--tag", help="Filter by tag")) -> None:
    entries = [entry for entry in registry.load_registry() if entry.done]
    if tag:
        entries = [entry for entry in entries if tag in entry.tags]
    payload = {"templates": [entry.to_dict() for entry in entries]}
    typer.echo(json.dumps(payload, indent=2))


@app.command()
def reuse(
    template_session: str = typer.Argument(..., help="Completed session to reuse"),
    goal: str | None = typer.Option(None, "--goal", help="New goal description"),
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
        "template_tasks": [task.model_dump(mode="json") for task in state.tasks],
        "goal": goal,
    }
    typer.echo(json.dumps(payload, indent=2))


@app.command()
def view(session: str | None = typer.Option(None, help="Session ID")) -> None:
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
    output: Path | None = typer.Option(None, "--output", "-o", help="Write to file"),
    apply: bool = typer.Option(False, "--apply", help="Insert into docs/agents.md"),
    target: Path | None = typer.Option(None, "--target", help="Target file"),
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
def web(session: str | None = typer.Option(None, help="Session ID")) -> None:
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
    session: str | None = typer.Option(None, help="Session ID"),
    note: str = typer.Option("Manual snapshot", "--note"),
) -> None:
    try:
        _, session_dir = _load_session(session)
        sha = create_snapshot(session_dir, note)
        log_session_event(session_dir, f"Snapshot created: {sha}")
    except (PlanloopError, RuntimeError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps({"snapshot": sha}, indent=2))


@app.command()
def restore(
    snapshot_ref: str = typer.Argument(..., help="Snapshot commit"),
    session: str | None = typer.Option(None, help="Session ID"),
) -> None:
    try:
        _, session_dir = _load_session(session)
        restore_snapshot(session_dir, snapshot_ref)
        restored_state = refresh_registry(session_dir)
        validate_state(restored_state)
        log_session_event(session_dir, f"Restored snapshot {snapshot_ref}")
    except (PlanloopError, RuntimeError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps({"restored": snapshot_ref}, indent=2))


@app.command()
def suggest(
    session: str | None = typer.Option(None, help="Session ID"),
    depth: str = typer.Option("medium", help="Context depth (shallow/medium/deep)"),
    focus: str | None = typer.Option(None, help="Focus area (e.g., 'src/auth')"),
    auto_approve: bool = typer.Option(False, help="Skip interactive approval"),
    dry_run: bool = typer.Option(False, help="Preview without adding"),
    limit: int | None = typer.Option(None, help="Max suggestions"),
) -> None:
    """Analyze codebase and suggest tasks."""
    try:
        state, session_dir = _load_session(session)
        validate_state(state)
        
        # Get suggest config
        config = get_suggest_config()
        
        # Override limit if specified
        if limit is not None:
            config.max_suggestions = limit
        
        # Initialize suggestion engine
        engine = SuggestionEngine(state, config)
        
        # Generate suggestions
        project_root = Path(state.project_root) if state.project_root else session_dir.parent
        suggestions = engine.generate_suggestions(
            project_root=project_root,
            depth=depth
        )
        
        if not suggestions:
            typer.echo("No suggestions generated.")
            return
        
        # Display suggestions
        typer.echo(f"\n🔍 Found {len(suggestions)} suggestion(s)\n")
        
        approved_suggestions = []
        
        if dry_run:
            # Just display suggestions in dry-run mode
            for i, suggestion in enumerate(suggestions, 1):
                _display_suggestion(i, len(suggestions), suggestion)
            return
        
        if auto_approve:
            # Auto-approve all suggestions
            approved_suggestions = suggestions
        else:
            # Interactive approval
            for i, suggestion in enumerate(suggestions, 1):
                _display_suggestion(i, len(suggestions), suggestion)
                
                if typer.confirm("Add this task?"):
                    approved_suggestions.append(suggestion)
        
        if not approved_suggestions:
            typer.echo("\nNo tasks added.")
            return
        
        # Generate update payload with AddTaskInput objects
        from .core.update_payload import AddTaskInput
        
        add_tasks = []
        for suggestion in approved_suggestions:
            # Combine rationale and implementation notes into implementation_notes
            full_notes = f"{suggestion.rationale}\n\nImplementation notes:\n{suggestion.implementation_notes}"
            if suggestion.affected_files:
                full_notes += f"\n\nAffected files:\n" + "\n".join(f"- {f}" for f in suggestion.affected_files)
            
            add_task = AddTaskInput(
                title=suggestion.title,
                type=suggestion.type,
                depends_on=suggestion.depends_on,
                implementation_notes=full_notes
            )
            add_tasks.append(add_task)
        
        # Apply update
        payload = UpdatePayload(
            session=state.session,
            add_tasks=add_tasks
        )
        
        with acquire_lock(session_dir):
            state = apply_update(state, payload)
            save_session_state(session_dir, state)
        
        typer.echo(f"\n✓ Added {len(approved_suggestions)} task(s) to plan")
        log_session_event(session_dir, f"Suggest command: added {len(approved_suggestions)} tasks")
        
    except PlanloopError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _display_suggestion(index: int, total: int, suggestion: TaskSuggestion) -> None:
    """Display a task suggestion in a formatted way."""
    typer.echo("━" * 50)
    typer.echo(f"Suggestion {index}/{total} [{suggestion.priority.upper()} PRIORITY]")
    typer.echo(f"\nTitle: {suggestion.title}")
    typer.echo(f"Type: {suggestion.type.value}")
    typer.echo(f"Rationale: {suggestion.rationale}")
    typer.echo(f"Files: {', '.join(suggestion.affected_files) if suggestion.affected_files else 'N/A'}")
    typer.echo(f"Notes: {suggestion.implementation_notes}")
    if suggestion.depends_on:
        typer.echo(f"Depends on: {', '.join(map(str, suggestion.depends_on))}")
    typer.echo()


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


@app.command()
def hello(name: str | None = typer.Option(None, "--name", help="Name to greet")) -> None:
    """Simple greeting command."""
    if name:
        typer.echo(f"Hello, {name}!")
    else:
        typer.echo("Hello, world!")

def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
