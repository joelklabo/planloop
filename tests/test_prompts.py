"""Tests for prompts loader."""
from __future__ import annotations

import pytest

from planloop.core.prompts import load_message, load_prompt


def test_load_prompt_returns_metadata_and_body():
    doc = load_prompt("core-v1", "goal")
    assert doc.metadata["set"] == "core-v1"
    assert doc.metadata["kind"] == "goal"
    assert "Goal Prompt" in doc.body


def test_messages_loader_reads_file():
    doc = load_message("missing-docs-warning")
    assert "planloop" in doc.body.lower()


def test_load_prompt_is_cached():
    doc1 = load_prompt("core-v1", "summary")
    doc2 = load_prompt("core-v1", "summary")
    assert doc1 is doc2


def test_load_prompt_missing_set_raises():
    with pytest.raises(FileNotFoundError):
        load_prompt("nope", "goal")
