#!/bin/bash

# Queue Manager for 6502 Kernel Multi-Agent System
# Manages task queues, agent status, and workflow chains

set -euo pipefail

QUEUE_DIR=".claude/queues"
LOGS_DIR=".claude/logs"
STATUS_DIR=".claude/status"
QUEUE_FILE="$QUEUE_DIR/task_queue.json"

# Ensure required directories exist
mkdir -p "$QUEUE_DIR" "$LOGS_DIR" "$STATUS_DIR"

# Function to get current timestamp
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Function to log queue operations
log_operation() {
    local operation="$1"
    local details="$2"
    local timestamp=$(get_timestamp)
    echo "[$timestamp] $operation: $details" >> "$LOGS_DIR/queue_operations.log"
}

# Function to update agent status
update_agent_status() {
    local agent="$1"
    local status="$2"
    local task_id="${3:-null}"
    local timestamp=$(get_timestamp)

    # Skip if agent name is empty or null
    if [ -z "$agent" ] || [ "$agent" = "null" ]; then
        return
    fi

    # Create temporary file for jq processing
    local temp_file=$(mktemp)

    jq ".agent_status[\"$agent\"].status = \"$status\" |
        .agent_status[\"$agent\"].last_activity = \"$timestamp\" |
        .agent_status[\"$agent\"].current_task = $task_id" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"
    log_operation "AGENT_STATUS_UPDATE" "Agent: $agent, Status: $status, Task: $task_id"
}

# Function to add task to queue
add_task() {
    local task_title="$1"
    local agent="$2"
    local priority="${3:-normal}"
    local task_type="${4:-}"  # Task type (analysis, technical_analysis, implementation, testing)
    local source_file="${5:-}"  # Source document to process
    local description="${6:-No description}"  # Prompt/instructions for agent

    local task_id="task_$(date +%s)_$$"
    local timestamp=$(get_timestamp)

    local task_object=$(jq -n \
        --arg id "$task_id" \
        --arg title "$task_title" \
        --arg agent "$agent" \
        --arg priority "$priority" \
        --arg task_type "$task_type" \
        --arg description "$description" \
        --arg source_file "$source_file" \
        --arg created "$timestamp" \
        --arg status "pending" \
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
            result: null
        }')

    local temp_file=$(mktemp)
    jq ".pending_tasks += [$task_object]" "$QUEUE_FILE" > "$temp_file"
    mv "$temp_file" "$QUEUE_FILE"

    log_operation "TASK_ADDED" "ID: $task_id, Agent: $agent, Title: $task_title"
    echo "$task_id"
}

# Function to load task prompt template
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

# Function to invoke Claude Code with agent and task
invoke_agent() {
    local agent="$1"
    local task_id="$2"
    local source_file="$3"
    local log_base_dir="$4"  # Base directory for log files
    local task_type="$5"  # Task type for template lookup
    local task_description="$6"  # Task instructions

    # Get agent configuration file
    local agent_config=".claude/agents/${agent}.md"

    if [ ! -f "$agent_config" ]; then
        echo "Error: Agent config not found: $agent_config"
        return 1
    fi

    if [ ! -f "$source_file" ]; then
        echo "Error: Source file not found: $source_file"
        return 1
    fi

    # Create log file path based on source file location
    local log_dir="${log_base_dir}/logs"
    mkdir -p "$log_dir"
    local log_file="${log_dir}/${agent}_${task_id}_$(date +%Y%m%d_%H%M%S).log"

    # Load task template
    local template=$(load_task_template "$task_type")
    if [ $? -ne 0 ]; then
        echo "Failed to load task template for type: $task_type"
        return 1
    fi

    # Build the Claude Code prompt by substituting variables in template
    # Use a more robust method to handle special characters and newlines
    local prompt="$template"
    prompt="${prompt//\$\{agent\}/$agent}"
    prompt="${prompt//\$\{agent_config\}/$agent_config}"
    prompt="${prompt//\$\{source_file\}/$source_file}"
    prompt="${prompt//\$\{task_description\}/$task_description}"
    prompt="${prompt//\$\{task_id\}/$task_id}"

    local start_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local start_timestamp=$(date +%s)

    echo "=== Starting Agent Execution ===" | tee "$log_file"
    echo "Start Time: $start_time" | tee -a "$log_file"
    echo "Agent: $agent" | tee -a "$log_file"
    echo "Task ID: $task_id" | tee -a "$log_file"
    echo "Source File: $source_file" | tee -a "$log_file"
    echo "Log: $log_file" | tee -a "$log_file"
    echo "" | tee -a "$log_file"

    # Invoke Claude Code with bypassPermissions and capture output
    claude --permission-mode bypassPermissions "$prompt" 2>&1 | tee -a "$log_file"

    local exit_code=${PIPESTATUS[0]}
    local end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local end_timestamp=$(date +%s)
    local duration=$((end_timestamp - start_timestamp))

    echo "" | tee -a "$log_file"
    echo "=== Agent Execution Complete ===" | tee -a "$log_file"
    echo "End Time: $end_time" | tee -a "$log_file"
    echo "Duration: ${duration}s" | tee -a "$log_file"
    echo "Exit Code: $exit_code" | tee -a "$log_file"

    # Extract status from agent output and log it in standardized format
    local status=$(grep -E "(READY_FOR_[A-Z_]+|COMPLETED|BLOCKED:)" "$log_file" | tail -1 | grep -oE "(READY_FOR_[A-Z_]+|COMPLETED|BLOCKED:[^*]*)" | head -1)

    if [ -n "$status" ]; then
        echo "Exit Status: $status" | tee -a "$log_file"
    else
        echo "Exit Status: UNKNOWN" | tee -a "$log_file"
    fi
    echo "" | tee -a "$log_file"

    # Now extract the standardized status for processing
    local status=$(tail -10 "$log_file" | grep "^Exit Status:" | cut -d' ' -f3-)

    if [ -n "$status" ]; then
        echo "Detected Status: $status" | tee -a "$log_file"
        echo ""
        echo "Auto-completing task with status: $status"
        echo -n "Proceed? [Y/n]: "
        read -r proceed

        if [[ ! "$proceed" =~ ^[Nn]$ ]]; then
            complete_task "$task_id" "$status" "true"
        else
            echo "Task completion cancelled. Complete manually with:"
            echo "  ./queue_manager.sh complete $task_id '$status' --auto-chain"
        fi
    else
        echo "Warning: Could not extract completion status from agent output"
        echo "Review log file: $log_file"
        echo "Complete manually with:"
        echo "  ./queue_manager.sh complete $task_id '<STATUS>' --auto-chain"
    fi


    return $exit_code
}

# Function to start specific task
start_task() {
    local task_id="$1"
    local timestamp=$(get_timestamp)

    # Check if task exists in pending queue
    local task_exists=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")

    if [ -z "$task_exists" ]; then
        echo "Task $task_id not found in pending queue"
        return 1
    fi

    # Extract task info
    local task_title=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local task_type=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .task_type" "$QUEUE_FILE")
    local task_description=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .description" "$QUEUE_FILE")
    local agent=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")
    local source_file=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .source_file" "$QUEUE_FILE")

    # Validate source file exists
    if [ -z "$source_file" ] || [ "$source_file" = "null" ]; then
        echo "Error: No source file specified for task $task_id"
        return 1
    fi

    if [ ! -f "$source_file" ]; then
        echo "Error: Source file not found: $source_file"
        return 1
    fi

    local temp_file=$(mktemp)

    # Move task from pending to active and update timestamps
    jq "(.pending_tasks[] | select(.id == \"$task_id\")) |= (.status = \"active\" | .started = \"$timestamp\") |
        .active_workflows += [.pending_tasks[] | select(.id == \"$task_id\")] |
        .pending_tasks = [.pending_tasks[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"

    update_agent_status "$agent" "active" "\"$task_id\""
    log_operation "TASK_STARTED" "ID: $task_id, Agent: $agent, Source: $source_file"

    echo "$task_id"

    # Invoke the agent via Claude Code
    # Extract directory name from source file for logging
    local log_base_dir=$(dirname "$source_file")
    invoke_agent "$agent" "$task_id" "$source_file" "$log_base_dir" "$task_type" "$task_description"
}

# Function to analyze enhancement and determine next agent
determine_next_agent() {
    local enhancement_name="$1"
    local status="$2"

    # Look for enhancement file in directory structure
    local enhancement_file=""
    if [ -f "enhancements/${enhancement_name}/${enhancement_name}.md" ]; then
        enhancement_file="enhancements/${enhancement_name}/${enhancement_name}.md"
    elif [ -f "enhancements/${enhancement_name}.md" ]; then
        # Fallback for old structure
        enhancement_file="enhancements/${enhancement_name}.md"
    elif [ -f "enhancements/${enhancement_name}_requirements_analysis.md" ]; then
        # Extract base name from requirements file
        local base_name=$(echo "$enhancement_name" | sed 's/_requirements_analysis$//')
        if [ -f "enhancements/${base_name}/${base_name}.md" ]; then
            enhancement_file="enhancements/${base_name}/${base_name}.md"
        elif [ -f "enhancements/${base_name}.md" ]; then
            enhancement_file="enhancements/${base_name}.md"
        fi
    fi

    if [ -z "$enhancement_file" ]; then
        echo "HUMAN_CHOICE_REQUIRED"
        return
    fi

    # Analyze status to determine next phase
    case "$status" in
        *"READY_FOR_DEVELOPMENT"*)
            # Check enhancement file for agent guidance
            if grep -qi "architecture.*cpp-developer\|cpp.*architect" "$enhancement_file" 2>/dev/null; then
                echo "cpp-developer"
            elif grep -qi "architecture.*assembly-developer\|assembly.*architect\|6502.*architect" "$enhancement_file" 2>/dev/null; then
                echo "assembly-developer"
            # Analyze content for technology hints
            elif grep -qi "C++\|main\.cpp\|\.cpp\|\.h\|simulator\|emulator" "$enhancement_file" 2>/dev/null; then
                echo "cpp-developer"
            elif grep -qi "assembly\|kernel\.asm\|\.asm\|6502\|monitor\|hardware" "$enhancement_file" 2>/dev/null; then
                echo "assembly-developer"
            else
                echo "HUMAN_CHOICE_REQUIRED"
            fi
            ;;
        *"READY_FOR_IMPLEMENTATION"*)
            # Implementation usually stays with same agent as architecture
            # But check if different agent specified
            if grep -qi "implementation.*cpp-developer\|cpp.*implement" "$enhancement_file" 2>/dev/null; then
                echo "cpp-developer"
            elif grep -qi "implementation.*assembly-developer\|assembly.*implement\|6502.*implement" "$enhancement_file" 2>/dev/null; then
                echo "assembly-developer"
            # Default: analyze content
            elif grep -qi "C++\|main\.cpp\|\.cpp\|\.h" "$enhancement_file" 2>/dev/null; then
                echo "cpp-developer"
            elif grep -qi "assembly\|kernel\.asm\|\.asm\|6502" "$enhancement_file" 2>/dev/null; then
                echo "assembly-developer"
            else
                echo "HUMAN_CHOICE_REQUIRED"
            fi
            ;;
        *"READY_FOR_INTEGRATION"*|*"READY_FOR_TESTING"*)
            echo "testing-agent"
            ;;
        *)
            echo "HUMAN_CHOICE_REQUIRED"
            ;;
    esac
}

# Function to suggest next task based on status
suggest_next_task() {
    local task_id="$1"
    local result="$2"

    # Extract enhancement name from completed task title
    local task_title=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local enhancement_name=""

    # Try to extract enhancement name from various title patterns
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
        # For simple titles, try to extract likely enhancement name
        enhancement_name=$(echo "$task_title" | sed -E 's/^(Test |Analyze |Validate |Architecture |Implementation |Testing )//' | sed -E 's/ (enhancement|completion|design|of .+)$//')
    fi

    if [ -z "$enhancement_name" ]; then
        echo "Note: Could not determine enhancement name from task title for auto-chaining"
        return
    fi

    local next_agent=$(determine_next_agent "$enhancement_name" "$result")

    if [ "$next_agent" = "HUMAN_CHOICE_REQUIRED" ]; then
        echo ""
        echo "AUTO-CHAIN: Multiple agents could handle the next phase:"
        case "$result" in
            *"READY_FOR_DEVELOPMENT"*)
                echo "  [1] cpp-developer (C++ architecture)"
                echo "  [2] assembly-developer (6502 architecture)"
                echo "  [3] Manual task creation"
                ;;
            *"READY_FOR_IMPLEMENTATION"*)
                echo "  [1] cpp-developer (C++ implementation)"
                echo "  [2] assembly-developer (6502 implementation)"
                echo "  [3] Manual task creation"
                ;;
            *)
                echo "  [1] Manual task creation (status analysis unclear)"
                ;;
        esac
        echo -n "Choose assignment [1-3]: "
        read -r choice

        case "$choice" in
            "1") next_agent="cpp-developer" ;;
            "2") next_agent="assembly-developer" ;;
            *) echo "Manual task creation selected"; return ;;
        esac
    fi

    # Generate next task based on status
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
        local new_task_id=$(add_task "$next_title" "$next_agent" "high" "$enhancement_name" "$next_description")
        echo "✅ Created task: $new_task_id"
    else
        echo "Auto-chain cancelled - create next task manually"
    fi
}

