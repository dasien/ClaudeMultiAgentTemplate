#!/bin/bash

################################################################################
# on-subagent-stop.sh - Enhanced Subagent Completion Hook
#
# Manages workflow transitions with contract-based validation and integration
#
# Version: 3.0.0 - Updated to use cmat command structure
################################################################################

set -euo pipefail

# Initialize cmat command
CMAT=".claude/scripts/cmat"

# Read the subagent output from stdin
SUBAGENT_OUTPUT=$(cat)

################################################################################
# Detect completion status from agent output
################################################################################

SUBAGENT_STATUS=""

# Check for all possible status codes
if echo "$SUBAGENT_OUTPUT" | grep -q "READY_FOR_DEVELOPMENT"; then
    SUBAGENT_STATUS="READY_FOR_DEVELOPMENT"
elif echo "$SUBAGENT_OUTPUT" | grep -q "READY_FOR_IMPLEMENTATION"; then
    SUBAGENT_STATUS="READY_FOR_IMPLEMENTATION"
elif echo "$SUBAGENT_OUTPUT" | grep -q "READY_FOR_TESTING"; then
    SUBAGENT_STATUS="READY_FOR_TESTING"
elif echo "$SUBAGENT_OUTPUT" | grep -q "READY_FOR_INTEGRATION"; then
    SUBAGENT_STATUS="READY_FOR_INTEGRATION"
elif echo "$SUBAGENT_OUTPUT" | grep -q "TESTING_COMPLETE"; then
    SUBAGENT_STATUS="TESTING_COMPLETE"
elif echo "$SUBAGENT_OUTPUT" | grep -q "DOCUMENTATION_COMPLETE"; then
    SUBAGENT_STATUS="DOCUMENTATION_COMPLETE"
elif echo "$SUBAGENT_OUTPUT" | grep -q "INTEGRATION_COMPLETE"; then
    SUBAGENT_STATUS="INTEGRATION_COMPLETE"
elif echo "$SUBAGENT_OUTPUT" | grep -q "INTEGRATION_FAILED"; then
    SUBAGENT_STATUS="INTEGRATION_FAILED"
elif echo "$SUBAGENT_OUTPUT" | grep -q "BLOCKED:"; then
    SUBAGENT_STATUS=$(echo "$SUBAGENT_OUTPUT" | grep -o "BLOCKED:.*" | head -1)
fi

echo "=== AGENT WORKFLOW TRANSITION ==="
echo "Detected Status: $SUBAGENT_STATUS"
echo

################################################################################
# Process workflow transition if status detected
################################################################################

