#!/usr/bin/env bash
################################################################################
# Script Name: workflow-commands.sh
# Description: Workflow orchestration and contract-based validation
#              Manages agent contracts, output validation, workflow chaining,
#              and determines workflow transitions based on agent contracts
# Author: Brian Gentry
# Created: 2025
# Version: 3.0.0
#
# Usage: cmat workflow <command> [OPTIONS]
#
# Commands:
#   validate <agent> <enhancement_dir>
#       Validate agent outputs against contract requirements
#   next-agent <agent> <status>
#       Determine next agent based on current agent and status code
#   next-source <enhancement> <next_agent> <current_agent>
#       Build source file path for next agent in workflow
#   auto-chain <task_id> <status>
#       Automatically create and start next workflow task
#   template <template_name> [description]
#       Execute predefined workflow template
#
# Contract Validation:
#   - Checks required output files exist
#   - Validates metadata headers (5 required fields)
#   - Verifies output directory structure
#   - Confirms additional required files present
#
# Status Codes:
#   READY_FOR_DEVELOPMENT, READY_FOR_IMPLEMENTATION, READY_FOR_TESTING,
#   TESTING_COMPLETE, DOCUMENTATION_COMPLETE, INTEGRATION_COMPLETE,
#   BLOCKED: <reason>
#
# Dependencies:
#   - common-commands.sh (sourced)
#   - queue-commands.sh (called for task operations)
#   - AGENT_CONTRACTS.json (contract definitions)
#   - jq (JSON processor)
#
# Exit Codes:
#   0 - Success or validation passed
#   1 - Validation failed or agent not found
################################################################################

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-commands.sh"

#############################################################################
# CONTRACT OPERATIONS
#############################################################################

get_agent_contract() {
    local agent="$1"

    if [ ! -f "$CONTRACTS_FILE" ]; then
        echo "Error: Agent contracts file not found: $CONTRACTS_FILE" >&2
        return 1
    fi

    local contract
    contract=$(jq -r ".agents[\"$agent\"]" "$CONTRACTS_FILE" 2>/dev/null)

    if [ "$contract" = "null" ] || [ -z "$contract" ]; then
        echo "Error: Agent not found in contracts: $agent" >&2
        return 1
    fi

    echo "$contract"
    return 0
}

validate_agent_outputs() {
    local agent="$1"
    local enhancement_dir="$2"

    local contract
    contract=$(get_agent_contract "$agent")
    if [ $? -ne 0 ]; then
        return 1
    fi

    local output_dir root_doc
    output_dir=$(echo "$contract" | jq -r '.outputs.output_directory')
    root_doc=$(echo "$contract" | jq -r '.outputs.root_document')

    # Check root document (critical for workflow handoff)
    local root_path="$enhancement_dir/$output_dir/$root_doc"
    if [ ! -f "$root_path" ]; then
        echo "❌ Required root document missing: $root_path"
        return 1
    fi

    # Check additional required files
    local additional_files
    additional_files=$(echo "$contract" | jq -r '.outputs.additional_required[]' 2>/dev/null)
    if [ -n "$additional_files" ]; then
        while IFS= read -r file; do
            if [ -n "$file" ]; then
                local file_path="$enhancement_dir/$output_dir/$file"
                if [ ! -f "$file_path" ]; then
                    echo "❌ Required file missing: $file_path"
                    return 1
                fi
            fi
        done <<< "$additional_files"
    fi

    # Validate metadata header if required
    if [ "$(echo "$contract" | jq -r '.metadata_required')" = "true" ]; then
        if ! grep -q "^---$" "$root_path"; then
            echo "❌ Missing required metadata header in $root_path"
            return 1
        fi

        # Check for required fields
        local missing_fields=()

        if ! grep -q "^enhancement:" "$root_path"; then
            missing_fields+=("enhancement")
        fi

        if ! grep -q "^agent:" "$root_path"; then
            missing_fields+=("agent")
        fi

        if ! grep -q "^task_id:" "$root_path"; then
            missing_fields+=("task_id")
        fi

        if ! grep -q "^timestamp:" "$root_path"; then
            missing_fields+=("timestamp")
        fi

        if ! grep -q "^status:" "$root_path"; then
            missing_fields+=("status")
        fi

        if [ ${#missing_fields[@]} -gt 0 ]; then
            echo "❌ Metadata missing required fields in $root_path: ${missing_fields[*]}"
            return 1
        fi
    fi

    echo "✅ Output validation passed: $root_path"
    return 0
}

determine_next_agent() {
    local current_agent="$1"
    local status="$2"

    local contract
    contract=$(get_agent_contract "$current_agent")
    if [ $? -ne 0 ]; then
        echo "UNKNOWN"
        return 1
    fi

    # Check success statuses
    local next_agents
    next_agents=$(echo "$contract" | \
        jq -r ".statuses.success[] | select(.code == \"$status\") | .next_agents[]" 2>/dev/null)

    if [ -n "$next_agents" ]; then
        echo "$next_agents" | head -1
        return 0
    fi

    echo "UNKNOWN"
    return 1
}

build_next_source() {
    local enhancement_name="$1"
    local next_agent="$2"
    local current_agent="$3"

    local current_contract
    current_contract=$(get_agent_contract "$current_agent")
    if [ $? -ne 0 ]; then
        return 1
    fi

    local output_dir root_doc
    output_dir=$(echo "$current_contract" | jq -r '.outputs.output_directory')
    root_doc=$(echo "$current_contract" | jq -r '.outputs.root_document')

    echo "enhancements/$enhancement_name/$output_dir/$root_doc"
    return 0
}

get_task_type_for_agent() {
    local agent="$1"

    local contract
    contract=$(get_agent_contract "$agent")
    if [ $? -ne 0 ]; then
        echo "unknown"
        return 0
    fi

    local role
    role=$(echo "$contract" | jq -r '.role')

    case "$role" in
        "analysis") echo "analysis" ;;
        "technical_design") echo "technical_analysis" ;;
        "implementation") echo "implementation" ;;
        "testing") echo "testing" ;;
        "documentation") echo "documentation" ;;
        "integration") echo "integration" ;;
        *) echo "unknown" ;;
    esac

    return 0
}

