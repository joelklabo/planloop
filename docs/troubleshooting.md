# Troubleshooting Guide

## Development Environment Issues

### "error: failed to compile `pydantic-core`" or Rust-related errors

**Problem**: uv fails to install dependencies with Rust compilation errors.

**Cause**: Some packages (like `pydantic-core`) require Rust toolchain to build from source when pre-built wheels aren't available for your platform.

**Solution**:

1. **Install Rust toolchain**:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   cargo --version  # Verify installation
   ```

2. **Retry setup**:
   ```bash
   ./setup-dev.sh
   ```

3. **If still failing**, clear uv cache and retry:
   ```bash
   rm -rf ~/.cache/uv
   ./setup-dev.sh
   ```

### "Python version mismatch" after updating pyproject.toml

**Problem**: After changing Python version requirements in `pyproject.toml`, environment breaks.

**Solution**:

1. **Remove existing venv**:
   ```bash
   rm -rf .venv
   ```

2. **Rerun setup**:
   ```bash
   ./setup-dev.sh
   source .venv/bin/activate
   ```

3. **Verify**:
   ```bash
   ./verify-env.sh
   ```

### "ModuleNotFoundError" after pulling latest changes

**Problem**: New dependencies added but not installed in your environment.

**Solution**:

1. **Update dependencies**:
   ```bash
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

2. **If that fails, reset environment**:
   ```bash
   rm -rf .venv
   ./setup-dev.sh
   ```

### "ImportError: cannot import name X" with pydantic

**Problem**: Pydantic version mismatch or incomplete installation.

**Cause**: Often happens when pydantic-core (Rust package) fails to build but installation continues.

**Solution**:

1. **Check if Rust is installed**:
   ```bash
   cargo --version
   ```

2. **If not, install Rust** (see above)

3. **Force reinstall pydantic**:
   ```bash
   source .venv/bin/activate
   uv pip uninstall pydantic pydantic-core
   uv pip install pydantic
   ```

4. **If still broken, reset environment**:
   ```bash
   rm -rf .venv
   ./setup-dev.sh
   ```

## uv-Specific Issues

### "uv not found" after installation

**Problem**: uv installed but not in PATH.

**Solution**:

```bash
# Add uv to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or restart your shell
exec $SHELL

# Verify
uv --version
```

### "Network timeout" during package installation

**Problem**: Network issues or PyPI unavailable.

**Solution**:

1. **Check network connection**

2. **Retry with timeout increase**:
   ```bash
   UV_HTTP_TIMEOUT=120 uv pip install -e ".[dev]"
   ```

3. **Use a mirror** (if in a restricted network):
   ```bash
   uv pip install -e ".[dev]" --index-url https://pypi.org/simple
   ```

### "Lock file out of date" warnings

**Problem**: uv.lock is out of sync with pyproject.toml.

**Solution**:

```bash
# Regenerate lock file
uv lock

# Or use --no-lock
uv pip install -e ".[dev]" --no-lock
```

## Test Failures

### Tests pass locally but fail in CI

**Common causes**:

1. **Platform differences** (macOS vs Linux)
2. **Environment differences** (packages, versions)
3. **Timing issues** (race conditions)

**Solution**:

1. **Check CI logs** for specific errors

2. **Run tests with same Python version as CI**:
   ```bash
   uv venv --python 3.11.14  # Match CI exactly
   source .venv/bin/activate
   pytest tests/
   ```

3. **Test in isolation**:
   ```bash
   pytest tests/test_specific.py::test_function -v
   ```

### "Permission denied" errors during tests

**Problem**: Tests trying to write to protected locations.

**Solution**:

Tests should use `tmp_path` fixture (pytest provides this):

```python
def test_something(tmp_path):
    # Write to tmp_path, not system directories
    test_file = tmp_path / "test.txt"
    test_file.write_text("data")
```

## IDE Issues

### VS Code: "Import could not be resolved"

**Problem**: VS Code not using venv Python interpreter.

**Solution**:

1. **Select interpreter**:
   - `Cmd+Shift+P` → "Python: Select Interpreter"
   - Choose `.venv/bin/python`

2. **Reload window**:
   - `Cmd+Shift+P` → "Developer: Reload Window"

### PyCharm: "No module named 'planloop'"

**Problem**: PyCharm not configured to use venv.

**Solution**:

1. **Settings** → **Project** → **Python Interpreter**
2. **Add Interpreter** → **Existing** → Select `.venv/bin/python`
3. **Apply**

## Getting Help

If you're still stuck:

1. **Check GitHub Issues**: [github.com/joelklabo/planloop/issues](https://github.com/joelklabo/planloop/issues)
2. **Run diagnostics**:
   ```bash
   ./verify-env.sh
   planloop selftest --json
   ```
3. **Create an issue** with:
   - Your platform (macOS/Linux version)
   - Python version (`python --version`)
   - Error message (full traceback)
   - Steps to reproduce
