"""Tests for suggest feature configuration."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from planloop.config import get_suggest_config, SuggestConfig


@pytest.fixture
def mock_config_file(tmp_path, monkeypatch):
    """Create a mock config file."""
    config_dir = tmp_path / ".planloop"
    config_dir.mkdir()
    config_file = config_dir / "config.yml"
    
    # Patch the home directory
    with patch("planloop.config.initialize_home", return_value=config_dir):
        yield config_file


def test_suggest_config_defaults():
    """SuggestConfig should have sensible defaults."""
    config = SuggestConfig()
    
    # LLM defaults
    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-4o-mini"
    assert config.llm_temperature == 0.7
    assert config.llm_max_tokens == 4000
    
    # Context defaults
    assert config.context_depth == "medium"
    assert config.include_git_history is True
    assert config.max_recent_commits == 10
    assert config.include_todos is True
    
    # Filter defaults
    assert "__pycache__" in config.ignore_patterns
    assert ".git" in config.ignore_patterns
    assert config.focus_paths == []


def test_get_suggest_config_returns_defaults_when_no_file():
    """get_suggest_config should return defaults if no config file exists."""
    with patch("planloop.config.load_config", return_value={}):
        config = get_suggest_config()
        
        assert config.llm_provider == "openai"
        assert config.context_depth == "medium"


def test_get_suggest_config_loads_from_file():
    """get_suggest_config should load settings from config file."""
    from planloop.config import reset_config_cache
    
    mock_config = {
        "suggest": {
            "llm": {
                "provider": "anthropic",
                "model": "claude-3-sonnet",
                "temperature": 0.5,
                "max_tokens": 2000
            },
            "context": {
                "depth": "deep",
                "include_git_history": False,
                "max_recent_commits": 20
            },
            "filters": {
                "ignore_patterns": ["*.log", "build/"],
                "focus_paths": ["src/", "tests/"]
            }
        }
    }
    
    reset_config_cache()  # Clear cache before patching
    with patch("planloop.config.load_config", return_value=mock_config):
        config = get_suggest_config()
        
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3-sonnet"
        assert config.llm_temperature == 0.5
        assert config.llm_max_tokens == 2000
        assert config.context_depth == "deep"
        assert config.include_git_history is False
        assert config.max_recent_commits == 20
        assert "*.log" in config.ignore_patterns
        assert "src/" in config.focus_paths
    
    reset_config_cache()  # Clear cache after


def test_get_suggest_config_api_key_from_env(monkeypatch):
    """get_suggest_config should load API key from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    
    with patch("planloop.config.load_config", return_value={}):
        config = get_suggest_config()
        
        # Should have the env var name stored
        assert config.llm_api_key_env == "OPENAI_API_KEY"


def test_get_suggest_config_api_key_from_config():
    """get_suggest_config should load API key env var name from config."""
    from planloop.config import reset_config_cache
    
    mock_config = {
        "suggest": {
            "llm": {
                "provider": "openai",
                "api_key_env": "MY_CUSTOM_KEY"
            }
        }
    }
    
    reset_config_cache()
    with patch("planloop.config.load_config", return_value=mock_config):
        config = get_suggest_config()
        
        assert config.llm_api_key_env == "MY_CUSTOM_KEY"
    
    reset_config_cache()


def test_get_suggest_config_partial_settings():
    """get_suggest_config should merge partial settings with defaults."""
    from planloop.config import reset_config_cache
    
    mock_config = {
        "suggest": {
            "llm": {
                "model": "gpt-4-turbo"
            }
        }
    }
    
    reset_config_cache()
    with patch("planloop.config.load_config", return_value=mock_config):
        config = get_suggest_config()
        
        # Should override model but keep other defaults
        assert config.llm_model == "gpt-4-turbo"
        assert config.llm_provider == "openai"  # default
        assert config.llm_temperature == 0.7  # default
        assert config.context_depth == "medium"  # default
    
    reset_config_cache()


def test_suggest_config_validates_provider():
    """SuggestConfig should validate provider is valid."""
    # Valid providers
    SuggestConfig(llm_provider="openai")
    SuggestConfig(llm_provider="anthropic")
    SuggestConfig(llm_provider="ollama")
    
    # Invalid provider should raise validation error
    with pytest.raises(Exception):  # Pydantic validation error
        SuggestConfig(llm_provider="invalid")


def test_suggest_config_validates_depth():
    """SuggestConfig should validate depth is valid."""
    # Valid depths
    SuggestConfig(context_depth="shallow")
    SuggestConfig(context_depth="medium")
    SuggestConfig(context_depth="deep")
    
    # Invalid depth should raise validation error
    with pytest.raises(Exception):  # Pydantic validation error
        SuggestConfig(context_depth="invalid")


def test_get_suggest_config_uses_cache(monkeypatch):
    """get_suggest_config should cache results."""
    from planloop.config import reset_config_cache
    
    reset_config_cache()
    
    # First call loads from config
    config1 = get_suggest_config()
    # Second call should use cache
    config2 = get_suggest_config()
    
    # Should be the same object (cached)
    assert config1 is config2
    
    reset_config_cache()
