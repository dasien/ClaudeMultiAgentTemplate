#!/usr/bin/env bash
################################################################################
# Script Name: cmat
# Description: Claude Multi-Agent Template - Main Command Launcher
#              Central entry point for all CMAT operations, routing commands
#              to specialized subsystems (queue, workflow, skills, integration, agents)
# Author: Brian Gentry
# Created: 2025
# Version: 4.0.0
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

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common utilities for version/help commands
source "$SCRIPT_DIR/common-commands.sh"

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
        show_version --full
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