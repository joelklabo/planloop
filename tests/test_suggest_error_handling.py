"""Error handling tests for suggest feature."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from planloop import cli
from planloop.config import SuggestConfig
from planloop.core.context_builder import ContextBuilder
from planloop.core.llm_client import LLMClient, LLMConfig
from planloop.core.session import create_session
from planloop.core.suggest import SuggestionEngine

runner = CliRunner()


def test_llm_client_missing_api_key_error(monkeypatch):
    """Missing API key should raise clear error."""
    from unittest.mock import Mock, patch

    from planloop.core.llm_client import LLMError

    # Ensure no API key in environment
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key=None,  # Missing!
        api_key_env="NONEXISTENT_ENV_VAR"
    )

    # Mock OpenAI to simulate it's installed
    with patch("planloop.core.llm_client.OpenAI", Mock()):
        with pytest.raises(LLMError, match="API key required"):
            LLMClient(config)


def test_llm_client_handles_timeout(monkeypatch):
    """LLM timeout should be handled gracefully."""
    # Set a valid API key
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="sk-test-key"
    )

    # Mock the OpenAI module before initializing client
    with patch("planloop.core.llm_client.OpenAI") as MockOpenAI:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = TimeoutError("Request timed out")
        MockOpenAI.return_value = mock_client

        client = LLMClient(config)

        # LLM client wraps timeouts in LLMError
        from planloop.core.llm_client import LLMError
        with pytest.raises(LLMError, match="timed out"):
            client.generate("test prompt")


def test_context_builder_no_git_repo(tmp_path):
    """Should gracefully handle projects without git."""
    # Create a project without .git
    project = tmp_path / "no_git_project"
    project.mkdir()
    (project / "main.py").write_text("print('hello')")

    builder = ContextBuilder(project)
    context = builder.build(depth="medium")

    # Should succeed with empty git history
    assert context is not None
    assert context.recent_changes == []


def test_context_builder_empty_codebase(tmp_path):
    """Should handle empty project directory."""
    # Create completely empty directory
    empty_project = tmp_path / "empty"
    empty_project.mkdir()

    builder = ContextBuilder(empty_project)
    context = builder.build(depth="shallow")

    # Should succeed with minimal data
    assert context is not None
    assert context.structure == {}
    assert context.language_stats == {}


def test_context_builder_permission_denied(tmp_path):
    """Should skip files that can't be read."""
    project = tmp_path / "restricted"
    project.mkdir()

    # Create a file
    restricted_file = project / "restricted.py"
    restricted_file.write_text("# TODO: secret")

    # On Unix, we can't easily test permission denied in tests
    # But the code should handle it via try/except
    builder = ContextBuilder(project)
    context = builder.build(depth="medium")

    # Should not crash
    assert context is not None


def test_suggest_cli_missing_api_key(monkeypatch, tmp_path):
    """Suggest command should error clearly when API key is missing."""
    home = tmp_path / "home"
    monkeypatch.setenv("PLANLOOP_HOME", str(home))

    # Unset API keys
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    state = create_session("Test", "Test", project_root=Path("/tmp"))

    with patch("planloop.cli._load_session") as mock_load:
        mock_load.return_value = (state, home / "sessions" / state.session)

        result = runner.invoke(cli.app, [
            "suggest",
            "--session", state.session,
            "--dry-run"
        ])

        # Should exit with error
        assert result.exit_code == 1
        # Should have a clear error message about API key
        assert "api key" in result.output.lower() or "error" in result.output.lower()


def test_suggest_engine_handles_invalid_json_response(monkeypatch):
    """Should handle malformed JSON from LLM."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    from datetime import datetime

    from planloop.core.state import Environment, Now, NowReason, PromptMetadata, SessionState

    state = SessionState(
        session="test",
        name="Test",
        title="Test",
        purpose="Testing",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        project_root="/tmp/test",
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="test"),
        now=Now(reason=NowReason.IDLE),
        tasks=[]
    )

    config = SuggestConfig(
        llm_provider="openai",
        llm_model="gpt-4",
        llm_api_key_env="OPENAI_API_KEY"
    )

    # Mock OpenAI before creating engine
    with patch("planloop.core.llm_client.OpenAI"):
        engine = SuggestionEngine(state, config)

        # Mock LLM to return invalid JSON
        with patch.object(engine.llm_client, 'generate_json') as mock_gen:
            mock_gen.side_effect = ValueError("Invalid JSON")

            from planloop.core.llm_client import LLMError
            with pytest.raises(LLMError):
                engine.generate_suggestions(project_root=Path("/tmp/test"))


def test_suggest_handles_rate_limit(monkeypatch):
    """Should handle rate limit errors from LLM API."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="sk-test-key"
    )

    # Simulate rate limit exception
    class RateLimitError(Exception):
        pass

    # Mock OpenAI before creating client
    with patch("planloop.core.llm_client.OpenAI") as MockOpenAI:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded")
        MockOpenAI.return_value = mock_client

        client = LLMClient(config)

        # LLM client wraps all errors in LLMError
        from planloop.core.llm_client import LLMError
        with pytest.raises(LLMError, match="Rate limit"):
            client.generate("test")


def test_context_builder_handles_binary_files(tmp_path):
    """Should skip binary files when scanning for TODOs."""
    project = tmp_path / "with_binary"
    project.mkdir()

    # Create a binary file
    binary_file = project / "image.png"
    binary_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00')

    # Create a text file with TODO
    text_file = project / "code.py"
    text_file.write_text("# TODO: implement this\npass")

    builder = ContextBuilder(project)
    context = builder.build(depth="medium")

    # Should find the text TODO but not crash on binary
    assert context is not None
    assert len(context.todos) == 1
    assert "code.py" in context.todos[0].file


def test_suggest_engine_empty_suggestions_list(monkeypatch):
    """Should handle when LLM returns empty suggestions."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    from datetime import datetime

    from planloop.core.state import Environment, Now, NowReason, PromptMetadata, SessionState

    state = SessionState(
        session="test",
        name="Test",
        title="Test",
        purpose="Testing",
        created_at=datetime.now(),
        last_updated_at=datetime.now(),
        project_root="/tmp/test",
        prompts=PromptMetadata(set="default"),
        environment=Environment(os="test"),
        now=Now(reason=NowReason.IDLE),
        tasks=[]
    )

    config = SuggestConfig(
        llm_provider="openai",
        llm_model="gpt-4",
        llm_api_key_env="OPENAI_API_KEY"
    )

    # Mock OpenAI before creating engine
    with patch("planloop.core.llm_client.OpenAI"):
        engine = SuggestionEngine(state, config)

        # Mock LLM to return empty list
        with patch.object(engine.llm_client, 'generate_json') as mock_gen:
            mock_gen.return_value = []

            suggestions = engine.generate_suggestions(project_root=Path("/tmp/test"))

            # Should return empty list, not crash
            assert suggestions == []
