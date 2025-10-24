#!/usr/bin/env bash
################################################################################
# Script Name: cmat
# Description: Claude Multi-Agent Template - Main Command Launcher
#              Central entry point for all CMAT operations, routing commands
#              to specialized subsystems (queue, workflow, skills, integration, agents)
# Author: Brian Gentry
# Created: 2025
# Version: 3.0.0
#
# Usage: cmat <category> <command> [OPTIONS]
#
# Categories:
#   queue         Task queue management (add, start, complete, cancel, status, list)
#   workflow      Workflow orchestration (validate, auto-chain, templates)
#   skills        Skills management (list, get, load, prompt, test)
#   integration   External system integration (add, sync, sync-all)
#   agents        Agent operations (list, invoke, generate-json)
#   version       Show version and system information
#   help          Show this help message
#
# Examples:
#   cmat queue add "Task" "agent" "high" "analysis" "source.md" "Description"
#   cmat queue status
#   cmat skills list
#   cmat workflow validate requirements-analyst enhancements/feature
#   cmat integration sync <task_id>
#
# For detailed help on a category:
#   cmat queue --help
#   cmat workflow --help
#   cmat skills --help
#
# Dependencies:
#   - bash 4.0+
#   - jq (JSON processor)
#   - claude (Claude Code CLI)
#   - All subsystem scripts in .claude/scripts/
#
# Exit Codes:
#   0 - Success
#   1 - Invalid command or error
################################################################################

set -euo pipefail

readonly VERSION="3.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common utilities for version/help commands
source "$SCRIPT_DIR/common-commands.sh"

show_help() {
    cat << 'EOF'
cmat - Claude Multi-Agent Template Command Launcher

Usage: cmat <category> <command> [options]

QUEUE COMMANDS:
  cmat queue add <title> <agent> <priority> <type> <source> <desc> [auto_complete] [auto_chain]
  cmat queue start <task_id>
  cmat queue complete <task_id> [result] [--auto-chain]
  cmat queue cancel <task_id> [reason]
  cmat queue cancel-all [reason]
  cmat queue fail <task_id> [error]
  cmat queue status
  cmat queue list <queue_type> [format]
  cmat queue metadata <task_id> <key> <value>

WORKFLOW COMMANDS:
  cmat workflow validate <agent> <enhancement_dir>
  cmat workflow next-agent <agent> <status>
  cmat workflow next-source <enhancement> <next_agent> <current_agent>
  cmat workflow auto-chain <task_id> <status>
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
  cmat queue add "New feature" "requirements-analyst" "high" "analysis" "enhancements/feat/feat.md" "Analyze"
  cmat queue status
  cmat skills list
  cmat workflow validate "architect" "enhancements/feature"

For backward compatibility, you can still use:
  .claude/scripts/queue-commands.sh status    (direct call)

EOF
}

show_version() {
    echo "cmat v${VERSION}"
    echo "Claude Multi-Agent Template System"
    echo ""
    check_dependencies
    echo ""
    echo "Environment:"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Queue File: $QUEUE_FILE"
    echo "  Contracts: $CONTRACTS_FILE"
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

    if [ -f "$CONTRACTS_FILE" ]; then
        local agent_count
        agent_count=$(jq '.agents | length' "$CONTRACTS_FILE" 2>/dev/null || echo "0")
        echo "  Agents: $agent_count defined"
    fi

    if [ -f "$SKILLS_FILE" ]; then
        local skills_count
        skills_count=$(jq '.skills | length' "$SKILLS_FILE" 2>/dev/null || echo "0")
        echo "  Skills: $skills_count available"
    fi
}

#############################################################################
# COMMAND ROUTER
#############################################################################

case "${1:-help}" in
    "queue")
        shift
        "$SCRIPT_DIR/queue-commands.sh" "$@"
        ;;

    "workflow")
        shift
        "$SCRIPT_DIR/workflow-commands.sh" "$@"
        ;;

    "skills")
        shift
        "$SCRIPT_DIR/skills-commands.sh" "$@"
        ;;

    "integration")
        shift
        "$SCRIPT_DIR/integration-commands.sh" "$@"
        ;;

    "agents")
        shift
        "$SCRIPT_DIR/agent-commands.sh" "$@"
        ;;

    "version"|"-v"|"--version")
        show_version
        ;;

    "help"|"--help"|"-h")
        show_help
        ;;

    *)
        echo "Error: Unknown command category: $1"
        echo ""
        echo "Available categories: queue, workflow, skills, integration, agents"
        echo "Run 'cmat help' for full usage information"
        exit 1
        ;;
esac