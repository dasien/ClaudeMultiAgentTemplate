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

# Debug log
DEBUG_LOG="$PROJECT_ROOT/.claude/logs/hook_debug.log"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Hook started, cwd=$(pwd)" >> "$DEBUG_LOG"

# Read hook input from stdin
HOOK_INPUT=$(cat)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Hook input: $HOOK_INPUT" >> "$DEBUG_LOG"

# Check if we're in a task execution context
TASK_ID="${CMAT_CURRENT_TASK_ID:-}"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] TASK_ID=$TASK_ID" >> "$DEBUG_LOG"

if [ -z "$TASK_ID" ]; then
    # Not a task execution, skip cost tracking
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] No TASK_ID, exiting" >> "$DEBUG_LOG"
    exit 0
fi

# Extract session info from hook input
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // ""')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] TRANSCRIPT_PATH=$TRANSCRIPT_PATH" >> "$DEBUG_LOG"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] File exists: $([ -f "$TRANSCRIPT_PATH" ] && echo "yes" || echo "no")" >> "$DEBUG_LOG"

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Transcript not found, exiting" >> "$DEBUG_LOG"
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

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Running: $PYTHON_CMD -m cmat costs extract $TASK_ID $TRANSCRIPT_PATH $SESSION_ID" >> "$DEBUG_LOG"
RESULT=$("$PYTHON_CMD" -m cmat costs extract "$TASK_ID" "$TRANSCRIPT_PATH" "$SESSION_ID" 2>&1) || true
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Result: $RESULT" >> "$DEBUG_LOG"