if [ -n "$SUBAGENT_STATUS" ] && [ -x "$CMAT" ]; then
    # Find the current active task
    CURRENT_TASK_ID=$(jq -r '.active_workflows[0].id' .claude/queues/task_queue.json 2>/dev/null)

    if [ -n "$CURRENT_TASK_ID" ] && [ "$CURRENT_TASK_ID" != "null" ]; then
        # Get task details
        TASK=$(jq -r ".active_workflows[] | select(.id == \"$CURRENT_TASK_ID\")" .claude/queues/task_queue.json)
        AGENT=$(echo "$TASK" | jq -r '.assigned_agent')
        SOURCE_FILE=$(echo "$TASK" | jq -r '.source_file')
        AUTO_CHAIN=$(echo "$TASK" | jq -r '.auto_chain // false')

        # Extract enhancement name
        ENHANCEMENT_NAME=$(echo "$SOURCE_FILE" | sed -E 's|^enhancements/([^/]+)/.*|\1|')
        ENHANCEMENT_DIR="enhancements/$ENHANCEMENT_NAME"

        ########################################################################
        # Handle Integration Agent Completions Differently
        ########################################################################

        if [ "$AGENT" = "integration-coordinator" ] || \
           [ "$AGENT" = "github-integration-coordinator" ] || \
           [ "$AGENT" = "atlassian-integration-coordinator" ]; then

            if [ "$SUBAGENT_STATUS" = "INTEGRATION_COMPLETE" ]; then
                # Mark integration task complete
                "$CMAT" queue complete "$CURRENT_TASK_ID" "$SUBAGENT_STATUS"
                echo "✅ Integration task completed successfully"

                # Get integration details
                TASK_DETAILS=$(jq -r ".completed_tasks[-1] | select(.assigned_agent | contains(\"integration\"))" .claude/queues/task_queue.json 2>/dev/null)

                if [ -n "$TASK_DETAILS" ]; then
                    PARENT_TASK=$(echo "$TASK_DETAILS" | jq -r '.metadata.parent_task_id // empty')
                    WORKFLOW_STATUS=$(echo "$TASK_DETAILS" | jq -r '.metadata.workflow_status // empty')

                    if [ -n "$PARENT_TASK" ] && [ "$PARENT_TASK" != "null" ]; then
                        echo "📋 Integrated for workflow status: $WORKFLOW_STATUS"
                        echo "🔗 Parent task: $PARENT_TASK"
                    fi
                fi

                echo ""
                echo "Integration tasks update external systems:"
                echo "  • GitHub: Issues, PRs, labels"
                echo "  • Jira: Tickets, status updates"
                echo "  • Confluence: Documentation pages"

            elif [ "$SUBAGENT_STATUS" = "INTEGRATION_FAILED" ]; then
                # Mark integration task failed
                "$CMAT" queue fail "$CURRENT_TASK_ID" "$SUBAGENT_STATUS"
                echo "❌ Integration with external systems failed"
                echo ""
                echo "⚠️  Manual intervention required"
                echo ""
                echo "Check the integration log for details:"
                LOG_FILE=$(find enhancements/*/logs -name "*integration*coordinator_*" -type f 2>/dev/null | tail -1)
                if [ -n "$LOG_FILE" ]; then
                    echo "  Log: $LOG_FILE"
                    echo ""
                    echo "Common issues:"
                    echo "  • API rate limits exceeded"
                    echo "  • Authentication failures"
                    echo "  • Missing configuration"
                    echo ""
                    echo "To retry:"
                    echo "  cmat integration sync $CURRENT_TASK_ID"
                fi
            fi

        ########################################################################
        # Handle Regular Agent Completions (Requirements, Architect, etc.)
        ########################################################################

        else
            # Validate agent outputs using contract
            echo "🔍 Validating agent outputs..."

            if "$CMAT" workflow validate "$AGENT" "$ENHANCEMENT_DIR"; then
                # Validation passed - mark task complete
                "$CMAT" queue complete "$CURRENT_TASK_ID" "$SUBAGENT_STATUS"
                echo "📋 Task marked complete: $CURRENT_TASK_ID"

                ################################################################
                # Check if status indicates workflow continuation (not blocked)
                ################################################################

                if [[ ! "$SUBAGENT_STATUS" =~ ^BLOCKED ]]; then

                    ############################################################
                    # Integration Task Creation (GitHub/Jira/Confluence)
                    ############################################################

                    # Check if this status requires external integration
                    case "$SUBAGENT_STATUS" in
                        "READY_FOR_DEVELOPMENT"|"READY_FOR_IMPLEMENTATION"|"READY_FOR_TESTING"|"TESTING_COMPLETE"|"DOCUMENTATION_COMPLETE")
                            # Check AUTO_INTEGRATE environment variable
                            AUTO_INTEGRATE="${AUTO_INTEGRATE:-prompt}"
                            SHOULD_INTEGRATE="false"

                            case "$AUTO_INTEGRATE" in
                                "always")
                                    SHOULD_INTEGRATE="true"
                                    echo ""
                                    echo "🔗 Auto-integration enabled (always mode)"
                                    ;;
                                "never")
                                    SHOULD_INTEGRATE="false"
                                    echo ""
                                    echo "ℹ️  Auto-integration disabled (never mode)"
                                    ;;
                                *)
                                    echo ""
                                    echo "🔗 This status may require integration with external systems:"
                                    echo "   Status: $SUBAGENT_STATUS"
                                    echo "   This would create GitHub issues, Jira tickets, or update documentation."
                                    echo ""
                                    echo -n "Create integration task? [y/N]: "
                                    read -r response
                                    if [[ "$response" =~ ^[Yy]$ ]]; then
                                        SHOULD_INTEGRATE="true"
                                    fi
                                    ;;
                            esac

                            if [ "$SHOULD_INTEGRATE" = "true" ]; then
                                "$CMAT" integration add \
                                    "$SUBAGENT_STATUS" \
                                    "$SOURCE_FILE" \
                                    "$AGENT" \
                                    "$CURRENT_TASK_ID"
                                echo "🔗 Integration task created"
                            fi
                            ;;
                    esac

                    ############################################################
                    # Auto-Chain to Next Agent (Contract-Based)
                    ############################################################

                    # Determine next agent from contract
                    NEXT_AGENT=$("$CMAT" workflow next-agent "$AGENT" "$SUBAGENT_STATUS" 2>/dev/null || echo "UNKNOWN")

                    if [ "$NEXT_AGENT" != "UNKNOWN" ] && [ -n "$NEXT_AGENT" ]; then
                        # Check if auto-chain is enabled
                        if [ "$AUTO_CHAIN" = "true" ]; then
                            echo ""
                            echo "🔗 Auto-chaining enabled..."
                            "$CMAT" workflow auto-chain "$CURRENT_TASK_ID" "$SUBAGENT_STATUS"
                        else
                            # Prompt for manual chain
                            echo ""
                            echo "🔗 Next Agent Suggestion:"
                            echo "   Agent: $NEXT_AGENT"

                            # Build next source path
                            NEXT_SOURCE=$("$CMAT" workflow next-source "$ENHANCEMENT_NAME" "$NEXT_AGENT" "$AGENT")
                            echo "   Source: $NEXT_SOURCE"
                            echo ""
                            echo -n "Create next task? [y/N]: "
                            read -r response
                            if [[ "$response" =~ ^[Yy]$ ]]; then
                                "$CMAT" workflow auto-chain "$CURRENT_TASK_ID" "$SUBAGENT_STATUS"
                            fi
                        fi
                    else
                        # No next agent - workflow complete or needs manual decision
                        echo ""
                        echo "✅ Workflow phase complete"

                        case "$SUBAGENT_STATUS" in
                            "DOCUMENTATION_COMPLETE")
                                echo "🎉 Enhancement fully complete!"
                                echo "   All phases finished: Requirements → Architecture → Implementation → Testing → Documentation"
                                ;;
                            "TESTING_COMPLETE")
                                echo "📚 Optional: Create documentation"
                                echo ""
                                echo -n "Queue documentation task? [y/N]: "
                                read -r doc_response
                                if [[ "$doc_response" =~ ^[Yy]$ ]]; then
                                    DOC_SOURCE=$("$CMAT" workflow next-source "$ENHANCEMENT_NAME" "documenter" "$AGENT")
                                    DOC_TASK_ID=$("$CMAT" queue add \
                                        "Create documentation for $ENHANCEMENT_NAME" \
                                        "documenter" \
                                        "normal" \
                                        "documentation" \
                                        "$DOC_SOURCE" \
                                        "Document feature for users and developers" \
                                        "false" \
                                        "false")
                                    echo "📚 Documentation task queued: $DOC_TASK_ID"
                                else
                                    echo "Skipping documentation - feature complete"
                                fi
                                ;;
                            *)
                                echo "   No automatic next step - manual review may be needed"
                                ;;
                        esac
                    fi

                else
                    # Workflow blocked
                    echo ""
                    echo "⚠️  Task blocked: $SUBAGENT_STATUS"
                    echo "   Manual intervention required to proceed"
                fi

            else
                # Validation failed
                echo "❌ Agent output validation failed"
                echo "Task marked as BLOCKED - manual review required"
                "$CMAT" queue fail "$CURRENT_TASK_ID" "Output validation failed: Required outputs missing"

                echo ""
                echo "Common issues:"
                echo "  • Root document not created in correct location"
                echo "  • Missing required metadata header"
                echo "  • Files created in wrong directory"
                echo ""
                echo "Expected output structure:"
                echo "  $ENHANCEMENT_DIR/$AGENT/<root_document>"
            fi
        fi
    fi
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
echo "=== SUBAGENT OUTPUT ==="
echo "$SUBAGENT_OUTPUT"
echo "========================="