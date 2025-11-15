"""Session state models for planloop."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field, PositiveInt


class TaskType(str, Enum):
    TEST = "test"
    FIX = "fix"
    REFACTOR = "refactor"
    FEATURE = "feature"
    DOC = "doc"
    CHORE = "chore"
    DESIGN = "design"
    INVESTIGATE = "investigate"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    WAITING = "WAITING"


class Task(BaseModel):
    id: PositiveInt
    title: str
    type: TaskType
    status: TaskStatus = TaskStatus.TODO
    depends_on: List[PositiveInt] = Field(default_factory=list)
    commit_sha: Optional[str] = None
    last_updated_at: Optional[datetime] = None


class SignalLevel(str, Enum):
    BLOCKER = "blocker"
    HIGH = "high"
    INFO = "info"


class SignalType(str, Enum):
    CI = "ci"
    LINT = "lint"
    BENCH = "bench"
    SYSTEM = "system"
    OTHER = "other"


class Signal(BaseModel):
    id: str
    type: SignalType
    kind: str
    level: SignalLevel
    open: bool = True
    title: str
    message: str
    link: Optional[str] = None
    extra: dict = Field(default_factory=dict)
    attempts: int = 0


class NowReason(str, Enum):
    CI_BLOCKER = "ci_blocker"
    TASK = "task"
    COMPLETED = "completed"
    IDLE = "idle"
    WAITING_ON_LOCK = "waiting_on_lock"
    DEADLOCKED = "deadlocked"
    ESCALATED = "escalated"


class Now(BaseModel):
    reason: NowReason
    task_id: Optional[int] = None
    signal_id: Optional[str] = None


class ArtifactType(str, Enum):
    DIFF = "diff"
    LOG = "log"
    FILE = "file"
    URL = "url"
    OTHER = "other"


class Artifact(BaseModel):
    type: ArtifactType
    path: Optional[str] = None
    summary: str
    commit_sha: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class Environment(BaseModel):
    os: str
    python: Optional[str] = None
    xcode: Optional[str] = None
    node: Optional[str] = None


class PromptMetadata(BaseModel):
    set: str
    goal_version: Optional[str] = None
    handshake_version: Optional[str] = None
    summary_version: Optional[str] = None


class SessionState(BaseModel):
    schema_version: int = 1
    version: int = 1
    session: str
    name: str
    title: str
    purpose: str
    created_at: datetime
    last_updated_at: datetime
    project_root: str
    branch: Optional[str] = None
    prompts: PromptMetadata
    environment: Environment
    tasks: List[Task] = Field(default_factory=list)
    signals: List[Signal] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    context_notes: List[str] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    now: Now
    done: bool = False
    final_summary: Optional[str] = None

    def compute_now(self) -> Now:
        """Compute the next action based on current state."""
        if self.signals:
            blockers = [s for s in self.signals if s.open and s.level == SignalLevel.BLOCKER]
            if blockers:
                return Now(reason=NowReason.CI_BLOCKER, signal_id=blockers[0].id)

        in_progress = [task for task in self.tasks if task.status == TaskStatus.IN_PROGRESS]
        if in_progress:
            return Now(reason=NowReason.TASK, task_id=in_progress[0].id)

        ready_tasks = [
            task
            for task in self.tasks
            if task.status == TaskStatus.TODO and all(
                self._task_done(dep_id) for dep_id in task.depends_on
            )
        ]
        if ready_tasks:
            return Now(reason=NowReason.TASK, task_id=ready_tasks[0].id)

        if self.tasks and all(
            task.status in {TaskStatus.DONE, TaskStatus.OUT_OF_SCOPE, TaskStatus.SKIPPED}
            for task in self.tasks
        ):
            return Now(reason=NowReason.COMPLETED)

        return Now(reason=NowReason.IDLE)

    def _task_done(self, task_id: int) -> bool:
        for task in self.tasks:
            if task.id == task_id:
                return task.status == TaskStatus.DONE
        return False


class StateValidationError(ValueError):
    """Raised when a SessionState fails validation."""


def _check_unique_task_ids(tasks: List[Task]) -> List[str]:
    seen: Set[int] = set()
    errors: List[str] = []
    for task in tasks:
        if task.id in seen:
            errors.append(f"Duplicate task id {task.id}")
        seen.add(task.id)
    return errors


def _check_dependencies(tasks: List[Task]) -> List[str]:
    valid_ids = {task.id for task in tasks}
    errors: List[str] = []
    for task in tasks:
        for dep in task.depends_on:
            if dep not in valid_ids:
                errors.append(f"Task {task.id} depends on unknown task {dep}")
            if dep == task.id:
                errors.append(f"Task {task.id} cannot depend on itself")
    return errors


def _detect_cycles(tasks: List[Task]) -> List[str]:
    graph: Dict[int, List[int]] = {task.id: task.depends_on for task in tasks}
    visiting: Set[int] = set()
    visited: Set[int] = set()
    errors: List[str] = []

    def dfs(node: int) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph and dfs(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    for node in graph:
        if dfs(node):
            errors.append("Circular dependency detected")
            break

    return errors


def validate_state(state: SessionState) -> None:
    """Validate state invariants, raising StateValidationError when invalid."""
    errors: List[str] = []
    errors.extend(_check_unique_task_ids(state.tasks))
    errors.extend(_check_dependencies(state.tasks))
    errors.extend(_detect_cycles(state.tasks))

    expected_now = state.compute_now()
    if state.now.model_dump() != expected_now.model_dump():
        errors.append("State 'now' field is out of sync with compute_now()")

    if errors:
        raise StateValidationError("; ".join(errors))
