#!/usr/bin/env bash
################################################################################
# Script Name: workflow-commands.sh
# Description: Workflow orchestration and template management
#              Updated for workflow-based orchestration (v5.0.0)
################################################################################

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-commands.sh"

# Workflow templates file
readonly WORKFLOW_TEMPLATES_FILE="$PROJECT_ROOT/.claude/queues/workflow_templates.json"

#############################################################################
# VALIDATION OPERATIONS
#############################################################################

validate_agent_outputs() {
    local agent="$1"
    local enhancement_dir="$2"
    local required_output_filename="$3"

    # Get agent definition from agents.json
    local agent_def
    agent_def=$(jq -r ".agents[] | select(.[\"agent-file\"] == \"$agent\")" "$AGENTS_DIR/agents.json")

    if [ -z "$agent_def" ] || [ "$agent_def" = "null" ]; then
        echo "❌ Agent not found in agents.json: $agent"
        return 1
    fi

    # Check if metadata is required for this agent
    local metadata_required
    metadata_required=$(echo "$agent_def" | jq -r '.validations.metadata_required // true')

    local required_dir="$enhancement_dir/$agent/required_output"
    local required_file="$required_dir/$required_output_filename"

    # Check required directory exists
    if [ ! -d "$required_dir" ]; then
        echo "❌ Required output directory missing: $required_dir"
        return 1
    fi

    # Check required file exists
    if [ ! -f "$required_file" ]; then
        echo "❌ Required output file missing: $required_file"
        return 1
    fi

    # Check metadata header if required
    if [ "$metadata_required" = "true" ]; then
        if ! grep -q "^---$" "$required_file"; then
            echo "❌ Missing metadata header in: $required_file"
            return 1
        fi

        # Validate required metadata fields
        local missing_fields=()
        grep -q "^enhancement:" "$required_file" || missing_fields+=("enhancement")
        grep -q "^agent:" "$required_file" || missing_fields+=("agent")
        grep -q "^task_id:" "$required_file" || missing_fields+=("task_id")
        grep -q "^timestamp:" "$required_file" || missing_fields+=("timestamp")
        grep -q "^status:" "$required_file" || missing_fields+=("status")

        if [ ${#missing_fields[@]} -gt 0 ]; then
            echo "❌ Metadata missing required fields: ${missing_fields[*]}"
            return 1
        fi
    fi

    echo "✅ Output validation passed: $required_file"
    return 0
}

agent_exists() {
    local agent="$1"

    local exists
    exists=$(jq -r ".agents[] | select(.[\"agent-file\"] == \"$agent\") | .name" "$AGENTS_DIR/agents.json")

    if [ -z "$exists" ]; then
        return 1
    fi

    return 0
}

get_task_type_for_agent() {
    local agent="$1"

    local agent_def
    agent_def=$(jq -r ".agents[] | select(.[\"agent-file\"] == \"$agent\")" "$AGENTS_DIR/agents.json")

    if [ -z "$agent_def" ] || [ "$agent_def" = "null" ]; then
        echo "unknown"
        return 0
    fi

    local role
    role=$(echo "$agent_def" | jq -r '.role // "unknown"')

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

#############################################################################
# TEMPLATE MANAGEMENT
#############################################################################

create_workflow_template() {
    local template_name="$1"
    local description="$2"

    if [ ! -f "$WORKFLOW_TEMPLATES_FILE" ]; then
        echo "Error: Workflow templates file not found: $WORKFLOW_TEMPLATES_FILE" >&2
        return 1
    fi

    # Check if template already exists
    local exists
    exists=$(jq -r ".workflows | has(\"$template_name\")" "$WORKFLOW_TEMPLATES_FILE")
    if [ "$exists" = "true" ]; then
        echo "❌ Error: Template '$template_name' already exists" >&2
        return 1
    fi

    local timestamp
    timestamp=$(get_timestamp)

    # Create template object with empty steps array
    local temp_file
    temp_file=$(mktemp)

    jq --arg name "$template_name" \
       --arg desc "$description" \
       --arg ts "$timestamp" \
       '.workflows[$name] = {
           name: $desc,
           description: $desc,
           steps: []
       }' "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"

    mv "$temp_file" "$WORKFLOW_TEMPLATES_FILE"

    log_operation "TEMPLATE_CREATED" "Template: $template_name"
    echo "✅ Created workflow template: $template_name"
    return 0
}

list_workflow_templates() {
    if [ ! -f "$WORKFLOW_TEMPLATES_FILE" ]; then
        echo "Error: Workflow templates file not found: $WORKFLOW_TEMPLATES_FILE" >&2
        return 1
    fi

    # Display templates with name, description, and step count
    jq -r '.workflows | to_entries[] |
        "\(.key) - \(.value.description) (\(.value.steps | length) steps)"' \
        "$WORKFLOW_TEMPLATES_FILE"
}

show_workflow_template() {
    local template_name="$1"

    if [ ! -f "$WORKFLOW_TEMPLATES_FILE" ]; then
        echo "Error: Workflow templates file not found: $WORKFLOW_TEMPLATES_FILE" >&2
        return 1
    fi

    # Check if template exists
    local exists
    exists=$(jq -r ".workflows | has(\"$template_name\")" "$WORKFLOW_TEMPLATES_FILE")
    if [ "$exists" != "true" ]; then
        echo "❌ Error: Template '$template_name' not found" >&2
        return 1
    fi

    # Get template details
    local template
    template=$(jq -r ".workflows[\"$template_name\"]" "$WORKFLOW_TEMPLATES_FILE")

    local description steps_count
    description=$(echo "$template" | jq -r '.description')
    steps_count=$(echo "$template" | jq -r '.steps | length')

    echo "Template: $template_name"
    echo "Description: $description"
    echo "Steps: $steps_count"
    echo ""
    echo "Workflow:"

    if [ "$steps_count" -eq 0 ]; then
        echo "  (no steps defined)"
    else
        # Display steps with transitions
        local i=0
        while [ $i -lt $steps_count ]; do
            local step agent input output
            step=$(echo "$template" | jq -r ".steps[$i]")
            agent=$(echo "$step" | jq -r '.agent')
            input=$(echo "$step" | jq -r '.input')
            output=$(echo "$step" | jq -r '.required_output')

            echo "  Step $i: $agent"
            echo "    Input: $input"
            echo "    Output: $output"

            # Show transitions
            local statuses
            statuses=$(echo "$step" | jq -r '.on_status | keys[]' 2>/dev/null)
            if [ -n "$statuses" ]; then
                echo "    Transitions:"
                while IFS= read -r status; do
                    local next_step auto_chain
                    next_step=$(echo "$step" | jq -r ".on_status[\"$status\"].next_step // null")
                    auto_chain=$(echo "$step" | jq -r ".on_status[\"$status\"].auto_chain // false")
                    echo "      $status → ${next_step:-END} (auto: $auto_chain)"
                done <<< "$statuses"
            fi
            echo ""
            ((i++))
        done
    fi
}

delete_workflow_template() {
    local template_name="$1"

    if [ ! -f "$WORKFLOW_TEMPLATES_FILE" ]; then
        echo "Error: Workflow templates file not found: $WORKFLOW_TEMPLATES_FILE" >&2
        return 1
    fi

    # Check if template exists
    local exists
    exists=$(jq -r ".workflows | has(\"$template_name\")" "$WORKFLOW_TEMPLATES_FILE")
    if [ "$exists" != "true" ]; then
        echo "❌ Error: Template '$template_name' not found" >&2
        return 1
    fi

    local temp_file
    temp_file=$(mktemp)

    jq --arg name "$template_name" \
       'del(.workflows[$name])' "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"

    mv "$temp_file" "$WORKFLOW_TEMPLATES_FILE"

    log_operation "TEMPLATE_DELETED" "Template: $template_name"
    echo "✅ Deleted workflow template: $template_name"
    return 0
}

#############################################################################
# STEP MANAGEMENT
#############################################################################

add_step_to_template() {
    local template_name="$1"
    local agent="$2"
    local input="$3"
    local output="$4"
    local position="${5:-}"

    # Validate agent exists
    if ! agent_exists "$agent"; then
        echo "❌ Error: Agent '$agent' not found in agents.json" >&2
        return 1
    fi

    # Build step object
    local step_object
    step_object=$(jq -n \
        --arg agent "$agent" \
        --arg input "$input" \
        --arg output "$output" \
        '{
            agent: $agent,
            input: $input,
            required_output: $output,
            on_status: {}
        }')

    # Add to workflow template
    local temp_file
    temp_file=$(mktemp)

    if [ -n "$position" ]; then
        jq --arg name "$template_name" \
           --argjson step "$step_object" \
           --argjson pos "$position" \
           '.workflows[$name].steps |= (.[0:$pos] + [$step] + .[$pos:])' \
           "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"
    else
        jq --arg name "$template_name" \
           --argjson step "$step_object" \
           '.workflows[$name].steps += [$step]' \
           "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"
    fi

    mv "$temp_file" "$WORKFLOW_TEMPLATES_FILE"

    log_operation "TEMPLATE_STEP_ADDED" "Template: $template_name, Agent: $agent"
    echo "✅ Added step: $agent"
    echo "   Input: $input"
    echo "   Output: $output"
}

edit_step() {
    local template_name="$1"
    local step_number="$2"
    local new_input="${3:-}"
    local new_output="${4:-}"

    local step_index=$((step_number - 1))

    if [ -z "$new_input" ] && [ -z "$new_output" ]; then
        echo "❌ Error: Must provide at least input or output to edit" >&2
        return 1
    fi

    local temp_file
    temp_file=$(mktemp)

    # Build jq update expression
    local jq_updates=".workflows[\"$template_name\"].steps[$step_index]"
    if [ -n "$new_input" ]; then
        jq_updates="$jq_updates | .input = \"$new_input\""
    fi
    if [ -n "$new_output" ]; then
        jq_updates="$jq_updates | .required_output = \"$new_output\""
    fi

    # Apply update
    local updated_step
    updated_step=$(jq "$jq_updates" "$WORKFLOW_TEMPLATES_FILE")

    # Replace entire file with update
    jq --argjson updated "$updated_step" \
       --arg name "$template_name" \
       --argjson idx "$step_index" \
       '.workflows[$name].steps[$idx] = $updated' \
       "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"

    mv "$temp_file" "$WORKFLOW_TEMPLATES_FILE"

    log_operation "TEMPLATE_STEP_EDITED" "Template: $template_name, Step: $step_number"
    echo "✅ Updated step $step_number"
}

remove_step_from_template() {
    local template_name="$1"
    local step_number="$2"

    if [ ! -f "$WORKFLOW_TEMPLATES_FILE" ]; then
        echo "Error: Workflow templates file not found: $WORKFLOW_TEMPLATES_FILE" >&2
        return 1
    fi

    # Validate step number
    if ! [[ "$step_number" =~ ^[0-9]+$ ]]; then
        echo "❌ Error: Step number must be a positive integer" >&2
        return 1
    fi

    # Get steps count
    local steps_count
    steps_count=$(jq -r ".workflows[\"$template_name\"].steps | length" "$WORKFLOW_TEMPLATES_FILE")

    # Convert to 0-indexed
    local index=$((step_number - 1))

    if [ "$index" -lt 0 ] || [ "$index" -ge "$steps_count" ]; then
        echo "❌ Error: Step number $step_number is out of range (1-$steps_count)" >&2
        return 1
    fi

    # Get agent name before removing (for logging)
    local agent
    agent=$(jq -r ".workflows[\"$template_name\"].steps[$index].agent" "$WORKFLOW_TEMPLATES_FILE")

    local temp_file
    temp_file=$(mktemp)

    jq --arg name "$template_name" \
       --argjson idx "$index" \
       '.workflows[$name].steps |= del(.[$idx])' \
       "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"

    mv "$temp_file" "$WORKFLOW_TEMPLATES_FILE"

    log_operation "TEMPLATE_STEP_REMOVED" "Template: $template_name, Step: $step_number ($agent)"
    echo "✅ Removed step $step_number ($agent) from template"
    return 0
}

list_template_steps() {
    local template_name="$1"

    if [ ! -f "$WORKFLOW_TEMPLATES_FILE" ]; then
        echo "Error: Workflow templates file not found: $WORKFLOW_TEMPLATES_FILE" >&2
        return 1
    fi

    # Check if template exists
    local exists
    exists=$(jq -r ".workflows | has(\"$template_name\")" "$WORKFLOW_TEMPLATES_FILE")
    if [ "$exists" != "true" ]; then
        echo "❌ Error: Template '$template_name' not found" >&2
        return 1
    fi

    echo "Steps in '$template_name':"

    local steps_count
    steps_count=$(jq -r ".workflows[\"$template_name\"].steps | length" "$WORKFLOW_TEMPLATES_FILE")

    if [ "$steps_count" -eq 0 ]; then
        echo "  (no steps defined)"
        return 0
    fi

    # List steps with numbers (0-indexed to match array)
    local i=0
    while [ $i -lt $steps_count ]; do
        local agent
        agent=$(jq -r ".workflows[\"$template_name\"].steps[$i].agent" "$WORKFLOW_TEMPLATES_FILE")
        echo "  $i. $agent"
        ((i++))
    done
}

show_template_step() {
    local template_name="$1"
    local step_number="$2"

    if [ ! -f "$WORKFLOW_TEMPLATES_FILE" ]; then
        echo "Error: Workflow templates file not found: $WORKFLOW_TEMPLATES_FILE" >&2
        return 1
    fi

    # Check if template exists
    local exists
    exists=$(jq -r ".workflows | has(\"$template_name\")" "$WORKFLOW_TEMPLATES_FILE")
    if [ "$exists" != "true" ]; then
        echo "❌ Error: Template '$template_name' not found" >&2
        return 1
    fi

    # Validate step number
    if ! [[ "$step_number" =~ ^[0-9]+$ ]]; then
        echo "❌ Error: Step number must be a non-negative integer" >&2
        return 1
    fi

    # Get steps count
    local steps_count
    steps_count=$(jq -r ".workflows[\"$template_name\"].steps | length" "$WORKFLOW_TEMPLATES_FILE")

    if [ "$step_number" -lt 0 ] || [ "$step_number" -ge "$steps_count" ]; then
        echo "❌ Error: Step number $step_number is out of range (0-$((steps_count-1)))" >&2
        return 1
    fi

    # Get step details
    local step
    step=$(jq -r ".workflows[\"$template_name\"].steps[$step_number]" "$WORKFLOW_TEMPLATES_FILE")

    echo "Step $step_number of '$template_name':"
    echo "$step" | jq '.'
}

#############################################################################
# TRANSITION MANAGEMENT
#############################################################################

add_transition() {
    local template_name="$1"
    local step_number="$2"
    local status_code="$3"
    local next_step="$4"
    local auto_chain="${5:-true}"

    local step_index="$step_number"

    local temp_file
    temp_file=$(mktemp)

    jq --arg name "$template_name" \
       --argjson idx "$step_index" \
       --arg status "$status_code" \
       --arg next "$next_step" \
       --arg auto "$auto_chain" \
       '.workflows[$name].steps[$idx].on_status[$status] = {
           next_step: ($next | if . == "null" then null else . end),
           auto_chain: ($auto == "true")
       }' "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"

    mv "$temp_file" "$WORKFLOW_TEMPLATES_FILE"

    log_operation "TRANSITION_ADDED" "Template: $template_name, Step: $step_number, Status: $status_code → $next_step"
    echo "✅ Added transition: $status_code → ${next_step:-END} (auto: $auto_chain)"
}

remove_transition() {
    local template_name="$1"
    local step_number="$2"
    local status_code="$3"

    local step_index="$step_number"

    local temp_file
    temp_file=$(mktemp)

    jq --arg name "$template_name" \
       --argjson idx "$step_index" \
       --arg status "$status_code" \
       'del(.workflows[$name].steps[$idx].on_status[$status])' \
       "$WORKFLOW_TEMPLATES_FILE" > "$temp_file"

    mv "$temp_file" "$WORKFLOW_TEMPLATES_FILE"

    log_operation "TRANSITION_REMOVED" "Template: $template_name, Step: $step_number, Status: $status_code"
    echo "✅ Removed transition: $status_code"
}

list_transitions() {
    local template_name="$1"
    local step_number="$2"

    local step_index="$step_number"

    echo "Transitions for step $step_number:"
    jq -r --arg name "$template_name" \
          --argjson idx "$step_index" \
          '.workflows[$name].steps[$idx].on_status | to_entries[] |
           "  \(.key) → \(.value.next_step // "END") (auto_chain: \(.value.auto_chain))"' \
          "$WORKFLOW_TEMPLATES_FILE"
}

#############################################################################
# WORKFLOW VALIDATION
#############################################################################

validate_workflow() {
    local template_name="$1"

    echo "Validating workflow: $template_name"

    local errors=0

    # Check workflow exists
    if ! jq -e ".workflows[\"$template_name\"]" "$WORKFLOW_TEMPLATES_FILE" >/dev/null 2>&1; then
        echo "❌ Workflow not found: $template_name"
        return 1
    fi

    local steps
    steps=$(jq -r ".workflows[\"$template_name\"].steps | length" "$WORKFLOW_TEMPLATES_FILE")

    if [ "$steps" -eq 0 ]; then
        echo "❌ Workflow has no steps"
        return 1
    fi

    for ((i=0; i<steps; i++)); do
        local step
        step=$(jq -r ".workflows[\"$template_name\"].steps[$i]" "$WORKFLOW_TEMPLATES_FILE")

        local agent input output transitions
        agent=$(echo "$step" | jq -r '.agent')
        input=$(echo "$step" | jq -r '.input')
        output=$(echo "$step" | jq -r '.required_output')
        transitions=$(echo "$step" | jq -r '.on_status | length')

        echo "Step $i: $agent"

        # Validate agent exists
        if ! agent_exists "$agent"; then
            echo "  ❌ Agent not found: $agent"
            ((errors++))
        fi

        # Validate input defined
        if [ -z "$input" ] || [ "$input" = "null" ]; then
            echo "  ❌ No input defined"
            ((errors++))
        fi

        # Validate output defined
        if [ -z "$output" ] || [ "$output" = "null" ]; then
            echo "  ❌ No required_output defined"
            ((errors++))
        fi

        # Validate has transitions
        if [ "$transitions" -eq 0 ]; then
            echo "  ⚠️  Warning: No transitions defined"
        fi

        # Validate transition targets exist
        local next_steps
        next_steps=$(echo "$step" | jq -r '.on_status[].next_step // empty')
        while IFS= read -r next_step; do
            if [ -n "$next_step" ] && [ "$next_step" != "null" ]; then
                # Check if next step agent exists in agents.json
                if ! agent_exists "$next_step"; then
                    echo "  ❌ Transition references non-existent agent: $next_step"
                    ((errors++))
                fi
            fi
        done <<< "$next_steps"
    done

    if [ $errors -eq 0 ]; then
        echo ""
        echo "✅ Workflow validation passed"
        return 0
    else
        echo ""
        echo "❌ Validation failed with $errors errors"
        return 1
    fi
}

#############################################################################
# WORKFLOW EXECUTION
#############################################################################

start_workflow() {
    local workflow_name="$1"
    local enhancement_name="$2"

    # Validate workflow exists
    if ! jq -e ".workflows[\"$workflow_name\"]" "$WORKFLOW_TEMPLATES_FILE" >/dev/null 2>&1; then
        echo "❌ Workflow not found: $workflow_name"
        return 1
    fi

    # Validate workflow before starting
    echo "🔍 Validating workflow..."
    if ! validate_workflow "$workflow_name"; then
        echo "❌ Workflow validation failed - cannot start"
        return 1
    fi

    # Get first step
    local first_step
    first_step=$(jq -r ".workflows[\"$workflow_name\"].steps[0]" "$WORKFLOW_TEMPLATES_FILE")

    if [ -z "$first_step" ] || [ "$first_step" = "null" ]; then
        echo "❌ Workflow has no steps"
        return 1
    fi

    local agent input
    agent=$(echo "$first_step" | jq -r '.agent')
    input=$(echo "$first_step" | jq -r '.input')

    # Resolve input path
    input="${input//\{enhancement_name\}/$enhancement_name}"

    # Verify input exists
    if [ ! -f "$input" ] && [ ! -d "$input" ]; then
        echo "❌ Input file/directory not found: $input"
        echo "   Expected: $input"
        return 1
    fi

    # Get task type from agent role
    local task_type
    task_type=$(get_task_type_for_agent "$agent")

    echo ""
    echo "🚀 Starting workflow: $workflow_name"
    echo "   Enhancement: $enhancement_name"
    echo "   First step: $agent (step 0)"
    echo "   Input: $input"
    echo ""

    # Create first task
    local task_id
    task_id=$("$SCRIPT_DIR/queue-commands.sh" add \
        "Workflow: $workflow_name - $enhancement_name" \
        "$agent" \
        "high" \
        "$task_type" \
        "$input" \
        "Workflow: $workflow_name, Step 0" \
        "true" \
        "true" \
        "$enhancement_name")

    if [ -z "$task_id" ]; then
        echo "❌ Failed to create task"
        return 1
    fi

    # Add workflow metadata
    "$SCRIPT_DIR/queue-commands.sh" metadata "$task_id" "workflow_name" "$workflow_name"
    "$SCRIPT_DIR/queue-commands.sh" metadata "$task_id" "workflow_step" "0"

    echo "✅ Created task: $task_id"
    echo ""
    echo "Starting task..."

    # Start the task
    "$SCRIPT_DIR/queue-commands.sh" start "$task_id"
}

#############################################################################
# COMMAND ROUTER
#############################################################################

case "${1:-}" in
    "validate-output")
        if [ $# -lt 4 ]; then
            echo "Usage: cmat workflow validate-output <agent> <enhancement_dir> <required_output>"
            exit 1
        fi
        validate_agent_outputs "$2" "$3" "$4"
        ;;

    "get-task-type")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat workflow get-task-type <agent>"
            exit 1
        fi
        get_task_type_for_agent "$2"
        ;;

    "create")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow create <template_name> <description>" >&2
            exit 1
        fi
        create_workflow_template "$2" "$3"
        ;;

    "list")
        list_workflow_templates
        ;;

    "show")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat workflow show <template_name>" >&2
            exit 1
        fi
        show_workflow_template "$2"
        ;;

    "delete")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat workflow delete <template_name>" >&2
            exit 1
        fi
        delete_workflow_template "$2"
        ;;

    "add-step")
        if [ $# -lt 5 ]; then
            echo "Usage: cmat workflow add-step <template_name> <agent> <input> <output> [position]" >&2
            exit 1
        fi
        add_step_to_template "$2" "$3" "$4" "$5" "${6:-}"
        ;;

    "edit-step")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow edit-step <template_name> <step_num> [input] [output]" >&2
            exit 1
        fi
        edit_step "$2" "$3" "${4:-}" "${5:-}"
        ;;

    "remove-step")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow remove-step <template_name> <step_num>" >&2
            exit 1
        fi
        remove_step_from_template "$2" "$3"
        ;;

    "list-steps")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat workflow list-steps <template_name>" >&2
            exit 1
        fi
        list_template_steps "$2"
        ;;

    "show-step")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow show-step <template_name> <step_num>" >&2
            exit 1
        fi
        show_template_step "$2" "$3"
        ;;

    "add-transition")
        if [ $# -lt 5 ]; then
            echo "Usage: cmat workflow add-transition <template_name> <step_num> <status> <next_step> [auto_chain]" >&2
            echo "  next_step: agent name or 'null' for workflow end" >&2
            echo "  auto_chain: true|false (default: true)" >&2
            exit 1
        fi
        add_transition "$2" "$3" "$4" "$5" "${6:-true}"
        ;;

    "remove-transition")
        if [ $# -lt 4 ]; then
            echo "Usage: cmat workflow remove-transition <template_name> <step_num> <status>" >&2
            exit 1
        fi
        remove_transition "$2" "$3" "$4"
        ;;

    "list-transitions")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow list-transitions <template_name> <step_num>" >&2
            exit 1
        fi
        list_transitions "$2" "$3"
        ;;

    "validate")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat workflow validate <template_name>" >&2
            exit 1
        fi
        validate_workflow "$2"
        ;;

    "start")
        if [ $# -lt 3 ]; then
            echo "Usage: cmat workflow start <workflow_name> <enhancement_name>" >&2
            exit 1
        fi
        start_workflow "$2" "$3"
        ;;

    *)
        echo "Unknown workflow command: ${1:-}" >&2
        echo "" >&2
        echo "Template Management:" >&2
        echo "  create <name> <description>    Create new workflow template" >&2
        echo "  list                            List all templates" >&2
        echo "  show <name>                     Show template details" >&2
        echo "  delete <name>                   Delete template" >&2
        echo "  validate <name>                 Validate template structure" >&2
        echo "" >&2
        echo "Step Management:" >&2
        echo "  add-step <name> <agent> <input> <output> [pos]" >&2
        echo "  edit-step <name> <step> [input] [output]" >&2
        echo "  remove-step <name> <step>" >&2
        echo "  list-steps <name>" >&2
        echo "  show-step <name> <step>" >&2
        echo "" >&2
        echo "Transition Management:" >&2
        echo "  add-transition <name> <step> <status> <next> [auto]" >&2
        echo "  remove-transition <name> <step> <status>" >&2
        echo "  list-transitions <name> <step>" >&2
        echo "" >&2
        echo "Execution:" >&2
        echo "  start <workflow_name> <enhancement_name>" >&2
        echo "" >&2
        echo "Utilities:" >&2
        echo "  validate-output <agent> <dir> <file>" >&2
        echo "  get-task-type <agent>" >&2
        exit 1
        ;;
esac