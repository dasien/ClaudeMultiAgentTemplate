#!/usr/bin/env bash

################################################################################
# Script Name: queue_manager.sh
# Description: Queue Manager for Multi-Agent Development System
#              Manages task queues, agent status, and workflow chains with
#              GitHub/Atlassian integration support
# Author: Brian Gentry
# Created: 2025
# Version: 1.0.2
#
# Usage: ./queue_manager.sh COMMAND [OPTIONS]
#
# Commands:
#   add <title> <agent> <priority> <task_type> <source_file> <description> [auto_complete] [auto_chain]
#       Add a new task to the queue
#   add-integration <workflow_status> <source_file> <previous_agent> [parent_task_id]
#       Add an integration task for external system sync
#   start <task_id>
#       Start execution of a pending task
#   complete <task_id> [result] [--auto-chain]
#       Mark a task as completed
#   fail <task_id> [error]
#       Mark a task as failed
#   cancel <task_id> [reason]
#       Cancel a pending or active task
#   cancel-all [reason]
#       Cancel all pending and active tasks
#   update-metadata <task_id> <key> <value>
#       Update metadata for a task
#   sync-external <task_id>
#       Create integration task for specific completed task
#   sync-all
#       Create integration tasks for all unsynced completed tasks
#   workflow <workflow_name> [description]
#       Start a predefined workflow chain
#   list_tasks <queue> [format]
#       List tasks in JSON format (queues: pending, active, completed, failed, all)
#   status
#       Show current queue status (default command)
#   version
#       Show version and dependency information
#
# Examples:
#   ./queue_manager.sh version
#   ./queue_manager.sh add "Analyze feature" analyst high analysis doc.md "Review requirements"
#   ./queue_manager.sh start task_1234567890_12345
#   ./queue_manager.sh complete task_1234567890_12345 "READY_FOR_DEVELOPMENT" --auto-chain
#   ./queue_manager.sh status
#
# Dependencies:
#   - jq (JSON processor)
#   - claude (Claude Code CLI)
#   - Standard Unix tools (date, grep, awk, sed)
#
# Environment Variables:
#   AUTO_INTEGRATE - Control integration task creation (always|never|prompt)
#                    Default: prompt
#
# Exit Codes:
#   0 - Success
#   1 - General error or task not found
#
# File Structure:
#   .claude/queues/task_queue.json - Main queue database
#   .claude/logs/ - Operation logs
#   .claude/status/ - Agent status files
#   .claude/agents/ - Agent configuration files
################################################################################

set -euo pipefail

#############################################################################
# GLOBAL VARIABLES
#############################################################################

readonly VERSION="1.0.2"
readonly QUEUE_DIR=".claude/queues"
readonly LOGS_DIR=".claude/logs"
readonly STATUS_DIR=".claude/status"
readonly QUEUE_FILE="$QUEUE_DIR/task_queue.json"

# Ensure required directories exist
mkdir -p "$QUEUE_DIR" "$LOGS_DIR" "$STATUS_DIR"


