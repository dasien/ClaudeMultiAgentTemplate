# Claude Multi-Agent Development Template

A workflow-based multi-agent development system using Claude Code. This template provides specialized AI agents orchestrated by customizable workflow templates with automated validation, comprehensive skills, and intelligent learning.

**Version**: 8.6.1

---

## What Is This?

This template provides a multi-agent system that breaks down software development into specialized roles, orchestrated by flexible workflow templates:

**Core Agents**:
- **Requirements Analyst**: Analyzes user needs and creates implementation plans
- **Architect**: Designs system architecture and technical specifications
- **Implementer**: Writes production-quality code
- **Tester**: Creates and runs comprehensive test suites
- **Documenter**: Maintains project documentation
- **Code Reviewer**: Reviews code for quality and security

**Integration Agents**:
- **GitHub Integration Coordinator**: Syncs workflow with GitHub issues and PRs
- **Atlassian Integration Coordinator**: Syncs workflow with Jira and Confluence

**Skills System**: 14+ specialized skills providing domain expertise, automatically injected into agent prompts.

---

## Features

### Core System
- **7 Specialized Agents** - Clear responsibilities, reusable across workflows
- **Workflow Templates** - Define agent sequences, inputs, outputs, and transitions
- **Output Validation** - Automatic validation of required outputs
- **Automated Workflows** - Template-driven intelligent task chaining
- **Task Queue System** - Organize and track work
- **Skills System** - Domain expertise in reusable modules

### Intelligence & Tracking
- **Learnings System** - RAG-based memory that improves over time
- **YAML Completion Blocks** - Structured status reporting from agents
- **Cost Tracking** - Automatic token usage and cost tracking per task
- **Model Management** - Configure and track Claude model pricing

### Integration
- **GitHub Sync** - Issues, PRs, and labels
- **Jira/Confluence Sync** - Tickets and documentation

---

## Prerequisites

- **Python 3.10+** - Core runtime
- **Claude Code** - Multi-agent orchestration platform

Optional:
- **Node.js 16+** - For MCP servers (GitHub/Jira integration)
- **pyyaml** - YAML parsing (pip install pyyaml)

---

## Installation

### Step 1: Copy Template Files

```bash
# Navigate to your project root
cd /path/to/your/project

# Copy the .claude directory
cp -r /path/to/ClaudeMultiAgentTemplate/.claude ./

# Create enhancements directory
mkdir -p enhancements
```

### Step 2: Verify Installation

```bash
cd .claude

# Check version
python -m cmat version
# Should show: CMAT version 8.6.1

# Check queue status
python -m cmat queue status

# List available agents
python -m cmat agents list
```

### Step 3: Configure Cost Tracking Hook (Optional)

Create or update `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/on-session-end-cost.sh"
          }
        ]
      }
    ]
  }
}
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "No module named 'cmat'" | Run from `.claude` directory: `cd .claude && python -m cmat version` |
| "Task queue file not found" | Check `.claude/data/` directory exists |
| "Agent not found" | Regenerate: `python -m cmat agents generate` |
| Permission denied on hook | `chmod +x .claude/hooks/on-session-end-cost.sh` |

---

## Quick Start

### 1. Add Project Learnings

Prime the RAG system with knowledge about your project:

```bash
cd .claude

# Add project-specific learnings
python -m cmat learnings add "This project uses Python 3.10+ with pytest for testing"
python -m cmat learnings add "API responses should use snake_case for JSON keys"

# View stored learnings
python -m cmat learnings list
```

### 2. Create an Enhancement

```bash
# From project root
mkdir -p enhancements/my-feature

cat > enhancements/my-feature/my-feature.md << 'EOF'
# My Feature

## Description
Add new functionality to the system.

## Acceptance Criteria
- Feature implemented
- Tests passing
- Documented
EOF
```

### 3. Start a Workflow

```bash
cd .claude

# List available workflows
python -m cmat workflow list

# Start a workflow
python -m cmat workflow start new-feature-development my-feature
```

### 4. Monitor Progress

```bash
# Check queue status
python -m cmat queue status

# List active tasks
python -m cmat queue list active

