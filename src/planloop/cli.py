"""Initial Typer entrypoint for planloop.

Task A2 only requires packaging + a placeholder CLI so `planloop --help` works.
Real commands will arrive in Task A3.
"""
from __future__ import annotations

import typer

app = typer.Typer(help="planloop CLI (placeholder)")


def main() -> None:
    """Entry point for `python -m planloop.cli`."""
    app()


if __name__ == "__main__":  # pragma: no cover - convenience entry point
    main()
