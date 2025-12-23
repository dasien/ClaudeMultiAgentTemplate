# Claude Multi-Agent Development Template

A workflow-based multi-agent development system using Claude Code. This template provides specialized AI agents orchestrated by customizable workflow templates with automated validation, comprehensive skills, and intelligent learning.

**Version**: 8.2.0

## What Is This?

This template provides a multi-agent system that breaks down software development into specialized roles, orchestrated by flexible workflow templates:

- **Requirements Analyst**: Analyzes user needs and creates implementation plans
- **Architect**: Designs system architecture and technical specifications
- **Implementer**: Writes production-quality code
- **Tester**: Creates and runs comprehensive test suites
- **Documenter**: Maintains project documentation
- **Code Reviewer**: Reviews code for quality and security

**Integration Agents**:
- **GitHub Integration Coordinator**: Syncs workflow with GitHub issues and PRs
- **Atlassian Integration Coordinator**: Syncs workflow with Jira and Confluence

**Skills System**:
- 14+ specialized skills providing domain expertise
- Automatically injected into agent prompts
- Organized by category (analysis, architecture, implementation, testing, documentation)

## Features

### Core System
- **7 Specialized Agents** - Clear responsibilities, reusable across workflows
- **Workflow Templates** - Define agent sequences, inputs, outputs, and transitions
- **Output Validation** - Automatic validation of required outputs
- **Automated Workflows** - Template-driven intelligent task chaining
- **Task Queue System** - Organize and track work
- **Skills System** - Domain expertise in reusable modules
- **Flexible Orchestration** - Same agent, different workflows, different behavior

### Intelligence & Tracking
- **Learnings System** - RAG-based memory that improves over time
- **YAML Completion Blocks** - Structured status reporting from agents
- **Cost Tracking** - Automatic token usage and cost tracking per task
- **Model Management** - Configure and track Claude model pricing
- **Comprehensive Logging** - Agent execution logged for analysis
- **Metadata Headers** - All outputs are self-documenting and traceable

### Integration
- **GitHub Sync** - Issues, PRs, and labels
- **Jira/Confluence Sync** - Tickets and documentation

---

## Quick Start

### 1. Install

```bash
# Copy .claude directory to your project
cp -r ClaudeMultiAgentTemplate/.claude /path/to/your/project/

# Verify installation
cd /path/to/your/project/.claude
python -m cmat version
```

### 2. Test

```bash
# List available workflows
python -m cmat queue status

# List agents
python -m cmat agents list

# View learnings (if any)
python -m cmat learnings list
```

### 3. Start a Workflow

```bash
# Create enhancement spec
mkdir -p enhancements/my-feature
echo "# My Feature\n\nDescription of what to build..." > enhancements/my-feature/my-feature.md

# Use Claude Code to start a workflow via Task tool with workflow-related agents
```

### 4. Customize

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for adapting to your project.

---

## Project Structure

```
your-project/
├── .claude/                      # Multi-agent system (v8.2.0)
│   ├── cmat/                     # Python package
│   │   ├── __init__.py          # Version and exports
│   │   ├── __main__.py          # CLI entry point
│   │   ├── cmat.py              # Main CMAT class
│   │   ├── models/              # Data models (Task, Agent, Learning, etc.)
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
│   │   ├── workflow_templates.json # Workflow definitions
│   │   ├── learnings.json       # RAG learnings storage
│   │   ├── models.json          # Claude model definitions
│   │   └── tools.json           # Tool definitions
│   ├── hooks/                    # Automation hooks
│   │   └── on-session-end-cost.sh # Cost tracking hook
│   ├── docs/                     # Documentation
│   └── tests/                    # Python tests
├── enhancements/                 # Feature requests
│   └── feature-name/
│       ├── feature-name.md      # Enhancement spec
│       ├── requirements-analyst/
│       │   ├── required_output/
│       │   └── optional_output/
│       ├── architect/
│       │   └── ...
│       └── logs/
└── [your project files]
```

---

## System Architecture

### Python Services

```
CMAT (entry point)
├── queue: QueueService       # Task state management
├── agents: AgentService      # Agent registry and generation
├── skills: SkillsService     # Skills loading and prompt building
├── workflow: WorkflowService # Template management and orchestration
├── tasks: TaskService        # Prompt building and execution
├── learnings: LearningsService # RAG memory system
└── models: ModelService      # Model configuration and cost extraction
```