auto_chain() {
    local task_id="$1"
    local status="$2"

    # Get task details
    local task
    task=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\")" "$QUEUE_FILE")

    if [ -z "$task" ] || [ "$task" = "null" ]; then
        echo "❌ Task not found in completed tasks: $task_id"
        return 1
    fi

    local agent source_file parent_auto_complete parent_auto_chain
    agent=$(echo "$task" | jq -r '.assigned_agent')
    source_file=$(echo "$task" | jq -r '.source_file')
    parent_auto_complete=$(echo "$task" | jq -r '.auto_complete // false')
    parent_auto_chain=$(echo "$task" | jq -r '.auto_chain // false')

    # Extract enhancement name
    local enhancement_name enhancement_dir
    enhancement_name=$(extract_enhancement_name "$source_file")
    enhancement_dir="enhancements/$enhancement_name"

    # Validate current agent outputs
    echo "🔍 Validating outputs from $agent..."
    if ! validate_agent_outputs "$agent" "$enhancement_dir"; then
        echo "❌ Cannot chain: Required outputs missing"
        return 1
    fi

    # Determine next agent
    local next_agent
    next_agent=$(determine_next_agent "$agent" "$status")

    if [ "$next_agent" = "UNKNOWN" ]; then
        echo "ℹ️  No automatic next agent for status: $status"
        return 0
    fi

    # Build next source file path
    local next_source
    next_source=$(build_next_source "$enhancement_name" "$next_agent" "$agent")

    # Verify next source exists
    if [ ! -f "$next_source" ]; then
        echo "❌ Cannot chain: Next source file missing: $next_source"
        return 1
    fi

    # Build next task details
    local next_title next_desc task_type
    next_title="Process $enhancement_name with $next_agent"
    next_desc="Continue workflow for $enhancement_name following $agent completion"
    task_type=$(get_task_type_for_agent "$next_agent")

    # Create next task - inherit automation settings
    local new_task_id
    new_task_id=$("$SCRIPT_DIR/queue-commands.sh" add \
        "$next_title" \
        "$next_agent" \
        "high" \
        "$task_type" \
        "$next_source" \
        "$next_desc" \
        "$parent_auto_complete" \
        "$parent_auto_chain")

    echo "✅ Auto-chained to $next_agent: $new_task_id"
    echo "   Source: $next_source"
    echo "   Inherited automation: auto_complete=$parent_auto_complete, auto_chain=$parent_auto_chain"
    echo ""
    echo "🚀 Auto-starting next task..."

    # Auto-start the task
    "$SCRIPT_DIR/queue-commands.sh" start "$new_task_id"

    return $?
}

run_workflow_template() {
    local workflow_name="$1"
    local task_description="${2:-Workflow execution}"

    local templates_file="$PROJECT_ROOT/.claude/queues/workflow_templates.json"

    local workflow_exists
    workflow_exists=$(jq -r ".workflow_chains | has(\"$workflow_name\")" "$QUEUE_FILE")
    if [ "$workflow_exists" != "true" ]; then
        echo "Error: Workflow '$workflow_name' not found"
        return 1
    fi

    echo "Starting workflow: $workflow_name"

    # Get first step(s) of workflow
    local first_step
    first_step=$(jq -r ".workflow_chains[\"$workflow_name\"].steps[0]" "$QUEUE_FILE")

    if [[ $first_step == \[* ]]; then
        # Parallel execution
        echo "Parallel execution detected"
        jq -r ".workflow_chains[\"$workflow_name\"].steps[0][]" "$QUEUE_FILE" | while read -r agent; do
            "$SCRIPT_DIR/queue-commands.sh" add "Workflow: $workflow_name" "$agent" "high" "" "" "$task_description"
        done
    else
        # Sequential execution
        "$SCRIPT_DIR/queue-commands.sh" add "Workflow: $workflow_name" "$first_step" "high" "" "" "$task_description"
    fi
}

#############################################################################
# COMMAND ROUTER
#############################################################################

case "${1:-}" in
    "validate")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow validate <agent> <enhancement_dir>"
            exit 1
        fi
        validate_agent_outputs "$2" "$3"
        ;;

    "next-agent")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow next-agent <agent> <status>"
            exit 1
        fi
        determine_next_agent "$2" "$3"
        ;;

    "next-source")
        if [ $# -lt 4 ]; then
            echo "Usage: cmat workflow next-source <enhancement> <next_agent> <current_agent>"
            exit 1
        fi
        build_next_source "$2" "$3" "$4"
        ;;

    "auto-chain")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow auto-chain <task_id> <status>"
            exit 1
        fi
        auto_chain "$2" "$3"
        ;;

    "template")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat workflow template <template_name> [description]"
            exit 1
        fi
        run_workflow_template "$2" "${3:-Workflow execution}"
        ;;
    "get-contract")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat workflow get-contract <agent>"
            exit 1
        fi
        get_agent_contract "$2"
        ;;

    *)
        echo "Unknown workflow command: ${1:-}" >&2
        echo "Usage: cmat workflow <validate|next-agent|next-source|auto-chain|template>" >&2
        exit 1
        ;;
esac