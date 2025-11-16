#!/usr/bin/env bash
# Test real agent CLIs to understand their behavior and requirements

set -euo pipefail

echo "=== Testing Real Agent CLIs ==="
echo ""

# Setup test environment
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
echo "Test directory: $TEST_DIR"
echo ""

# Create a simple test file
cat > test.txt << 'EOF'
This is a test file.
Task: List the files in this directory.
EOF

echo "=== 1. Testing GitHub Copilot CLI ==="
echo "Command: copilot --help"
copilot --help 2>&1 | head -30 || echo "Copilot help failed"
echo ""

echo "Attempting simple prompt with Copilot..."
echo "Command: copilot -p 'List files in current directory' --no-color"
timeout 30s copilot -p "List the files in the current directory using ls" --no-color 2>&1 || {
    echo "Copilot execution timed out or failed"
}
echo ""

echo "=== 2. Testing Claude CLI ==="
echo "Command: claude --version"
claude --version 2>&1 || echo "Claude version check failed"
echo ""

echo "Command: claude --help"
claude --help 2>&1 | head -30 || echo "Claude help failed"
echo ""

echo "Attempting simple prompt with Claude..."
echo "Command: claude -p 'List files in current directory' --print"
timeout 30s claude -p "List the files in the current directory using ls" --print 2>&1 || {
    echo "Claude execution timed out or failed"
}
echo ""

echo "=== 3. Checking for model information ==="
echo ""

echo "Copilot model detection:"
copilot --help 2>&1 | grep -i "model" | head -5 || echo "No model flags found in Copilot"
echo ""

echo "Claude model detection:"
claude --help 2>&1 | grep -i "model" | head -5 || echo "No model flags found in Claude"
echo ""

echo "=== 4. Testing with planloop context ==="
echo "Setting up minimal planloop environment..."

export PLANLOOP_HOME="$TEST_DIR/.planloop"
mkdir -p "$PLANLOOP_HOME"

# Try a planloop-specific command
echo ""
echo "Testing Copilot with planloop command:"
timeout 30s copilot -p "Run the command: echo 'Hello from Copilot'" --no-color 2>&1 || {
    echo "Copilot planloop test timed out or failed"
}

echo ""
echo "Testing Claude with planloop command:"
timeout 30s claude -p "Run the command: echo 'Hello from Claude'" --print --allowedTools "Bash" 2>&1 || {
    echo "Claude planloop test timed out or failed"
}

echo ""
echo "=== Test Complete ==="
echo "Test directory: $TEST_DIR"
echo "Review output above to understand agent behavior"