### Workflow-Based Design

```
Workflow Template
  │
  ├─ Step 0: requirements-analyst
  │    ├─ input: "enhancement spec file"
  │    ├─ required_output: "analysis.md"
  │    └─ on_status:
  │         ├─ READY_FOR_DEVELOPMENT → Step 1 (auto_chain)
  │         └─ BLOCKED → Stop (halt status)
  │
  ├─ Step 1: architect
  │    ├─ input: "step 0 outputs"
  │    ├─ required_output: "design.md"
  │    └─ on_status:
  │         ├─ READY_FOR_IMPLEMENTATION → Step 2 (auto_chain)
  │         └─ NEEDS_CLARIFICATION → Stop (halt status)
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

### Task Queue States

```
pending → active → completed
                 → failed
                 → cancelled
```

---

## CLI Reference

```bash
python -m cmat <command> [options]

# Learnings (RAG memory system)
python -m cmat learnings list                    # List all learnings
python -m cmat learnings add "<content>"         # Add a manual learning
python -m cmat learnings delete <id>             # Delete a learning
python -m cmat learnings show <id>               # Show learning details
python -m cmat learnings search "<query>"        # Search learnings

# Queue management
python -m cmat queue status                      # Show queue summary
python -m cmat queue list [pending|active|completed|failed|all]

# Agents
python -m cmat agents list                       # List all agents
python -m cmat agents generate                   # Regenerate agents.json

# Models
python -m cmat models list                       # List Claude models
python -m cmat models show <id>                  # Show model details
python -m cmat models set-default <id>           # Set default model

# Cost tracking
python -m cmat costs extract <task_id> <transcript_path> [session_id]
python -m cmat costs show <task_id>              # Show task cost
python -m cmat costs enhancement <name>          # Show enhancement cost

# Version
python -m cmat version                           # Show CMAT version
```

---

## Development Workflow Example

### Standard Feature Development

```
1. requirements-analyst (Step 0)
   Input:  enhancements/feature/feature.md
   Output: enhancements/feature/requirements-analyst/required_output/analysis_summary.md
   Status: READY_FOR_DEVELOPMENT
   → Triggers: architect (Step 1)

2. architect (Step 1)
   Input:  enhancements/feature/requirements-analyst/required_output/
   Output: enhancements/feature/architect/required_output/implementation_plan.md
   Status: READY_FOR_IMPLEMENTATION
   → Triggers: implementer (Step 2)

3. implementer (Step 2)
   Input:  enhancements/feature/architect/required_output/
   Output: enhancements/feature/implementer/required_output/implementation_summary.md
   Status: READY_FOR_TESTING
   → Triggers: tester (Step 3)

4. tester (Step 3)
   Input:  enhancements/feature/implementer/required_output/
   Output: enhancements/feature/tester/required_output/test_summary.md
   Status: TESTING_COMPLETE
   → Triggers: documenter (Step 4)

5. documenter (Step 4)
   Input:  enhancements/feature/tester/required_output/
   Output: enhancements/feature/documenter/required_output/documentation_summary.md
   Status: DOCUMENTATION_COMPLETE
   → Workflow complete
```

---

## Skills System

### Built-in Skills (14+)

**Analysis**: Requirements Elicitation, User Story Writing, Bug Triage
**Architecture**: API Design, Architecture Patterns, Agent Design
**Implementation**: Error Handling, Code Refactoring, SQL Development
**Testing**: Test Design Patterns, Test Coverage
**Documentation**: Technical Writing, API Documentation
**UI Design**: Desktop UI, Web UI

### Managing Skills

```bash
# View skills assigned to agents
python -m cmat agents list
```

### Creating Custom Skills

1. Create skill directory with `SKILL.md`
2. Register in `skills.json`
3. Assign to agents
4. Regenerate: `python -m cmat agents generate`

See [.claude/docs/SKILLS_GUIDE.md](.claude/docs/SKILLS_GUIDE.md) for complete guide.

---

## Learnings System

CMAT includes a RAG-based learnings system that captures insights from agent outputs and user feedback. Learnings are automatically retrieved and injected into agent prompts when relevant.

### Adding Learnings

```bash
# Manual learning
python -m cmat learnings add "Always use pytest fixtures for database tests" --tags testing,python

