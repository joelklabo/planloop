"""Session state models for planloop."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

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
