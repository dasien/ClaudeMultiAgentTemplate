#!/usr/bin/env bash
################################################################################
# Script Name: agent-commands.sh
# Description: Agent operations and invocation
#              Handles agent execution, template loading, prompt construction,
#              and agents.json generation from agent markdown files
# Author: Brian Gentry
# Created: 2025
#
# Usage: cmat agents <command> [OPTIONS]
#
# Commands:
#   list
#       List all available agents from agents.json
#   invoke <agent> <task_id> <source> <log_dir> <type> <desc> <auto_complete> <auto_chain>
#       Execute agent with specified task parameters
#   generate-json
#       Generate agents.json from agent markdown frontmatter
#
# Agent Invocation Process:
#   1. Load task template based on task type
#   2. Inject skills section for agent
#   3. Substitute template variables
#   4. Execute claude with constructed prompt
#   5. Log execution and capture status
#   6. Auto-complete if configured
#
# Template Variables:
#   ${agent}, ${agent_config}, ${source_file}, ${task_description},
#   ${task_id}, ${task_type}, ${root_document}, ${output_directory},
#   ${enhancement_name}, ${enhancement_dir}, ${success_statuses}, ${failure_pattern}
#
# Dependencies:
#   - common-commands.sh (sourced)
#   - skills-commands.sh (called for prompt building)
#   - queue-commands.sh (called for completion)
#   - workflow-commands.sh (called for contract queries)
#   - TASK_PROMPT_DEFAULTS.md (templates)
#   - claude (Claude Code CLI)
#   - jq (JSON processor)
#
# Exit Codes:
#   0 - Success
#   1 - Agent not found, template error, or execution failure
################################################################################

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-commands.sh"

#############################################################################
# HELPER FUNCTIONS
#############################################################################