# View learnings
python -m cmat learnings list

# Search for relevant learnings
python -m cmat learnings search "database testing patterns"
```

### Learning Sources

- **Agent outputs**: Automatically extracted after task completion
- **User feedback**: Manually added via CLI
- **Code patterns**: Detected during analysis (future)

---

## Requirements

- **Python 3.10+** - Core runtime
- **Claude Code** - Multi-agent orchestration platform
- **pyyaml** - YAML parsing (optional, included in standard lib on most systems)

Optional:
- **Node.js 16+** - For MCP servers (GitHub/Jira integration)

---

## Documentation

### Getting Started
- **[README.md](README.md)** - This file - Overview and architecture
- **[INSTALLATION.md](INSTALLATION.md)** - Setup and verification
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start
- **[DEMO.md](DEMO.md)** - Hands-on demo walkthrough
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapting to your project

### System Reference
- **[CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md)** - Complete command reference
- **[QUEUE_SYSTEM.md](.claude/docs/QUEUE_SYSTEM_GUIDE.md)** - Queue operations
- **[WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md)** - Workflow patterns
- **[WORKFLOW_TEMPLATES.md](.claude/docs/WORKFLOW_TEMPLATE_GUIDE.md)** - Template management
- **[SKILLS_GUIDE.md](.claude/docs/SKILLS_GUIDE.md)** - Skills system
- **[AGENT_GUIDE.md](.claude/docs/AGENT_GUIDE.md)** - Agent creation

### Features
- **[LEARNINGS_GUIDE.md](.claude/docs/LEARNINGS_GUIDE.md)** - RAG memory system
- **[STATUS_COMPLETION.md](.claude/docs/STATUS_COMPLETION.md)** - YAML completion blocks
- **[COST_TRACKING.md](.claude/docs/COST_TRACKING.md)** - Token usage and costs

### Integration
- **[INTEGRATION_GUIDE.md](.claude/docs/INTEGRATION_GUIDE.md)** - GitHub/Jira integration

---

## Learning Path

### For First-Time Users

1. **Install** - [INSTALLATION.md](INSTALLATION.md)
2. **Quick Start** - [QUICKSTART.md](QUICKSTART.md) - 5 minute test
3. **Understand Workflows** - [.claude/docs/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md)
4. **Learn Templates** - [.claude/docs/WORKFLOW_TEMPLATE_GUIDE.md](.claude/docs/WORKFLOW_TEMPLATE_GUIDE.md)
5. **Explore Skills** - [.claude/docs/SKILLS_GUIDE.md](.claude/docs/SKILLS_GUIDE.md)
6. **Customize** - [CUSTOMIZATION.md](CUSTOMIZATION.md)

### Key Concepts

- **Workflow Templates**: Define agent sequences and orchestration
- **Output Directories**: Standardized `required_output/` and `optional_output/`
- **Status Transitions**: Workflows define what each status means
- **YAML Completion Blocks**: Structured status reporting from agents
- **Task Metadata**: Carries workflow context (workflow_name, workflow_step)
- **Skills**: Domain expertise automatically provided to agents
- **Learnings**: RAG memory that improves over time
- **Validation**: Outputs validated before workflow continues

---

## Quick Reference

### View System Status
```bash
python -m cmat version           # Version info
python -m cmat queue status      # Queue counts
python -m cmat agents list       # Available agents
python -m cmat models list       # Claude models
```

### Manage Learnings
```bash
python -m cmat learnings list    # All learnings
python -m cmat learnings add "Learning content"
python -m cmat learnings search "query"
```

### Track Costs
```bash
python -m cmat costs show <task_id>
python -m cmat costs enhancement <name>
```

---

## Links

- **Claude Code**: https://claude.ai/code
- **Complete Documentation**: See `.claude/docs/` directory

---

**Ready to start?** See [QUICKSTART.md](QUICKSTART.md) for a 5-minute walkthrough, then try [DEMO.md](DEMO.md) for a hands-on example.

**Need help?** See [.claude/docs/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) for patterns and [.claude/docs/CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md) for commands.

**Want to customize?** See [CUSTOMIZATION.md](CUSTOMIZATION.md) for adapting to your project.
