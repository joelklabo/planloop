# Development Environment Setup

This project uses **uv** for Python environment management to ensure consistency across all developers and agents.

## For Humans

Run the automated setup script:
```bash
./setup-dev.sh
source .venv/bin/activate
```

Or use Make commands:
```bash
make setup
make test
```

## For Agents

**ALWAYS** activate the virtual environment before running Python commands:

```bash
# Activate the environment
source .venv/bin/activate

# Then run commands
python --version    # Will be 3.11.x
pytest tests/ -v
planloop status
```

### If environment is broken or missing:

```bash
# Reset everything
./setup-dev.sh

# Or manually:
uv venv --python 3.11
uv pip install -e ".[dev]"
source .venv/bin/activate
```

### Common Issues

**Problem**: `python: command not found` or wrong Python version
**Solution**: Activate the venv first with `source .venv/bin/activate`

**Problem**: Import errors or missing packages
**Solution**: Reinstall deps with `uv pip install -e ".[dev]"`

**Problem**: Tests fail with syntax errors about `|` in type hints
**Solution**: You're using Python 3.9. This project requires 3.11+. Run `./setup-dev.sh`

## Why uv?

- **Fast**: 10-100x faster than pip
- **Reproducible**: Guarantees exact Python version (3.11)
- **Simple**: One command to set up everything
- **Reliable**: No more "works on my machine" issues

## Files to Know

- `.python-version` - Specifies Python 3.11 requirement
- `pyproject.toml` - Project metadata and dependencies
- `setup-dev.sh` - Automated setup script
- `Makefile` - Convenient shortcuts for common tasks
