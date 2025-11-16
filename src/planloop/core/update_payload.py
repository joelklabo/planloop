"""Models describing planloop update payload schemas."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, PositiveInt

from .state import Artifact, TaskStatus, TaskType


class TaskStatusPatch(BaseModel):
    id: PositiveInt
    status: Optional[TaskStatus] = None
    new_title: Optional[str] = None


class AddTaskInput(BaseModel):
    title: str
    type: Optional[TaskType] = None
    depends_on: List[PositiveInt] = Field(default_factory=list)
    implementation_notes: Optional[str] = None


class UpdateTaskInput(BaseModel):
    id: PositiveInt
    new_title: Optional[str] = None
    new_type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None


class AgentInfo(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    contact: Optional[str] = None


class UpdatePayload(BaseModel):
    session: str
    last_seen_version: Optional[str] = None
    tasks: List[TaskStatusPatch] = Field(default_factory=list)
    add_tasks: List[AddTaskInput] = Field(default_factory=list)
    update_tasks: List[UpdateTaskInput] = Field(default_factory=list)
    context_notes: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    agent: Optional[AgentInfo] = None
    final_summary: Optional[str] = None

    @staticmethod
    def model_validate(data):
        """Validate and coerce version field to string if needed."""
        if isinstance(data, dict) and "last_seen_version" in data:
            if isinstance(data["last_seen_version"], int):
                data["last_seen_version"] = str(data["last_seen_version"])
        return BaseModel.model_validate.__func__(UpdatePayload, data)
