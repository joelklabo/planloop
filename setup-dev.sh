#!/usr/bin/env bash
# Foolproof development environment setup using uv
# Run this script to set up or reset your development environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✓ uv installed: $(uv --version)"

# Check for Rust (needed for pydantic-core and other Rust-based packages)
echo ""
echo "Checking for Rust toolchain..."
if command -v cargo &> /dev/null; then
    RUST_VERSION=$(cargo --version | awk '{print $2}')
    echo "✓ Rust installed: $RUST_VERSION"
else
    echo -e "${YELLOW}⚠️  Rust not found${NC}"
    echo ""
    echo "Some Python packages (like pydantic-core) require Rust to build from source."
    echo "uv will attempt to use pre-built wheels, but if those fail, you'll need Rust."
    echo ""
    echo "To install Rust:"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo ""
    echo "Continuing with setup (will use pre-built wheels if available)..."
    sleep 2
fi

# Create/sync venv with exact Python version
echo ""
echo "Setting up Python 3.11 virtual environment..."
uv venv --python 3.11

echo "✓ Virtual environment created"

# Install dependencies with retry logic
echo ""
echo "Installing dependencies..."

MAX_RETRIES=2
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if uv pip install -e ".[dev]"; then
        echo "✓ Dependencies installed"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}⚠️  Installation failed, retrying ($RETRY_COUNT/$MAX_RETRIES)...${NC}"
            sleep 2
        else
            echo -e "${RED}❌ Installation failed after $MAX_RETRIES attempts${NC}"
            echo ""
            echo "Common fixes:"
            echo "1. Install Rust toolchain:"
            echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            echo ""
            echo "2. Clear uv cache and retry:"
            echo "   rm -rf ~/.cache/uv"
            echo "   ./setup-dev.sh"
            echo ""
            echo "3. Check network connection (packages are downloaded from PyPI)"
            exit 1
        fi
    fi
done

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
