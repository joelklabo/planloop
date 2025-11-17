"""Tests for LLM client abstraction."""
from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest

from planloop.core.llm_client import LLMClient, LLMConfig, LLMError


def test_llm_config_validates_provider():
    """LLMConfig should validate provider is one of supported types."""
    # Valid providers
    LLMConfig(provider="openai", model="gpt-4")
    LLMConfig(provider="anthropic", model="claude-3-sonnet")
    LLMConfig(provider="ollama", model="llama2")
    
    # Invalid provider should raise validation error
    with pytest.raises(Exception):  # Pydantic validation error
        LLMConfig(provider="invalid", model="test")


def test_llm_config_defaults():
    """LLMConfig should have sensible defaults."""
    config = LLMConfig(provider="openai", model="gpt-4")
    assert config.temperature == 0.7
    assert config.max_tokens == 4000
    assert config.api_key is None
    assert config.base_url is None


def test_llm_client_openai_generate(monkeypatch):
    """LLMClient should call OpenAI API and return response."""
    # Mock the OpenAI client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated text"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("planloop.core.llm_client.OpenAI", return_value=mock_client):
        config = LLMConfig(provider="openai", model="gpt-4", api_key="test-key")
        client = LLMClient(config)
        
        result = client.generate("Test prompt")
        
        assert result == "Generated text"
        mock_client.chat.completions.create.assert_called_once()


def test_llm_client_anthropic_generate(monkeypatch):
    """LLMClient should call Anthropic API and return response."""
    # Mock the Anthropic client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Generated text")]
    mock_client.messages.create.return_value = mock_response
    
    with patch("planloop.core.llm_client.Anthropic", return_value=mock_client):
        config = LLMConfig(provider="anthropic", model="claude-3-sonnet", api_key="test-key")
        client = LLMClient(config)
        
        result = client.generate("Test prompt")
        
        assert result == "Generated text"
        mock_client.messages.create.assert_called_once()


def test_llm_client_generate_json():
    """LLMClient should parse JSON responses."""
    mock_client = Mock()
    mock_response = Mock()
    json_output = {"key": "value", "count": 42}
    mock_response.choices = [Mock(message=Mock(content=json.dumps(json_output)))]
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("planloop.core.llm_client.OpenAI", return_value=mock_client):
        config = LLMConfig(provider="openai", model="gpt-4", api_key="test-key")
        client = LLMClient(config)
        
        result = client.generate_json("Test prompt", schema={"type": "object"})
        
        assert result == json_output
        assert isinstance(result, dict)


def test_llm_client_raises_on_api_error():
    """LLMClient should raise LLMError on API failures."""
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    with patch("planloop.core.llm_client.OpenAI", return_value=mock_client):
        config = LLMConfig(provider="openai", model="gpt-4", api_key="test-key")
        client = LLMClient(config)
        
        with pytest.raises(LLMError):
            client.generate("Test prompt")


def test_llm_client_requires_api_key_for_cloud_providers():
    """LLMClient should require API key for OpenAI and Anthropic."""
    # OpenAI without key should raise error
    config = LLMConfig(provider="openai", model="gpt-4")
    with pytest.raises(LLMError, match="API key required"):
        LLMClient(config)
    
    # Anthropic without key should raise error
    config = LLMConfig(provider="anthropic", model="claude-3-sonnet")
    with pytest.raises(LLMError, match="API key required"):
        LLMClient(config)


def test_llm_client_ollama_doesnt_require_api_key():
    """LLMClient should allow Ollama without API key (local model)."""
    # Mock the requests module
    mock_requests = Mock()
    mock_post_response = Mock()
    mock_post_response.json.return_value = {"response": "Generated text"}
    mock_post_response.status_code = 200
    mock_requests.post.return_value = mock_post_response
    
    with patch("planloop.core.llm_client.requests", mock_requests):
        config = LLMConfig(provider="ollama", model="llama2")
        client = LLMClient(config)
        
        result = client.generate("Test prompt")
        assert result == "Generated text"
        mock_requests.post.assert_called_once()


def test_llm_client_loads_api_key_from_env(monkeypatch):
    """LLMClient should load API key from environment variable."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-test-key")
    
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("planloop.core.llm_client.OpenAI") as mock_openai:
        mock_openai.return_value = mock_client
        
        config = LLMConfig(provider="openai", model="gpt-4")
        client = LLMClient(config)
        
        # Should succeed because env var is set
        result = client.generate("Test")
        assert result == "Test"
        
        # Verify OpenAI was initialized with the env key
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["api_key"] == "env-test-key"
