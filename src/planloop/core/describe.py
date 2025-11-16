"""Schema export helpers for planloop."""
from __future__ import annotations

from typing import Any

from .state import (
    ArtifactType,
    NowReason,
    SessionState,
    SignalLevel,
    SignalType,
    TaskStatus,
    TaskType,
)
from .update_payload import UpdatePayload


def state_schema() -> dict[str, Any]:
    """Return the JSON schema for SessionState."""
    return SessionState.model_json_schema()


def update_schema() -> dict[str, Any]:
    """Return the JSON schema for update payloads."""
    return UpdatePayload.model_json_schema()


def enum_reference() -> dict[str, Any]:
    """Return the enum values agents care about."""
    return {
        "task_types": [t.value for t in TaskType],
        "task_statuses": [s.value for s in TaskStatus],
        "signal_levels": [lvl.value for lvl in SignalLevel],
        "signal_types": [typ.value for typ in SignalType],
        "artifact_types": [typ.value for typ in ArtifactType],
        "now_reasons": [reason.value for reason in NowReason],
    }


def describe_payload() -> dict[str, Any]:
    """Aggregate describe output for planloop agents."""
    return {
        "state_schema": state_schema(),
        "update_schema": update_schema(),
        "enums": enum_reference(),
        "error_codes": [],
        "usage_hints": {
            "update_payload": {
                "required_fields": ["session"],
                "common_fields": ["last_seen_version", "add_tasks", "update_tasks", "context_notes", "next_steps"],
                "note": "Use 'add_tasks' to create new tasks, 'update_tasks' to modify existing ones, 'tasks' for status-only patches"
            }
        }
    }


__all__ = [
    "state_schema",
    "update_schema",
    "enum_reference",
    "describe_payload",
]