# Function to complete task
complete_task() {
    local task_id="$1"
    local result="${2:-completed successfully}"
    local auto_chain="${3:-false}"
    local timestamp=$(get_timestamp)

    # Get task info before moving it
    local task_title=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local enhancement_name="unknown"
    if [[ "$task_title" =~ ^"Analyze "(.+)" enhancement"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"for "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"of "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    fi

    local temp_file=$(mktemp)

    # Move task from active to completed
    jq "(.active_workflows[] | select(.id == \"$task_id\")) |= (.status = \"completed\" | .completed = \"$timestamp\" | .result = \"$result\") |
        .completed_tasks += [.active_workflows[] | select(.id == \"$task_id\")] |
        .active_workflows = [.active_workflows[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"

    # Get agent for this task and update status
    local agent=$(jq -r ".completed_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")
    if [ -n "$agent" ] && [ "$agent" != "null" ]; then
        update_agent_status "$agent" "idle" "null"
    fi

    log_operation "TASK_COMPLETED" "ID: $task_id, Agent: $agent, Result: $result"


    # If auto-chain requested, suggest next task
    if [ "$auto_chain" = "true" ]; then
        suggest_next_task "$task_id" "$result"
    fi
}

# Function to fail task
fail_task() {
    local task_id="$1"
    local error="${2:-task failed}"
    local timestamp=$(get_timestamp)

    # Get task info before moving it
    local task_title=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .title" "$QUEUE_FILE")
    local enhancement_name="unknown"
    if [[ "$task_title" =~ ^"Analyze "(.+)" enhancement"$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"for "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    elif [[ "$task_title" =~ ^.*"of "(.+)$ ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
    fi

    local temp_file=$(mktemp)

    # Move task from active to failed
    jq "(.active_workflows[] | select(.id == \"$task_id\")) |= (.status = \"failed\" | .completed = \"$timestamp\" | .result = \"$error\") |
        .failed_tasks += [.active_workflows[] | select(.id == \"$task_id\")] |
        .active_workflows = [.active_workflows[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"

    # Get agent for this task and update status
    local agent=$(jq -r ".failed_tasks[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")
    update_agent_status "$agent" "idle" "null"

    log_operation "TASK_FAILED" "ID: $task_id, Agent: $agent, Error: $error"

}

# Function to cancel/remove task
cancel_task() {
    local task_id="$1"
    local reason="${2:-task cancelled}"

    local temp_file=$(mktemp)

    # Check if task is in pending_tasks
    local in_pending=$(jq -r ".pending_tasks[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    if [ -n "$in_pending" ]; then
        # Remove from pending tasks
        jq ".pending_tasks = [.pending_tasks[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"
        mv "$temp_file" "$QUEUE_FILE"
        log_operation "TASK_CANCELLED" "ID: $task_id, Status: pending, Reason: $reason"
        echo "Cancelled pending task: $task_id"
        return
    fi

    # Check if task is in active_workflows
    local in_active=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .id" "$QUEUE_FILE")
    if [ -n "$in_active" ]; then
        # Get agent for this task and update status
        local agent=$(jq -r ".active_workflows[] | select(.id == \"$task_id\") | .assigned_agent" "$QUEUE_FILE")

        # Remove from active workflows
        jq ".active_workflows = [.active_workflows[] | select(.id != \"$task_id\")]" "$QUEUE_FILE" > "$temp_file"
        mv "$temp_file" "$QUEUE_FILE"

        # Update agent status to idle
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

# Function to show queue status
show_status() {
    echo "=== 6502 Kernel Multi-Agent Queue Status ==="
    echo

    echo "📋 Agent Status:"
    jq -r '.agent_status | to_entries[] | "  • \(.key): \(.value.status) (Last: \(.value.last_activity // "never"))"' "$QUEUE_FILE"
    echo

    echo "⏳ Pending Tasks:"
    local pending_count=$(jq '.pending_tasks | length' "$QUEUE_FILE")
    if [ "$pending_count" -gt 0 ]; then
        jq -r '.pending_tasks[] | "  • [\(.priority)] \(.title) → \(.assigned_agent) (ID: \(.id))"' "$QUEUE_FILE"
    else
        echo "  No pending tasks"
    fi
    echo

    echo "🔄 Active Workflows:"
    local active_count=$(jq '.active_workflows | length' "$QUEUE_FILE")
    if [ "$active_count" -gt 0 ]; then
        jq -r '.active_workflows[] | "  • \(.title) → \(.assigned_agent) (Started: \(.started), ID: \(.id))"' "$QUEUE_FILE"
    else
        echo "  No active workflows"
    fi
    echo

    echo "✅ Recently Completed:"
    jq -r '.completed_tasks[-3:] | reverse | .[] | "  • \(.title) → \(.assigned_agent) (\(.completed))"' "$QUEUE_FILE" 2>/dev/null || echo "  No completed tasks"
}

# Function to start workflow chain
start_workflow() {
    local workflow_name="$1"
    local task_description="${2:-Workflow execution}"

    local workflow_exists=$(jq -r ".workflow_chains | has(\"$workflow_name\")" "$QUEUE_FILE")
    if [ "$workflow_exists" != "true" ]; then
        echo "Error: Workflow '$workflow_name' not found"
        return 1
    fi

    echo "Starting workflow: $workflow_name"

    # Get first step(s) of workflow
    local first_step=$(jq -r ".workflow_chains[\"$workflow_name\"].steps[0]" "$QUEUE_FILE")

    if [[ $first_step == \[* ]]; then
        # Parallel execution - multiple agents
        echo "Parallel execution detected"
        jq -r ".workflow_chains[\"$workflow_name\"].steps[0][]" "$QUEUE_FILE" | while read -r agent; do
            add_task "Workflow: $workflow_name" "$agent" "high" "" "$task_description"
        done
    else
        # Sequential execution - single agent
        add_task "Workflow: $workflow_name" "$first_step" "high" "" "$task_description"
    fi
}

# Main command processing
case "${1:-status}" in
    "add")
        if [ $# -lt 7 ]; then
            echo "Usage: $0 add <title> <agent> <priority> <task_type> <source_file> <description>"
            echo "Task types: analysis, technical_analysis, implementation, testing"
            exit 1
        fi
        add_task "$2" "$3" "$4" "$5" "$6" "$7"
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

        # Check for --auto-chain flag in any position
        auto_chain="false"
        if [[ "$*" == *"--auto-chain"* ]]; then
            auto_chain="true"
        fi

        # Extract result message (everything except --auto-chain)
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

    "workflow")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 workflow <workflow_name> [description]"
            exit 1
        fi
        start_workflow "$2" "${3:-Workflow execution}"
        ;;

    "status"|*)
        show_status
        ;;
esac