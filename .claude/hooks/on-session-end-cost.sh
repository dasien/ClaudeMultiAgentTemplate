#!/bin/bash
################################################################################
# on-session-end-cost.sh - Extract cost from session transcript
#
# Thin passthrough hook that delegates cost extraction to Python.
# Receives transcript path from Claude CLI and passes it to cmat.
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Check if we're in a task execution context
TASK_ID="${CMAT_CURRENT_TASK_ID:-}"

if [ -z "$TASK_ID" ]; then
    # Not a task execution, skip cost tracking
    exit 0
fi

# Extract session info from hook input
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // ""')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Call Python to handle cost extraction
cd "$PROJECT_ROOT/.claude"

# Use project's venv if available, otherwise system python
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON_CMD="python3"
fi

"$PYTHON_CMD" -m cmat costs extract "$TASK_ID" "$TRANSCRIPT_PATH" "$SESSION_ID" 2>/dev/null || true