#!/bin/bash

# Generate agents.json from agent markdown files
# This script extracts YAML frontmatter from agent .md files and creates agents.json

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$SCRIPT_DIR"
OUTPUT_FILE="$AGENTS_DIR/agents.json"

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
echo '{"agents":[' > "$OUTPUT_FILE"

first=true
for agent_file in "$AGENTS_DIR"/*.md; do
    [ -f "$agent_file" ] || continue

    # Extract YAML frontmatter
    if grep -q "^---$" "$agent_file"; then
        # Add comma between agents
        if [ "$first" = false ]; then
            echo ',' >> "$OUTPUT_FILE"
        fi
        first=false

        # Get filename without path and extension
        filename=$(basename "$agent_file" .md)

        # Extract frontmatter (between --- markers) and convert to JSON
        awk '/^---$/{f=!f;next} f' "$agent_file" | yaml_to_json "$filename" >> "$OUTPUT_FILE"
    fi
done

# Close JSON array
echo ']}' >> "$OUTPUT_FILE"

echo "✓ Generated $OUTPUT_FILE"