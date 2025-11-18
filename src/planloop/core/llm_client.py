"""LLM client abstraction for multiple providers."""
from __future__ import annotations

import json
import os
from typing import Any, Literal

from pydantic import BaseModel

# Optional imports for LLM providers
try:
    from anthropic import Anthropic  # type: ignore[import-not-found]
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI  # type: ignore[import-not-found]
except ImportError:
    OpenAI = None

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None


class LLMError(Exception):
    """Base error for LLM client failures."""


class LLMConfig(BaseModel):
    """Configuration for LLM client."""

    provider: Literal["openai", "anthropic", "ollama"]
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4000


class LLMClient:
    """Abstract client for multiple LLM providers."""

    def __init__(self, config: LLMConfig):
        """Initialize LLM client with configuration.

        Args:
            config: LLM configuration

        Raises:
            LLMError: If API key is required but not provided
        """
        self.config = config
        self._client: Any = None

        # For cloud providers, require API key (from config or env)
        if config.provider in ("openai", "anthropic"):
            api_key = config.api_key or self._get_api_key_from_env(config.provider)
            if not api_key:
                raise LLMError(f"API key required for {config.provider}")
            self.config = config.model_copy(update={"api_key": api_key})

        # Initialize provider-specific client
        self._initialize_client()

    def _get_api_key_from_env(self, provider: str) -> str | None:
        """Get API key from environment variable."""
        if provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        return None

    def _initialize_client(self) -> None:
        """Initialize provider-specific client."""
        if self.config.provider == "openai":
            if OpenAI is None:
                raise LLMError("openai package not installed. Run: pip install openai")

            kwargs = {"api_key": self.config.api_key}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            self._client = OpenAI(**kwargs)

        elif self.config.provider == "anthropic":
            if Anthropic is None:
                raise LLMError("anthropic package not installed. Run: pip install anthropic")

            kwargs = {"api_key": self.config.api_key}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            self._client = Anthropic(**kwargs)

        elif self.config.provider == "ollama":
            # Ollama uses REST API via requests module
            if requests is None:
                raise LLMError("requests package not installed. Run: pip install requests")
            self._client = requests

    def generate(self, prompt: str, schema: dict | None = None) -> str:
        """Generate text from prompt.

        Args:
            prompt: Input prompt
            schema: Optional JSON schema for structured output

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        try:
            if self.config.provider == "openai":
                return self._generate_openai(prompt, schema)
            elif self.config.provider == "anthropic":
                return self._generate_anthropic(prompt, schema)
            elif self.config.provider == "ollama":
                return self._generate_ollama(prompt, schema)
            else:
                raise LLMError(f"Unknown provider: {self.config.provider}")
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Generation failed: {e}") from e

    def generate_json(self, prompt: str, schema: dict) -> dict:
        """Generate JSON response from prompt.

        Args:
            prompt: Input prompt
            schema: JSON schema for validation

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If generation or parsing fails
        """
        response = self.generate(prompt, schema)
        try:
            parsed: dict[Any, Any] = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse JSON response: {e}") from e

    def _generate_openai(self, prompt: str, schema: dict | None = None) -> str:
        """Generate using OpenAI API."""
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        # Use JSON mode if schema provided
        if schema:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            raise LLMError("OpenAI returned empty content")
        return str(content)

    def _generate_anthropic(self, prompt: str, schema: dict | None = None) -> str:
        """Generate using Anthropic API."""
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        # Anthropic doesn't have built-in JSON mode, but we can request it in prompt
        if schema:
            prompt_with_schema = f"{prompt}\n\nRespond with valid JSON matching this schema:\n{json.dumps(schema)}"
            kwargs["messages"] = [{"role": "user", "content": prompt_with_schema}]

        response = self._client.messages.create(**kwargs)
        text = response.content[0].text
        return str(text)

    def _generate_ollama(self, prompt: str, schema: dict | None = None) -> str:
        """Generate using Ollama local API."""
        base_url = self.config.base_url or "http://localhost:11434"

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }

        if schema:
            # Ollama supports JSON mode via format parameter
            payload["format"] = "json"

        response = self._client.post(f"{base_url}/api/generate", json=payload)

        if response.status_code != 200:
            raise LLMError(f"Ollama API error: {response.status_code} {response.text}")

        response_data = response.json()
        return str(response_data["response"])
