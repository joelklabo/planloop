"""Textual TUI application for viewing sessions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

try:  # pragma: no cover - optional dependency guard
    from textual.app import App, ComposeResult
    from textual.widgets import DataTable, Footer, Header, Static
    TEXTUAL_AVAILABLE = True
except ImportError:  # pragma: no cover
    App = object  # type: ignore
    ComposeResult = object  # type: ignore
    DataTable = Footer = Header = Static = object  # type: ignore
    TEXTUAL_AVAILABLE = False

from ..core.state import SessionState


@dataclass
class SessionViewModel:
    session: str
    title: str
    now_reason: str
    tasks: list[tuple[str, str, str]]
    signals: list[tuple[str, str]]

    @classmethod
    def from_state(cls, state: SessionState) -> SessionViewModel:
        tasks = [
            (str(task.id), task.title, task.status.value)
            for task in state.tasks
        ]
        signals = [
            (signal.title, "OPEN" if signal.open else "CLOSED")
            for signal in state.signals
        ]
        return cls(
            session=state.session,
            title=state.title,
            now_reason=state.now.reason.value,
            tasks=tasks,
            signals=signals,
        )


if TEXTUAL_AVAILABLE:  # pragma: no cover - UI layer

    class PlanloopViewApp(App):
        """Simple Textual application that renders session state."""

        BINDINGS = [("q", "quit", "Quit")]

        def __init__(self, model: SessionViewModel) -> None:
            super().__init__()
            self.model = model

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(
                f"Session: {self.model.session}\nTitle: {self.model.title}\n"
                f"Now: {self.model.now_reason}",
                id="summary",
            )
            tasks: DataTable = DataTable(id="tasks")
            tasks.add_columns("ID", "Title", "Status")
            for row in self.model.tasks:
                tasks.add_row(*row)
            yield tasks

            signals: DataTable = DataTable(id="signals")
            signals.add_columns("Signal", "State")
            for signal_row in self.model.signals:
                signals.add_row(*signal_row)
            yield signals
            yield Footer()

else:  # pragma: no cover

    class PlanloopViewApp:  # type: ignore
        def __init__(self, *_: object, **__: object) -> None:
            raise RuntimeError("textual is not installed; `pip install textual`")
