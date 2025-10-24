#!/usr/bin/env bash
################################################################################
# Script Name: skills-commands.sh
# Description: Skills management and prompt generation
#              Manages agent skills, loads skill definitions, and builds
#              skills sections for agent prompts
# Author: Brian Gentry
# Created: 2025
# Version: 3.0.0
#
# Usage: cmat skills <command> [OPTIONS]
#
# Commands:
#   list
#       Display all available skills from skills.json
#   get <agent-name>
#       Get skills assigned to a specific agent
#   load <skill-directory>
#       Load and display a skill's SKILL.md content
#   prompt <agent-name>
#       Build complete skills section for agent prompt
#   test
#       Test all skills system functions
#
# Skills Structure:
#   .claude/skills/
#   ├── skills.json                  Skill registry
#   └── <skill-directory>/
#       └── SKILL.md                 Skill definition
#
# Skill Categories:
#   analysis, architecture, implementation, testing, documentation,
#   ui-design, database
#
# Dependencies:
#   - common-commands.sh (sourced)
#   - skills.json (skill registry)
#   - SKILL.md files (skill definitions)
#   - jq (JSON processor)
#
# Exit Codes:
#   0 - Success
#   1 - Skill not found or file missing
################################################################################

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-commands.sh"

#############################################################################
# SKILLS OPERATIONS
#############################################################################

list_skills() {
    if [ ! -f "$SKILLS_FILE" ]; then
        echo '{"skills": []}'
        return 1
    fi

    cat "$SKILLS_FILE" | jq '.'
}

get_agent_skills() {
    local agent_name="$1"
    local agent_file="$AGENTS_DIR/${agent_name}.md"

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

load_skill() {
    local skill_dir="$1"
    local skill_file="$SKILLS_DIR/${skill_dir}/SKILL.md"

    if [ ! -f "$skill_file" ]; then
        echo "Error: Skill not found: $skill_dir" >&2
        return 1
    fi

    # Read skill file, skip frontmatter (between --- markers)
    awk '/^---$/{f=!f;next} !f' "$skill_file"
    return 0
}

build_skills_prompt() {
    local agent="$1"
    local agent_config="$AGENTS_DIR/${agent}.md"

    # Get agent's skills
    local skills_json
    skills_json=$(get_agent_skills "$agent")

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
            skill_content=$(load_skill "$skill_dir")

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

test_skills() {
    echo "=== Testing Skills System ==="
    echo ""

    echo "1. Skills Data:"
    list_skills
    echo ""

    echo "2. Requirements Analyst Skills:"
    get_agent_skills "requirements-analyst"
    echo ""

    echo "3. Load Sample Skill (if exists):"
    if [ -f "$SKILLS_DIR/requirements-elicitation/SKILL.md" ]; then
        load_skill "requirements-elicitation" | head -20
        echo "... (truncated)"
    else
        echo "Skill not found - create .claude/skills/requirements-elicitation/SKILL.md first"
    fi
    echo ""

    echo "4. Build Skills Prompt for requirements-analyst:"
    build_skills_prompt "requirements-analyst" | head -30
    echo "... (truncated)"
}

#############################################################################
# COMMAND ROUTER
#############################################################################

case "${1:-list}" in
    "list")
        list_skills
        ;;

    "get")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat skills get <agent-name>"
            echo "Example: cmat skills get requirements-analyst"
            exit 1
        fi
        get_agent_skills "$2"
        ;;

    "load")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat skills load <skill-directory>"
            echo "Example: cmat skills load requirements-elicitation"
            exit 1
        fi
        load_skill "$2"
        ;;

    "prompt")
        if [ $# -lt 2 ]; then
            echo "Usage: cmat skills prompt <agent-name>"
            echo "Example: cmat skills prompt requirements-analyst"
            exit 1
        fi
        build_skills_prompt "$2"
        ;;

    "test")
        test_skills
        ;;

    *)
        echo "Unknown skills command: ${1:-}" >&2
        echo "Usage: cmat skills <list|get|load|prompt|test>" >&2
        exit 1
        ;;
esac