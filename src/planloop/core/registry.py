"""Session registry helpers."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from ..home import SESSIONS_DIR, initialize_home

REGISTRY_FILE = "index.json"


@dataclass
class SessionSummary:
    session: str
    name: str
    title: str
    tags: List[str]
    project_root: str
    created_at: str
    last_updated_at: str
    done: bool

    def to_dict(self) -> dict:
        return {
            "session": self.session,
            "name": self.name,
            "title": self.title,
            "tags": self.tags,
            "project_root": self.project_root,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
            "done": self.done,
        }


def _registry_path() -> Path:
    home = initialize_home()
    return home / REGISTRY_FILE


def load_registry() -> List[SessionSummary]:
    path = _registry_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    sessions = data.get("sessions", [])
    return [SessionSummary(**entry) for entry in sessions]


def save_registry(entries: List[SessionSummary]) -> None:
    path = _registry_path()
    payload = {
        "sessions": [entry.to_dict() for entry in entries],
        "updated_at": datetime.utcnow().isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def upsert_session(summary: SessionSummary) -> None:
    entries = load_registry()
    filtered = [entry for entry in entries if entry.session != summary.session]
    filtered.append(summary)
    save_registry(sorted(filtered, key=lambda e: e.last_updated_at, reverse=True))
