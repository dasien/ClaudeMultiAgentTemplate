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

# Core agent execution logic shared by both invoke and invoke-direct
# This function contains all the common prompt building and Claude execution logic
# All context should be passed in as parameters - this function should not derive context
execute_agent_core() {
    local agent="$1"
    local agent_config="$2"
    local input_file="$3"
    local output_dir="$4"
    local task_description="$5"
    local log_file="$6"
    local task_type="$7"
    local task_id="$8"
    local enhancement_name="$9"
    local enhancement_dir="${10}"
    local required_output_filename="${11}"
    local expected_statuses="${12}"

    # Load task template
    local template
    template=$(load_task_template "$task_type")
    if [ $? -ne 0 ]; then
        echo "Failed to load task template for type: $task_type" >&2
        return 1
    fi

    # Build skills section
    local skills_section
    skills_section=$("$SCRIPT_DIR/skills-commands.sh" prompt "$agent")
    if [ -n "$skills_section" ]; then
        template="${template}${skills_section}"
    fi

    # Determine input instruction
    local input_instruction
    if [ -z "$input_file" ] || [ "$input_file" = "null" ]; then
        input_instruction="Work from the task description provided."
    elif [ -f "$input_file" ]; then
        input_instruction="Read and process this file: $input_file"
    elif [ -d "$input_file" ]; then
        input_instruction="Read and process all files in this directory: $input_file"
    else
        input_instruction="Input: $input_file"
    fi

    # Build prompt with workflow context (passed as parameters)
    local prompt="$template"

    # Substitute variables in template
    prompt="${prompt//\$\{agent\}/$agent}"
    prompt="${prompt//\$\{agent_config\}/$agent_config}"
    prompt="${prompt//\$\{source_file\}/$input_file}"
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
    echo "Input: $input_file" | tee -a "$log_file"
    echo "Output: $output_dir" | tee -a "$log_file"
    echo "Log: $log_file" | tee -a "$log_file"
    echo "" | tee -a "$log_file"

    # Log the complete prompt
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

    # Execute claude with bypass permissions
    claude --permission-mode bypassPermissions "$prompt" >> "$log_file" 2>&1
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

    return $exit_code
}

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
    enhancement_name=$(extract_enhancement_name "$source_file" "$task_id")
    enhancement_dir="enhancements/$enhancement_name"

    # Set output directory for agent outputs
    local output_dir="$enhancement_dir/$agent"
    mkdir -p "$output_dir"

    # Validate source file exists (optional for ad-hoc tasks)
    if [ -n "$source_file" ] && [ "$source_file" != "null" ]; then
        if [ ! -f "$source_file" ] && [ ! -d "$source_file" ]; then
            echo "Error: Source file or directory not found: $source_file"
            return 1
        fi
    else
        echo "Note: No source file specified - running as ad-hoc task with enhancement dir: $enhancement_dir"
        source_file=""
    fi

    # Create log file
    local log_dir log_file
    log_dir="${log_base_dir}/logs"
    mkdir -p "$log_dir"
    log_file="${log_dir}/${agent}_${task_id}_$(date +%Y%m%d_%H%M%S).log"

    # Set timestamp for start.
    local start_timestamp
    start_timestamp=$(date +%s)

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

    # Get required output filename from workflow or use default
    local required_output_filename="${workflow_output:-output.md}"

    # Execute agent in background to capture PID (for cancellation support)
    execute_agent_core "$agent" "$agent_config" "$source_file" "$output_dir" "$task_description" \
                       "$log_file" "$task_type" "$task_id" "$enhancement_name" "$enhancement_dir" \
                       "$required_output_filename" "$expected_statuses" &

    # Get the process id.
    local claude_pid=$!

    # Store PID in task metadata immediately so it can be killed if cancelled
    "$SCRIPT_DIR/queue-commands.sh" metadata "$task_id" "process_pid" "$claude_pid" 2>/dev/null || true

    # Wait for the claude process to complete
    wait $claude_pid
    local exit_code=$?

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

