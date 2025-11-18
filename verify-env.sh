#!/usr/bin/env bash
# Quick environment verification for agents
# Run this if you're unsure about the environment state

set -euo pipefail

echo "🔍 Verifying development environment..."
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    echo "   Run: ./setup-dev.sh"
    exit 1
fi
echo "✓ Virtual environment exists"

# Check if venv is activated
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Run: source .venv/bin/activate"
    echo ""
fi

# Check Python version
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 11 ]; then
        echo "✓ Python version: $PYTHON_VERSION (OK)"
    else
        echo "❌ Python version: $PYTHON_VERSION (need 3.11+)"
        echo "   Run: ./setup-dev.sh"
        exit 1
    fi
else
    echo "❌ Python not found in PATH"
    echo "   Run: source .venv/bin/activate"
    exit 1
fi

# Check if planloop is installed
if python -c "import planloop" 2>/dev/null; then
    echo "✓ planloop package installed"
else
    echo "❌ planloop package not installed"
    echo "   Run: uv pip install -e '.[dev]'"
    exit 1
fi

# Check if test dependencies are installed
if python -c "import pytest" 2>/dev/null; then
    echo "✓ pytest installed"
else
    echo "❌ pytest not installed"
    echo "   Run: uv pip install -e '.[dev]'"
    exit 1
fi

# Quick smoke test
echo ""
echo "Running quick smoke test..."
if python -c "from planloop.core import state; print('Import test: OK')" 2>/dev/null; then
    echo "✓ Imports working"
else
    echo "❌ Import test failed"
    exit 1
fi

echo ""
echo "✅ Environment is ready!"
echo ""
echo "Quick commands:"
echo "  make test      # Run all tests"
echo "  make lint      # Run linters"
echo "  make format    # Format code"
