# Claude Multi-Agent Development Template

A workflow-based multi-agent development system using Claude Code. This template provides specialized AI agents orchestrated by customizable workflow templates with automated validation and comprehensive skills.

**Version**: 5.1.1

## 🎯 What Is This?

This template provides a multi-agent system that breaks down software development into specialized roles, orchestrated by flexible workflow templates:

- **Requirements Analyst**: Analyzes user needs and creates implementation plans
- **Architect**: Designs system architecture and technical specifications
- **Implementer**: Writes production-quality code
- **Tester**: Creates and runs comprehensive test suites
- **Documenter**: Maintains project documentation

**Integration Agents**:
- **GitHub Integration Coordinator**: Syncs workflow with GitHub issues and PRs
- **Atlassian Integration Coordinator**: Syncs workflow with Jira and Confluence

**Skills System**:
- 14+ specialized skills providing domain expertise
- Automatically injected into agent prompts
- Organized by category (analysis, architecture, implementation, testing, documentation)

## ✨ Features

### Core System (v5.0)
- 🤖 **7 Specialized Agents** - Clear responsibilities, reusable across workflows
- 📋 **Workflow Templates** - Define agent sequences, inputs, outputs, and transitions
- ✅ **Output Validation** - Automatic validation of required outputs
- 🔄 **Automated Workflows** - Template-driven intelligent task chaining
- 📊 **Task Queue System** - Organize and track work
- 🧠 **Skills System** - Domain expertise in reusable modules
- 🎯 **Flexible Orchestration** - Same agent, different workflows, different behavior

### Quality & Tracking
- 📝 **Metadata Headers** - All outputs are self-documenting and traceable
- 🧪 **Comprehensive Logging** - Agent execution logged for analysis
- 💰 **Cost Tracking** - Automatic token usage and cost tracking per task
- 🔗 **Cross-Platform Sync** - GitHub and Jira/Confluence integration
- 🗂️ **Modular Architecture** - Clean separation of concerns

## 🆕 What's New in v5.0

### Workflow-Based Orchestration

**Before**: Agents defined their own workflow position and next steps
**After**: Workflows define everything - agents are reusable components

```json
// Workflow template defines orchestration
{
  "agent": "architect",
  "input": "{previous_step}/required_output/",
  "required_output": "design.md",
  "on_status": {
    "READY_FOR_IMPLEMENTATION": {
      "next_step": "implementer",
      "auto_chain": true
    }
  }
}
```

### Benefits

✅ **Flexibility** - Same agent in different workflows with different inputs/outputs
✅ **User Control** - Create/modify workflows via CLI
✅ **Simplicity** - Workflows are single source of truth
✅ **Reusability** - Agents are truly pluggable components
✅ **Custom Status Codes** - Workflows define what status codes mean

### Standardized Output Structure

All agents now use convention-based directories:
```
enhancements/{enhancement}/{ agent}/
├── required_output/
│   └── {workflow-specified-file}
└── optional_output/
    └── [additional files]
```

### Simplified Agent Definitions

Agents now focus purely on capabilities:
```json
{
  "name": "Architect",
  "role": "technical_design",
  "tools": [...],
  "skills": [...],
  "validations": {
    "metadata_required": true
  }
}
```

No more input/output/status specifications in agents!

---

## 🚀 Quick Start

### 1. Install
```bash
# Copy .claude directory to your project
cp -r ClaudeMultiAgentTemplate/.claude /path/to/your/project/

# Make scripts executable
chmod +x /path/to/your/project/.claude/scripts/*.sh
chmod +x /path/to/your/project/.claude/hooks/*.sh
```

### 2. Test
```bash
# List available workflows
cmat workflow list

# Create test enhancement
mkdir -p enhancements/test
echo "# Test" > enhancements/test/test.md

# Start workflow
cmat workflow start new_feature_development test

# Monitor
cmat queue status
```

### 3. Customize
See [CUSTOMIZATION.md](CUSTOMIZATION.md) for adapting to your project.

---

## 📁 Project Structure

