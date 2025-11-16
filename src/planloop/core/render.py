"""PLAN.md rendering and parsing helpers."""
from __future__ import annotations

from typing import Any

import yaml

from .state import Artifact, SessionState, Signal, Task

PLANLOOP_VERSION = "1.5"


def _front_matter_dict(state: SessionState) -> dict[str, Any]:
    return {
        "planloop_version": PLANLOOP_VERSION,
        "schema_version": state.schema_version,
        "session": state.session,
        "name": state.name,
        "title": state.title,
        "purpose": state.purpose,
        "project_root": state.project_root,
        "branch": state.branch,
        "prompt_set": state.prompts.set,
        "created_at": state.created_at.isoformat(),
        "last_updated_at": state.last_updated_at.isoformat(),
        "tags": [],
        "environment": state.environment.model_dump(),
    }


def _render_front_matter(data: dict[str, Any]) -> str:
    dumped = yaml.safe_dump(data, sort_keys=False).strip()
    return f"---\n{dumped}\n---\n"


def _format_tasks(tasks: list[Task]) -> str:
    if not tasks:
        return "_No tasks defined._"
    lines = [
        "| ID | Title | Type | Status | Depends | Commit |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task in tasks:
        depends = ", ".join(str(dep) for dep in task.depends_on) or "-"
        commit = task.commit_sha or "-"
        lines.append(
            f"| {task.id} | {task.title} | {task.type.value} | {task.status.value} | {depends} | {commit} |"
        )
    return "\n".join(lines)


def _format_bullets(items: list[str]) -> str:
    if not items:
        return "- _None_"
    return "\n".join(f"- {item}" for item in items)


def _format_signals(signals: list[Signal]) -> str:
    if not signals:
        return "- _No signals_"
    lines = []
    for signal in signals:
        status = "OPEN" if signal.open else "CLOSED"
        lines.append(
            f"- [{signal.level.value}] ({status}) {signal.title} — {signal.message}"
        )
    return "\n".join(lines)


def _format_artifacts(artifacts: list[Artifact]) -> str:
    if not artifacts:
        return "- _No artifacts recorded_"
    lines = []
    for artifact in artifacts:
        path = artifact.path or "(in memory)"
        lines.append(f"- {artifact.type.value}: {artifact.summary} ({path})")
    return "\n".join(lines)


def render_plan(state: SessionState) -> str:
    """Render the PLAN.md representation for the given state."""
    front_matter = _render_front_matter(_front_matter_dict(state))
    sections = [
        f"# Plan: {state.title}",
        "",
        "## Tasks",
        _format_tasks(state.tasks),
        "",
        "## Context",
        _format_bullets(state.context_notes),
        "",
        "## Next Steps",
        _format_bullets(state.next_steps),
        "",
        "## Signals (Snapshot)",
        _format_signals(state.signals),
        "",
        "## Agent Work Log",
        "- _Not implemented yet_",
        "",
        "## Artifacts",
        _format_artifacts(state.artifacts),
        "",
        "## Final Summary",
        state.final_summary or "_Not provided yet_",
    ]
    body = "\n".join(sections)
    return front_matter + "\n" + body + "\n"


def parse_front_matter(document: str) -> tuple[dict[str, Any], str]:
    """Parse front matter from a PLAN.md string."""
    if not document.startswith("---\n"):
        return {}, document
    remainder = document[4:]
    end = remainder.find("\n---\n")
    if end == -1:
        return {}, document
    front = remainder[:end]
    body = remainder[end + 5 :]
    data = yaml.safe_load(front) or {}
    return data, body


__all__ = ["render_plan", "parse_front_matter"]