# Helper function to get workflow state from task metadata
get_workflow_state() {
    local task_id="$1"

    # Get task from queue (check all queues: pending, active, completed)
    local task
    task=$(jq -r "
        (.pending_tasks[] // empty),
        (.active_workflows[] // empty),
        (.completed_tasks[] // empty) |
        select(.id == \"$task_id\")
    " "$QUEUE_FILE" 2>/dev/null)

    if [ -z "$task" ] || [ "$task" = "null" ]; then
        return 1
    fi

    # Extract workflow metadata
    local workflow_name workflow_step
    workflow_name=$(echo "$task" | jq -r '.metadata.workflow_name // empty')
    workflow_step=$(echo "$task" | jq -r '.metadata.workflow_step // empty')

    # Return workflow state as JSON
    if [ -n "$workflow_name" ]; then
        jq -n \
            --arg name "$workflow_name" \
            --arg step "$workflow_step" \
            '{
                workflow_name: $name,
                current_step_index: ($step | tonumber)
            }'
    fi
}

#############################################################################
# TEMPLATE OPERATIONS
#############################################################################

load_task_template() {
    local task_type="$1"

    if [ ! -f "$TEMPLATES_FILE" ]; then
        echo "Error: Task prompt template file not found: $TEMPLATES_FILE" >&2
        return 1
    fi

    # Extract template based on task type
    local template_content=""
    case "$task_type" in
        "analysis")
            template_content=$(awk '/^# ANALYSIS_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$TEMPLATES_FILE")
            ;;
        "technical_analysis")
            template_content=$(awk '/^# TECHNICAL_ANALYSIS_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$TEMPLATES_FILE")
            ;;
        "implementation")
            template_content=$(awk '/^# IMPLEMENTATION_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$TEMPLATES_FILE")
            ;;
        "testing")
            template_content=$(awk '/^# TESTING_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$TEMPLATES_FILE")
            ;;
        "integration")
            template_content=$(awk '/^# INTEGRATION_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$TEMPLATES_FILE")
            if [ -z "$template_content" ]; then
                template_content="You are the integration-coordinator agent. Process the task described in the source file and synchronize with external systems as appropriate."
            fi
            ;;
        "documentation")
            template_content=$(awk '/^# DOCUMENTATION_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' "$TEMPLATES_FILE")
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

#############################################################################
# AGENT INVOCATION
#############################################################################

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
    local agent_config="$AGENTS_DIR/${agent}.md"
    if [ ! -f "$agent_config" ]; then
        echo "Error: Agent config not found: $agent_config"
        return 1
    fi

    # Extract enhancement name
    local enhancement_name enhancement_dir
    enhancement_name=$(extract_enhancement_name "$source_file")
    enhancement_dir="enhancements/$enhancement_name"

    # Validate source file exists
    if [ ! -f "$source_file" ] && [ ! -d "$source_file" ]; then
        echo "Error: Source file or directory not found: $source_file"
        return 1
    fi

    # Create log file
    local log_dir log_file
    log_dir="${log_base_dir}/logs"
    mkdir -p "$log_dir"
    log_file="${log_dir}/${agent}_${task_id}_$(date +%Y%m%d_%H%M%S).log"

    # Load task template
    local template
    template=$(load_task_template "$task_type")
    if [ $? -ne 0 ]; then
        echo "Failed to load task template for type: $task_type"
        return 1
    fi

    # Build skills section
    local skills_section
    skills_section=$("$SCRIPT_DIR/skills-commands.sh" prompt "$agent")

    if [ -n "$skills_section" ]; then
        template="${template}${skills_section}"
    fi

    # Get workflow context to extract expected statuses and required output
    local workflow_state expected_statuses workflow_output
    workflow_state=$(get_workflow_state "$task_id" 2>/dev/null)

    if [ -n "$workflow_state" ] && [ "$workflow_state" != "null" ]; then
        # Get workflow name and current step
        local workflow_name current_step_index
        workflow_name=$(echo "$workflow_state" | jq -r '.workflow_name')
        current_step_index=$(echo "$workflow_state" | jq -r '.current_step_index')

        # Load workflow definition
        local workflow step
        workflow=$(jq -r ".workflows[\"$workflow_name\"]" "$WORKFLOW_TEMPLATES_FILE" 2>/dev/null)
        step=$(echo "$workflow" | jq -r ".steps[$current_step_index]" 2>/dev/null)

        if [ -n "$step" ] && [ "$step" != "null" ]; then
            # Get required output filename from workflow step
            workflow_output=$(echo "$step" | jq -r '.required_output // "output.md"')

            # Extract expected statuses from on_status keys
            expected_statuses=$(echo "$step" | jq -r '.on_status | keys | map("- `" + . + "`") | join("\n")')
        fi
    fi

    # If no workflow context or no expected statuses, use generic message
    if [ -z "$expected_statuses" ]; then
        expected_statuses="(No workflow-defined statuses - output any appropriate status)"
    fi

    # Determine input instruction based on source_file type
    local input_instruction
    if [ -f "$source_file" ]; then
        input_instruction="Read and process this file: $source_file"
    elif [ -d "$source_file" ]; then
        input_instruction="Read and process all files in this directory: $source_file"
    else
        input_instruction="Input: $source_file"
    fi

    # Get required output filename from workflow or use default
    local required_output_filename="${workflow_output:-output.md}"

    # Substitute variables
    local prompt="$template"
    prompt="${prompt//\$\{agent\}/$agent}"
    prompt="${prompt//\$\{agent_config\}/$agent_config}"
    prompt="${prompt//\$\{source_file\}/$source_file}"
    prompt="${prompt//\$\{task_description\}/$task_description}"
    prompt="${prompt//\$\{task_id\}/$task_id}"
    prompt="${prompt//\$\{task_type\}/$task_type}"
    prompt="${prompt//\$\{enhancement_name\}/$enhancement_name}"
    prompt="${prompt//\$\{enhancement_dir\}/$enhancement_dir}"
    prompt="${prompt//\$\{input_instruction\}/$input_instruction}"
    prompt="${prompt//\$\{required_output_filename\}/$required_output_filename}"
    prompt="${prompt//\$\{expected_statuses\}/$expected_statuses}"

    local start_time start_timestamp
    start_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    start_timestamp=$(date +%s)

    # Log execution start
    echo "=== Starting Agent Execution ===" | tee "$log_file"
    echo "Start Time: $start_time" | tee -a "$log_file"
    echo "Agent: $agent" | tee -a "$log_file"
    echo "Task ID: $task_id" | tee -a "$log_file"
    echo "Source File: $source_file" | tee -a "$log_file"
    echo "Enhancement: $enhancement_name" | tee -a "$log_file"
    echo "Required Output: $required_output_filename" | tee -a "$log_file"
    echo "Log: $log_file" | tee -a "$log_file"
    echo "Cost Tracking: ENABLED (SessionEnd hook)" | tee -a "$log_file"
    echo "" | tee -a "$log_file"

    # Log the complete prompt sent to agent
    {
        echo "====================================================================="
        echo "PROMPT SENT TO AGENT"
        echo "====================================================================="
        echo ""
        echo "$prompt"
        echo ""
        echo "====================================================================="
        echo "END OF PROMPT"
        echo "====================================================================="
        echo ""
        echo ""
    } >> "$log_file"

    # Set context for SessionEnd hook (cost tracking)
    export CMAT_CURRENT_TASK_ID="$task_id"
    export CMAT_CURRENT_LOG_FILE="$log_file"
    export CMAT_AGENT="$agent"
    export CMAT_ENHANCEMENT="$enhancement_name"

    # Invoke Claude Code with bypass permissions in background to capture PID
    claude --permission-mode bypassPermissions "$prompt" >> "$log_file" 2>&1 &

    local claude_pid=$!

    # Store PID in task metadata immediately so it can be killed if cancelled
    "$SCRIPT_DIR/queue-commands.sh" metadata "$task_id" "process_pid" "$claude_pid" 2>/dev/null || true

    # Wait for the claude process to complete
    wait $claude_pid
    local exit_code=$?

    # Unset context after execution (SessionEnd hook will have already run)
    unset CMAT_CURRENT_TASK_ID CMAT_CURRENT_LOG_FILE CMAT_AGENT CMAT_ENHANCEMENT

    local end_time end_timestamp duration
    end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    end_timestamp=$(date +%s)
    duration=$((end_timestamp - start_timestamp))

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

    # Look for common status patterns: READY_FOR_*, *_COMPLETE, BLOCKED:
    status=$(grep -E "(READY_FOR_[A-Z_]+|[A-Z_]+_COMPLETE|BLOCKED:)" "$log_file" | tail -1 | grep -oE "(READY_FOR_[A-Z_]+|[A-Z_]+_COMPLETE|BLOCKED:[^*]*)" | head -1)

    if [ -n "$status" ]; then
        echo "Exit Status: $status" >> "$log_file"
        echo "Exit Status: $status"
    else
        echo "Exit Status: UNKNOWN" >> "$log_file"
        echo "Exit Status: UNKNOWN"
    fi
    echo "" >> "$log_file"
    echo ""

    # Extract status for auto-completion
    status=$(tail -10 "$log_file" | grep "^Exit Status:" | cut -d' ' -f3-)

    if [ -n "$status" ]; then
        echo "Detected Status: $status" >> "$log_file"
        echo "" >> "$log_file"

        if [ "$auto_complete" = "true" ]; then
            echo "Auto-completing task (non-interactive mode)" >> "$log_file"
            "$SCRIPT_DIR/queue-commands.sh" complete "$task_id" "$status" "$auto_chain"
        else
            echo "Auto-completing task with status: $status"
            echo -n "Proceed? [Y/n]: "
            read -r proceed

            if [[ ! "$proceed" =~ ^[Nn]$ ]]; then
                "$SCRIPT_DIR/queue-commands.sh" complete "$task_id" "$status" "$auto_chain"
            else
                echo "Task completion cancelled. Complete manually with:"
                echo "  cmat queue complete $task_id '$status' --auto-chain"
            fi
        fi
    else
        echo "Warning: Could not extract completion status from agent output"
        echo "Review log file: $log_file"
        echo "Complete manually with:"
        echo "  cmat queue complete $task_id '<STATUS>' --auto-chain"
    fi

    return $exit_code
}

list_agents() {
    local agents_file="$AGENTS_DIR/agents.json"

    if [ ! -f "$agents_file" ]; then
        echo "Error: agents.json not found: $agents_file"
        return 1
    fi

    jq '.' "$agents_file"
}

generate_agents_json() {
    local agents_file="$AGENTS_DIR/agents.json"

    # Function to convert YAML frontmatter to JSON
    yaml_to_json() {
        local filename="$1"
        local name="" description="" tools_json="[]" skills_json="[]"

        while IFS= read -r line; do
            # Extract tools array
            if [[ "$line" =~ ^tools:[[:space:]]*\[.*\][[:space:]]*$ ]]; then
                tools_json=$(echo "$line" | sed 's/^tools:[[:space:]]*//')
                continue
            fi

            # Extract skills array
            if [[ "$line" =~ ^skills:[[:space:]]*\[.*\][[:space:]]*$ ]]; then
                skills_json=$(echo "$line" | sed 's/^skills:[[:space:]]*//')
                continue
            fi

            # Extract key:value pairs
            if [[ "$line" =~ ^[[:space:]]*([^:]+):[[:space:]]*(.*)[[:space:]]*$ ]]; then
                key="${BASH_REMATCH[1]}"
                value="${BASH_REMATCH[2]}"
                value=$(echo "$value" | sed 's/^["'\'']\(.*\)["'\'']$/\1/')

                case "$key" in
                    name) name="$value" ;;
                    description) description="$value" ;;
                esac
            fi
        done

        cat <<EOF
  {
    "name": "$name",
    "agent-file": "$filename",
    "tools": $tools_json,
    "skills": $skills_json,
    "description": "$description"
  }
EOF
    }

    # Generate JSON
    echo '{"agents":[' > "$agents_file"

    local first=true
    for agent_md in "$AGENTS_DIR"/*.md; do
        [ -f "$agent_md" ] || continue

        if grep -q "^---$" "$agent_md"; then
            if [ "$first" = false ]; then
                echo ',' >> "$agents_file"
            fi
            first=false

            local filename
            filename=$(basename "$agent_md" .md)

            awk '/^---$/{f=!f;next} f' "$agent_md" | yaml_to_json "$filename" >> "$agents_file"
        fi
    done

    echo ']}' >> "$agents_file"

    echo "✓ Generated $agents_file"
}

#############################################################################
# COMMAND ROUTER
#############################################################################

case "${1:-list}" in
    "list")
        list_agents
        ;;

    "invoke")
        if [ $# -lt 8 ]; then
            echo "Usage: cmat agents invoke <agent> <task_id> <source> <log_dir> <type> <desc> <auto_complete> <auto_chain>"
            exit 1
        fi
        invoke_agent "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9"
        ;;

    "generate-json")
        generate_agents_json
        ;;

    *)
        echo "Unknown agents command: ${1:-}" >&2
        echo "Usage: cmat agents <list|invoke|generate-json>" >&2
        exit 1
        ;;
esac