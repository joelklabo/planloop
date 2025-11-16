"""Models describing planloop update payload schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field, PositiveInt, model_validator

from .state import Artifact, TaskStatus, TaskType


class TaskStatusPatch(BaseModel):
    id: PositiveInt
    status: TaskStatus | None = None
    new_title: str | None = None


class AddTaskInput(BaseModel):
    title: str
    type: TaskType | None = None
    depends_on: list[PositiveInt] = Field(default_factory=list)
    implementation_notes: str | None = None


class UpdateTaskInput(BaseModel):
    id: PositiveInt
    new_title: str | None = None
    new_type: TaskType | None = None
    status: TaskStatus | None = None


class AgentInfo(BaseModel):
    name: str | None = None
    version: str | None = None
    contact: str | None = None


class UpdatePayload(BaseModel):
    session: str
    last_seen_version: str | None = None
    tasks: list[TaskStatusPatch] = Field(default_factory=list)
    add_tasks: list[AddTaskInput] = Field(default_factory=list)
    update_tasks: list[UpdateTaskInput] = Field(default_factory=list)
    context_notes: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    agent: AgentInfo | None = None
    final_summary: str | None = None
    done: bool | None = None

    @model_validator(mode="before")
    def _coerce_version_to_string(cls, data: object) -> object:
        """Coerce last_seen_version to string if it's an integer."""
        if isinstance(data, dict) and "last_seen_version" in data:
            if isinstance(data["last_seen_version"], int):
                data["last_seen_version"] = str(data["last_seen_version"])
        return data