```
your-project/
├── .claude/                      # Multi-agent system (v5.0)
│   ├── scripts/                  # Command scripts
│   │   ├── cmat.sh              # Main command launcher
│   │   ├── queue-commands.sh     # Queue operations
│   │   ├── workflow-commands.sh  # Workflow management
│   │   ├── skills-commands.sh    # Skills management
│   │   ├── integration-commands.sh # External sync
│   │   └── agent-commands.sh     # Agent operations
│   ├── agents/                   # Agent definitions
│   │   ├── *.md                 # Agent specifications
│   │   ├── agents.json          # Agent registry
│   │   └── generate_agents_json.sh
│   ├── skills/                   # Skills system
│   │   ├── skills.json          # Skills registry
│   │   └── */SKILL.md           # 14+ skills
│   ├── hooks/                    # Workflow automation
│   │   ├── on-subagent-stop.sh  # Workflow orchestration
│   │   └── on-session-end-cost.sh # Cost tracking
│   ├── queues/                   # Task management
│   │   ├── task_queue.json
│   │   └── workflow_templates.json
│   └── docs/                     # Documentation
├── enhancements/                # Feature requests
│   └── feature-name/
│       ├── feature-name.md           # Enhancement spec
│       ├── requirements-analyst/
│       │   ├── required_output/
│       │   └── optional_output/
│       ├── architect/
│       │   ├── required_output/
│       │   └── optional_output/
│       └── logs/
└── [your project files]
```

---

## 🗂️ System Architecture

### Workflow-Based Design

```
Workflow Template
  │
  ├─ Step 0: requirements-analyst
  │    ├─ input: "enhancement spec file"
  │    ├─ required_output: "analysis.md"
  │    └─ on_status:
  │         └─ READY_FOR_DEVELOPMENT → Step 1
  │
  ├─ Step 1: architect
  │    ├─ input: "step 0 outputs"
  │    ├─ required_output: "design.md"
  │    └─ on_status:
  │         └─ READY_FOR_IMPLEMENTATION → Step 2
  │
  └─ ... (continues through workflow)
```

**Task Metadata** carries workflow context:
```json
{
  "workflow_name": "new_feature_development",
  "workflow_step": 0
}
```

**Hook** orchestrates using workflow:
1. Extract status from agent output
2. Get workflow context from task metadata
3. Check if status in current step's `on_status`
4. If yes → create next task (step + 1)
5. If no → stop workflow

### Agent Specialization

| Agent | Role | Responsibilities | Skills |
|-------|------|------------------|--------|
| requirements-analyst | analysis | What to build | Requirements Elicitation, User Stories, Bug Triage |
| architect | technical_design | How to build it | API Design, Architecture Patterns, UI Design |
| implementer | implementation | Build it | Error Handling, Code Refactoring, SQL |
| tester | testing | Validate it | Test Patterns, Coverage, Bug Triage |
| documenter | documentation | Document it | Technical Writing, API Docs |

---

## 📄 Development Workflow

### Example: Standard Feature Development

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

## 📚 Documentation

### Getting Started
- **[README.md](README.md)** - This file - Overview and architecture
- **[INSTALLATION.md](INSTALLATION.md)** - Setup and verification
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapting to your project

### System Reference
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow patterns
- **[WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md)** - Template management
- **[SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md)** - Complete command reference
- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Skills system
- **[agents.json](.claude/agents/agents.json)** - Agent definitions
- **[workflow_templates.json](.claude/queues/workflow_templates.json)** - Workflow storage

### Advanced Topics
- **[INTEGRATION_GUIDE.md](.claude/docs/INTEGRATION_GUIDE.md)** - GitHub/Jira integration
- **[MCP_CONFIGURATION_GUIDE.md](.claude/mcp-servers/MCP_CONFIGURATION_GUIDE.md)** - MCP setup
- **[MIGRATION_v4_to_v5.md](MIGRATION_v4_to_v5.md)** - Upgrade from v4.x

---

## 🛠️ Requirements

- **Claude Code** - Multi-agent orchestration platform
- **bash** - Shell scripting
- **jq** - JSON processing

Optional:
- **Node.js 16+** - For MCP servers (GitHub/Jira integration)

---

## 🔧 Command Reference

### Workflow Commands (NEW in v5.0)
```bash
cmat workflow create <n> <desc>         # Create template
cmat workflow list                      # List all workflows
cmat workflow show <n>                  # Show workflow details
cmat workflow start <workflow> <enh>    # Start workflow
cmat workflow add-step <n> <agent> <input> <o>
cmat workflow add-transition <n> <step> <status> <next>
cmat workflow validate <n>              # Validate template
```

### Queue Commands
```bash
cmat queue status                       # View status
cmat queue list <type>                  # List tasks
cmat queue show-task-cost <id>          # View task cost
cmat queue show-enhancement-cost <n>    # View enhancement cost
```

### Skills Commands
```bash
cmat skills list                        # List all skills
cmat skills get <agent>                 # Get agent skills
cmat skills load <skill>                # View skill content
```

See [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) for complete documentation.

---

## 🎯 Skills System

