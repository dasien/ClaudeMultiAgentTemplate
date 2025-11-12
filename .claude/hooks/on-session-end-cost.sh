#!/bin/bash
################################################################################
# on-session-end-cost.sh - Extract cost from session transcript
#
# Parses the transcript JSONL file to extract token usage and calculate costs
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Check if we're in a task execution context
TASK_ID="${CMAT_CURRENT_TASK_ID:-}"
LOG_FILE="${CMAT_CURRENT_LOG_FILE:-}"

if [ -z "$TASK_ID" ]; then
    # Not a task execution, skip cost tracking
    exit 0
fi

# Extract session info from hook input
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // "unknown"')
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // ""')
REASON=$(echo "$HOOK_INPUT" | jq -r '.reason // "unknown"')

if [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "⚠️  Transcript not found: $TRANSCRIPT_PATH" >&2
    exit 0
fi

echo "=== Extracting Cost from Transcript ===" >&2
echo "Task ID: $TASK_ID" >&2
echo "Session ID: $SESSION_ID" >&2
echo "Transcript: $TRANSCRIPT_PATH" >&2

# Extract all assistant messages with usage data from transcript
# The transcript is JSONL format - one JSON object per line
USAGE_SUMMARY=$(grep -a '"type":"assistant"' "$TRANSCRIPT_PATH" | \
    jq -s '
        map(select(.message.usage != null) | .message.usage) |
        {
            total_input_tokens: (map(.input_tokens // 0) | add),
            total_output_tokens: (map(.output_tokens // 0) | add),
            total_cache_creation_tokens: (map(.cache_creation_input_tokens // 0) | add),
            total_cache_read_tokens: (map(.cache_read_input_tokens // 0) | add),
            model: (map(.model // "claude-sonnet-4-5-20250929") | .[0])
        }
    ')

# Extract token counts
INPUT_TOKENS=$(echo "$USAGE_SUMMARY" | jq -r '.total_input_tokens // 0')
OUTPUT_TOKENS=$(echo "$USAGE_SUMMARY" | jq -r '.total_output_tokens // 0')
CACHE_CREATION_TOKENS=$(echo "$USAGE_SUMMARY" | jq -r '.total_cache_creation_tokens // 0')
CACHE_READ_TOKENS=$(echo "$USAGE_SUMMARY" | jq -r '.total_cache_read_tokens // 0')

# Determine model from transcript (default to Sonnet 4.5)
MODEL=$(grep -a '"model":' "$TRANSCRIPT_PATH" | head -1 | grep -oE 'claude-[a-z]+-[0-9]+-[0-9]+-[0-9]+' || echo "claude-sonnet-4-5-20250929")

# Load model pricing from models.json
MODELS_FILE="$PROJECT_ROOT/.claude/models/models.json"

if [ ! -f "$MODELS_FILE" ]; then
    echo "⚠️  models.json not found, using fallback pricing" >&2
    # Fallback to Sonnet 4.5 pricing
    INPUT_PRICE=3.00
    OUTPUT_PRICE=15.00
    CACHE_WRITE_PRICE=3.75
    CACHE_READ_PRICE=0.30
    MODEL_NAME="claude-sonnet-4.5"
else
    # Find matching model by checking patterns
    MODEL_KEY=""
    for key in $(jq -r '.models | keys[]' "$MODELS_FILE"); do
        PATTERN=$(jq -r ".models[\"$key\"].pattern" "$MODELS_FILE")
        # Split pattern on | and test each part separately
        IFS='|' read -ra PATTERNS <<< "$PATTERN"
        for pat in "${PATTERNS[@]}"; do
            case "$MODEL" in
                $pat)
                    MODEL_KEY="$key"
                    break 2  # Break out of both loops
                    ;;
            esac
        done
    done

    # If no match found, use default model
    if [ -z "$MODEL_KEY" ]; then
        MODEL_KEY=$(jq -r '.default_model' "$MODELS_FILE")
        echo "⚠️  Model '$MODEL' not found in models.json, using default: $MODEL_KEY" >&2
    fi

    # Extract pricing information
    MODEL_NAME=$(jq -r ".models[\"$MODEL_KEY\"].name" "$MODELS_FILE")
    INPUT_PRICE=$(jq -r ".models[\"$MODEL_KEY\"].pricing.input" "$MODELS_FILE")
    OUTPUT_PRICE=$(jq -r ".models[\"$MODEL_KEY\"].pricing.output" "$MODELS_FILE")
    CACHE_WRITE_PRICE=$(jq -r ".models[\"$MODEL_KEY\"].pricing.cache_write" "$MODELS_FILE")
    CACHE_READ_PRICE=$(jq -r ".models[\"$MODEL_KEY\"].pricing.cache_read" "$MODELS_FILE")
fi

# Calculate total cost
COST_USD=$(echo "scale=4; \
    ($INPUT_TOKENS * $INPUT_PRICE + \
     $OUTPUT_TOKENS * $OUTPUT_PRICE + \
     $CACHE_CREATION_TOKENS * $CACHE_WRITE_PRICE + \
     $CACHE_READ_TOKENS * $CACHE_READ_PRICE) / 1000000" | bc)

if [ "$COST_USD" != "0" ] && [ "$COST_USD" != "0.0000" ]; then
    # Store cost data in task metadata
    "$PROJECT_ROOT/.claude/scripts/cmat.sh" queue metadata "$TASK_ID" "cost_input_tokens" "$INPUT_TOKENS"
    "$PROJECT_ROOT/.claude/scripts/cmat.sh" queue metadata "$TASK_ID" "cost_output_tokens" "$OUTPUT_TOKENS"
    "$PROJECT_ROOT/.claude/scripts/cmat.sh" queue metadata "$TASK_ID" "cost_cache_creation_tokens" "$CACHE_CREATION_TOKENS"
    "$PROJECT_ROOT/.claude/scripts/cmat.sh" queue metadata "$TASK_ID" "cost_cache_read_tokens" "$CACHE_READ_TOKENS"
    "$PROJECT_ROOT/.claude/scripts/cmat.sh" queue metadata "$TASK_ID" "cost_usd" "$COST_USD"
    "$PROJECT_ROOT/.claude/scripts/cmat.sh" queue metadata "$TASK_ID" "cost_model" "$MODEL_NAME"
    "$PROJECT_ROOT/.claude/scripts/cmat.sh" queue metadata "$TASK_ID" "session_id" "$SESSION_ID"

    # Log to task log file if available
    if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
        {
            echo ""
            echo "╔════════════════════════════════════════════════════════════╗"
            echo "║                    COST INFORMATION                        ║"
            echo "╚════════════════════════════════════════════════════════════╝"
            echo ""
            printf "  Model:                 %s\n" "$MODEL_NAME"
            printf "  Input Tokens:          %'d\n" "$INPUT_TOKENS"
            printf "  Output Tokens:         %'d\n" "$OUTPUT_TOKENS"
            printf "  Cache Creation:        %'d tokens\n" "$CACHE_CREATION_TOKENS"
            printf "  Cache Read:            %'d tokens\n" "$CACHE_READ_TOKENS"
            printf "  Total Cost:            \$%.4f USD\n" "$COST_USD"
            echo ""
            printf "  Session ID:            %s\n" "$SESSION_ID"
            echo ""
            echo "════════════════════════════════════════════════════════════"
            echo ""
        } >> "$LOG_FILE"
    fi

    echo "✅ Cost captured successfully" >&2
    printf "   Input:          %'d tokens\n" "$INPUT_TOKENS" >&2
    printf "   Output:         %'d tokens\n" "$OUTPUT_TOKENS" >&2
    printf "   Cache Creation: %'d tokens\n" "$CACHE_CREATION_TOKENS" >&2
    printf "   Cache Read:     %'d tokens\n" "$CACHE_READ_TOKENS" >&2
    printf "   Total Cost:     \$%.4f USD\n" "$COST_USD" >&2
else
    echo "⚠️  No usage data found in transcript" >&2
fi

exit 0