################################################################################
# Display version information and check dependencies
# Globals:
#   VERSION
#   QUEUE_FILE
#   LOGS_DIR
#   STATUS_DIR
# Arguments:
#   None
# Outputs:
#   Writes version and dependency information to stdout
# Returns:
#   0 if all dependencies met, 1 if any are missing or outdated
################################################################################
show_version() {
    echo "Queue Manager v${VERSION}"
    echo "Multi-Agent Development System"
    echo ""
    echo "Dependencies:"
    
    local all_deps_ok=0
    
    # Check jq
    if command -v jq &> /dev/null; then
        local jq_version
        jq_version=$(jq --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
        echo "  ✓ jq v$jq_version"
    else
        echo "  ✗ jq - NOT FOUND (required)"
        all_deps_ok=1
    fi
    
    # Check claude
    if command -v claude &> /dev/null; then
        local claude_version
        claude_version=$(claude --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
        if [ -n "$claude_version" ]; then
            echo "  ✓ claude v$claude_version"
        else
            echo "  ✓ claude (version unknown)"
        fi
    else
        echo "  ✗ claude - NOT FOUND (required)"
        all_deps_ok=1
    fi
    
    # Check bash version
    echo "  ✓ bash v${BASH_VERSION}"
    
    # Check optional tools
    if command -v git &> /dev/null; then
        local git_version
        git_version=$(git --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
        echo "  ○ git v$git_version (optional)"
    fi
    
    echo ""
    echo "Environment:"
    echo "  Queue File: $QUEUE_FILE"
    echo "  Logs Dir: $LOGS_DIR"
    echo "  Status Dir: $STATUS_DIR"
    
    if [ -f "$QUEUE_FILE" ]; then
        local pending_count
        pending_count=$(jq '.pending_tasks | length' "$QUEUE_FILE" 2>/dev/null || echo "0")
        local active_count
        active_count=$(jq '.active_workflows | length' "$QUEUE_FILE" 2>/dev/null || echo "0")
        local completed_count
        completed_count=$(jq '.completed_tasks | length' "$QUEUE_FILE" 2>/dev/null || echo "0")
        echo "  Tasks: $pending_count pending, $active_count active, $completed_count completed"
    else
        echo "  Queue: Not initialized"
    fi
    
    return $all_deps_ok
}

################################################################################
# Get current UTC timestamp in ISO 8601 format
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Writes timestamp to stdout (format: YYYY-MM-DDTHH:MM:SSZ)
################################################################################
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

################################################################################
# Log queue operation to operations log file
# Globals:
#   LOGS_DIR
# Arguments:
#   $1 - Operation type (e.g., TASK_ADDED, TASK_STARTED)
#   $2 - Operation details
# Outputs:
#   Appends log entry to queue_operations.log
################################################################################
log_operation() {
    local operation="$1"
    local details="$2"
    local timestamp
    timestamp=$(get_timestamp)
    echo "[$timestamp] $operation: $details" >> "$LOGS_DIR/queue_operations.log"
}

################################################################################
# Update agent status in queue database
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Agent name
#   $2 - Status (active, idle)
#   $3 - Task ID (optional, use "null" for none)
# Outputs:
#   Updates QUEUE_FILE with new agent status
#   Logs operation to queue_operations.log
################################################################################
update_agent_status() {
    local agent="$1"
    local status="$2"
    local task_id="${3:-null}"
    local timestamp
    timestamp=$(get_timestamp)

    # Skip if agent name is empty or null
    if [ -z "$agent" ] || [ "$agent" = "null" ]; then
        return
    fi

    local temp_file
    temp_file=$(mktemp)

    jq ".agent_status[\"$agent\"].status = \"$status\" |
        .agent_status[\"$agent\"].last_activity = \"$timestamp\" |
        .agent_status[\"$agent\"].current_task = $task_id" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"
    log_operation "AGENT_STATUS_UPDATE" "Agent: $agent, Status: $status, Task: $task_id"
}

################################################################################
# Add a new task to the pending queue
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Task title
#   $2 - Assigned agent name
#   $3 - Priority (low, normal, high)
#   $4 - Task type (analysis, technical_analysis, implementation, testing, integration)
#   $5 - Source file path to process
#   $6 - Description/instructions for the agent
#   $7 - Auto-complete flag (true/false, default: false)
#   $8 - Auto-chain flag (true/false, default: false)
# Outputs:
#   Writes task ID to stdout
#   Updates QUEUE_FILE with new task
#   Logs operation
################################################################################
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
        --argjson auto_complete "$auto_complete" \
        --argjson auto_chain "$auto_chain" \
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
            auto_complete: $auto_complete,
            auto_chain: $auto_chain,
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

################################################################################
# Add an integration task for external system synchronization
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Workflow status (e.g., READY_FOR_DEVELOPMENT, TESTING_COMPLETE)
#   $2 - Source file path
#   $3 - Previous agent name
#   $4 - Parent task ID (optional)
# Outputs:
#   Writes confirmation message to stdout
#   Creates integration task via add_task function
# Returns:
#   0 on success
################################################################################
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

    local task_id
    task_id=$(add_task \
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

################################################################################
# Update metadata fields for a task
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Task ID
#   $2 - Metadata key
#   $3 - Metadata value
# Outputs:
#   Writes confirmation or error message to stdout
#   Updates QUEUE_FILE with new metadata
# Returns:
#   0 on success, 1 if task not found
################################################################################
update_metadata() {
    local task_id="$1"
    local key="$2"
    local value="$3"

    local temp_file
    temp_file=$(mktemp)

    # Check which queue the task is in
    local in_pending
    in_pending=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    local in_active
    in_active=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    local in_completed
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

################################################################################
# Check if a workflow status requires external integration
# Globals:
#   None
# Arguments:
#   $1 - Status string to check
# Returns:
#   0 if integration needed, 1 otherwise
################################################################################
needs_integration() {
    local status="$1"

    case "$status" in
        *"READY_FOR_DEVELOPMENT"*|*"READY_FOR_IMPLEMENTATION"*|*"READY_FOR_TESTING"*|*"TESTING_COMPLETE"*|*"DOCUMENTATION_COMPLETE"*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

################################################################################
# Load task prompt template from file
# Globals:
#   None
# Arguments:
#   $1 - Task type (analysis, technical_analysis, implementation, testing, integration)
# Outputs:
#   Writes template content to stdout
# Returns:
#   0 on success, 1 if template not found
################################################################################
load_task_template() {
    local task_type="$1"
    local template_file=".claude/TASK_PROMPT_DEFAULTS.md"

    if [ ! -f "$template_file" ]; then
        echo "Error: Task prompt template file not found: $template_file" >&2
        return 1
    fi

    # Extract template based on task type
    local template_content=""
    case "$task_type" in
        "analysis")
            template_content=$(awk '/^# ANALYSIS_TEMPLATE$/{flag=1; next} /^---$/{flag=0} flag' "$template_file")
            ;;
        "technical_analysis")
            template_content=$(awk '/^# TECHNICAL_ANALYSIS_TEMPLATE$/{flag=1; next} /^---$/{flag=0} flag' "$template_file")
            ;;
        "implementation")
            template_content=$(awk '/^# IMPLEMENTATION_TEMPLATE$/{flag=1; next} /^---$/{flag=0} flag' "$template_file")
            ;;
        "testing")
            template_content=$(awk '/^# TESTING_TEMPLATE$/{flag=1; next} /^---$/{flag=0} flag' "$template_file")
            ;;
        "integration")
            template_content=$(awk '/^# INTEGRATION_TEMPLATE$/{flag=1; next} /^---$/{flag=0} flag' "$template_file")
            if [ -z "$template_content" ]; then
                template_content="You are the integration-coordinator agent. Process the task described in the source file and synchronize with external systems as appropriate."
            fi
            ;;
        *)
            echo "Error: Unknown task type: $task_type" >&2
            return 1
            ;;
    esac

    if [ -z "$template_content" ]; then
        echo "Error: No template found for task type: $task_type" >&2
        return 1
    fi

    echo "$template_content"
    return 0
}

################################################################################
# Invoke Claude Code agent to execute a task
# Globals:
#   None
# Arguments:
#   $1 - Agent name
#   $2 - Task ID
#   $3 - Source file path
#   $4 - Log base directory
#   $5 - Task type
#   $6 - Task description
#   $7 - Auto-complete flag (true/false)
#   $8 - Auto-chain flag (true/false)
# Outputs:
#   Writes execution log to file
#   Writes progress to stdout
# Returns:
#   Claude Code exit code
################################################################################
invoke_agent() {
    local agent="$1"
    local task_id="$2"
    local source_file="$3"
    local log_base_dir="$4"
    local task_type="$5"
    local task_description="$6"
    local auto_complete="${7:-false}"
    local auto_chain="${8:-false}"

    # Validate agent configuration exists
    local agent_config=".claude/agents/${agent}.md"
    if [ ! -f "$agent_config" ]; then
        echo "Error: Agent config not found: $agent_config"
        return 1
    fi

    # Validate source file exists
    if [ ! -f "$source_file" ]; then
        echo "Error: Source file not found: $source_file"
        return 1
    fi

    # Create log file path
    local log_dir="${log_base_dir}/logs"
    mkdir -p "$log_dir"
    local log_file
    log_file="${log_dir}/${agent}_${task_id}_$(date +%Y%m%d_%H%M%S).log"

    # Load and prepare task template
    local template
    template=$(load_task_template "$task_type")
    if [ $? -ne 0 ]; then
        echo "Failed to load task template for type: $task_type"
        return 1
    fi

    # Substitute variables in template
    local prompt="$template"
    prompt="${prompt//\$\{agent\}/$agent}"
    prompt="${prompt//\$\{agent_config\}/$agent_config}"
    prompt="${prompt//\$\{source_file\}/$source_file}"
    prompt="${prompt//\$\{task_description\}/$task_description}"
    prompt="${prompt//\$\{task_id\}/$task_id}"

    local start_time
    start_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local start_timestamp
    start_timestamp=$(date +%s)

    # Log execution start
    echo "=== Starting Agent Execution ===" | tee "$log_file"
    echo "Start Time: $start_time" | tee -a "$log_file"
    echo "Agent: $agent" | tee -a "$log_file"
    echo "Task ID: $task_id" | tee -a "$log_file"
    echo "Source File: $source_file" | tee -a "$log_file"
    echo "Log: $log_file" | tee -a "$log_file"
    echo "" | tee -a "$log_file"

    # Invoke Claude Code with bypass permissions
    claude --permission-mode bypassPermissions "$prompt" 2>&1 | tee -a "$log_file"

    local exit_code=${PIPESTATUS[0]}
    local end_time
    end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local end_timestamp
    end_timestamp=$(date +%s)
    local duration=$((end_timestamp - start_timestamp))

    # Write completion markers
    {
        echo ""
        echo "=== Agent Execution Complete ==="
        echo "End Time: $end_time"
        echo "Duration: ${duration}s"
        echo "Exit Code: $exit_code"
    } >> "$log_file"

    echo ""
    echo "=== Agent Execution Complete ==="
    echo "End Time: $end_time"
    echo "Duration: ${duration}s"
    echo "Exit Code: $exit_code"

    # Extract and log exit status
    local status
    status=$(grep -E "(READY_FOR_[A-Z_]+|COMPLETED|BLOCKED:|INTEGRATION_COMPLETE|INTEGRATION_FAILED)" "$log_file" | tail -1 | grep -oE "(READY_FOR_[A-Z_]+|COMPLETED|BLOCKED:[^*]*|INTEGRATION_COMPLETE|INTEGRATION_FAILED)" | head -1)

    if [ -n "$status" ]; then
        echo "Exit Status: $status" >> "$log_file"
        echo "Exit Status: $status"
    else
        echo "Exit Status: UNKNOWN" >> "$log_file"
        echo "Exit Status: UNKNOWN"
    fi
    echo "" >> "$log_file"
    echo ""

    # Extract standardized status for auto-completion
    status=$(tail -10 "$log_file" | grep "^Exit Status:" | cut -d' ' -f3-)

    if [ -n "$status" ]; then
        echo "Detected Status: $status" >> "$log_file"
        echo "" >> "$log_file"

        if [ "$auto_complete" = "true" ]; then
            # Non-interactive mode
            echo "Auto-completing task (non-interactive mode)" >> "$log_file"
            complete_task "$task_id" "$status" "$auto_chain"
        else
            # Interactive mode - prompt user
            echo "Auto-completing task with status: $status"
            echo -n "Proceed? [Y/n]: "
            read -r proceed

            if [[ ! "$proceed" =~ ^[Nn]$ ]]; then
                complete_task "$task_id" "$status" "$auto_chain"
            else
                echo "Task completion cancelled. Complete manually with:"
                echo "  ./queue_manager.sh complete $task_id '$status' --auto-chain"
            fi
        fi
    else
        echo "Warning: Could not extract completion status from agent output"
        echo "Review log file: $log_file"
        echo "Complete manually with:"
        echo "  ./queue_manager.sh complete $task_id '<STATUS>' --auto-chain"
    fi

    return $exit_code
}

################################################################################
# Start execution of a pending task
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Task ID
# Outputs:
#   Writes task ID to stdout
#   Updates QUEUE_FILE moving task to active queue
#   Invokes agent via invoke_agent function
# Returns:
#   0 on success, 1 if task not found or validation fails
################################################################################
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

    # Extract task information before moving to active
    local task_title
    task_title=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local task_type
    task_type=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .task_type" "$QUEUE_FILE")
    local task_description
    task_description=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .description" "$QUEUE_FILE")
    local agent
    agent=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")
    local source_file
    source_file=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .source_file" "$QUEUE_FILE")
    local auto_complete
    auto_complete=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .auto_complete // false" "$QUEUE_FILE")
    local auto_chain
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

    # Invoke the agent
    local log_base_dir
    log_base_dir=$(dirname "$source_file")
    invoke_agent "$agent" "$task_id" "$source_file" "$log_base_dir" "$task_type" "$task_description" "$auto_complete" "$auto_chain"
}

################################################################################
# Determine next agent based on workflow status
# Globals:
#   None
# Arguments:
#   $1 - Enhancement name (unused but kept for compatibility)
#   $2 - Workflow status
# Outputs:
#   Writes next agent name or "HUMAN_CHOICE_REQUIRED" to stdout
################################################################################
determine_next_agent() {
    local enhancement_name="$1"
    local status="$2"

    case "$status" in
        *"READY_FOR_DEVELOPMENT"*)
            echo "architect"
            ;;
        *"READY_FOR_IMPLEMENTATION"*)
            echo "implementer"
            ;;
        *"READY_FOR_TESTING"*)
            echo "tester"
            ;;
        *"TESTING_COMPLETE"*)
            echo "documenter"
            ;;
        *)
            echo "HUMAN_CHOICE_REQUIRED"
            ;;
    esac
}

