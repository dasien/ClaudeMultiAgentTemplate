#!/usr/bin/env bash
################################################################################
# Script Name: common-commands.sh
# Description: Shared utilities and common functions for CMAT subsystems
#              Provides core functions for path resolution, logging, timestamps,
#              directory management, and agent status updates
# Author: Brian Gentry
# Created: 2025
#
# Usage: Source this file from other scripts
#        source "$(dirname "$0")/common-commands.sh"
#
# Provided Functions:
#   find_project_root()          Find .claude/ parent directory
#   get_timestamp()              Generate ISO 8601 UTC timestamp
#   log_operation(op, details)   Log operation to queue_operations.log
#   log_error(message)           Log error message
#   log_info(message)            Log info message
#   check_dependencies()         Verify required tools installed
#   ensure_directories()         Create required directory structure
#   update_agent_status()        Update agent status in queue
#   extract_enhancement_name()   Extract enhancement name from path
#   extract_enhancement_title()  Extract enhancement title from file
#   needs_integration()          Check if status requires integration
#
# Exported Variables:
#   PROJECT_ROOT      Project root directory path
#   QUEUE_FILE        Path to task_queue.json
#   SKILLS_FILE       Path to skills.json
#   WORKFLOW_TEMPLATES_FILE  Path to workflow_templates.json
#   AGENTS_DIR        Path to agents directory
#   AGENTS_FILE       Path to agents.json
#   SKILLS_DIR        Path to skills directory
#   LOGS_DIR          Path to logs directory
#   STATUS_DIR        Path to status directory
#   TEMPLATES_FILE    Path to TASK_PROMPT_DEFAULTS.md
#
# Dependencies:
#   - jq (JSON processor)
#   - Standard Unix tools (date, mkdir, awk, sed)
#
# Exit Codes:
#   1 - Project root not found (exits immediately)
################################################################################

#############################################################################
# VERSION
#############################################################################

readonly VERSION="6.0.1"

#############################################################################
# PROJECT NAVIGATION
#############################################################################

find_project_root() {
    local current_dir="$(pwd)"

    while [ "$current_dir" != "/" ]; do
        if [ -d "$current_dir/.claude" ]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done

    echo "Error: Could not find .claude directory. Run from within project." >&2
    return 1
}

# Initialize project root
PROJECT_ROOT=$(find_project_root)
if [ $? -ne 0 ]; then
    exit 1
fi

# Global paths
readonly AGENTS_DIR="$PROJECT_ROOT/.claude/agents"
readonly SKILLS_DIR="$PROJECT_ROOT/.claude/skills"
readonly LOGS_DIR="$PROJECT_ROOT/.claude/logs"
readonly STATUS_DIR="$PROJECT_ROOT/.claude/status"
readonly QUEUE_FILE="$PROJECT_ROOT/.claude/queues/task_queue.json"
readonly SKILLS_FILE="$PROJECT_ROOT/.claude/skills/skills.json"
readonly WORKFLOW_TEMPLATES_FILE="$PROJECT_ROOT/.claude/queues/workflow_templates.json"
readonly TEMPLATES_FILE="$PROJECT_ROOT/.claude/docs/TASK_PROMPT_DEFAULTS.md"
readonly AGENTS_FILE="$PROJECT_ROOT/.claude/agents/agents.json"

#############################################################################
# DIRECTORY MANAGEMENT
#############################################################################

ensure_directories() {
    mkdir -p "$PROJECT_ROOT/.claude/queues"
    mkdir -p "$PROJECT_ROOT/.claude/logs"
    mkdir -p "$PROJECT_ROOT/.claude/status"
}

#############################################################################
# TIMESTAMPS & LOGGING
#############################################################################

get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log_operation() {
    local operation="$1"
    local details="$2"
    local timestamp
    timestamp=$(get_timestamp)
    echo "[$timestamp] $operation: $details" >> "$LOGS_DIR/queue_operations.log"
}

