"""Session history helpers using git."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import history_enabled

GITIGNORE_CONTENT = """# planloop session history\nartifacts/\nlogs/\n*.log\n*.tmp\n"""

GIT_AUTHOR = "planloop"
GIT_EMAIL = "planloop@example.com"


def _git_available() -> bool:
    return shutil.which("git") is not None


def ensure_repo(session_dir: Path) -> bool:
    if not history_enabled() or not _git_available():
        return False
    git_dir = session_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=session_dir, check=True)
        subprocess.run(["git", "config", "user.name", GIT_AUTHOR], cwd=session_dir, check=True)
        subprocess.run(["git", "config", "user.email", GIT_EMAIL], cwd=session_dir, check=True)
        gitignore = session_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(GITIGNORE_CONTENT, encoding="utf-8")
    return True


def commit_state(session_dir: Path, message: str, allow_empty: bool = False) -> None:
    if not ensure_repo(session_dir):
        return
    tracked = ["state.json", "PLAN.md"]
    gitignore = session_dir / ".gitignore"
    if gitignore.exists():
        tracked.append(".gitignore")
    subprocess.run(["git", "add", *tracked], cwd=session_dir, check=True)
    cmd = ["git", "commit", "-m", message]
    if allow_empty:
        cmd.insert(2, "--allow-empty")
    result = subprocess.run(cmd, cwd=session_dir)
    if result.returncode not in (0, 1):
        result.check_returncode()


def create_snapshot(session_dir: Path, note: str) -> str:
    if not ensure_repo(session_dir):
        raise RuntimeError("History not enabled")
    commit_state(session_dir, f"Snapshot: {note}", allow_empty=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=session_dir, text=True, capture_output=True, check=True)
    return sha.stdout.strip()


def restore_snapshot(session_dir: Path, ref: str) -> None:
    if not ensure_repo(session_dir):
        raise RuntimeError("History not enabled")
    subprocess.run(["git", "reset", "--hard", ref], cwd=session_dir, check=True)


__all__ = [
    "ensure_repo",
    "commit_state",
    "create_snapshot",
    "restore_snapshot",
]