################################################################################
# Suggest and optionally create next task in workflow chain
# Globals:
#   QUEUE_FILE
#   AUTO_INTEGRATE (environment variable)
# Arguments:
#   $1 - Completed task ID
#   $2 - Task result/status
# Outputs:
#   Writes suggestions and prompts to stdout
#   May create integration task if needed
#   May create next workflow task if user confirms
################################################################################
suggest_next_task() {
    local task_id="$1"
    local result="$2"

    # Check if integration is needed
    if needs_integration "$result"; then
        local source_file
        source_file=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .source_file" "$QUEUE_FILE")
        local agent
        agent=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")

        local auto_integrate="${AUTO_INTEGRATE:-prompt}"
        local should_integrate="false"

        case "$auto_integrate" in
            "always")
                should_integrate="true"
                echo "🔗 Auto-integration enabled (always mode)"
                ;;
            "never")
                should_integrate="false"
                echo "ℹ️  Auto-integration disabled (never mode)"
                ;;
            *)
                echo ""
                echo "🔗 This status may require integration with external systems:"
                echo "   Status: $result"
                echo "   This would create GitHub issues, Jira tickets, or update documentation."
                echo ""
                echo -n "Create integration task? [y/N]: "
                read -r response
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    should_integrate="true"
                fi
                ;;
        esac

        if [ "$should_integrate" = "true" ]; then
            add_integration_task "$result" "$source_file" "$agent" "$task_id"
        fi
    fi

    # Extract enhancement name for workflow continuation
    local task_title
    task_title=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local enhancement_name=""

    # Try to extract enhancement name from title patterns
    if [[ "$task_title" =~ ^.*"for "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"of "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^"Analyze "(.+)" enhancement"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^"Validate "(.+)" completion"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^"Test "(.+)" enhancement"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^(.+)" enhancement"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^(.+)$ ]]; then
        enhancement_name=$(echo "$task_title" | sed -E 's/^(Test |Analyze |Validate |Architecture |Implementation |Testing )//' | sed -E 's/ (enhancement|completion|design|of .+)$//')
    fi

    # Skip workflow suggestion for integration tasks
    if [[ "$task_title" == "Integrate:"* ]]; then
        echo "✅ Integration task completed"
        return
    fi

    if [ -z "$enhancement_name" ]; then
        echo "Note: Could not determine enhancement name from task title for auto-chaining"
        return
    fi

    local next_agent
    next_agent=$(determine_next_agent "$enhancement_name" "$result")

    if [ "$next_agent" = "HUMAN_CHOICE_REQUIRED" ]; then
        echo ""
        echo "Cannot automatically determine next agent for status: $result"
        echo "Please create the next task manually with queue_manager.sh"
        return
    fi

    # Generate next task details based on status
    local next_title=""
    local next_description=""

    case "$result" in
        *"READY_FOR_DEVELOPMENT"*)
            next_title="Architecture design for $enhancement_name"
            next_description="Design architecture and system structure for $enhancement_name enhancement"
            ;;
        *"READY_FOR_IMPLEMENTATION"*)
            next_title="Implementation of $enhancement_name"
            next_description="Implement $enhancement_name following architectural design"
            ;;
        *"READY_FOR_INTEGRATION"*|*"READY_FOR_TESTING"*)
            next_title="Validate $enhancement_name completion"
            next_description="Test and validate $enhancement_name implementation"
            ;;
        *)
            echo "Note: Status '$result' not recognized for auto-chaining"
            return
            ;;
    esac

    echo ""
    echo "AUTO-CHAIN SUGGESTION:"
    echo "  Title: $next_title"
    echo "  Agent: $next_agent"
    echo "  Description: $next_description"
    echo ""
    echo -n "Create this task? [y/N]: "
    read -r create_task

    if [[ "$create_task" =~ ^[Yy]$ ]]; then
        local new_task_id
        new_task_id=$(add_task "$next_title" "$next_agent" "high" "$enhancement_name" "$next_description")
        echo "✅ Created task: $new_task_id"
    else
        echo "Auto-chain cancelled - create next task manually"
    fi
}

