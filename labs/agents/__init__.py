"""Agent adapters for prompt lab."""

from .command import ClaudeAdapter, CopilotAdapter, OpenAIAdapter

__all__ = ["CopilotAdapter", "OpenAIAdapter", "ClaudeAdapter"]
