#!/bin/bash

# Enhanced hook with queue system integration
# Manages workflow transitions and updates task queues

set -euo pipefail

# Initialize queue manager
QUEUE_MANAGER=".claude/queues/queue_manager.sh"

# Read the subagent output from stdin
SUBAGENT_OUTPUT=$(cat)

# Parse subagent name and status from the output
SUBAGENT_NAME=""
SUBAGENT_STATUS=""

# Extract agent information from output
if echo "$SUBAGENT_OUTPUT" | grep -q "READY_FOR_DEVELOPMENT"; then
    SUBAGENT_NAME="requirements-analyst"
    SUBAGENT_STATUS="READY_FOR_DEVELOPMENT"
elif echo "$SUBAGENT_OUTPUT" | grep -q "READY_FOR_TESTING"; then
    SUBAGENT_NAME="cpp-developer"
    SUBAGENT_STATUS="READY_FOR_TESTING"
elif echo "$SUBAGENT_OUTPUT" | grep -q "READY_FOR_INTEGRATION"; then
    SUBAGENT_NAME="assembly-developer"
    SUBAGENT_STATUS="READY_FOR_INTEGRATION"
elif echo "$SUBAGENT_OUTPUT" | grep -q "TESTING_COMPLETE"; then
    SUBAGENT_NAME="testing-agent"
    SUBAGENT_STATUS="TESTING_COMPLETE"
fi

echo "=== AGENT WORKFLOW TRANSITION ==="
echo "Completed Agent: $SUBAGENT_NAME"
echo "Status: $SUBAGENT_STATUS"
echo

# Update queue system if agent and status detected
if [ -n "$SUBAGENT_NAME" ] && [ -n "$SUBAGENT_STATUS" ] && [ -x "$QUEUE_MANAGER" ]; then
    # Find and complete the current task for this agent
    CURRENT_TASK_ID=$(jq -r ".active_workflows[] | select(.assigned_agent == \"$SUBAGENT_NAME\") | .id" .claude/queues/task_queue.json 2>/dev/null | head -n 1)

    if [ -n "$CURRENT_TASK_ID" ] && [ "$CURRENT_TASK_ID" != "null" ]; then
        "$QUEUE_MANAGER" complete "$CURRENT_TASK_ID" "$SUBAGENT_STATUS"
        echo "📋 Updated task queue: Completed task $CURRENT_TASK_ID"
    fi
fi

# Determine next steps and queue follow-up tasks
case "$SUBAGENT_STATUS" in
    "READY_FOR_DEVELOPMENT")
        echo "✅ Requirements analysis complete"
        echo "📋 Next: Choose development track (C++ or Assembly)"
        echo
        echo "🚀 Auto-queuing next tasks:"
        if [ -x "$QUEUE_MANAGER" ]; then
            CPP_TASK_ID=$("$QUEUE_MANAGER" add "Implement C++ development tools" "cpp-developer" "high" "Build emulation and testing tools based on requirements")
            ASM_TASK_ID=$("$QUEUE_MANAGER" add "Implement 6502 assembly kernel" "assembly-developer" "high" "Build kernel and monitor programs based on requirements")
            echo "  • C++ Development Task: $CPP_TASK_ID"
            echo "  • Assembly Development Task: $ASM_TASK_ID"
            echo
            echo "Suggested workflows:"
            echo "  • Sequential: .claude/queues/queue_manager.sh start cpp-developer"
            echo "  • Parallel: Start both agents simultaneously"
        else
            echo "Suggested next steps:"
            echo "  • For C++ development tools: Use 'cpp-developer' agent"
            echo "  • For 6502 assembly kernel: Use 'assembly-developer' agent"
        fi
        ;;

    "READY_FOR_TESTING")
        echo "✅ C++ implementation complete"
        echo "🧪 Next: Run comprehensive testing"
        echo
        if [ -x "$QUEUE_MANAGER" ]; then
            TEST_TASK_ID=$("$QUEUE_MANAGER" add "Test C++ components" "testing-agent" "high" "Unit and integration tests for C++ development tools")
            echo "🚀 Auto-queued testing task: $TEST_TASK_ID"
            echo "  Start with: .claude/queues/queue_manager.sh start testing-agent"
        else
            echo "Suggested next steps:"
            echo "  • Use 'testing-agent' for automated testing"
        fi
        ;;

    "READY_FOR_INTEGRATION")
        echo "✅ Assembly implementation complete"
        echo "🔗 Next: Integration and final testing"
        echo
        if [ -x "$QUEUE_MANAGER" ]; then
            INTEGRATION_TASK_ID=$("$QUEUE_MANAGER" add "Integration testing" "testing-agent" "critical" "Test assembly-C++ integration and hardware validation")
            echo "🚀 Auto-queued integration task: $INTEGRATION_TASK_ID"
            echo "  Start with: .claude/queues/queue_manager.sh start testing-agent"
        else
            echo "Suggested next steps:"
            echo "  • Use 'testing-agent' for hardware validation"
        fi
        ;;

    "TESTING_COMPLETE")
        echo "✅ All testing complete"
        echo "🎉 Ready for deployment/release"
        echo
        echo "Project Status: READY_FOR_RELEASE"
        if [ -x "$QUEUE_MANAGER" ]; then
            echo "📊 Final Queue Status:"
            "$QUEUE_MANAGER" status
        fi
        ;;

    *)
        echo "⚠️  Unknown status from subagent"
        echo "Manual intervention may be required"
        ;;
esac

# Show current queue status
if [ -x "$QUEUE_MANAGER" ]; then
    echo
    echo "📊 Current Queue Status:"
    "$QUEUE_MANAGER" status
fi

echo
echo "=== SUBAGENT OUTPUT ==="
echo "$SUBAGENT_OUTPUT"
echo "========================="