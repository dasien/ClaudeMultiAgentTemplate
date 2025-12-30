#!/bin/bash
################################################################################
# on-session-end-cost.sh - Extract cost from session transcript
#
# Thin passthrough hook that delegates cost extraction to Python.
# Receives transcript path from Claude CLI and passes it to cmat.
#
# Required environment variables (set by CMAT UI when starting tasks):
#   CMAT_CURRENT_TASK_ID - The task ID being executed
#   CMAT_ROOT - Path to CMAT installation (contains src/core)
################################################################################

set -euo pipefail

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

# Find CMAT root - use env var if set, otherwise fail silently
CMAT_ROOT="${CMAT_ROOT:-}"
if [ -z "$CMAT_ROOT" ] || [ ! -d "$CMAT_ROOT/src/core" ]; then
    # CMAT not found, skip cost tracking
    exit 0
fi

# Use CMAT's Python path
export PYTHONPATH="$CMAT_ROOT/src:${PYTHONPATH:-}"

# Use system python
python3 -m core costs extract "$TASK_ID" "$TRANSCRIPT_PATH" "$SESSION_ID" 2>/dev/null || true