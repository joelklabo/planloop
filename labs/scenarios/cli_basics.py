"""CLI basics scenario for prompt lab."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from planloop.core.session import create_session, save_session_state
from planloop.core.state import Task, TaskStatus, TaskType
from planloop.home import SESSIONS_DIR, initialize_home


@dataclass
class ScenarioResult:
    session_id: str
    session_dir: Path


@dataclass
class CLIBasicsScenario:
    name: str = "cli-basics"
    description: str = "Seed a session with two small tasks to exercise status/update flows."

    def setup(self, home: Path) -> ScenarioResult:
        initialize_home()
        state = create_session("CLI Basics", "Exercise planloop CLI", project_root=home)
        state.tasks = [
            Task(id=1, title="Add hello command", type=TaskType.FEATURE),
            Task(id=2, title="Write unit tests", type=TaskType.TEST, status=TaskStatus.TODO, depends_on=[1]),
        ]
        save_session_state(home / SESSIONS_DIR / state.session, state, message="lab scenario seed")
        session_dir = home / SESSIONS_DIR / state.session
        return ScenarioResult(session_id=state.session, session_dir=session_dir)
