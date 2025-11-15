"""Utilities for generating planloop guide content."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .core.prompts import load_prompt

GUIDE_HEADER = "planloop Agent Instructions"
MARKER = "<!-- PLANLOOP-INSTALLED -->"


def render_guide(prompt_set: str = "core-v1") -> str:
    goal = load_prompt(prompt_set, "goal")
    handshake = load_prompt(prompt_set, "handshake")
    summary = load_prompt(prompt_set, "summary")
    reuse = load_prompt(prompt_set, "reuse_template")

    sections = [
        f"# {GUIDE_HEADER}",
        MARKER,
        "\n## Goal Prompt",
        goal.body,
        "\n## Handshake",
        handshake.body,
        "\n## Summary Prompt",
        summary.body,
        "\n## Reuse Template Prompt",
        reuse.body,
    ]
    return "\n".join(sections)


def detect_marker(text: str) -> bool:
    return MARKER in text


def insert_guide(path: Path, content: str) -> None:
    if path.exists():
        original = path.read_text(encoding="utf-8")
        if detect_marker(original):
            return
        new_text = original.rstrip() + "\n\n" + content + "\n"
    else:
        new_text = content + "\n"
    path.write_text(new_text, encoding="utf-8")


__all__ = ["render_guide", "insert_guide", "detect_marker", "GUIDE_HEADER", "MARKER"]
