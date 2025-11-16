"""Configuration helpers for planloop."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

from .home import CONFIG_FILE_NAME, initialize_home


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    home = initialize_home()
    path = home / CONFIG_FILE_NAME
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def history_enabled() -> bool:
    config = load_config()
    return bool(config.get("history", {}).get("enabled", False))


def logging_level() -> str:
    config = load_config()
    value = config.get("logging", {}).get("level", "INFO")
    return str(value)


def safe_mode_defaults() -> dict:
    config = load_config()
    update_cfg = config.get("safe_modes", {}).get("update", {})
    return {
        "dry_run": bool(update_cfg.get("dry_run", False)),
        "no_plan_edit": bool(update_cfg.get("no_plan_edit", False)),
        "strict": bool(update_cfg.get("strict", False)),
    }


def reset_config_cache() -> None:
    load_config.cache_clear()
