"""Logging helpers for planloop."""
from __future__ import annotations

import logging
from pathlib import Path

from .config import logging_level

LOGGER_NAME = "planloop"
LOG_FILENAME = "planloop.log"

_LOGGER: logging.Logger | None = None
_SESSION_HANDLERS: dict[Path, logging.Handler] = {}
_FORMATTER = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")


def _resolve_level(name: str) -> int:
    level = getattr(logging, name.upper(), logging.INFO)
    if isinstance(level, int):
        return level
    return logging.INFO


def get_logger() -> logging.Logger:
    """Return the configured planloop logger."""

    global _LOGGER
    if _LOGGER is None:
        logger = logging.getLogger(LOGGER_NAME)
        logger.setLevel(_resolve_level(logging_level()))
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        logger.propagate = False
        _LOGGER = logger
    return _LOGGER


def set_level(level_name: str) -> None:
    """Override the logger level at runtime (used when config changes)."""

    logger = get_logger()
    logger.setLevel(_resolve_level(level_name))


def _ensure_session_handler(logger: logging.Logger, session_dir: Path) -> logging.Handler:
    session_dir = session_dir.resolve()
    handler = _SESSION_HANDLERS.get(session_dir)
    if handler is not None:
        return handler
    logs_dir = session_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / LOG_FILENAME
    handler = logging.FileHandler(log_path)
    handler.setFormatter(_FORMATTER)
    logger.addHandler(handler)
    _SESSION_HANDLERS[session_dir] = handler
    return handler


def log_event(message: str, *, level: int = logging.INFO) -> None:
    """Log a global event (not tied to a specific session)."""

    logger = get_logger()
    logger.log(level, message)


def log_session_event(session_dir: Path, message: str, *, level: int = logging.INFO) -> None:
    """Log an event scoped to a session directory."""

    logger = get_logger()
    _ensure_session_handler(logger, session_dir)
    logger.log(level, message)


__all__ = ["get_logger", "log_event", "log_session_event", "set_level", "LOG_FILENAME", "LOGGER_NAME"]
