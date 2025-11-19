#!/bin/bash

################################################################################
# on-subagent-stop.sh - Workflow-Driven Orchestration Hook
#
# Manages workflow transitions using workflow templates and task metadata
#
# Version: 5.0.0 - Simplified workflow-based orchestration
################################################################################

set -euo pipefail

# Debug: Log that hook was triggered
echo "[DEBUG] Hook triggered at $(date)" >> .claude/logs/hook_debug.log

# Initialize cmat command
CMAT=".claude/scripts/cmat.sh"

# Read the subagent output from stdin
SUBAGENT_OUTPUT=$(cat)

# Debug: Log what was received
echo "[DEBUG] Received input (first 500 chars):" >> .claude/logs/hook_debug.log
echo "$SUBAGENT_OUTPUT" | head -c 500 >> .claude/logs/hook_debug.log
echo "" >> .claude/logs/hook_debug.log

################################################################################
# Extract completion status from agent output
################################################################################

# Extract the status line (agent should output: "Status: SOME_STATUS" or just "SOME_STATUS")
SUBAGENT_STATUS=$(echo "$SUBAGENT_OUTPUT" | grep -oE "Status:[[:space:]]*[A-Z_:]+" | sed 's/Status:[[:space:]]*//' | head -1)

# If not found in that format, try to find common status patterns
if [ -z "$SUBAGENT_STATUS" ]; then
    SUBAGENT_STATUS=$(echo "$SUBAGENT_OUTPUT" | grep -oE "(READY_FOR_[A-Z_]+|[A-Z_]+_COMPLETE|BLOCKED:[^*]*|NEEDS_[A-Z_:]+|BASELINE_[A-Z_]+|INTEGRATION_[A-Z_]+)" | head -1)
fi

echo "=== AGENT WORKFLOW TRANSITION ==="
echo "Detected Status: ${SUBAGENT_STATUS:-UNKNOWN}"
echo

# If no status detected, cannot proceed
if [ -z "$SUBAGENT_STATUS" ]; then
    echo "⚠️  No status detected in agent output"
    echo "Agent must output a status code"
    exit 0
fi

################################################################################
# Process workflow transition
################################################################################

