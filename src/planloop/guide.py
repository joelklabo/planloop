"""Utilities for generating planloop guide content."""
from __future__ import annotations

import re
from pathlib import Path

from .core.prompts import load_prompt

GUIDE_HEADER = "planloop Agent Instructions"
GUIDE_VERSION = "2.0"  # Increment when prompts change significantly
MARKER = f"<!-- PLANLOOP-INSTALLED v{GUIDE_VERSION} -->"


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
    """Check if any planloop marker exists in text."""
    return "PLANLOOP-INSTALLED" in text


def get_guide_version() -> str:
    """Get current guide version."""
    return GUIDE_VERSION


def is_guide_outdated(text: str) -> bool:
    """Check if installed guide version is older than current."""
    # Extract version from marker
    match = re.search(r"PLANLOOP-INSTALLED v([\d.]+)", text)
    if not match:
        # No version marker = very old, needs update
        return True
    
    installed_version = match.group(1)
    return installed_version != GUIDE_VERSION


def insert_guide(path: Path, content: str, force: bool = False) -> None:
    """Insert or update guide content.
    
    Args:
        path: Target file path
        content: Guide content to insert
        force: If True, replace existing guide content
    """
    if path.exists():
        original = path.read_text(encoding="utf-8")
        
        if detect_marker(original):
            if not force and not is_guide_outdated(original):
                # Up-to-date, no action needed
                return
            
            # Replace old guide content, preserve custom additions
            # Find start of guide (marker) and end (next ## or EOF)
            marker_pattern = r"<!--\s*PLANLOOP-INSTALLED[^>]*-->"
            match = re.search(marker_pattern, original)
            
            if match:
                # Find where guide content ends (before custom sections)
                start_pos = match.start()
                # Look for user's custom content after guide
                custom_section = re.search(r"\n## (?!Goal|Handshake|Summary|Reuse)", original[start_pos:])
                
                if custom_section:
                    end_pos = start_pos + custom_section.start()
                    custom_content = original[end_pos:]
                    new_text = original[:start_pos] + content + "\n" + custom_content
                else:
                    # No custom content, just replace from marker to EOF
                    new_text = original[:start_pos] + content + "\n"
            else:
                # Marker exists but can't find position, append
                new_text = original.rstrip() + "\n\n" + content + "\n"
        else:
            # No marker, append to existing content
            new_text = original.rstrip() + "\n\n" + content + "\n"
    else:
        new_text = content + "\n"
    
    path.write_text(new_text, encoding="utf-8")


__all__ = [
    "render_guide",
    "insert_guide",
    "detect_marker",
    "get_guide_version",
    "is_guide_outdated",
    "GUIDE_HEADER",
    "MARKER",
    "GUIDE_VERSION",
]
