#!/usr/bin/env bash
################################################################################
# Script Name: queue-commands.sh
# Description: Task queue lifecycle management
#              Handles task creation, execution, completion, cancellation,
#              status tracking, and metadata updates
# Author: Brian Gentry
# Created: 2025
# Version: 3.0.0
#
# Usage: cmat queue <command> [OPTIONS]
#
# Commands:
#   add <title> <agent> <priority> <type> <source> <desc> [auto_complete] [auto_chain]
#       Add a new task to the pending queue
#   start <task_id>
#       Move task from pending to active and invoke agent
#   complete <task_id> [result] [--auto-chain]
#       Mark active task as completed
#   fail <task_id> [error]
#       Mark active task as failed
#   cancel <task_id> [reason]
#       Cancel pending or active task
#   cancel-all [reason]
#       Cancel all pending and active tasks
#   status
#       Display current queue status and task counts
#   list <queue_type> [format]
#       List tasks (types: pending, active, completed, failed, all)
#   metadata <task_id> <key> <value>
#       Update task metadata field
#
# Task Priorities:
#   critical, high, normal, low
#
# Task Types:
#   analysis, technical_analysis, implementation, testing, documentation, integration
#
# Dependencies:
#   - common-commands.sh (sourced)
#   - agent-commands.sh (called for task execution)
#   - workflow-commands.sh (called for auto-chaining)
#   - jq (JSON processor)
#
# Exit Codes:
#   0 - Success
#   1 - Task not found or validation error
################################################################################

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-commands.sh"

#############################################################################
# QUEUE OPERATIONS
#############################################################################

add_task() {
    local task_title="$1"
    local agent="$2"
    local priority="${3:-normal}"
    local task_type="${4:-}"
    local source_file="${5:-}"
    local description="${6:-No description}"
    local auto_complete="${7:-false}"
    local auto_chain="${8:-false}"

    local task_id
    task_id="task_$(date +%s)_$$"
    local timestamp
    timestamp=$(get_timestamp)

    local task_object
    task_object=$(jq -n \
        --arg id "$task_id" \
        --arg title "$task_title" \
        --arg agent "$agent" \
        --arg priority "$priority" \
        --arg task_type "$task_type" \
        --arg description "$description" \
        --arg source_file "$source_file" \
        --arg created "$timestamp" \
        --arg status "pending" \
        --arg auto_complete "$auto_complete" \
        --arg auto_chain "$auto_chain" \
        '{
            id: $id,
            title: $title,
            assigned_agent: $agent,
            priority: $priority,
            task_type: $task_type,
            description: $description,
            source_file: $source_file,
            created: $created,
            status: $status,
            started: null,
            completed: null,
            result: null,
            auto_complete: ($auto_complete == "true"),
            auto_chain: ($auto_chain == "true"),
            metadata: {
                github_issue: null,
                jira_ticket: null,
                github_pr: null,
                confluence_page: null,
                parent_task_id: null,
                workflow_status: null
            }
        }')

    local temp_file
    temp_file=$(mktemp)
    jq ".pending_tasks += [$task_object]" "$QUEUE_FILE" > "$temp_file"
    mv "$temp_file" "$QUEUE_FILE"

    log_operation "TASK_ADDED" "ID: $task_id, Agent: $agent, Title: $task_title"
    echo "$task_id"
}

