"""Minimal FastAPI-based web view for planloop sessions."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

try:  # pragma: no cover
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    FASTAPI_AVAILABLE = False
    HTMLResponse = None  # type: ignore
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str) -> None:
            super().__init__(detail)

from ..core.state import SessionState
from ..home import SESSIONS_DIR, initialize_home
from ..tui.app import SessionViewModel


def load_state(session_id: Optional[str]) -> SessionState:
    home = initialize_home()
    session = session_id or (home / "current_session").read_text().strip()
    if not session:
        raise HTTPException(status_code=404, detail="No session specified")
    state_path = home / SESSIONS_DIR / session / "state.json"
    if not state_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionState.model_validate_json(state_path.read_text())


if FASTAPI_AVAILABLE:
    app = FastAPI()
else:  # pragma: no cover
    class _StubApp:
        ...

    app = _StubApp()


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    home = initialize_home()
    sessions = sorted((home / SESSIONS_DIR).iterdir(), key=lambda p: p.name)
    links = "".join(
        f"<li><a href='/sessions/{path.name}'>{path.name}</a></li>" for path in sessions
    )
    return f"<h1>planloop Sessions</h1><ul>{links}</ul>"


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_view(session_id: str) -> str:
    state = load_state(session_id)
    model = SessionViewModel.from_state(state)
    tasks = "".join(
        f"<tr><td>{tid}</td><td>{title}</td><td>{status}</td></tr>"
        for tid, title, status in model.tasks
    )
    signals = "".join(
        f"<tr><td>{title}</td><td>{status}</td></tr>"
        for title, status in model.signals
    )
    return f"""
    <h1>{model.title}</h1>
    <p><strong>Session:</strong> {model.session}</p>
    <p><strong>Now:</strong> {model.now_reason}</p>
    <h2>Tasks</h2>
    <table border='1'><tr><th>ID</th><th>Title</th><th>Status</th></tr>{tasks}</table>
    <h2>Signals</h2>
    <table border='1'><tr><th>Signal</th><th>State</th></tr>{signals}</table>
    """
