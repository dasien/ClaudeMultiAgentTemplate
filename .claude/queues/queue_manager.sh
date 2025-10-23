#!/usr/bin/env bash

################################################################################
# Script Name: queue_manager.sh
# Description: Queue Manager for Multi-Agent Development System
#              Manages task queues, agent status, and workflow chains with
#              contract-based validation and GitHub/Atlassian integration
# Author: Brian Gentry
# Created: 2025
# Version: 2.1.0
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
#   validate_agent_outputs <agent> <enhancement_dir>
#       Validate agent outputs against contract (NEW)
#   determine_next_agent_from_contract <agent> <status>
#       Determine next agent based on contract (NEW)
#   build_next_source_path <enhancement_name> <next_agent> <current_agent>
#       Build source file path for next agent (NEW)
#   auto_chain_validated <task_id> <status>
#       Auto-chain to next agent with validation (NEW)
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
################################################################################

set -euo pipefail

#############################################################################
# GLOBAL VARIABLES
#############################################################################

readonly VERSION="2.1.0"
readonly QUEUE_DIR=".claude/queues"
readonly LOGS_DIR=".claude/logs"
readonly STATUS_DIR=".claude/status"
readonly QUEUE_FILE="$QUEUE_DIR/task_queue.json"
readonly CONTRACTS_FILE=".claude/AGENT_CONTRACTS.json"

# Ensure required directories exist
mkdir -p "$QUEUE_DIR" "$LOGS_DIR" "$STATUS_DIR"

#############################################################################
# SKILLS MANAGEMENT FUNCTIONS (NEW in v2.1)
#############################################################################

################################################################################
# Get skills data from skills.json
# Globals:
#   None
# Outputs:
#   Writes skills JSON to stdout
# Returns:
#   0 on success, 1 if file not found
################################################################################
get_skills_data() {
    local skills_file=".claude/skills/skills.json"

    if [ ! -f "$skills_file" ]; then
        echo "{\"skills\": []}"
        return 1
    fi

    cat "$skills_file"
    return 0
}

################################################################################
# Get agent's skills from agent configuration file
# Globals:
#   None
# Arguments:
#   $1 - Agent config file path (e.g., ".claude/agents/requirements-analyst.md")
# Outputs:
#   Writes JSON array of skill directory names to stdout
# Returns:
#   0 on success
################################################################################
get_agent_skills() {
    local agent_file="$1"

    if [ ! -f "$agent_file" ]; then
        echo "[]"
        return 0
    fi

    # Extract skills from YAML frontmatter (between first two --- markers)
    local skills
    skills=$(awk '/^---$/{f=!f;next} f && /^skills:/' "$agent_file" | sed 's/^skills:[[:space:]]*//')

    if [ -z "$skills" ]; then
        echo "[]"
    else
        echo "$skills"
    fi
    return 0
}

################################################################################
# Load skill content from SKILL.md file
# Globals:
#   None
# Arguments:
#   $1 - Skill directory name
# Outputs:
#   Writes skill content to stdout (without frontmatter)
# Returns:
#   0 on success, 1 if skill file not found
################################################################################
load_skill_content() {
    local skill_dir="$1"
    local skill_file=".claude/skills/${skill_dir}/SKILL.md"

    if [ ! -f "$skill_file" ]; then
        echo "# Skill Not Found: $skill_dir"
        return 1
    fi

    # Read skill file, skip frontmatter (between --- markers)
    awk '/^---$/{f=!f;next} !f' "$skill_file"
    return 0
}

################################################################################
# Build skills section for agent prompt
# Globals:
#   None
# Arguments:
#   $1 - Agent name
# Outputs:
#   Writes skills content to append to prompt
# Returns:
#   0 on success
################################################################################
build_skills_prompt() {
    local agent="$1"
    local agent_config=".claude/agents/${agent}.md"

    # Get agent's skills
    local skills_json
    skills_json=$(get_agent_skills "$agent_config")

    # If no skills or empty array, return empty
    if [ "$skills_json" = "[]" ] || [ -z "$skills_json" ]; then
        return 0
    fi

    # Parse skill directories from JSON array
    local skill_dirs
    skill_dirs=$(echo "$skills_json" | jq -r '.[]' 2>/dev/null)

    if [ -z "$skill_dirs" ]; then
        return 0
    fi

    # Build skills section
    cat <<'EOF'

################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

You have access to the following specialized skills that enhance your capabilities.
Use these skills when they are relevant to your task:

EOF

    # Load each skill
    local skill_count=0
    while IFS= read -r skill_dir; do
        if [ -n "$skill_dir" ]; then
            local skill_content
            skill_content=$(load_skill_content "$skill_dir")

            if [ $? -eq 0 ]; then
                ((skill_count++))
                echo "---"
                echo ""
                echo "$skill_content"
                echo ""
            fi
        fi
    done <<< "$skill_dirs"

    if [ $skill_count -gt 0 ]; then
        cat <<'EOF'
---

**Using Skills**: Apply the above skills as appropriate to accomplish your objectives.
Reference specific skills in your work when they guide your approach or decisions.

################################################################################

EOF
    fi

    return 0
}

