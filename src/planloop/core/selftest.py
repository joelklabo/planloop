"""Self-test harness that simulates agent workflows."""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..home import PLANLOOP_HOME_ENV, SESSIONS_DIR, initialize_home
from .session import create_session, load_session_state_from_disk, save_session_state
from .signals import close_signal, open_signal
from .state import (
    NowReason,
    SessionState,
    Signal,
    SignalLevel,
    SignalType,
    TaskStatus,
    TaskType,
    validate_state,
)
from .update import apply_update
from .update_payload import AddTaskInput, TaskStatusPatch, UpdatePayload


@dataclass
class ScenarioResult:
    """Result for a single self-test scenario."""

    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": "passed" if self.passed else "failed",
            "detail": self.detail,
        }


class SelfTestFailure(RuntimeError):
    """Raised when one or more scenarios fail."""

    def __init__(self, results: Sequence[ScenarioResult]) -> None:
        super().__init__("Self-test scenarios failed")
        self.results = list(results)


def run_selftest() -> list[ScenarioResult]:
    """Execute all scenarios inside a temporary PLANLOOP_HOME."""

    original_home = os.environ.get(PLANLOOP_HOME_ENV)
    results: list[ScenarioResult] = []
    with tempfile.TemporaryDirectory(prefix="planloop-selftest-") as tmp_home:
        os.environ[PLANLOOP_HOME_ENV] = tmp_home
        home_path = initialize_home()
        for name, scenario in _SCENARIOS:
            try:
                detail = scenario(home_path)
            except Exception as exc:  # pragma: no cover - surfaced via CLI tests
                results.append(ScenarioResult(name=name, passed=False, detail=str(exc)))
            else:
                results.append(ScenarioResult(name=name, passed=True, detail=detail))
        if original_home is None:
            os.environ.pop(PLANLOOP_HOME_ENV, None)
        else:
            os.environ[PLANLOOP_HOME_ENV] = original_home
    if not all(result.passed for result in results):
        raise SelfTestFailure(results)
    return results


def _apply_update(
    state: SessionState,
    session_dir: Path,
    *,
    add_tasks: Iterable[AddTaskInput] | None = None,
    status_changes: Iterable[tuple[int, TaskStatus]] | None = None,
    context_notes: list[str] | None = None,
    next_steps: list[str] | None = None,
    final_summary: str | None = None,
    message: str = "selftest update",
) -> SessionState:
    payload = UpdatePayload(
        session=state.session,
        last_seen_version=str(state.version),
        add_tasks=list(add_tasks or []),
        tasks=[TaskStatusPatch(id=task_id, status=status) for task_id, status in status_changes or []],
        context_notes=context_notes or [],
        next_steps=next_steps or [],
        final_summary=final_summary,
    )
    state = apply_update(state, payload)
    validate_state(state)
    save_session_state(session_dir, state, message=message)
    return state


def _scenario_clean_run(home: Path) -> str:
    state = create_session("Selftest Clean", "UI polish", project_root=Path("/selftest/clean"))
    session_dir = home / SESSIONS_DIR / state.session

    state = _apply_update(
        state,
        session_dir,
        add_tasks=[
            AddTaskInput(title="Add button", type=TaskType.FEATURE),
            AddTaskInput(title="Write docs", type=TaskType.DOC),
        ],
        context_notes=["Clean scenario initialized"],
        next_steps=["Finish both tasks"],
    )
    state = _apply_update(
        state,
        session_dir,
        status_changes=[(1, TaskStatus.DONE), (2, TaskStatus.DONE)],
        final_summary="UI polish complete",
        message="selftest clean completion",
    )
    reloaded = load_session_state_from_disk(session_dir)
    if reloaded.now.reason != NowReason.COMPLETED:
        raise AssertionError("Expected clean scenario to complete")
    return "Clean scenario completed with final summary"


def _scenario_ci_blocker(home: Path) -> str:
    state = create_session("Selftest CI", "Crash fix", project_root=Path("/selftest/ci"))
    session_dir = home / SESSIONS_DIR / state.session
    state = _apply_update(
        state,
        session_dir,
        add_tasks=[AddTaskInput(title="Fix failing test", type=TaskType.FIX)],
        context_notes=["CI scenario bootstrapped"],
    )
    signal = Signal(
        id="ci-selftest",
        type=SignalType.CI,
        kind="build",
        level=SignalLevel.BLOCKER,
        title="Selftest CI failure",
        message="Simulated CI breakage",
    )
    open_signal(state, signal=signal)
    validate_state(state)
    save_session_state(session_dir, state, message="selftest ci blocker open")
    if state.now.reason != NowReason.CI_BLOCKER:
        raise AssertionError("Expected now.reason to reflect ci_blocker")
    close_signal(state, signal.id)
    validate_state(state)
    save_session_state(session_dir, state, message="selftest ci blocker closed")
    if state.now.reason != NowReason.TASK:  # type: ignore[comparison-overlap]
        raise AssertionError("Expected now.reason to return to task")
    return "CI blocker opened and cleared"


