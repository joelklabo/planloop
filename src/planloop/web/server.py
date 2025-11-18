"""Minimal FastAPI-based web view for planloop sessions.

The module must remain importable even when FastAPI is missing so that the rest
of the CLI can run without optional dependencies installed. Route definitions
are therefore gated by ``FASTAPI_AVAILABLE`` and consumers should use
``get_app()`` instead of touching ``app`` directly.
"""
from __future__ import annotations

from ..core.state import SessionState
from ..home import CURRENT_SESSION_POINTER, SESSIONS_DIR, initialize_home
from ..tui.app import SessionViewModel

try:  # pragma: no cover - optional dependency guard
    from fastapi import FastAPI, HTTPException  # type: ignore[import-not-found]
    from fastapi.responses import HTMLResponse, FileResponse  # type: ignore[import-not-found]
    from fastapi.staticfiles import StaticFiles  # type: ignore[import-not-found]
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    FastAPI = None
    HTMLResponse = None
    HTTPException = None
    FileResponse = None
    StaticFiles = None
    CORSMiddleware = None
    FASTAPI_AVAILABLE = False


app: FastAPI | None = None

if FASTAPI_AVAILABLE:  # pragma: no cover - exercised in integration tests
    from pathlib import Path
    
    app = FastAPI()
    
    # Add CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Get frontend build directory
    frontend_dir = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"

    def load_state(session_id: str | None) -> SessionState:
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

    # API endpoints
    @app.get("/api/sessions")
    async def list_sessions():
        """List all sessions."""
        home = initialize_home()
        sessions_path = home / SESSIONS_DIR
        if not sessions_path.exists():
            return []
        
        sessions = []
        for session_dir in sorted(sessions_path.iterdir(), key=lambda p: p.name, reverse=True):
            if session_dir.is_dir():
                state_file = session_dir / "state.json"
                if state_file.exists():
                    try:
                        state = SessionState.model_validate_json(state_file.read_text(encoding="utf-8"))
                        sessions.append({
                            "id": session_dir.name,
                            "description": state.title or state.purpose,
                            "task_count": len(state.tasks),
                            "signal_count": len(state.signals),
                        })
                    except Exception:
                        pass
        return sessions
    
    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get session details."""
        state = load_state(session_id)
        return state.model_dump()
    
    @app.get("/api/sessions/{session_id}/tasks")
    async def get_session_tasks(session_id: str):
        """Get tasks for a specific session."""
        state = load_state(session_id)
        return [task.model_dump() for task in state.tasks]
    
    @app.get("/api/sessions/{session_id}/signals")
    async def get_session_signals(session_id: str):
        """Get signals for a specific session."""
        state = load_state(session_id)
        return [signal.model_dump() for signal in state.signals]
    
    # Legacy HTML endpoints (kept for backward compatibility)
    @app.get("/legacy", response_class=HTMLResponse)
    async def legacy_index() -> str:
        home = initialize_home()
        sessions = sorted((home / SESSIONS_DIR).iterdir(), key=lambda p: p.name)
        links = "".join(
            f"<li><a href='/legacy/sessions/{path.name}'>{path.name}</a></li>" for path in sessions
        )
        return f"<h1>planloop Sessions</h1><ul>{links}</ul>"

    @app.get("/legacy/sessions/{session_id}", response_class=HTMLResponse)
    async def legacy_session_view(session_id: str) -> str:
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
    
    # Serve React frontend (if built)
    if frontend_dir.exists():
        app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve React app for all non-API routes."""
            # API routes handled above
            if full_path.startswith("api/") or full_path.startswith("legacy/"):
                raise HTTPException(status_code=404, detail="Not found")
            
            # Try to serve the requested file
            file_path = frontend_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            
            # Otherwise serve index.html (SPA fallback)
            index_path = frontend_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            
            # Frontend not built yet
            return HTMLResponse(
                content="""
                <h1>Planloop Web Dashboard</h1>
                <p>Frontend not built yet. Run <code>cd frontend && npm run build</code></p>
                <p>Or use legacy view: <a href="/legacy">/legacy</a></p>
                """,
                status_code=503
            )

else:

    def load_state(session_id: str | None) -> SessionState:
        raise RuntimeError("fastapi is not installed")


def get_app() -> FastAPI:
    """Return the FastAPI app or raise when the dependency is missing."""
    if not FASTAPI_AVAILABLE or app is None:  # pragma: no cover - trivial guard
        raise RuntimeError("fastapi is not installed")
    return app


__all__ = ["FASTAPI_AVAILABLE", "app", "get_app", "load_state"]