################################################################################
# Mark task as completed and move to completed queue
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Task ID
#   $2 - Result message (default: "completed successfully")
#   $3 - Auto-chain flag (true/false, default: false)
# Outputs:
#   Updates QUEUE_FILE
#   Logs operation
#   May trigger suggest_next_task if auto_chain is true
################################################################################
complete_task() {
    local task_id="$1"
    local result="${2:-completed successfully}"
    local auto_chain="${3:-false}"
    local timestamp
    timestamp=$(get_timestamp)

    # Extract enhancement name from task title
    local task_title
    task_title=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local enhancement_name="unknown"
    
    if [[ "$task_title" =~ ^"Analyze "(.+)" enhancement"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"for "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"of "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    fi

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

    # Suggest next task if auto-chain requested
    if [ "$auto_chain" = "true" ]; then
        suggest_next_task "$task_id" "$result"
    fi
}

################################################################################
# Mark task as failed and move to failed queue
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Task ID
#   $2 - Error message (default: "task failed")
# Outputs:
#   Updates QUEUE_FILE
#   Logs operation
################################################################################
fail_task() {
    local task_id="$1"
    local error="${2:-task failed}"
    local timestamp
    timestamp=$(get_timestamp)

    # Extract enhancement name from task title
    local task_title
    task_title=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local enhancement_name="unknown"
    
    if [[ "$task_title" =~ ^"Analyze "(.+)" enhancement"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"for "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"of "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    fi

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
    update_agent_status "$agent" "idle" "null"

    log_operation "TASK_FAILED" "ID: $task_id, Agent: $agent, Error: $error"
}

################################################################################
# Cancel a pending or active task
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Task ID
#   $2 - Cancellation reason (default: "task cancelled")
# Outputs:
#   Writes confirmation message to stdout
#   Updates QUEUE_FILE
#   Logs operation
# Returns:
#   0 on success, 1 if task not found
################################################################################
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

################################################################################
# Create integration task for specific completed task
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Task ID
# Outputs:
#   Creates integration task via add_integration_task
# Returns:
#   0 on success, 1 if task not found or not completed
################################################################################
sync_external() {
    local task_id="$1"

    local task
    task=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\")" "$QUEUE_FILE")

    if [ -z "$task" ]; then
        echo "❌ Task not found or not completed: $task_id"
        return 1
    fi

    local source_file
    source_file=$(echo "$task" | jq -r '.source_file')
    local result
    result=$(echo "$task" | jq -r '.result')
    local agent
    agent=$(echo "$task" | jq -r '.assigned_agent')

    echo "🔗 Creating integration task for: $task_id"
    add_integration_task "$result" "$source_file" "$agent" "$task_id"
}

################################################################################
# Create integration tasks for all unsynced completed tasks
# Globals:
#   QUEUE_FILE
# Outputs:
#   Writes progress messages to stdout
#   Creates integration tasks for eligible completed tasks
################################################################################
sync_all() {
    echo "🔍 Scanning for tasks requiring integration..."

    local count=0
    local task_ids
    task_ids=$(jq -r '.completed_tasks[] | select(.result != null and .result != "completed successfully") | select(.metadata.github_issue == null) | .id' "$QUEUE_FILE")

    while IFS= read -r task_id; do
        if [ -n "$task_id" ] && needs_integration "$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .result" "$QUEUE_FILE")"; then
            local task
            task=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\")" "$QUEUE_FILE")
            local result
            result=$(echo "$task" | jq -r '.result')
            local source_file
            source_file=$(echo "$task" | jq -r '.source_file')
            local agent
            agent=$(echo "$task" | jq -r '.assigned_agent')

            add_integration_task "$result" "$source_file" "$agent" "$task_id"
            ((count++))
        fi
    done <<< "$task_ids"

    echo "✅ Created $count integration tasks"
}

#############################################################################
# STATUS AND DISPLAY FUNCTIONS
#############################################################################

################################################################################
# Display current queue status
# Globals:
#   QUEUE_FILE
# Outputs:
#   Writes formatted status report to stdout
################################################################################
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
    integration_count=$(jq '[.pending_tasks[], .active_workflows[]] | map(select(.assigned_agent == "integration-coordinator")) | length' "$QUEUE_FILE")
    if [ "$integration_count" -gt 0 ]; then
        jq -r '[.pending_tasks[], .active_workflows[]] | .[] | select(.assigned_agent == "integration-coordinator") | "  • \(.title) (Status: \(.status), ID: \(.id))"' "$QUEUE_FILE"
    else
        echo "  No integration tasks"
    fi
    echo

    echo "✅ Recently Completed:"
    jq -r '.completed_tasks[-3:] | reverse | .[] | "  • \(.title) → \(.assigned_agent) (\(.completed))"' "$QUEUE_FILE" 2>/dev/null || echo "  No completed tasks"
}

