"""Typer CLI skeleton for planloop.

Task A3 requires stubbing primary commands (`status`, `update`, `alert`,
`describe`, `selftest`) so agents can discover the interface even before the
implementation lands.
"""
from __future__ import annotations

import json
from typing import Optional

import typer

app = typer.Typer(help="planloop CLI")


class NotImplementedCLIError(RuntimeError):
    """Explicit error for unimplemented commands."""


def _stub_message(command: str) -> str:
    return (
        f"planloop {command} is not implemented yet. "
        "Follow docs/plan.md milestones to add functionality."
    )


@app.command()
def status(session: Optional[str] = typer.Option(None, help="Session ID"), json_output: bool = typer.Option(False, "--json", help="Show JSON")) -> None:
    """Show the current planloop session status (stub)."""
    if json_output:
        typer.echo(json.dumps({"error": _stub_message("status")}, indent=2))
    raise NotImplementedCLIError(_stub_message("status"))


@app.command()
def update(_: Optional[str] = typer.Option(None, "--payload", help="JSON payload path")) -> None:
    """Apply a structured update to the session (stub)."""
    raise NotImplementedCLIError(_stub_message("update"))


@app.command()
def alert() -> None:
    """Manage planloop signals (stub)."""
    raise NotImplementedCLIError(_stub_message("alert"))


@app.command()
def describe(json_output: bool = typer.Option(True, "--json")) -> None:
    """Emit planloop schema information (stub)."""
    if json_output:
        typer.echo(json.dumps({"error": _stub_message("describe")}, indent=2))
    raise NotImplementedCLIError(_stub_message("describe"))


@app.command()
def selftest() -> None:
    """Run planloop's self-test harness (stub)."""
    raise NotImplementedCLIError(_stub_message("selftest"))


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
