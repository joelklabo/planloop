"""Minimal FastAPI-based web view for planloop sessions.

The module must remain importable even when FastAPI is missing so that the rest
of the CLI can run without optional dependencies installed. Route definitions
are therefore gated by ``FASTAPI_AVAILABLE`` and consumers should use
``get_app()`` instead of touching ``app`` directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency guard
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore
    HTMLResponse = None  # type: ignore
    FASTAPI_AVAILABLE = False

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str) -> None:
            self.status_code = status_code
            super().__init__(detail)

from ..core.state import SessionState
from ..home import CURRENT_SESSION_POINTER, SESSIONS_DIR, initialize_home
from ..tui.app import SessionViewModel


def load_state(session_id: Optional[str]) -> SessionState:
    home = initialize_home()
    session = session_id
    if not session:
        pointer_path = home / CURRENT_SESSION_POINTER
        if pointer_path.exists():
            session = pointer_path.read_text(encoding="utf-8").strip()
    if not session:
        raise HTTPException(status_code=404, detail="No session specified")
    state_path = home / SESSIONS_DIR / session / "state.json"
    if not state_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionState.model_validate_json(state_path.read_text(encoding="utf-8"))


app: Optional[FastAPI] = None  # type: ignore[assignment]

if FASTAPI_AVAILABLE:  # pragma: no cover - exercised in integration tests
    app = FastAPI()

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


def get_app() -> FastAPI:
    """Return the FastAPI app or raise when the dependency is missing."""
    if not FASTAPI_AVAILABLE or app is None:  # pragma: no cover - trivial guard
        raise RuntimeError("fastapi is not installed")
    return app


__all__ = ["FASTAPI_AVAILABLE", "app", "get_app", "load_state"]