start_task() {
    local task_id="$1"
    local timestamp
    timestamp=$(get_timestamp)

    # Check if task exists in pending queue
    local task_exists
    task_exists=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")

    if [ -z "$task_exists" ]; then
        echo "Task $task_id not found in pending queue"
        return 1
    fi

    # Extract task information
    local task_title agent task_type task_description source_file auto_complete auto_chain
    task_title=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    task_type=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .task_type" "$QUEUE_FILE")
    task_description=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .description" "$QUEUE_FILE")
    agent=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")
    source_file=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .source_file" "$QUEUE_FILE")
    auto_complete=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .auto_complete // false" "$QUEUE_FILE")
    auto_chain=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .auto_chain // false" "$QUEUE_FILE")

    echo "Task auto_complete: $auto_complete"
    echo "Task auto_chain: $auto_chain"

    # Validate source file
    if [ -z "$source_file" ] || [ "$source_file" = "null" ]; then
        echo "Error: No source file specified for task $task_id"
        return 1
    fi

    if [ ! -f "$source_file" ]; then
        echo "Error: Source file not found: $source_file"
        return 1
    fi

    local temp_file
    temp_file=$(mktemp)

    # Move task from pending to active
    jq "(.pending_tasks[] | select(.id == \"$task_id\")) |= (.status = \"active\" | .started = \"$timestamp\") |
        .active_workflows += [.pending_tasks[] | select(.id == \"$task_id\")] |
        .pending_tasks = [.pending_tasks[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"

    update_agent_status "$agent" "active" "\"$task_id\""
    log_operation "TASK_STARTED" "ID: $task_id, Agent: $agent, Source: $source_file"

    echo "$task_id"

    # Invoke the agent - delegate to agent-commands
    local enhancement_name
    enhancement_name=$(extract_enhancement_name "$source_file")
    local log_base_dir="enhancements/$enhancement_name"

    "$SCRIPT_DIR/agent-commands.sh" invoke "$agent" "$task_id" "$source_file" "$log_base_dir" "$task_type" "$task_description" "$auto_complete" "$auto_chain"
}

complete_task() {
    local task_id="$1"
    local result="${2:-completed successfully}"
    local auto_chain="${3:-false}"
    local timestamp
    timestamp=$(get_timestamp)

    local temp_file
    temp_file=$(mktemp)

    # Move task from active to completed
    jq "(.active_workflows[] | select(.id == \"$task_id\")) |= (.status = \"completed\" | .completed = \"$timestamp\" | .result = \"$result\") |
        .completed_tasks += [.active_workflows[] | select(.id == \"$task_id\")] |
        .active_workflows = [.active_workflows[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"

    # Update agent status to idle
    local agent
    agent=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")
    if [ -n "$agent" ] && [ "$agent" != "null" ]; then
        update_agent_status "$agent" "idle" "null"
    fi

    log_operation "TASK_COMPLETED" "ID: $task_id, Agent: $agent, Result: $result"

    # Handle auto-chaining if enabled
    if [ "$auto_chain" = "true" ]; then
        "$SCRIPT_DIR/workflow-commands.sh" auto-chain "$task_id" "$result"
    fi
}

fail_task() {
    local task_id="$1"
    local error="${2:-task failed}"
    local timestamp
    timestamp=$(get_timestamp)

    local temp_file
    temp_file=$(mktemp)

    # Move task from active to failed
    jq "(.active_workflows[] | select(.id == \"$task_id\")) |= (.status = \"failed\" | .completed = \"$timestamp\" | .result = \"$error\") |
        .failed_tasks += [.active_workflows[] | select(.id == \"$task_id\")] |
        .active_workflows = [.active_workflows[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"

    # Update agent status to idle
    local agent
    agent=$(jq -r ".failed_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")
    if [ -n "$agent" ] && [ "$agent" != "null" ]; then
        update_agent_status "$agent" "idle" "null"
    fi

    log_operation "TASK_FAILED" "ID: $task_id, Agent: $agent, Error: $error"
}

cancel_task() {
    local task_id="$1"
    local reason="${2:-task cancelled}"

    local temp_file
    temp_file=$(mktemp)

    # Check if task is in pending_tasks
    local in_pending
    in_pending=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    if [ -n "$in_pending" ]; then
        jq ".pending_tasks = [.pending_tasks[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"
        mv "$temp_file" "$QUEUE_FILE"
        log_operation "TASK_CANCELLED" "ID: $task_id, Status: pending, Reason: $reason"
        echo "Cancelled pending task: $task_id"
        return
    fi

    # Check if task is in active_workflows
    local in_active
    in_active=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    if [ -n "$in_active" ]; then
        local agent
        agent=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")

        jq ".active_workflows = [.active_workflows[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"
        mv "$temp_file" "$QUEUE_FILE"

        if [ -n "$agent" ] && [ "$agent" != "null" ]; then
            update_agent_status "$agent" "idle" "null"
        fi

        log_operation "TASK_CANCELLED" "ID: $task_id, Status: active, Agent: $agent, Reason: $reason"
        echo "Cancelled active task: $task_id (agent $agent set to idle)"
        return
    fi

    echo "Task $task_id not found in pending or active queues"
    return 1
}

cancel_all_tasks() {
    local reason="${1:-bulk cancellation}"
    echo "Cancelling all pending and active tasks..."

    # Cancel all pending tasks
    local pending_tasks pending_count=0
    pending_tasks=$(jq -r '.pending_tasks[].id' "$QUEUE_FILE")
    for task_id in $pending_tasks; do
        if [ -n "$task_id" ]; then
            cancel_task "$task_id" "$reason"
            ((pending_count++))
        fi
    done

    # Cancel all active tasks
    local active_tasks active_count=0
    active_tasks=$(jq -r '.active_workflows[].id' "$QUEUE_FILE")
    for task_id in $active_tasks; do
        if [ -n "$task_id" ]; then
            cancel_task "$task_id" "$reason"
            ((active_count++))
        fi
    done

    echo "✅ Cancelled $pending_count pending and $active_count active tasks"
}

update_metadata() {
    local task_id="$1"
    local key="$2"
    local value="$3"

    local temp_file
    temp_file=$(mktemp)

    # Check which queue the task is in
    local in_pending in_active in_completed
    in_pending=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    in_active=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    in_completed=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")

    if [ -n "$in_pending" ]; then
        jq --arg id "$task_id" \
           --arg k "$key" \
           --arg v "$value" \
           '(.pending_tasks[] | select(.id == $id) | .metadata[$k]) = $v' "$QUEUE_FILE" > "$temp_file"
    elif [ -n "$in_active" ]; then
        jq --arg id "$task_id" \
           --arg k "$key" \
           --arg v "$value" \
           '(.active_workflows[] | select(.id == $id) | .metadata[$k]) = $v' "$QUEUE_FILE" > "$temp_file"
    elif [ -n "$in_completed" ]; then
        jq --arg id "$task_id" \
           --arg k "$key" \
           --arg v "$value" \
           '(.completed_tasks[] | select(.id == $id) | .metadata[$k]) = $v' "$QUEUE_FILE" > "$temp_file"
    else
        echo "❌ Task not found: $task_id"
        return 1
    fi

    mv "$temp_file" "$QUEUE_FILE"
    log_operation "METADATA_UPDATE" "Task: $task_id, Key: $key, Value: $value"
    echo "✅ Updated metadata for $task_id: $key = $value"
}

show_status() {
    echo "=== Multi-Agent Queue Status ==="
    echo

    echo "📋 Agent Status:"
    jq -r '.agent_status | to_entries[] | "  • \(.key): \(.value.status) (Last: \(.value.last_activity // "never"))"' "$QUEUE_FILE"
    echo

    echo "⏳ Pending Tasks:"
    local pending_count
    pending_count=$(jq '.pending_tasks | length' "$QUEUE_FILE")
    if [ "$pending_count" -gt 0 ]; then
        jq -r '.pending_tasks[] | "  • [\(.priority)] \(.title) → \(.assigned_agent) (ID: \(.id))"' "$QUEUE_FILE"
    else
        echo "  No pending tasks"
    fi
    echo

    echo "🔄 Active Workflows:"
    local active_count
    active_count=$(jq '.active_workflows | length' "$QUEUE_FILE")
    if [ "$active_count" -gt 0 ]; then
        jq -r '.active_workflows[] | "  • \(.title) → \(.assigned_agent) (Started: \(.started), ID: \(.id))"' "$QUEUE_FILE"
    else
        echo "  No active workflows"
    fi
    echo

    echo "🔗 Integration Tasks:"
    local integration_count
    integration_count=$(jq '[.pending_tasks[], .active_workflows[]] | map(select(.assigned_agent | contains("integration"))) | length' "$QUEUE_FILE")
    if [ "$integration_count" -gt 0 ]; then
        jq -r '[.pending_tasks[], .active_workflows[]] | .[] | select(.assigned_agent | contains("integration")) | "  • \(.title) (Status: \(.status), ID: \(.id))"' "$QUEUE_FILE"
    else
        echo "  No integration tasks"
    fi
    echo

    echo "✅ Recently Completed:"
    jq -r '.completed_tasks[-3:] | reverse | .[] | "  • \(.title) → \(.assigned_agent) (\(.completed))"' "$QUEUE_FILE" 2>/dev/null || echo "  No completed tasks"
}

list_tasks() {
    local queue_type="$1"
    local format="${2:-json}"

    # JQ filter to calculate runtime on-demand
    local runtime_filter='
        if (.started != null and .completed != null) then
            . + {runtime_seconds: ((.completed | fromdateiso8601) - (.started | fromdateiso8601))}
        else
            . + {runtime_seconds: null}
        end
    '

    case "$queue_type" in
        "pending")
            if [ "$format" = "compact" ]; then
                jq -c ".pending_tasks[] | $runtime_filter" "$QUEUE_FILE"
            else
                jq ".pending_tasks | map($runtime_filter)" "$QUEUE_FILE"
            fi
            ;;
        "active")
            if [ "$format" = "compact" ]; then
                jq -c ".active_workflows[] | $runtime_filter" "$QUEUE_FILE"
            else
                jq ".active_workflows | map($runtime_filter)" "$QUEUE_FILE"
            fi
            ;;
        "completed")
            if [ "$format" = "compact" ]; then
                jq -c ".completed_tasks[] | $runtime_filter" "$QUEUE_FILE"
            else
                jq ".completed_tasks | map($runtime_filter)" "$QUEUE_FILE"
            fi
            ;;
        "failed")
            if [ "$format" = "compact" ]; then
                jq -c ".failed_tasks[] | $runtime_filter" "$QUEUE_FILE"
            else
                jq ".failed_tasks | map($runtime_filter)" "$QUEUE_FILE"
            fi
            ;;
        "all")
            if [ "$format" = "compact" ]; then
                jq -c "{pending: (.pending_tasks | map($runtime_filter)), active: (.active_workflows | map($runtime_filter)), completed: (.completed_tasks | map($runtime_filter)), failed: (.failed_tasks | map($runtime_filter))}" "$QUEUE_FILE"
            else
                jq "{pending: (.pending_tasks | map($runtime_filter)), active: (.active_workflows | map($runtime_filter)), completed: (.completed_tasks | map($runtime_filter)), failed: (.failed_tasks | map($runtime_filter))}" "$QUEUE_FILE"
            fi
            ;;
        *)
            echo "Error: Unknown queue type: $queue_type"
            echo "Valid types: pending, active, completed, failed, all"
            exit 1
            ;;
    esac
}

#############################################################################
# COMMAND ROUTER
#############################################################################

case "${1:-status}" in
    "add")
        if [ $# -lt 7 ]; then
            echo "Usage: cmat queue add <title> <agent> <priority> <task_type> <source_file> <description> [auto_complete] [auto_chain]"
            echo "Task types: analysis, technical_analysis, implementation, testing, integration, documentation"
            echo "auto_complete: true/false (default: false)"
            echo "auto_chain: true/false (default: false)"
            exit 1
        fi
        add_task "$2" "$3" "$4" "$5" "$6" "$7" "${8:-false}" "${9:-false}"
        ;;

    "start")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat queue start <task_id>"
            exit 1
        fi
        start_task "$2"
        ;;

"complete")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat queue complete <task_id> [result] [--auto-chain|true|false]" >&2
            exit 1
        fi

        # Check for --auto-chain flag OR true/false value
        auto_chain="false"
        if [[ "$*" == *"--auto-chain"* ]]; then
            auto_chain="true"
        elif [ "${4:-}" = "true" ]; then
            # Fourth parameter is literally "true"
            auto_chain="true"
        fi

        # Extract result message
        result_message="${3:-completed successfully}"
        if [ $# -ge 3 ] && [[ "$3" == "--auto-chain" ]]; then
            result_message="completed successfully"
        elif [ $# -ge 4 ] && [[ "$4" == "--auto-chain" ]]; then
            result_message="$3"
        elif [ $# -ge 4 ] && [[ "$4" == "true" || "$4" == "false" ]]; then
            # Fourth param is auto_chain flag value
            result_message="$3"
        fi

        complete_task "$2" "$result_message" "$auto_chain"
        ;;

    "cancel")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat queue cancel <task_id> [reason]"
            exit 1
        fi
        cancel_task "$2" "${3:-task cancelled}"
        ;;

    "cancel-all")
        cancel_all_tasks "${2:-bulk cancellation}"
        ;;

    "fail")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat queue fail <task_id> [error]"
            exit 1
        fi
        fail_task "$2" "${3:-task failed}"
        ;;

    "status")
        show_status
        ;;

    "list")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat queue list <queue_type> [format]"
            echo "Queues: pending, active, completed, failed, all"
            echo "Formats: json (default), compact"
            exit 1
        fi
        list_tasks "$2" "${3:-json}"
        ;;

    "metadata")
        if [ $# -lt 4 ]; then
            echo "Usage: cmat queue metadata <task_id> <key> <value>"
            exit 1
        fi
        update_metadata "$2" "$3" "$4"
        ;;

    *)
        echo "Unknown queue command: ${1:-status}" >&2
        echo "Usage: cmat queue <add|start|complete|cancel|cancel-all|fail|status|list|metadata>" >&2
        exit 1
        ;;
esac