#############################################################################
# CONTRACT-BASED FUNCTIONS (NEW)
#############################################################################

################################################################################
# Get agent contract information from AGENT_CONTRACTS.json
# Globals:
#   CONTRACTS_FILE
# Arguments:
#   $1 - Agent name
# Outputs:
#   Writes agent contract JSON to stdout
# Returns:
#   0 on success, 1 if agent not found or file missing
################################################################################
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

################################################################################
# Validate agent outputs exist and meet contract requirements
# Globals:
#   None
# Arguments:
#   $1 - Agent name
#   $2 - Enhancement directory path
# Outputs:
#   Writes validation messages to stdout
# Returns:
#   0 on success, 1 if validation fails
################################################################################
validate_agent_outputs() {
    local agent="$1"
    local enhancement_dir="$2"

    local contract
    contract=$(get_agent_contract "$agent")
    if [ $? -ne 0 ]; then
        return 1
    fi

    local output_dir
    output_dir=$(echo "$contract" | jq -r '.outputs.output_directory')
    local root_doc
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
        # Check for YAML frontmatter delimiters
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

################################################################################
# Determine next agent based on status and agent contract
# Globals:
#   None
# Arguments:
#   $1 - Current agent name
#   $2 - Completion status
# Outputs:
#   Writes next agent name to stdout, or "UNKNOWN" if none found
# Returns:
#   0 if next agent found, 1 otherwise
################################################################################
determine_next_agent_from_contract() {
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

################################################################################
# Build source file path for next agent based on current agent's output
# Globals:
#   None
# Arguments:
#   $1 - Enhancement name
#   $2 - Next agent name
#   $3 - Current agent name
# Outputs:
#   Writes source file path to stdout
# Returns:
#   0 on success, 1 on error
################################################################################
build_next_source_path() {
    local enhancement_name="$1"
    local next_agent="$2"
    local current_agent="$3"

    local current_contract
    current_contract=$(get_agent_contract "$current_agent")
    if [ $? -ne 0 ]; then
        return 1
    fi

    local output_dir
    output_dir=$(echo "$current_contract" | jq -r '.outputs.output_directory')
    local root_doc
    root_doc=$(echo "$current_contract" | jq -r '.outputs.root_document')

    echo "enhancements/$enhancement_name/$output_dir/$root_doc"
    return 0
}

################################################################################
# Get task type for agent based on role
# Globals:
#   None
# Arguments:
#   $1 - Agent name
# Outputs:
#   Writes task type to stdout
# Returns:
#   0 on success
################################################################################
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
        "analysis")
            echo "analysis"
            ;;
        "technical_design")
            echo "technical_analysis"
            ;;
        "implementation")
            echo "implementation"
            ;;
        "testing")
            echo "testing"
            ;;
        "documentation")
            echo "documentation"
            ;;
        "integration")
            echo "integration"
            ;;
        *)
            echo "unknown"
            ;;
    esac

    return 0
}

################################################################################
# Extract enhancement name from any source file path
# Globals:
#   None
# Arguments:
#   $1 - Source file path
# Outputs:
#   Writes enhancement name to stdout
################################################################################
extract_enhancement_name() {
    local source_file="$1"
    echo "$source_file" | sed -E 's|^enhancements/([^/]+)/.*|\1|'
}