# This command executes an agent synchronously without task queue integration.
# It is specifically designed for UI-driven operations like enhancement creation,
# agent creation, and task planning where the output is immediately consumed
# by the UI rather than being part of a workflow.
#
# Key differences from invoke:
#   - Synchronous execution (blocks until complete)
#   - No task queue integration
#   - No PID tracking or cancellation support
#   - No status extraction or auto-completion
#   - No cost tracking environment variables
#   - Custom output directory (not enhancement structure)
#   - Logs to main logs directory
#
# This is NOT intended for:
#   - Workflow execution
#   - Background task processing
#   - Operations requiring cancellation
#   - Operations requiring status tracking
#
invoke_agent_direct() {
    local agent="$1"
    local input_file="$2"
    local output_dir="$3"
    local task_description="${4:-UI-invoked task}"
    local task_type="${5:-analysis}"

    # Validate agent exists
    local agent_config="$AGENTS_DIR/${agent}.md"
    if [ ! -f "$agent_config" ]; then
        echo "Error: Agent config not found: $agent_config" >&2
        return 1
    fi

    # Create output directory
    mkdir -p "$output_dir"

    # Create log file in main logs directory (not enhancement-specific)
    local log_file="$LOGS_DIR/ui_agent_${agent}_$(date +%Y%m%d_%H%M%S).log"

    # Generate simple task ID for logging purposes only
    local task_id="ui_${agent}_$(date +%Y%m%d_%H%M%S)"

    # For UI invocations, extract enhancement name from output_dir if possible
    # Output dir is typically enhancements/.staging/{name} for enhancement creation
    local enhancement_name enhancement_dir
    if [[ "$output_dir" =~ enhancements/([^/]+) ]]; then
        enhancement_name="${BASH_REMATCH[1]}"
        # Enhancement dir is the output dir for direct invocations (staging or final)
        enhancement_dir="$output_dir"
    else
        # Fallback for non-enhancement operations
        enhancement_name="ui-operation"
        enhancement_dir="$output_dir"
    fi

    # Direct invocations have no workflow context - use defaults
    local required_output_filename="output.md"
    local expected_statuses="(No workflow-defined statuses - output any appropriate status)"

    # Execute agent core (synchronous - no background process)
    execute_agent_core "$agent" "$agent_config" "$input_file" "$output_dir" "$task_description" \
                       "$log_file" "$task_type" "$task_id" "$enhancement_name" "$enhancement_dir" \
                       "$required_output_filename" "$expected_statuses"
    local exit_code=$?

    # Simple output: return output directory on success
    if [ $exit_code -eq 0 ]; then
        echo "$output_dir"
    else
        echo "Error: Agent execution failed (exit code: $exit_code). See log: $log_file" >&2
    fi

    return $exit_code
}

list_agents() {
    if [ ! -f "$AGENTS_FILE" ]; then
        echo "Error: agents.json not found: $AGENTS_FILE"
        return 1
    fi

    jq '.' "$AGENTS_FILE"
}