if [ -x "$CMAT" ]; then
    # Find the current task (check active first, then most recent completed)
    # When auto_complete=false, task is still active when hook runs
    # When auto_complete=true, task is already completed when hook runs
    CURRENT_TASK_ID=$(jq -r '.active_workflows[0].id' .claude/queues/task_queue.json 2>/dev/null)

    if [ -z "$CURRENT_TASK_ID" ] || [ "$CURRENT_TASK_ID" = "null" ]; then
        # Not in active, check most recently completed task
        CURRENT_TASK_ID=$(jq -r '.completed_tasks[-1].id' .claude/queues/task_queue.json 2>/dev/null)
        TASK=$(jq -r ".completed_tasks[] | select(.id == \"$CURRENT_TASK_ID\")" .claude/queues/task_queue.json)
    else
        # Found in active workflows
        TASK=$(jq -r ".active_workflows[] | select(.id == \"$CURRENT_TASK_ID\")" .claude/queues/task_queue.json)
    fi

    if [ -z "$CURRENT_TASK_ID" ] || [ "$CURRENT_TASK_ID" = "null" ]; then
        echo "⚠️  No active or recently completed task found"
        exit 0
    fi
    AGENT=$(echo "$TASK" | jq -r '.assigned_agent')
    SOURCE_FILE=$(echo "$TASK" | jq -r '.source_file')
    AUTO_CHAIN=$(echo "$TASK" | jq -r '.auto_chain // false')
    ENHANCEMENT_TITLE=$(echo "$TASK" | jq -r '.metadata.enhancement_title // ""')

    # Get workflow context from task metadata
    WORKFLOW_NAME=$(echo "$TASK" | jq -r '.metadata.workflow_name // ""')
    WORKFLOW_STEP=$(echo "$TASK" | jq -r '.metadata.workflow_step // ""')

    # Extract enhancement name
    ENHANCEMENT_NAME=$(echo "$SOURCE_FILE" | sed -E 's|^enhancements/([^/]+)/.*|\1|')
    ENHANCEMENT_DIR="enhancements/$ENHANCEMENT_NAME"

    echo "Agent: $AGENT"
    echo "Enhancement: $ENHANCEMENT_NAME"
    echo "Workflow: ${WORKFLOW_NAME:-none}"
    echo "Step: ${WORKFLOW_STEP:-none}"
    echo

    ########################################################################
    # Validate Agent Outputs
    ########################################################################

    if [ -n "$WORKFLOW_NAME" ] && [ -n "$WORKFLOW_STEP" ]; then
        # Load workflow template to get required output
        WORKFLOW=$(jq -r ".workflows[\"$WORKFLOW_NAME\"]" .claude/queues/workflow_templates.json 2>/dev/null)

        if [ -n "$WORKFLOW" ] && [ "$WORKFLOW" != "null" ]; then
            CURRENT_STEP=$(echo "$WORKFLOW" | jq -r ".steps[$WORKFLOW_STEP]")
            REQUIRED_OUTPUT=$(echo "$CURRENT_STEP" | jq -r '.required_output // ""')

            if [ -n "$REQUIRED_OUTPUT" ]; then
                echo "🔍 Validating outputs..."

                # Check required output exists
                REQUIRED_FILE="$ENHANCEMENT_DIR/$AGENT/required_output/$REQUIRED_OUTPUT"

                if [ ! -f "$REQUIRED_FILE" ]; then
                    echo "❌ Required output file missing: $REQUIRED_FILE"
                    "$CMAT" queue fail "$CURRENT_TASK_ID" "Output validation failed: $REQUIRED_OUTPUT not found"
                    exit 1
                fi

                # Check metadata header if agent requires it
                AGENT_DEF=$(jq -r ".agents[] | select(.[\"agent-file\"] == \"$AGENT\")" .claude/agents/agents.json)
                METADATA_REQUIRED=$(echo "$AGENT_DEF" | jq -r '.validations.metadata_required // true')

                if [ "$METADATA_REQUIRED" = "true" ]; then
                    if ! grep -q "^---$" "$REQUIRED_FILE"; then
                        echo "❌ Missing metadata header in: $REQUIRED_FILE"
                        "$CMAT" queue fail "$CURRENT_TASK_ID" "Output validation failed: Missing metadata header"
                        exit 1
                    fi
                fi

                echo "✅ Output validation passed"
            fi
        fi
    fi

    ########################################################################
    # Complete Current Task (if not already completed)
    ########################################################################

    # Check if task is still active (auto_complete=false) or already completed (auto_complete=true)
    TASK_STATUS=$(echo "$TASK" | jq -r '.status')

    if [ "$TASK_STATUS" = "active" ]; then
        "$CMAT" queue complete "$CURRENT_TASK_ID" "$SUBAGENT_STATUS"
        echo "✅ Task completed: $CURRENT_TASK_ID"
    else
        echo "ℹ️  Task already completed: $CURRENT_TASK_ID"
    fi

    ########################################################################
    # Check for Workflow Continuation
    ########################################################################

    # If no workflow context, stop here
    if [ -z "$WORKFLOW_NAME" ] || [ -z "$WORKFLOW_STEP" ]; then
        echo ""
        echo "ℹ️  Task not part of a workflow - no automatic next step"
        exit 0
    fi

    # Load workflow template
    WORKFLOW=$(jq -r ".workflows[\"$WORKFLOW_NAME\"]" .claude/queues/workflow_templates.json 2>/dev/null)

    if [ -z "$WORKFLOW" ] || [ "$WORKFLOW" = "null" ]; then
        echo "⚠️  Workflow template not found: $WORKFLOW_NAME"
        exit 0
    fi

    # Get current step definition
    CURRENT_STEP=$(echo "$WORKFLOW" | jq -r ".steps[$WORKFLOW_STEP]")

    # Check if status has a defined transition
    TRANSITION=$(echo "$CURRENT_STEP" | jq -r ".on_status[\"$SUBAGENT_STATUS\"] // null")

    if [ -z "$TRANSITION" ] || [ "$TRANSITION" = "null" ]; then
        echo ""
        echo "⚠️  Status '$SUBAGENT_STATUS' not defined in workflow"
        echo "Workflow stopped - no automatic next step"
        exit 0
    fi

    # Get next step configuration
    NEXT_STEP_NAME=$(echo "$TRANSITION" | jq -r '.next_step // null')
    STEP_AUTO_CHAIN=$(echo "$TRANSITION" | jq -r '.auto_chain // false')

    if [ -z "$NEXT_STEP_NAME" ] || [ "$NEXT_STEP_NAME" = "null" ]; then
        echo ""
        echo "✅ Workflow complete - no next step defined"
        exit 0
    fi

    ########################################################################
    # Auto-Chain to Next Step
    ########################################################################

    if [ "$STEP_AUTO_CHAIN" = "false" ] && [ "$AUTO_CHAIN" = "false" ]; then
        echo ""
        echo "ℹ️  Auto-chain disabled for this step"
        echo "Next step: $NEXT_STEP_NAME"
        echo ""
        echo "To continue manually, create a task for: $NEXT_STEP_NAME"
        exit 0
    fi

    echo ""
    echo "🔗 Auto-chaining to: $NEXT_STEP_NAME"

    # Get next step details
    NEXT_STEP_INDEX=$((WORKFLOW_STEP + 1))
    NEXT_STEP_DEF=$(echo "$WORKFLOW" | jq -r ".steps[$NEXT_STEP_INDEX]")

    if [ -z "$NEXT_STEP_DEF" ] || [ "$NEXT_STEP_DEF" = "null" ]; then
        echo "❌ Next step not found at index $NEXT_STEP_INDEX"
        exit 1
    fi

    NEXT_AGENT=$(echo "$NEXT_STEP_DEF" | jq -r '.agent')
    NEXT_INPUT=$(echo "$NEXT_STEP_DEF" | jq -r '.input')

    # Resolve input path placeholders
    NEXT_INPUT="${NEXT_INPUT//\{enhancement_name\}/$ENHANCEMENT_NAME}"
    NEXT_INPUT="${NEXT_INPUT//\{previous_step\}/$ENHANCEMENT_DIR/$AGENT}"

    # Verify input exists
    if [ ! -f "$NEXT_INPUT" ] && [ ! -d "$NEXT_INPUT" ]; then
        echo "❌ Next step input not found: $NEXT_INPUT"
        echo "Cannot proceed with auto-chain"
        exit 1
    fi

    # Determine task type based on agent role
    NEXT_AGENT_DEF=$(jq -r ".agents[] | select(.[\"agent-file\"] == \"$NEXT_AGENT\")" .claude/agents/agents.json)
    NEXT_AGENT_ROLE=$(echo "$NEXT_AGENT_DEF" | jq -r '.role // "unknown"')

    case "$NEXT_AGENT_ROLE" in
        "analysis") NEXT_TASK_TYPE="analysis" ;;
        "technical_design") NEXT_TASK_TYPE="technical_analysis" ;;
        "implementation") NEXT_TASK_TYPE="implementation" ;;
        "testing") NEXT_TASK_TYPE="testing" ;;
        "documentation") NEXT_TASK_TYPE="documentation" ;;
        "integration") NEXT_TASK_TYPE="integration" ;;
        *) NEXT_TASK_TYPE="analysis" ;;
    esac

    # Create next task
    NEW_TASK_ID=$("$CMAT" queue add \
        "Process $ENHANCEMENT_NAME with $NEXT_AGENT" \
        "$NEXT_AGENT" \
        "high" \
        "$NEXT_TASK_TYPE" \
        "$NEXT_INPUT" \
        "Continue workflow: $WORKFLOW_NAME (step $NEXT_STEP_INDEX)" \
        "true" \
        "true" \
        "$ENHANCEMENT_TITLE")

    if [ -z "$NEW_TASK_ID" ]; then
        echo "❌ Failed to create next task"
        exit 1
    fi

    # Add workflow metadata to new task
    "$CMAT" queue metadata "$NEW_TASK_ID" "workflow_name" "$WORKFLOW_NAME"
    "$CMAT" queue metadata "$NEW_TASK_ID" "workflow_step" "$NEXT_STEP_INDEX"

    echo "✅ Created next task: $NEW_TASK_ID"
    echo "   Agent: $NEXT_AGENT"
    echo "   Input: $NEXT_INPUT"
    echo "   Step: $NEXT_STEP_INDEX"

    # Start the new task
    echo ""
    echo "🚀 Starting next task..."
    "$CMAT" queue start "$NEW_TASK_ID"
fi

################################################################################
# Show current queue status
################################################################################

if [ -x "$CMAT" ]; then
    echo ""
    echo "📊 Current Queue Status:"
    "$CMAT" queue status
fi

echo ""
echo "==========================="