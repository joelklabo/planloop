"""Helpers for tracking the current planloop session pointer."""
from __future__ import annotations

from pathlib import Path

from ..home import CURRENT_SESSION_POINTER, initialize_home


def pointer_path() -> Path:
    home = initialize_home()
    return home / CURRENT_SESSION_POINTER


def set_current_session(session_id: str) -> None:
    pointer_path().write_text(session_id, encoding="utf-8")


def get_current_session() -> str | None:
    path = pointer_path()
    data = path.read_text(encoding="utf-8").strip()
    return data or None


def clear_current_session() -> None:
    pointer_path().write_text("", encoding="utf-8")