def _scenario_dependency_chain(home: Path) -> str:
    state = create_session("Selftest Coverage", "Coverage pipeline", project_root=Path("/selftest/coverage"))
    session_dir = home / SESSIONS_DIR / state.session
    state = _apply_update(
        state,
        session_dir,
        add_tasks=[
            AddTaskInput(title="Add coverage tests", type=TaskType.TEST),
            AddTaskInput(title="Refactor module", type=TaskType.REFACTOR, depends_on=[1]),
        ],
        context_notes=["Coverage chain initialized"],
    )
    if state.now.reason != NowReason.TASK or state.now.task_id != 1:
        raise AssertionError("Expected task 1 to be active")
    state = _apply_update(
        state,
        session_dir,
        status_changes=[(1, TaskStatus.DONE)],
        message="selftest dependency step 1",
    )
    if state.now.task_id != 2:
        raise AssertionError("Expected dependent task to unlock")
    state = _apply_update(
        state,
        session_dir,
        status_changes=[(2, TaskStatus.DONE)],
        final_summary="Coverage pipeline wrapped",
        message="selftest dependency completion",
    )
    if state.now.reason != NowReason.COMPLETED:
        raise AssertionError("Expected dependency scenario to complete")
    return "Dependency chain resolved"


def _scenario_signal_and_tasks(home: Path) -> str:
    state = create_session("Selftest Signal and Tasks", "Handle signal then tasks", project_root=Path("/selftest/signal_tasks"))
    session_dir = home / SESSIONS_DIR / state.session

    # 1. Add initial tasks
    state = _apply_update(
        state,
        session_dir,
        add_tasks=[
            AddTaskInput(title="Initial Task 1", type=TaskType.FEATURE),
            AddTaskInput(title="Initial Task 2", type=TaskType.FEATURE),
            AddTaskInput(title="Initial Task 3", type=TaskType.FEATURE),
        ],
        context_notes=["Scenario initialized with tasks"],
    )
    if state.now.reason != NowReason.TASK or state.now.task_id != 1:
        raise AssertionError("Expected Task 1 to be active initially")

    # 2. Start working on Task 1
    state = _apply_update(
        state,
        session_dir,
        status_changes=[(1, TaskStatus.IN_PROGRESS)],
        message="Started Task 1",
    )
    if state.now.reason != NowReason.TASK or state.now.task_id != 1:
        raise AssertionError("Expected Task 1 to be in progress")

    # 3. Introduce a CI blocker signal
    signal = Signal(
        id="ci-blocker-for-tasks",
        type=SignalType.CI,
        kind="build",
        level=SignalLevel.BLOCKER,
        title="Simulated CI failure during tasks",
        message="CI failed, blocking further task work",
    )
    open_signal(state, signal=signal)
    validate_state(state)
    save_session_state(session_dir, state, message="CI blocker opened")

    if state.now.reason != NowReason.CI_BLOCKER:
        raise AssertionError("Expected now.reason to reflect ci_blocker after signal")

    # 4. Resolve the CI blocker
    close_signal(state, signal.id)
    validate_state(state)
    save_session_state(session_dir, state, message="CI blocker closed")

    if state.now.reason != NowReason.TASK or state.now.task_id != 1:
        raise AssertionError("Expected now.reason to return to Task 1 after signal resolution")

    # 5. Complete remaining tasks
    state = _apply_update(
        state,
        session_dir,
        status_changes=[(1, TaskStatus.DONE)],
        message="Completed Task 1 after CI fix",
    )
    if state.now.reason != NowReason.TASK or state.now.task_id != 2:
        raise AssertionError("Expected Task 2 to be active after Task 1 completion")

    state = _apply_update(
        state,
        session_dir,
        status_changes=[(2, TaskStatus.DONE)],
        message="Completed Task 2",
    )
    if state.now.reason != NowReason.TASK or state.now.task_id != 3:
        raise AssertionError("Expected Task 3 to be active after Task 2 completion")

    state = _apply_update(
        state,
        session_dir,
        status_changes=[(3, TaskStatus.DONE)],
        final_summary="All tasks completed after signal handling",
        message="Completed Task 3",
    )

    reloaded = load_session_state_from_disk(session_dir)
    if reloaded.now.reason != NowReason.COMPLETED:
        raise AssertionError("Expected scenario to complete after all tasks are done")

    return "Signal handled and all tasks completed successfully"


_SCENARIOS: list[tuple[str, Callable[[Path], str]]] = [
    ("clean_run", _scenario_clean_run),
    ("ci_blocker", _scenario_ci_blocker),
    ("dependency_chain", _scenario_dependency_chain),
    ("signal_and_tasks", _scenario_signal_and_tasks),
]


__all__ = ["run_selftest", "ScenarioResult", "SelfTestFailure"]
