#!/usr/bin/env bash
################################################################################
# Script Name: integration-commands.sh
# Description: External system integration management
#              Handles synchronization with GitHub, Jira, and Confluence
#              through integration coordinator agents
# Author: Brian Gentry
# Created: 2025
# Version: 3.0.0
#
# Usage: cmat integration <command> [OPTIONS]
#
# Commands:
#   add <workflow_status> <source_file> <previous_agent> [parent_task_id]
#       Create integration task for external system sync
#   sync <task_id>
#       Synchronize specific completed task to external systems
#   sync-all
#       Synchronize all unsynced completed tasks
#
# Integration Triggers:
#   READY_FOR_DEVELOPMENT     → Create GitHub issue, Jira ticket
#   READY_FOR_IMPLEMENTATION  → Update status, add labels
#   READY_FOR_TESTING         → Create pull request
#   TESTING_COMPLETE          → Post test results
#   DOCUMENTATION_COMPLETE    → Close issue, publish docs
#
# Environment Variables:
#   AUTO_INTEGRATE            Control automatic integration (always|never|prompt)
#                            Default: prompt
#
# Dependencies:
#   - common-commands.sh (sourced)
#   - queue-commands.sh (called for task creation)
#   - Integration coordinator agents (github, atlassian)
#   - MCP servers (optional, for actual sync)
#
# Exit Codes:
#   0 - Success
#   1 - Task not found or sync error
################################################################################

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-commands.sh"

#############################################################################
# INTEGRATION OPERATIONS
#############################################################################

add_integration_task() {
    local workflow_status="$1"
    local source_file="$2"
    local previous_agent="$3"
    local parent_task_id="${4:-}"

    local title="Integrate: ${workflow_status}"
    local description="Synchronize workflow state '${workflow_status}' with external systems (GitHub, Jira, Confluence)"

    # Determine priority based on workflow status
    local priority="normal"
    case "$workflow_status" in
        "READY_FOR_DEVELOPMENT"|"READY_FOR_TESTING")
            priority="high"
            ;;
        "DOCUMENTATION_COMPLETE")
            priority="low"
            ;;
    esac

    # Create integration task
    local task_id
    task_id=$("$SCRIPT_DIR/queue-commands.sh" add \
        "$title" \
        "integration-coordinator" \
        "$priority" \
        "integration" \
        "$source_file" \
        "$description")

    # Update task metadata with workflow context
    local temp_file
    temp_file=$(mktemp)
    jq --arg id "$task_id" \
       --arg status "$workflow_status" \
       --arg prev "$previous_agent" \
       --arg parent "$parent_task_id" \
       '(.pending_tasks[] | select(.id == $id) | .metadata) += {
           workflow_status: $status,
           previous_agent: $prev,
           parent_task_id: $parent
       }' "$QUEUE_FILE" > "$temp_file"
    mv "$temp_file" "$QUEUE_FILE"

    echo "🔗 Integration task created: $task_id"
    return 0
}

sync_external() {
    local task_id="$1"

    local task
    task=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\")" "$QUEUE_FILE")

    if [ -z "$task" ]; then
        echo "❌ Task not found or not completed: $task_id"
        return 1
    fi

    local source_file result agent
    source_file=$(echo "$task" | jq -r '.source_file')
    result=$(echo "$task" | jq -r '.result')
    agent=$(echo "$task" | jq -r '.assigned_agent')

    echo "🔗 Creating integration task for: $task_id"
    add_integration_task "$result" "$source_file" "$agent" "$task_id"
}

sync_all() {
    echo "🔍 Scanning for tasks requiring integration..."

    local count=0
    local task_ids
    task_ids=$(jq -r '.completed_tasks[] | select(.result != null and .result != "completed successfully") | select(.metadata.github_issue == null) | .id' "$QUEUE_FILE")

    while IFS= read -r task_id; do
        if [ -n "$task_id" ] && needs_integration "$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .result" "$QUEUE_FILE")"; then
            local task result source_file agent
            task=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\")" "$QUEUE_FILE")
            result=$(echo "$task" | jq -r '.result')
            source_file=$(echo "$task" | jq -r '.source_file')
            agent=$(echo "$task" | jq -r '.assigned_agent')

            add_integration_task "$result" "$source_file" "$agent" "$task_id"
            ((count++))
        fi
    done <<< "$task_ids"

    echo "✅ Created $count integration tasks"
}

#############################################################################
# COMMAND ROUTER
#############################################################################

case "${1:-}" in
    "add")
        if [ $# -lt 4 ]; then
            echo "Usage: cmat integration add <workflow_status> <source_file> <previous_agent> [parent_task_id]"
            exit 1
        fi
        add_integration_task "$2" "$3" "$4" "${5:-}"
        ;;

    "sync")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat integration sync <task_id>"
            exit 1
        fi
        sync_external "$2"
        ;;

    "sync-all")
        sync_all
        ;;

    *)
        echo "Unknown integration command: ${1:-}" >&2
        echo "Usage: cmat integration <add|sync|sync-all>" >&2
        exit 1
        ;;
esac