generate_agents_json() {
    # Function to convert YAML frontmatter to JSON
    yaml_to_json() {
        local filename="$1"
        local name=""
        local description=""
        local role=""
        local tools_json="[]"
        local skills_json="[]"
        local validations_json="{}"
        local in_validations=false

        # Parse YAML frontmatter
        while IFS= read -r line; do
            # Check if we're entering validations block
            if [[ "$line" =~ ^validations:[[:space:]]*$ ]]; then
                in_validations=true
                continue
            fi

            # If we hit another top-level key, exit validations block
            if [[ "$line" =~ ^[a-z_]+:[[:space:]] ]] && [ "$in_validations" = true ]; then
                in_validations=false
            fi

            # Parse validation fields (indented lines)
            if [ "$in_validations" = true ] && [[ "$line" =~ ^[[:space:]]+([^:]+):[[:space:]]*(.*) ]]; then
                key="${BASH_REMATCH[1]}"
                value="${BASH_REMATCH[2]}"

                # Handle different value types
                if [[ "$value" =~ ^(true|false)$ ]]; then
                    # Boolean
                    validations_json=$(echo "$validations_json" | jq --arg k "$key" --argjson v "$value" '. + {($k): $v}')
                elif [[ "$value" =~ ^[0-9]+$ ]]; then
                    # Number
                    validations_json=$(echo "$validations_json" | jq --arg k "$key" --argjson v "$value" '. + {($k): $v}')
                elif [[ "$value" =~ ^\[.*\]$ ]]; then
                    # Array
                    validations_json=$(echo "$validations_json" | jq --arg k "$key" --argjson v "$value" '. + {($k): $v}')
                else
                    # String (remove quotes if present)
                    value=$(echo "$value" | sed 's/^["'\'']\(.*\)["'\'']$/\1/')
                    validations_json=$(echo "$validations_json" | jq --arg k "$key" --arg v "$value" '. + {($k): $v}')
                fi
                continue
            fi

            # Check if this is the tools line with array
            if [[ "$line" =~ ^tools:[[:space:]]*\[.*\][[:space:]]*$ ]]; then
                # Extract array directly
                tools_json=$(echo "$line" | sed 's/^tools:[[:space:]]*//')
                continue
            fi

            # Check if this is the skills line with array
            if [[ "$line" =~ ^skills:[[:space:]]*\[.*\][[:space:]]*$ ]]; then
                # Extract array directly
                skills_json=$(echo "$line" | sed 's/^skills:[[:space:]]*//')
                continue
            fi

            # Check for key: value format (top-level only)
            if [[ "$line" =~ ^[[:space:]]*([^:]+):[[:space:]]*(.*)[[:space:]]*$ ]] && [ "$in_validations" = false ]; then
                key="${BASH_REMATCH[1]}"
                value="${BASH_REMATCH[2]}"

                # Remove quotes from value if present
                value=$(echo "$value" | sed 's/^["'\'']\(.*\)["'\'']$/\1/')

                case "$key" in
                    name)
                        name="$value"
                        ;;
                    description)
                        description="$value"
                        ;;
                    role)
                        role="$value"
                        ;;
                esac
            fi
        done

        # If validations is empty, set default
        if [ "$validations_json" = "{}" ]; then
            validations_json='{"metadata_required": true}'
        fi

        # Output JSON with role and validations
        cat <<EOF
  {
    "name": "$name",
    "agent-file": "$filename",
    "role": "$role",
    "tools": $tools_json,
    "skills": $skills_json,
    "description": "$description",
    "validations": $validations_json
  }
EOF
    }

    # Start JSON array
    echo '{"agents":[' > "$AGENTS_FILE"

    first=true
    for agent_file in "$AGENTS_DIR"/*.md; do
        [ -f "$agent_file" ] || continue

        # Check if file starts with frontmatter (--- on line 1)
        if head -1 "$agent_file" | grep -q "^---$"; then
            # Add comma between agents
            if [ "$first" = false ]; then
                echo ',' >> "$AGENTS_FILE"
            fi
            first=false

            # Get filename without path and extension
            filename=$(basename "$agent_file" .md)

            # Extract frontmatter (only between FIRST pair of --- markers)
            # This awk stops after finding the second ---, preventing extraction of example frontmatter
            awk '/^---$/ && NR==1 {next} /^---$/ && NR>1 {exit} {print}' "$agent_file" | yaml_to_json "$filename" >> "$AGENTS_FILE"
        fi
    done

    # Close JSON array
    echo ']}' >> "$AGENTS_FILE"

    echo "✓ Generated $AGENTS_FILE"
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

    "invoke-direct")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat agents invoke-direct <agent> <input_file> <output_dir> [description] [type]"
            echo ""
            echo "Direct agent invocation for UI operations (no task queue integration)."
            echo "This command is intended for UI-driven operations only."
            exit 1
        fi
        invoke_agent_direct "$2" "$3" "$4" "${5:-UI-invoked task}" "${6:-analysis}"
        ;;

    "generate-json")
        generate_agents_json
        ;;

    *)
        echo "Unknown agents command: ${1:-}" >&2
        echo "Usage: cmat agents <list|invoke|invoke-direct|generate-json>" >&2
        exit 1
        ;;
esac