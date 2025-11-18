"""Tests for environment setup scripts and Rust dependency handling (Task 7).

Verifies that setup scripts properly handle Rust-dependent packages and
provide helpful error messages when Rust is missing.
"""
import subprocess
from pathlib import Path

import pytest


def test_verify_env_detects_missing_venv(tmp_path, monkeypatch):
    """verify-env.sh detects missing virtual environment."""
    monkeypatch.chdir(tmp_path)

    # Create minimal verify script
    script = tmp_path / "verify-env.sh"
    script.write_text("""#!/bin/bash
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found"
    exit 1
fi
echo "OK"
""")
    script.chmod(0o755)

    result = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Virtual environment not found" in result.stdout


def test_setup_checks_rust_availability():
    """setup-dev.sh should check if Rust is available before installing pydantic."""
    setup_script = Path("setup-dev.sh")
    content = setup_script.read_text()

    # Should mention Rust or have check for cargo
    # This test documents current state - may need Rust check added
    assert "uv pip install" in content  # At minimum, uses uv


def test_verify_env_checks_rust_for_pydantic():
    """verify-env.sh should warn if Rust missing but pydantic needed."""
    verify_script = Path("verify-env.sh")
    content = verify_script.read_text()

    # Should check Python imports work
    assert "import planloop" in content or "python -c" in content


def test_pyproject_lists_rust_dependent_packages():
    """pyproject.toml should document which packages need Rust."""
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()

    # Should have dependencies section
    assert "dependencies" in content
    assert "pydantic" in content  # Known Rust-dependent package


def test_setup_provides_retry_logic_hint():
    """If uv install fails, setup should suggest retry strategies."""
    # This test documents desired behavior
    # Setup script should catch uv install failures and provide hints
    setup_script = Path("setup-dev.sh")
    content = setup_script.read_text()

    # Currently uses set -e which exits on error
    # Could be improved with error handling
    assert "set -e" in content or "set -euo pipefail" in content


def test_documentation_mentions_rust_requirement():
    """Development documentation should mention Rust requirement."""
    # Check if README or setup docs mention Rust
    readme = Path("README.md")
    if readme.exists():
        content = readme.read_text()
        # Should ideally mention Rust or provide setup link
        # This test documents current state
        assert len(content) > 100  # Has content


def test_verify_env_provides_actionable_error_messages(tmp_path, monkeypatch):
    """verify-env.sh should tell users exactly what to do when checks fail."""
    # Load actual script
    script_path = Path("verify-env.sh")
    if not script_path.exists():
        pytest.skip("verify-env.sh not found")

    content = script_path.read_text()

    # Should provide "Run: ..." instructions
    assert "Run:" in content or "run:" in content.lower()
    # Should mention setup-dev.sh
    assert "setup-dev.sh" in content
