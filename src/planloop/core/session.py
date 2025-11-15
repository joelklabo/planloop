"""Session creation and ID helpers."""
from __future__ import annotations

import secrets
from datetime import datetime
from pathlib import Path

from .deadlock import DeadlockTracker
from .registry import SessionSummary, upsert_session
from .render import render_plan
from .state import Environment, Now, NowReason, PromptMetadata, SessionState
from ..home import (
    CURRENT_SESSION_POINTER,
    SESSIONS_DIR,
    initialize_home,
)


def _slugify(text: str) -> str:
    cleaned = "-".join(
        "".join(ch.lower() if ch.isalnum() else " " for ch in text).split()
    )
    return cleaned or "session"


def new_session_id(name: str) -> str:
    slug = _slugify(name)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    rand = secrets.token_hex(2)
    return f"{slug}-{timestamp}-{rand}"


def _initial_state(session_id: str, name: str, title: str, project_root: Path) -> SessionState:
    now = Now(reason=NowReason.IDLE)
    env = Environment(os="unknown")
    prompts = PromptMetadata(set="core-v1")
    ts = datetime.utcnow()
    return SessionState(
        session=session_id,
        name=name,
        title=title,
        purpose="",
        created_at=ts,
        last_updated_at=ts,
        project_root=str(project_root),
        prompts=prompts,
        environment=env,
        now=now,
    )


def create_session(name: str, title: str, project_root: Path) -> SessionState:
    home = initialize_home()
    session_id = new_session_id(name)
    session_dir = home / SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    state = _initial_state(session_id, name, title, project_root)
    save_session_state(session_dir, state)

    (home / CURRENT_SESSION_POINTER).write_text(session_id, encoding="utf-8")
    DeadlockTracker().persist(session_dir / "deadlock.json")

    return state


def save_session_state(session_dir: Path, state: SessionState) -> None:
    state_path = session_dir / "state.json"
    plan_path = session_dir / "PLAN.md"
    state_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    plan_path.write_text(render_plan(state), encoding="utf-8")
    _update_registry(state)


def _update_registry(state: SessionState) -> None:
    summary = SessionSummary(
        session=state.session,
        name=state.name,
        title=state.title,
        tags=state.tags,
        project_root=state.project_root,
        created_at=state.created_at.isoformat(),
        last_updated_at=state.last_updated_at.isoformat(),
        done=state.done,
    )
    upsert_session(summary)
