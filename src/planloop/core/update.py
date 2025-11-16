"""State update helpers."""
from __future__ import annotations

from datetime import datetime

from .state import SessionState, Signal, Task, TaskStatus, TaskType
from .update_payload import AddTaskInput, TaskStatusPatch, UpdatePayload, UpdateTaskInput


class UpdateError(ValueError):
    """Raised when an update payload is invalid."""


def _apply_task_patch(task: Task, patch: TaskStatusPatch) -> None:
    if patch.status is not None:
        task.status = patch.status
    if patch.new_title is not None:
        task.title = patch.new_title
    task.last_updated_at = datetime.utcnow()


def _apply_update_task(task: Task, update: UpdateTaskInput) -> None:
    if update.new_title is not None:
        task.title = update.new_title
    if update.new_type is not None:
        task.type = update.new_type
    if update.status is not None:
        task.status = update.status
    task.last_updated_at = datetime.utcnow()


def _next_task_id(state: SessionState) -> int:
    if not state.tasks:
        return 1
    return max(task.id for task in state.tasks) + 1


def _add_new_task(state: SessionState, add: AddTaskInput, new_id: int) -> Task:
    task_type = add.type or TaskType.FEATURE
    task = Task(
        id=new_id,
        title=add.title,
        type=task_type,
        depends_on=add.depends_on,
    )
    state.tasks.append(task)
    return task


def validate_update_payload(state: SessionState, payload: UpdatePayload) -> None:
    if payload.session and payload.session != state.session:
        raise UpdateError("Payload session does not match state")
    if payload.last_seen_version and payload.last_seen_version != str(state.version):
        raise UpdateError("Version mismatch")


def apply_update(state: SessionState, payload: UpdatePayload) -> SessionState:

    id_to_task = {task.id: task for task in state.tasks}

    for patch in payload.tasks:
        task = id_to_task.get(patch.id)
        if not task:
            raise UpdateError(f"Unknown task id {patch.id}")
        _apply_task_patch(task, patch)

    for upd in payload.update_tasks:
        task = id_to_task.get(upd.id)
        if not task:
            raise UpdateError(f"Unknown task id {upd.id}")
        _apply_update_task(task, upd)

    next_id = _next_task_id(state)
    for add in payload.add_tasks:
        task = _add_new_task(state, add, next_id)
        id_to_task[task.id] = task
        next_id += 1

    if payload.context_notes:
        state.context_notes = payload.context_notes
    if payload.next_steps:
        state.next_steps = payload.next_steps
    if payload.artifacts:
        state.artifacts.extend(payload.artifacts)
    if payload.final_summary is not None:
        state.final_summary = payload.final_summary

    state.last_updated_at = datetime.utcnow()
    state.version += 1
    state.now = state.compute_now()
    return state


__all__ = ["apply_update", "UpdateError", "validate_update_payload"]