################################################################################
# Auto-chain to next agent with full validation
# Globals:
#   QUEUE_FILE
# Arguments:
#   $1 - Completed task ID
#   $2 - Completion status
# Outputs:
#   Writes progress and result messages to stdout
#   Creates next task if validation passes
# Returns:
#   0 on success, 1 if validation or chaining fails
################################################################################
auto_chain_validated() {
    local task_id="$1"
    local status="$2"

    # Get task details
    local task
    task=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\")" "$QUEUE_FILE")

    if [ -z "$task" ] || [ "$task" = "null" ]; then
        echo "❌ Task not found in completed tasks: $task_id"
        return 1
    fi

    local agent
    agent=$(echo "$task" | jq -r '.assigned_agent')
    local source_file
    source_file=$(echo "$task" | jq -r '.source_file')

    # Get parent task's automation settings to inherit them
    local parent_auto_complete
    parent_auto_complete=$(echo "$task" | jq -r '.auto_complete // false')
    local parent_auto_chain
    parent_auto_chain=$(echo "$task" | jq -r '.auto_chain // false')

    # Extract enhancement name from source file
    local enhancement_name
    enhancement_name=$(extract_enhancement_name "$source_file")
    local enhancement_dir="enhancements/$enhancement_name"

    # Validate current agent outputs
    echo "🔍 Validating outputs from $agent..."
    if ! validate_agent_outputs "$agent" "$enhancement_dir"; then
        echo "❌ Cannot chain: Required outputs missing"
        return 1
    fi

    # Determine next agent
    local next_agent
    next_agent=$(determine_next_agent_from_contract "$agent" "$status")

    if [ "$next_agent" = "UNKNOWN" ]; then
        echo "ℹ️  No automatic next agent for status: $status"
        return 0
    fi

    # Build next source file path
    local next_source
    next_source=$(build_next_source_path "$enhancement_name" "$next_agent" "$agent")

    # Verify next source exists
    if [ ! -f "$next_source" ]; then
        echo "❌ Cannot chain: Next source file missing: $next_source"
        return 1
    fi

    # Build next task description
    local next_title="Process $enhancement_name with $next_agent"
    local next_desc="Continue workflow for $enhancement_name following $agent completion"
    local task_type
    task_type=$(get_task_type_for_agent "$next_agent")

    # Create next task - inherit automation settings from parent
    local new_task_id
    new_task_id=$(add_task \
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

    # Automatically start the newly created task
    start_task "$new_task_id"

    return $?
}

#############################################################################
# UTILITY FUNCTIONS
#############################################################################

################################################################################
# Display version information and check dependencies
# Globals:
#   VERSION
#   QUEUE_FILE
#   LOGS_DIR
#   STATUS_DIR
#   CONTRACTS_FILE
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
    echo "  Contracts File: $CONTRACTS_FILE"
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

    if [ -f "$CONTRACTS_FILE" ]; then
        local agent_count
        agent_count=$(jq '.agents | length' "$CONTRACTS_FILE" 2>/dev/null || echo "0")
        echo "  Agents: $agent_count defined in contracts"
    else
        echo "  Contracts: Not found (⚠️ required for v2.0+)"
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

