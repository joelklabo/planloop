"""Test that prompt patterns are documented"""
import pytest
from pathlib import Path


def test_prompt_patterns_document_exists():
    """Verify that successful prompt patterns are documented"""
    doc_path = Path("docs/reference/successful-prompt-patterns.md")
    assert doc_path.exists(), "Prompt patterns documentation should exist"


def test_prompt_patterns_contains_key_sections():
    """Verify documentation has all necessary sections"""
    doc_path = Path("docs/reference/successful-prompt-patterns.md")
    content = doc_path.read_text()
    
    # Must document each agent
    assert "## Copilot" in content or "## GitHub Copilot" in content, "Must document Copilot patterns"
    assert "## Claude" in content, "Must document Claude patterns"
    
    # Must include performance metrics
    assert "pass rate" in content.lower() or "performance" in content.lower(), "Must include performance data"
    
    # Must include actual prompts or references
    assert "prompt" in content.lower(), "Must reference actual prompts"
    
    # Must explain what worked
    assert "pattern" in content.lower() or "technique" in content.lower(), "Must explain successful patterns"


def test_prompt_patterns_documents_versions():
    """Verify that prompt versions are tracked"""
    doc_path = Path("docs/reference/successful-prompt-patterns.md")
    content = doc_path.read_text()
    
    # Should track versions
    assert "v0.3" in content or "version" in content.lower(), "Should track prompt versions"
