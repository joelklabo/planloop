"""Configuration helpers for planloop."""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

import yaml
from pydantic import BaseModel

from .home import CONFIG_FILE_NAME, initialize_home


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
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
    get_suggest_config.cache_clear()


class SuggestConfig(BaseModel):
    """Configuration for the suggest feature."""

    # LLM settings
    llm_provider: Literal["openai", "anthropic", "ollama"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key_env: str = "OPENAI_API_KEY"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000
    llm_base_url: str | None = None

    # Context settings
    context_depth: Literal["shallow", "medium", "deep"] = "medium"
    include_git_history: bool = True
    max_recent_commits: int = 10
    include_todos: bool = True
    max_files_sample: int = 100

    # Filter settings
    ignore_patterns: list[str] = [
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".hypothesis",
        "node_modules",
        ".venv",
        "venv",
        "*.egg-info",
        "*.pyc",
        "*.pyo",
        ".DS_Store",
    ]
    focus_paths: list[str] = []

    # Suggestion settings
    max_suggestions: int = 5
    min_priority: Literal["low", "medium", "high"] = "low"
    auto_approve: bool = False


@lru_cache(maxsize=1)
def get_suggest_config() -> SuggestConfig:
    """Get suggest feature configuration with defaults."""
    config = load_config()
    suggest_cfg = config.get("suggest", {})

    # Extract nested config
    llm_cfg = suggest_cfg.get("llm", {})
    context_cfg = suggest_cfg.get("context", {})
    filters_cfg = suggest_cfg.get("filters", {})
    suggestions_cfg = suggest_cfg.get("suggestions", {})

    # Build SuggestConfig with overrides
    return SuggestConfig(
        # LLM settings
        llm_provider=llm_cfg.get("provider", "openai"),
        llm_model=llm_cfg.get("model", "gpt-4o-mini"),
        llm_api_key_env=llm_cfg.get("api_key_env", "OPENAI_API_KEY"),
        llm_temperature=llm_cfg.get("temperature", 0.7),
        llm_max_tokens=llm_cfg.get("max_tokens", 4000),
        llm_base_url=llm_cfg.get("base_url"),

        # Context settings
        context_depth=context_cfg.get("depth", "medium"),
        include_git_history=context_cfg.get("include_git_history", True),
        max_recent_commits=context_cfg.get("max_recent_commits", 10),
        include_todos=context_cfg.get("include_todos", True),
        max_files_sample=context_cfg.get("max_files_sample", 100),

        # Filter settings
        ignore_patterns=filters_cfg.get("ignore_patterns", SuggestConfig().ignore_patterns),
        focus_paths=filters_cfg.get("focus_paths", []),

        # Suggestion settings
        max_suggestions=suggestions_cfg.get("max_count", 5),
        min_priority=suggestions_cfg.get("min_priority", "low"),
        auto_approve=suggestions_cfg.get("auto_approve", False),
    )