### Built-in Skills (14+)

**Analysis**: Requirements Elicitation, User Story Writing, Bug Triage
**Architecture**: API Design, Architecture Patterns  
**Implementation**: Error Handling, Code Refactoring, SQL Development
**Testing**: Test Design Patterns, Test Coverage
**Documentation**: Technical Writing, API Documentation
**UI Design**: Desktop UI, Web UI

### Managing Skills
```bash
cmat skills list                # All skills
cmat skills get architect       # Agent's skills
cmat skills load api-design     # Skill content
```

### Creating Custom Skills

1. Create skill directory with SKILL.md
2. Register in skills.json
3. Assign to agents
4. Regenerate: `cmat agents generate-json`

See [SKILLS_GUIDE.md](SKILLS_GUIDE.md) for complete guide.

---

## 📖 How It Works

### Workflow Execution Example

```bash
# 1. User starts workflow
cmat workflow start new_feature_development user-auth

# 2. System creates first task
Task created:
  - agent: requirements-analyst
  - input: enhancements/user-auth/user-auth.md
  - metadata: {workflow_name: "new_feature_development", workflow_step: 0}

# 3. Agent executes and outputs status
Status: READY_FOR_DEVELOPMENT

# 4. Hook processes completion
- Validates: required_output/analysis_summary.md exists
- Checks workflow step 0 on_status["READY_FOR_DEVELOPMENT"]
- Finds: next_step = "architect", auto_chain = true
- Creates: New task for architect (step 1)
- Starts: New task automatically

# 5. Process repeats
architect → implementer → tester → documenter
Each step validates and chains to next
```

### Status Transition Rules

**Simple Rule**: If agent's output status matches an entry in the step's `on_status` map → continue. Otherwise → stop.

**Example**:
```json
{
  "on_status": {
    "READY_FOR_IMPLEMENTATION": {"next_step": "implementer", "auto_chain": true}
  }
}
```

- Agent outputs `READY_FOR_IMPLEMENTATION` → Creates implementer task
- Agent outputs `BLOCKED: Missing API spec` → Stops workflow (not in on_status)
- Agent outputs `NEEDS_RESEARCH` → Stops workflow (not in on_status)

---

## 🧪 Example Project

This template includes a working Python CLI task manager:

- **Source**: `src/task_manager.py` - Simple task management CLI
- **Tests**: `tests/test_task_manager.py` - Comprehensive test suite
- **Demo Enhancement**: `enhancements/demo-test/` - Minimal workflow test

---

## 🎓 Learning Path

### For First-Time Users

1. **Install** - [INSTALLATION.md](INSTALLATION.md)
2. **Quick Start** - [QUICKSTART.md](QUICKSTART.md) - 5 minute test
3. **Understand Workflows** - [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)
4. **Learn Templates** - [WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md)
5. **Explore Skills** - [SKILLS_GUIDE.md](SKILLS_GUIDE.md)
6. **Customize** - [CUSTOMIZATION.md](CUSTOMIZATION.md)

### Key Concepts

- **Workflow Templates**: Define agent sequences and orchestration
- **Output Directories**: Standardized `required_output/` and `optional_output/`
- **Status Transitions**: Workflows define what each status means
- **Task Metadata**: Carries workflow context (workflow_name, workflow_step)
- **Skills**: Domain expertise automatically provided to agents
- **Validation**: Outputs validated before workflow continues

---

## 🤝 Contributing

Suggested improvements:
- Additional workflow patterns
- Domain-specific skills
- Custom agents for specialized tasks
- Integration with additional platforms

---

## 📋 Quick Reference

### Start a Workflow
```bash
# Create enhancement spec
mkdir -p enhancements/feature
echo "# Feature" > enhancements/feature/feature.md

# Start workflow
cmat workflow start new_feature_development feature
```

### Create Custom Workflow
```bash
cmat workflow create my-workflow "Description"
cmat workflow add-step my-workflow <agent> <input> <o>
cmat workflow add-transition my-workflow <step> <status> <next>
cmat workflow start my-workflow <enhancement>
```

### Monitor
```bash
cmat queue status              # Current status
cmat queue list completed      # Completed tasks
```

---

## 🔗 Links

- **Claude Code**: https://claude.ai/code
- **Complete Documentation**: See `.claude/docs/` directory

---

**Ready to start?** See [QUICKSTART.md](QUICKSTART.md) for a 5-minute walkthrough.

**Need help?** See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for patterns and [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) for commands.

**Want to customize?** See [CUSTOMIZATION.md](CUSTOMIZATION.md) for adapting to your project.

---