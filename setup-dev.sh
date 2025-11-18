#!/usr/bin/env bash
# Foolproof development environment setup using uv
# Run this script to set up or reset your development environment

set -euo pipefail

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✓ uv installed: $(uv --version)"

# Create/sync venv with exact Python version
echo "Setting up Python 3.11 virtual environment..."
uv venv --python 3.11

echo "✓ Virtual environment created"

# Install dependencies
echo "Installing dependencies..."
uv pip install -e ".[dev]"

echo "✓ Dependencies installed"

# Verify installation
echo ""
echo "Verifying installation..."
source .venv/bin/activate
python --version
pytest --version

echo ""
echo "✅ Development environment ready!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest tests/ -v"
