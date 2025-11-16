"""Command-driven agent adapters for the prompt lab."""
from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class AgentResult:
    agent: str
    enabled: bool
    returncode: int | None
    stdout_path: Path | None
    stderr_path: Path | None
    message: str


class CommandAdapter:
    """Base adapter that shells out to a user-provided command."""

    def __init__(self, name: str, env_var: str, description: str) -> None:
        self.name = name
        self.env_var = env_var
        self.description = description

    def command(self) -> str | None:
        return os.environ.get(self.env_var)

    def run(self, env: Dict[str, str], workspace: Path, output_dir: Path) -> AgentResult:
        cmd = self.command()
        if not cmd:
            return AgentResult(self.name, False, None, None, None, f"Set {self.env_var} to enable {self.name} adapter")
        adapter_dir = output_dir / self.name
        adapter_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = adapter_dir / "stdout.txt"
        stderr_path = adapter_dir / "stderr.txt"
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
            result = subprocess.run(
                shlex.split(cmd),
                cwd=workspace,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
            )
        message = "success" if result.returncode == 0 else f"exit code {result.returncode}"
        return AgentResult(self.name, True, result.returncode, stdout_path, stderr_path, message)


class CopilotAdapter(CommandAdapter):
    def __init__(self) -> None:
        super().__init__("copilot", "PLANLOOP_LAB_COPILOT_CMD", "Command to invoke GitHub Copilot CLI agent")


class OpenAIAdapter(CommandAdapter):
    def __init__(self) -> None:
        super().__init__("openai", "PLANLOOP_LAB_OPENAI_CMD", "Command to invoke OpenAI/Codex agent")


class ClaudeAdapter(CommandAdapter):
    def __init__(self) -> None:
        super().__init__("claude", "PLANLOOP_LAB_CLAUDE_CMD", "Command to invoke Claude CLI agent")


__all__ = [
    "AgentResult",
    "CommandAdapter",
    "CopilotAdapter",
    "OpenAIAdapter",
    "ClaudeAdapter",
]
