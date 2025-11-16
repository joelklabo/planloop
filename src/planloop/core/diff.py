"""Helpers for computing human-friendly diffs between SessionState objects."""
from __future__ import annotations

from .state import SessionState, Task


def _task_snapshot(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "type": task.type.value,
        "status": task.status.value,
    }


def _compare_tasks(before: dict[int, Task], after: dict[int, Task]) -> dict:
    added: list[dict] = []
    removed: list[dict] = []
    updated: list[dict] = []

    for task_id, task in after.items():
        if task_id not in before:
            added.append(_task_snapshot(task))
            continue
        original = before[task_id]
        changes: dict = {}
        if original.title != task.title:
            changes["title"] = {"before": original.title, "after": task.title}
        if original.type != task.type:
            changes["type"] = {"before": original.type.value, "after": task.type.value}
        if original.status != task.status:
            changes["status"] = {"before": original.status.value, "after": task.status.value}
        if changes:
            updated.append({"task": _task_snapshot(task), "changes": changes})

    for task_id, task in before.items():
        if task_id not in after:
            removed.append(_task_snapshot(task))

    return {"added": added, "updated": updated, "removed": removed}


def state_diff(before: SessionState, after: SessionState) -> dict:
    """Return a diff summary between two session states."""

    tasks_before = {task.id: task for task in before.tasks}
    tasks_after = {task.id: task for task in after.tasks}
    diff = {
        "version": {"before": before.version, "after": after.version},
        "tasks": _compare_tasks(tasks_before, tasks_after),
    }

    if before.context_notes != after.context_notes:
        diff["context_notes"] = {"before": before.context_notes, "after": after.context_notes}
    if before.next_steps != after.next_steps:
        diff["next_steps"] = {"before": before.next_steps, "after": after.next_steps}
    if before.final_summary != after.final_summary:
        diff["final_summary"] = {"before": before.final_summary, "after": after.final_summary}

    return diff


__all__ = ["state_diff"]
