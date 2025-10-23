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
    local model=""
    local tools_json="[]"
    local skills_json="[]"
    local in_tools=false

    # Parse YAML frontmatter
    while IFS= read -r line; do
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

        # Check for key: value format
        if [[ "$line" =~ ^[[:space:]]*([^:]+):[[:space:]]*(.*)[[:space:]]*$ ]]; then
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
                model)
                    model="$value"
                    ;;
            esac
        fi
    done

    # Output JSON with skills field
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