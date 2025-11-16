"""Scenario registry for the prompt lab."""
from __future__ import annotations

from .cli_basics import CLIBasicsScenario

SCENARIOS = {
    "cli-basics": CLIBasicsScenario(),
}


def get_scenario(name: str):
    try:
        return SCENARIOS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown scenario {name}. Available: {', '.join(SCENARIOS)}") from exc


__all__ = ["SCENARIOS", "get_scenario"]