################################################################################
# Start a predefined workflow chain
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Workflow name
#   $2 - Task description (default: "Workflow execution")
# Outputs:
#   Writes progress messages to stdout
#   Creates tasks for workflow via add_task
# Returns:
#   0 on success, 1 if workflow not found
################################################################################
start_workflow() {
    local workflow_name="$1"
    local task_description="${2:-Workflow execution}"

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
            add_task "Workflow: $workflow_name" "$agent" "high" "" "$task_description"
        done
    else
        # Sequential execution
        add_task "Workflow: $workflow_name" "$first_step" "high" "" "$task_description"
    fi
}

#############################################################################
# MAIN COMMAND PROCESSOR
#############################################################################

case "${1:-status}" in
    "version")
        show_version
        exit $?
        ;;

    "add")
        if [ $# -lt 7 ]; then
            echo "Usage: $0 add <title> <agent> <priority> <task_type> <source_file> <description> [auto_complete] [auto_chain]"
            echo "Task types: analysis, technical_analysis, implementation, testing, integration"
            echo "auto_complete: true/false (default: false) - Auto-complete without prompting"
            echo "auto_chain: true/false (default: false) - Auto-chain to next task"
            exit 1
        fi
        add_task "$2" "$3" "$4" "$5" "$6" "$7" "${8:-false}" "${9:-false}"
        ;;

    "add-integration")
        if [ $# -lt 4 ]; then
            echo "Usage: $0 add-integration <workflow_status> <source_file> <previous_agent> [parent_task_id]"
            exit 1
        fi
        add_integration_task "$2" "$3" "$4" "${5:-}"
        ;;

    "start")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 start <task_id>"
            exit 1
        fi
        start_task "$2"
        ;;

    "complete")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 complete <task_id> [result] [--auto-chain]"
            exit 1
        fi

        # Check for --auto-chain flag
        auto_chain="false"
        if [[ "$*" == *"--auto-chain"* ]]; then
            auto_chain="true"
        fi

        # Extract result message
        result_message="${3:-completed successfully}"
        if [ $# -ge 3 ] && [[ "$3" == "--auto-chain" ]]; then
            result_message="completed successfully"
        elif [ $# -ge 4 ] && [[ "$4" == "--auto-chain" ]]; then
            result_message="$3"
        fi

        complete_task "$2" "$result_message" "$auto_chain"
        ;;

    "fail")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 fail <task_id> [error]"
            exit 1
        fi
        fail_task "$2" "${3:-task failed}"
        ;;

    "cancel")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 cancel <task_id> [reason]"
            exit 1
        fi
        cancel_task "$2" "${3:-task cancelled}"
        ;;

    "cancel-all")
        reason="${2:-bulk cancellation}"
        echo "Cancelling all pending and active tasks..."

        # Cancel all pending tasks
        pending_tasks=$(jq -r '.pending_tasks[].id' "$QUEUE_FILE")
        pending_count=0
        for task_id in $pending_tasks; do
            if [ -n "$task_id" ]; then
                cancel_task "$task_id" "$reason"
                ((pending_count++))
            fi
        done

        # Cancel all active tasks
        active_tasks=$(jq -r '.active_workflows[].id' "$QUEUE_FILE")
        active_count=0
        for task_id in $active_tasks; do
            if [ -n "$task_id" ]; then
                cancel_task "$task_id" "$reason"
                ((active_count++))
            fi
        done

        echo "✅ Cancelled $pending_count pending and $active_count active tasks"
        ;;

    "update-metadata")
        if [ $# -lt 4 ]; then
            echo "Usage: $0 update-metadata <task_id> <key> <value>"
            exit 1
        fi
        update_metadata "$2" "$3" "$4"
        ;;

    "sync-github"|"sync-jira"|"sync-external")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 sync-external <task_id>"
            exit 1
        fi
        sync_external "$2"
        ;;

    "sync-all")
        sync_all
        ;;

    "workflow")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 workflow <workflow_name> [description]"
            exit 1
        fi
        start_workflow "$2" "${3:-Workflow execution}"
        ;;

    "list_tasks")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 list_tasks <queue> [format]"
            echo "Queues: pending, active, completed, failed, all"
            echo "Formats: json (default), compact"
            exit 1
        fi

        queue_type="$2"
        format="${3:-json}"

        # JQ filter to calculate runtime on-demand
        runtime_filter='
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
        ;;

    "status"|*)
        show_status
        ;;
esac
