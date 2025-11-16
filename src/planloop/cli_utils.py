"""Shared CLI helpers."""
from __future__ import annotations

from typing import Callable, Iterable


def format_log_tail(lines: Iterable[str], limit: int = 10) -> str:
    """Return the last ``limit`` lines joined by newlines."""

    data = list(lines)
    return "\n".join(data[-limit:])


__all__ = ["format_log_tail"]