#############################################################################
# TASK MANAGEMENT FUNCTIONS
#############################################################################

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
            template_content=$(awk '/^# ANALYSIS_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$template_file")
            ;;
        "technical_analysis")
            template_content=$(awk '/^# TECHNICAL_ANALYSIS_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$template_file")
            ;;
        "implementation")
            template_content=$(awk '/^# IMPLEMENTATION_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$template_file")
            ;;
        "testing")
            template_content=$(awk '/^# TESTING_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$template_file")
            ;;
        "integration")
            template_content=$(awk '/^# INTEGRATION_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$template_file")
            if [ -z "$template_content" ]; then
                template_content="You are the integration-coordinator agent. Process the task described in the source file and synchronize with external systems as appropriate."
            fi
            ;;
        "documentation")
            template_content=$(awk '/^# DOCUMENTATION_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$template_file")
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

    # Get agent contract information
    local agent_contract
    agent_contract=$(get_agent_contract "$agent")
    if [ $? -ne 0 ]; then
        echo "Warning: Agent contract not found, using defaults"
        agent_contract="{}"
    fi

    local root_document
    root_document=$(echo "$agent_contract" | jq -r '.outputs.root_document // "output.md"')
    local output_directory
    output_directory=$(echo "$agent_contract" | jq -r '.outputs.output_directory // "output"')

    # Extract enhancement name from source file
    local enhancement_name
    enhancement_name=$(extract_enhancement_name "$source_file")
    local enhancement_dir="enhancements/$enhancement_name"

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

    # NEW: Build and append skills section
    local skills_section
    skills_section=$(build_skills_prompt "$agent")

    if [ -n "$skills_section" ]; then
        template="${template}${skills_section}"
    fi

    # Substitute variables in template
    local prompt="$template"
    prompt="${prompt//\$\{agent\}/$agent}"
    prompt="${prompt//\$\{agent_config\}/$agent_config}"
    prompt="${prompt//\$\{source_file\}/$source_file}"
    prompt="${prompt//\$\{task_description\}/$task_description}"
    prompt="${prompt//\$\{task_id\}/$task_id}"
    prompt="${prompt//\$\{task_type\}/$task_type}"
    prompt="${prompt//\$\{root_document\}/$root_document}"
    prompt="${prompt//\$\{output_directory\}/$output_directory}"
    prompt="${prompt//\$\{enhancement_name\}/$enhancement_name}"
    prompt="${prompt//\$\{enhancement_dir\}/$enhancement_dir}"

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
    echo "Enhancement: $enhancement_name" | tee -a "$log_file"
    echo "Output Directory: $output_directory" | tee -a "$log_file"
    echo "Root Document: $root_document" | tee -a "$log_file"
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

    # Invoke the agent - use enhancement directory for logs
    local enhancement_name
    enhancement_name=$(extract_enhancement_name "$source_file")
    local log_base_dir="enhancements/$enhancement_name"

    invoke_agent "$agent" "$task_id" "$source_file" "$log_base_dir" "$task_type" "$task_description" "$auto_complete" "$auto_chain"
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

    # Skip workflow suggestion for integration tasks
    local task_title
    task_title=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")

    if [[ "$task_title" == "Integrate:"* ]]; then
        echo "✅ Integration task completed"
        return
    fi

    # Use contract-based chaining for workflow tasks
    local agent
    agent=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")

    # Determine next agent from contract
    local next_agent
    next_agent=$(determine_next_agent_from_contract "$agent" "$result")

    if [ "$next_agent" = "UNKNOWN" ]; then
        echo ""
        echo "ℹ️  No automatic next agent for status: $result"
        echo "Workflow may be complete or require manual decision"
        return
    fi

    # Get source file and extract enhancement name
    local source_file
    source_file=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .source_file" "$QUEUE_FILE")
    local enhancement_name
    enhancement_name=$(extract_enhancement_name "$source_file")

    # Build next source path
    local next_source
    next_source=$(build_next_source_path "$enhancement_name" "$next_agent" "$agent")

    # Generate next task details
    local next_title="Process $enhancement_name with $next_agent"
    local next_description="Continue workflow for $enhancement_name following $agent completion"

    echo ""
    echo "AUTO-CHAIN SUGGESTION:"
    echo "  Title: $next_title"
    echo "  Agent: $next_agent"
    echo "  Source: $next_source"
    echo "  Description: $next_description"
    echo ""
    echo -n "Create this task? [y/N]: "
    read -r create_task

    if [[ "$create_task" =~ ^[Yy]$ ]]; then
        auto_chain_validated "$task_id" "$result"
    else
        echo "Auto-chain cancelled - create next task manually if needed"
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

    # Handle auto-chaining based on flag
    if [ "$auto_chain" = "true" ]; then
        # Auto-chain mode - validate and create next task automatically
        auto_chain_validated "$task_id" "$result"
    fi
    # Note: suggest_next_task is no longer used - replaced by auto_chain_validated
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
            add_task "Workflow: $workflow_name" "$agent" "high" "" "" "$task_description"
        done
    else
        # Sequential execution
        add_task "Workflow: $workflow_name" "$first_step" "high" "" "" "$task_description"
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
            echo "Task types: analysis, technical_analysis, implementation, testing, integration, documentation"
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

    "validate-agent-outputs")
        if [ $# -lt 3 ]; then
            echo "Usage: $0 validate-agent-outputs <agent> <enhancement_dir>"
            exit 1
        fi
        validate_agent_outputs "$2" "$3"
        ;;

    "determine-next-agent")
        if [ $# -lt 3 ]; then
            echo "Usage: $0 determine-next-agent <agent> <status>"
            exit 1
        fi
        determine_next_agent_from_contract "$2" "$3"
        ;;

    "build-next-source")
        if [ $# -lt 4 ]; then
            echo "Usage: $0 build-next-source <enhancement_name> <next_agent> <current_agent>"
            exit 1
        fi
        build_next_source_path "$2" "$3" "$4"
        ;;

    "auto-chain")
        if [ $# -lt 3 ]; then
            echo "Usage: $0 auto-chain <task_id> <status>"
            exit 1
        fi
        auto_chain_validated "$2" "$3"
        ;;

    "sync-external")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 sync-external <task_id>"
            exit 1
        fi
        sync_external "$2"
        ;;

    "sync-all")
        sync_all
        ;;

    "get-skills-data")
        get_skills_data | jq '.'
        ;;

    "get-agent-skills")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 get-agent-skills <agent-file>"
            echo "Example: $0 get-agent-skills requirements-analyst"
            exit 1
        fi
        get_agent_skills ".claude/agents/$2.md"
        ;;

    "load-skill")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 load-skill <skill-directory>"
            echo "Example: $0 load-skill requirements-elicitation"
            exit 1
        fi
        load_skill_content "$2"
        ;;

    "build-skills-prompt")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 build-skills-prompt <agent-name>"
            echo "Example: $0 build-skills-prompt requirements-analyst"
            exit 1
        fi
        build_skills_prompt "$2"
        ;;

    "test-skills")
        echo "=== Testing Skills System ==="
        echo ""
        echo "1. Skills Data:"
        get_skills_data | jq '.'
        echo ""
        echo "2. Requirements Analyst Skills:"
        get_agent_skills ".claude/agents/requirements-analyst.md"
        echo ""
        echo "3. Load Sample Skill (if exists):"
        if [ -f ".claude/skills/requirements-elicitation/SKILL.md" ]; then
            load_skill_content "requirements-elicitation" | head -20
            echo "... (truncated)"
        else
            echo "Skill not found - create .claude/skills/requirements-elicitation/SKILL.md first"
        fi
        echo ""
        echo "4. Build Skills Prompt for requirements-analyst:"
        build_skills_prompt "requirements-analyst" | head -30
        echo "... (truncated)"
        ;;

    "workflow")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 workflow <workflow_name> [description]"
            exit 1
        fi
        start_workflow "$2" "${3:-Workflow execution}"
        ;;

    "list-tasks")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 list-tasks <queue> [format]"
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

    "preview-prompt")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 preview-prompt <task_id>"
            exit 1
        fi

        # Get task details
        task_id="$2"
        task=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\")" "$QUEUE_FILE")

        if [ -z "$task" ] || [ "$task" = "null" ]; then
            echo "Task not found in pending queue: $task_id"
            exit 1
        fi

        # Extract task details
        agent=$(echo "$task" | jq -r '.assigned_agent')
        task_type=$(echo "$task" | jq -r '.task_type')
        source_file=$(echo "$task" | jq -r '.source_file')
        task_description=$(echo "$task" | jq -r '.description')

        # Get contract info
        agent_contract=$(get_agent_contract "$agent")
        root_document=$(echo "$agent_contract" | jq -r '.outputs.root_document // "output.md"')
        output_directory=$(echo "$agent_contract" | jq -r '.outputs.output_directory // "output"')
        enhancement_name=$(extract_enhancement_name "$source_file")
        enhancement_dir="enhancements/$enhancement_name"

        # Load template
        template=$(load_task_template "$task_type")

        # Build skills
        skills_section=$(build_skills_prompt "$agent")

        if [ -n "$skills_section" ]; then
            template="${template}${skills_section}"
        fi

        # Substitute variables
        prompt="$template"
        prompt="${prompt//\$\{agent\}/$agent}"
        prompt="${prompt//\$\{agent_config\}/.claude/agents/${agent}.md}"
        prompt="${prompt//\$\{source_file\}/$source_file}"
        prompt="${prompt//\$\{task_description\}/$task_description}"
        prompt="${prompt//\$\{task_id\}/$task_id}"
        prompt="${prompt//\$\{task_type\}/$task_type}"
        prompt="${prompt//\$\{root_document\}/$root_document}"
        prompt="${prompt//\$\{output_directory\}/$output_directory}"
        prompt="${prompt//\$\{enhancement_name\}/$enhancement_name}"
        prompt="${prompt//\$\{enhancement_dir\}/$enhancement_dir}"

        # Output the prompt
        echo "$prompt"
        ;;

    "status"|*)
        show_status
        ;;
esac