# View costs
python -m cmat costs enhancement my-feature
```

For a hands-on tutorial, see **[DEMO.md](DEMO.md)**.

---

## Project Structure

```
your-project/
├── .claude/                      # Multi-agent system
│   ├── cmat/                     # Python package
│   │   ├── __init__.py          # Version and exports
│   │   ├── __main__.py          # CLI entry point
│   │   ├── cmat.py              # Main CMAT class
│   │   ├── models/              # Data models
│   │   ├── services/            # Service classes
│   │   └── utils.py             # Utilities
│   ├── agents/                   # Agent definitions
│   │   ├── *.md                 # Agent specifications
│   │   └── agents.json          # Agent registry
│   ├── skills/                   # Skills system
│   │   ├── skills.json          # Skills registry
│   │   └── */SKILL.md           # 14+ skills
│   ├── data/                     # JSON data files
│   │   ├── task_queue.json      # Task queue state
│   │   ├── workflow_templates.json
│   │   ├── learnings.json       # RAG storage
│   │   └── models.json          # Claude models
│   ├── hooks/                    # Automation hooks
│   ├── docs/                     # Reference documentation
│   └── tests/                    # Python tests
├── enhancements/                 # Feature requests
│   └── feature-name/
│       ├── feature-name.md      # Enhancement spec
│       ├── requirements-analyst/
│       │   └── required_output/
│       ├── architect/
│       ├── implementer/
│       ├── tester/
│       ├── documenter/
│       └── logs/
└── [your project files]
```

---

## System Architecture

### Python Services

```
CMAT (entry point)
├── queue: QueueService       # Task state management
├── agents: AgentService      # Agent registry
├── skills: SkillsService     # Skills loading
├── workflow: WorkflowService # Orchestration
├── tasks: TaskService        # Execution
├── learnings: LearningsService # RAG memory
└── models: ModelService      # Model config & costs
```

### Workflow-Based Design

```
Workflow Template
  │
  ├─ Step 0: requirements-analyst
  │    ├─ input: "enhancement spec"
  │    ├─ required_output: "analysis.md"
  │    └─ on_status:
  │         ├─ READY_FOR_DEVELOPMENT → Step 1 (auto)
  │         └─ BLOCKED → Stop
  │
  ├─ Step 1: architect
  │    └─ on_status:
  │         ├─ READY_FOR_IMPLEMENTATION → Step 2 (auto)
  │         └─ NEEDS_CLARIFICATION → Stop
  │
  └─ ... (continues through workflow)
```

### Agent Completion Blocks

Agents report status using YAML completion blocks:

```yaml
---
agent: implementer
task_id: task_1234567890_12345
status: READY_FOR_TESTING
---
```

**Completion statuses** (workflow continues):
- `READY_FOR_DEVELOPMENT` - Requirements complete
- `READY_FOR_IMPLEMENTATION` - Design complete
- `READY_FOR_TESTING` - Implementation complete
- `TESTING_COMPLETE` - Tests passed
- `DOCUMENTATION_COMPLETE` - Docs updated

**Halt statuses** (workflow pauses):
- `BLOCKED: <reason>` - Cannot proceed
- `NEEDS_CLARIFICATION: <question>` - Requires input
- `TESTS_FAILED: <details>` - Tests need attention

---

## CLI Reference

```bash
# Run from .claude directory
cd /path/to/your/project/.claude
python -m cmat <command> [options]

# System info
python -m cmat version              # Version
python -m cmat queue status         # Queue summary
python -m cmat agents list          # List agents
python -m cmat models list          # List models

# Workflow management
python -m cmat workflow list        # Available workflows
python -m cmat workflow show <name> # Workflow details
python -m cmat workflow start <workflow> <enhancement>

# Queue management
python -m cmat queue list [pending|active|completed|failed|all]
python -m cmat queue complete <task_id> <status>
python -m cmat queue fail <task_id> <reason>
python -m cmat queue cancel <task_id> [reason]
python -m cmat queue rerun <task_id>

# Learnings (RAG memory)
python -m cmat learnings list
python -m cmat learnings add "<content>" [--tags tag1,tag2]
python -m cmat learnings search "<query>"
python -m cmat learnings delete <id>

# Cost tracking
python -m cmat costs show <task_id>
python -m cmat costs enhancement <name>

# Model management
python -m cmat models set-default <id>
```

For complete CLI documentation, see **[.claude/docs/CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md)**.

---

## Documentation

### Getting Started
- **[README.md](README.md)** - This file
- **[DEMO.md](DEMO.md)** - Hands-on demo walkthrough

### Reference Guides
- **[CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md)** - Complete command reference
- **[CUSTOMIZATION_GUIDE.md](.claude/docs/CUSTOMIZATION_GUIDE.md)** - Adapting to your project
- **[WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md)** - Workflow patterns
- **[SKILLS_GUIDE.md](.claude/docs/SKILLS_GUIDE.md)** - Skills system
- **[QUEUE_SYSTEM_GUIDE.md](.claude/docs/QUEUE_SYSTEM_GUIDE.md)** - Task queue operations

### Features
- **[LEARNINGS_GUIDE.md](.claude/docs/LEARNINGS_GUIDE.md)** - RAG memory system
- **[COST_TRACKING.md](.claude/docs/COST_TRACKING.md)** - Token usage and costs
- **[INTEGRATION_GUIDE.md](.claude/docs/INTEGRATION_GUIDE.md)** - GitHub/Jira integration

---

## Next Steps

1. **Try the Demo** - [DEMO.md](DEMO.md) - Hands-on walkthrough with the calculator project
2. **Customize** - [.claude/docs/CUSTOMIZATION_GUIDE.md](.claude/docs/CUSTOMIZATION_GUIDE.md) - Adapt for your project
3. **Learn Workflows** - [.claude/docs/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) - Workflow patterns
4. **Explore Skills** - [.claude/docs/SKILLS_GUIDE.md](.claude/docs/SKILLS_GUIDE.md) - Domain expertise

---

## Links

- **Claude Code**: https://claude.ai/code
- **Complete Documentation**: See `.claude/docs/` directory