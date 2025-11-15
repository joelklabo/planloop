"""PLANLOOP_HOME resolution helpers."""
from __future__ import annotations

import os
from pathlib import Path

PLANLOOP_HOME_ENV = "PLANLOOP_HOME"
DEFAULT_HOME_NAME = ".planloop"


def _expand_path(raw_path: str) -> Path:
    """Expand user/relative components for PLANLOOP_HOME overrides."""
    return Path(raw_path).expanduser().resolve()


def get_home() -> Path:
    """Return the PLANLOOP_HOME directory, creating it when missing."""
    env_override = os.environ.get(PLANLOOP_HOME_ENV)
    if env_override:
        home_path = _expand_path(env_override)
    else:
        home_path = (Path.home() / DEFAULT_HOME_NAME).resolve()
    home_path.mkdir(parents=True, exist_ok=True)
    return home_path


__all__ = ["get_home", "PLANLOOP_HOME_ENV", "DEFAULT_HOME_NAME"]