log_error() {
    local message="$1"
    echo "ERROR: $message" >&2
    log_operation "ERROR" "$message"
}

log_info() {
    local message="$1"
    echo "INFO: $message"
    log_operation "INFO" "$message"
}

#############################################################################
# DEPENDENCY CHECKING
#############################################################################

check_dependencies() {
    echo "Dependencies:"
    local all_ok=0

    if command -v jq &> /dev/null; then
        local jq_version
        jq_version=$(jq --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
        echo "  ✓ jq v$jq_version"
    else
        echo "  ✗ jq - NOT FOUND (required)"
        all_ok=1
    fi

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
        all_ok=1
    fi

    echo "  ✓ bash v${BASH_VERSION}"

    if command -v git &> /dev/null; then
        local git_version
        git_version=$(git --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
        echo "  ○ git v$git_version (optional)"
    fi

    return $all_ok
}

show_version() {
    local full_report="${1:-}"

    if [ "$full_report" = "--full" ]; then
        # Full version report with dependencies and environment
        echo "cmat v${VERSION}"
        echo "Claude Multi-Agent Template System"
        echo ""
        check_dependencies
        echo ""
        echo "Environment:"
        echo "  Project Root: $PROJECT_ROOT"
        echo "  Queue File: $QUEUE_FILE"
        echo "  Agents File: $AGENTS_FILE"
        echo "  Skills: $SKILLS_FILE"

        if [ -f "$QUEUE_FILE" ]; then
            local pending_count
            pending_count=$(jq '.pending_tasks | length' "$QUEUE_FILE" 2>/dev/null || echo "0")
            local active_count
            active_count=$(jq '.active_workflows | length' "$QUEUE_FILE" 2>/dev/null || echo "0")
            local completed_count
            completed_count=$(jq '.completed_tasks | length' "$QUEUE_FILE" 2>/dev/null || echo "0")
            echo "  Tasks: $pending_count pending, $active_count active, $completed_count completed"
        fi

        if [ -f "$AGENTS_FILE" ]; then
            local agent_count
            agent_count=$(jq '.agents | length' "$AGENTS_FILE" 2>/dev/null || echo "0")
            echo "  Agents: $agent_count defined"
        fi

        if [ -f "$SKILLS_FILE" ]; then
            local skills_count
            skills_count=$(jq '.skills | length' "$SKILLS_FILE" 2>/dev/null || echo "0")
            echo "  Skills: $skills_count available"
        fi
    else
        # Just output version number
        echo "$VERSION"
    fi
}

show_help() {
    cat << 'EOF'
cmat - Claude Multi-Agent Template Command Launcher

Usage: cmat <category> <command> [options]

QUEUE COMMANDS:
  cmat queue add <title> <agent> <priority> <type> <source> <desc> [auto_complete] [auto_chain] [enhancement_title]
  cmat queue start <task_id>
  cmat queue complete <task_id> [result] [--auto-chain]
  cmat queue cancel <task_id> [reason]
  cmat queue cancel-all [reason]
  cmat queue fail <task_id> [error]
  cmat queue status
  cmat queue list <queue_type> [format]
  cmat queue metadata <task_id> <key> <value>
  cmat queue preview-prompt <task_id>
  cmat queue clear-finished [--force]
  cmat queue init [--force]
  cmat queue show-task-cost <task_id>
  cmat queue show-enhancement-cost <enhancement_name>

WORKFLOW COMMANDS:
  Contract-based operations:
  cmat workflow validate <agent> <enhancement_dir>
  cmat workflow next-agent <agent> <status>
  cmat workflow next-source <enhancement> <next_agent> <current_agent>
  cmat workflow auto-chain <task_id> <status>
  cmat workflow get-contract <agent>

  Template management:
  cmat workflow create <template_name> <description>
  cmat workflow list
  cmat workflow show <template_name>
  cmat workflow delete <template_name>
  cmat workflow add-step <template_name> <agent> [--position=N]
  cmat workflow remove-step <template_name> <step_number>
  cmat workflow list-steps <template_name>
  cmat workflow show-step <template_name> <step_number>

  Template execution:
  cmat workflow template <template_name> [description]

SKILLS COMMANDS:
  cmat skills list
  cmat skills get <agent-name>
  cmat skills load <skill-directory>
  cmat skills prompt <agent-name>
  cmat skills test

INTEGRATION COMMANDS:
  cmat integration add <status> <source> <agent> [parent_task_id]
  cmat integration sync <task_id>
  cmat integration sync-all

AGENT COMMANDS:
  cmat agents list
  cmat agents invoke <agent> <task_id> <source> <log_dir> <type> <desc> [auto_complete] [auto_chain]
  cmat agents generate-json

UTILITY COMMANDS:
  cmat version
  cmat help

Examples:
  # Create custom workflow template
  cmat workflow create my-workflow "My custom workflow"
  cmat workflow add-step my-workflow architect
  cmat workflow add-step my-workflow implementer
  cmat workflow show my-workflow

  # Use in task creation (via UI or script)
  cmat queue add "New feature" "requirements-analyst" "high" "analysis" "enhancements/feat/feat.md" "Analyze"
  cmat queue status
  cmat skills list
  cmat workflow validate "architect" "enhancements/feature"

EOF
}

#############################################################################
# AGENT STATUS MANAGEMENT
#############################################################################

update_agent_status() {
    local agent="$1"
    local status="$2"
    local task_id="${3:-null}"
    local timestamp
    timestamp=$(get_timestamp)

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
# HELPER FUNCTIONS
#############################################################################

extract_enhancement_name() {
    local source_file="$1"
    local task_id="${2:-}"

    # If source_file is provided and follows enhancements/ pattern, extract from path
    if [ -n "$source_file" ] && [ "$source_file" != "null" ]; then
        local extracted
        extracted=$(echo "$source_file" | sed -E 's|^enhancements/([^/]+)/.*|\1|')

        # Check if extraction was successful (path changed)
        if [ "$extracted" != "$source_file" ]; then
            echo "$extracted"
            return
        fi
    fi

    # Fall back to task_id for ad-hoc tasks (tasks without workflow context)
    if [ -n "$task_id" ]; then
        echo "$task_id"
        return
    fi

    # Last resort: return "unknown"
    echo "unknown"
}

# Extract enhancement title from source file
# Looks for "Title:", "Enhancement:", or "Bug Fix:" fields (with or without markdown headers)
# Returns "Not part of an Enhancement" if not found
extract_enhancement_title() {
    local source_file="$1"

    if [ ! -f "$source_file" ]; then
        echo "Not part of an Enhancement"
        return
    fi

    # Try to extract title from various field formats
    local title

    # First try: Look for "Title:" field (with or without markdown header #)
    title=$(grep -m 1 -E "^#*[[:space:]]*Title:" "$source_file" 2>/dev/null | sed -E 's/^#*[[:space:]]*Title:[[:space:]]*//')

    # Second try: Look for "Enhancement:" field (with or without markdown header #)
    if [ -z "$title" ]; then
        title=$(grep -m 1 -E "^#*[[:space:]]*Enhancement:" "$source_file" 2>/dev/null | sed -E 's/^#*[[:space:]]*Enhancement:[[:space:]]*//')
    fi

    # Third try: Look for "Bug Fix:" field (with or without markdown header #)
    if [ -z "$title" ]; then
        title=$(grep -m 1 -E "^#*[[:space:]]*Bug Fix:" "$source_file" 2>/dev/null | sed -E 's/^#*[[:space:]]*Bug Fix:[[:space:]]*//')
    fi

    if [ -z "$title" ]; then
        echo "Not part of an Enhancement"
    else
        echo "$title"
    fi
}

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

#############################################################################
# INITIALIZATION
#############################################################################

# Ensure directories exist when sourced
ensure_directories