# Claude Multi-Agent Development Template

A contract-based multi-agent development workflow system using Claude Code. This template provides specialized AI agents with formal contracts, automated validation, and intelligent workflow chaining.

**Version**: 2.0.0 - Contract-based validation and automated workflow chains

## 🎯 What Is This?

This template provides a multi-agent system that breaks down software development into specialized roles, each handled by a dedicated Claude agent with formal contracts defining inputs, outputs, and workflow transitions:

- **Requirements Analyst**: Analyzes user needs and creates implementation plans
- **Architect**: Designs system architecture and technical specifications
- **Implementer**: Writes production-quality code
- **Tester**: Creates comprehensive test suites
- **Documenter**: Maintains project documentation

**Plus Integration Agents**:
- **GitHub Integration Coordinator**: Syncs workflow with GitHub issues and PRs
- **Atlassian Integration Coordinator**: Syncs workflow with Jira and Confluence

## ✨ Features

### Core System
- 🤖 **7 Specialized Agents** - Clear responsibilities defined by formal contracts
- 📜 **Agent Contracts** - Formal specifications for inputs, outputs, and statuses
- ✅ **Output Validation** - Automatic validation before workflow progression
- 🔄 **Automated Workflows** - Contract-based intelligent task chaining
- 📋 **Task Queue System** - Organize and track work across agents
- 📊 **Workflow Patterns** - Predefined patterns for common scenarios
- 🔍 **State Machine** - Formal state definitions and valid transitions

### Quality & Tracking
- 📝 **Metadata Headers** - All outputs are self-documenting and traceable
- 🧪 **Comprehensive Logging** - Agent execution logged for analysis
- 🔗 **Cross-Platform Sync** - GitHub and Jira/Confluence integration
- 🎯 **Contract Validation** - Outputs validated against formal specifications

### Example & Documentation
- 🐍 **Example Application** - Sample Python CLI app with full enhancement workflow
- 📚 **Complete Documentation** - Guides for every aspect of the system

## 🆕 What's New in v2.0

### Successfully Tested Features ✅

The v2.0 system has been validated with the **demo-test** enhancement, confirming:

- ✅ **Contract-Based Validation**: All outputs validated against AGENT_CONTRACTS.json
- ✅ **Metadata Headers**: All documents include required 5-field YAML frontmatter
- ✅ **Smart Auto-Chaining**: Correct next agent determined from contracts
- ✅ **Auto-Start**: Chained tasks automatically start (when auto_chain=true)
- ✅ **Settings Inheritance**: auto_complete and auto_chain propagate through workflow
- ✅ **Output Validation**: Files checked before workflow progression
- ✅ **Path Construction**: Next agent's source path built correctly from contracts
- ✅ **Complete Workflow**: Requirements → Architecture → Implementation → Testing → Documentation

### Key Improvements

- **Agent Contracts**: Formal JSON specifications replace implicit behavior
- **Output Validation**: Automated validation against contracts before chaining
- **Metadata Headers**: All documents include YAML frontmatter (enhancement, agent, task_id, timestamp, status)
- **Smart Auto-Chaining**: Contract-based next agent determination
- **Workflow State Machine**: Formal state definitions with valid transitions
- **Simplified Documentation**: Single source of truth (contracts) with human guides
- **Enhanced Error Messages**: Clear feedback when validation fails
- **Full Automation**: Set `auto_complete=true` and `auto_chain=true` for hands-off workflows

## 🚀 Quick Start

### 1. Install the Template

```bash
# Copy .claude directory to your project
cp -r ClaudeMultiAgentTemplate/.claude /path/to/your/project/

# Make scripts executable
chmod +x /path/to/your/project/.claude/hooks/*.sh
chmod +x /path/to/your/project/.claude/queues/*.sh
```

### 2. Configure Claude Code

Create `.claude/settings.local.json`:

```json
{
  "hooks": {
    "on_subagent_stop": ".claude/hooks/on-subagent-stop.sh"
  }
}
```

**Note**: The `on-stop` hook has been removed in v2.0. All workflow management is handled by the queue system and `on-subagent-stop.sh` hook.

### 3. Customize Agents

Edit agent files in `.claude/agents/` to customize for your project:
- Programming languages and frameworks
- Coding standards and conventions
- Testing requirements
- Documentation standards

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions.

### 4. Start Building

**Quick Test with Demo Enhancement**:

```bash
# Set environment to skip integration prompts
export AUTO_INTEGRATE="never"

# Create fully automated task
TASK_ID=$(.claude/queues/queue_manager.sh add \
  "Demo test - requirements analysis" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Analyze requirements for demo test enhancement" \
  true \
  true)

# Start and watch it run through entire workflow automatically
.claude/queues/queue_manager.sh start $TASK_ID

# The system will:
# 1. Run requirements-analyst → Create analysis_summary.md
# 2. Validate output and metadata header
# 3. Auto-create architect task
# 4. Auto-start architect → Create implementation_plan.md
# 5. Validate and auto-chain to implementer
# 6. Continue through tester → documenter
# 7. Complete with all outputs validated

# Verify results
ls enhancements/demo-test/
# Should show:
# - requirements-analyst/analysis_summary.md
# - architect/implementation_plan.md
# - implementer/test_plan.md
# - tester/test_summary.md
# - documenter/documentation_summary.md
# - logs/ (all agent execution logs in one directory)
```

**Automation Levels**:

```bash
# Fully Manual (prompts for everything)
.claude/queues/queue_manager.sh add "..." "..." "..." "..." "..." "..." false false

# Semi-Automated (auto-complete but manual chain)
.claude/queues/queue_manager.sh add "..." "..." "..." "..." "..." "..." true false

# Fully Automated (runs entire workflow hands-off) ⭐
.claude/queues/queue_manager.sh add "..." "..." "..." "..." "..." "..." true true

# Control integration tasks via environment variable
export AUTO_INTEGRATE="never"   # No integration (for testing)
export AUTO_INTEGRATE="always"  # Auto-create integration tasks
export AUTO_INTEGRATE="prompt"  # Ask before creating (default)
```

## 📁 Project Structure

```
your-project/
├── .claude/                      # Multi-agent system (v2.0)
│   ├── agents/                   # Agent definitions (enhanced)
│   │   ├── requirements-analyst.md
│   │   ├── architect.md
│   │   ├── implementer.md
│   │   ├── tester.md
│   │   ├── documenter.md
│   │   ├── github-integration-coordinator.md
│   │   └── atlassian-integration-coordinator.md
│   ├── hooks/                    # Workflow automation
│   │   └── on-subagent-stop.sh  # Enhanced with validation
│   ├── queues/                   # Task management
│   │   ├── queue_manager.sh     # v2.0 with contract validation
│   │   ├── task_queue.json
│   │   └── workflow_templates.json
│   ├── mcp-servers/             # MCP configuration (optional)
│   │   ├── github-config.json
│   │   ├── atlassian-config.json
│   │   └── [configuration guides]
│   ├── logs/                    # System logs
│   │   └── queue_operations.log
│   ├── status/                  # Workflow state
│   ├── AGENT_CONTRACTS.json     # **Source of truth** - Agent specifications
│   ├── WORKFLOW_STATES.json     # State machine definitions
│   ├── WORKFLOW_GUIDE.md        # Workflow patterns and queue commands
│   ├── INTEGRATION_GUIDE.md     # GitHub/Jira integration (detailed)
│   ├── TASK_PROMPT_DEFAULTS.md  # Agent prompt templates
│   └── settings.local.json      # Claude Code configuration
├── enhancements/                # Feature requests
│   └── feature-name/
│       ├── feature-name.md           # Enhancement spec
│       ├── requirements-analyst/     # Agent subdirectories
│       │   └── analysis_summary.md   # With metadata header
│       ├── architect/
│       │   └── implementation_plan.md
│       ├── implementer/
│       │   └── test_plan.md
│       ├── tester/
│       │   └── test_summary.md
│       ├── documenter/
│       │   └── documentation_summary.md
│       └── logs/                     # All agent logs
│           ├── requirements-analyst_task_*_*.log
│           ├── architect_task_*_*.log
│           ├── implementer_task_*_*.log
│           ├── tester_task_*_*.log
│           └── documenter_task_*_*.log
├── README.md                    # This file - project overview
├── INSTALLATION.md              # Setup instructions
├── CUSTOMIZATION.md             # Customization guide
└── [your project files]
```

## 🏗️ System Architecture

The multi-agent system follows a contract-based architecture where all behavior is formally specified.

### Core Components

**AGENT_CONTRACTS.json** (Source of Truth):
- Defines 7 specialized agents
- Specifies exact input/output requirements
- Declares success/failure status codes
- Maps workflow transitions (next_agents)
- Enforces output structure via validation

**WORKFLOW_STATES.json** (State Machine):
- Defines 11 workflow states
- Specifies valid state transitions
- Identifies terminal vs. transitional states
- Flags integration trigger points
- Documents state attributes

**queue_manager.sh** (Workflow Engine):
- Loads and validates agent contracts
- Manages task lifecycle (add, start, complete, fail, cancel)
- Validates outputs before workflow progression
- Auto-chains to next agent based on contracts
- Inherits automation settings through workflow
- Provides contract query functions

**on-subagent-stop.sh** (Hook Orchestration):
- Detects agent completion status
- Triggers output validation
- Handles integration task creation
- Manages auto-chaining
- Updates queue state

### Agent Specialization

Each agent has a **single, well-defined responsibility**:

| Agent | Role | Primary Function |
|-------|------|------------------|
| requirements-analyst | analysis | What needs to be built |
| architect | technical_design | How to build it (design) |
| implementer | implementation | Build it (code) |
| tester | testing | Validate it works |
| documenter | documentation | Explain how to use it |
| github-integration-coordinator | integration | Sync with GitHub |
| atlassian-integration-coordinator | integration | Sync with Jira/Confluence |

**Principle**: Agents never overstep their boundaries. Architectural decisions stay with architect, coding stays with implementer, testing stays with tester.

### Workflow Automation

The system supports multiple automation levels:

**Level 1: Fully Manual** (`false false`):
- Prompts to complete each task
- Prompts to create next task
- Prompts to start next task
- Full human control at every step

**Level 2: Auto-Complete** (`true false`):
- Auto-completes tasks
- Stops after completion
- Requires manual task creation

**Level 3: Auto-Chain** (`false true`):
- Prompts to complete
- Auto-creates and auto-starts next task
- Semi-automated workflow

**Level 4: Fully Automated** (`true true`) ⭐:
- Auto-completes tasks
- Auto-creates next tasks
- Auto-starts next tasks
- Zero-prompt workflow execution

**Plus Environment Control**:
```bash
export AUTO_INTEGRATE="never"   # Skip integration prompts
export AUTO_INTEGRATE="prompt"  # Ask before integration (default)
export AUTO_INTEGRATE="always"  # Auto-create integration tasks
```

## 🔄 Development Workflow

### Standard Feature Development

```
1. Requirements Analyst
   └─> Analyzes requirements, creates plan
       └─> Status: READY_FOR_DEVELOPMENT
       └─> Output: requirements-analyst/analysis_summary.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

2. Architect
   └─> Designs architecture and technical specs
       └─> Status: READY_FOR_IMPLEMENTATION
       └─> Output: architect/implementation_plan.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

3. Implementer
   └─> Writes production code
       └─> Status: READY_FOR_TESTING
       └─> Output: implementer/test_plan.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

4. Tester
   └─> Creates and runs test suite
       └─> Status: TESTING_COMPLETE
       └─> Output: tester/test_summary.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

5. Documenter (optional)
   └─> Updates documentation
       └─> Status: DOCUMENTATION_COMPLETE
       └─> Output: documenter/documentation_summary.md
       └─> Validation: ✓ File exists, ✓ Metadata header present
```

See [.claude/WORKFLOW_GUIDE.md](.claude/WORKFLOW_GUIDE.md) for other workflow patterns.

## 📚 Documentation

### Getting Started (Essential Reading)
- **[README.md](README.md)** - This file - Overview, architecture, quick start
- **[INSTALLATION.md](INSTALLATION.md)** - Step-by-step setup and verification
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapting template to your project

### System Reference (For Daily Use)
- **[.claude/WORKFLOW_GUIDE.md](.claude/WORKFLOW_GUIDE.md)** - Workflow patterns, queue commands, best practices
- **[.claude/AGENT_CONTRACTS.json](.claude/AGENT_CONTRACTS.json)** - **Source of truth** - Agent specifications
- **[.claude/WORKFLOW_STATES.json](.claude/WORKFLOW_STATES.json)** - State machine definitions

### Advanced Topics (As Needed)
- **[.claude/INTEGRATION_GUIDE.md](.claude/INTEGRATION_GUIDE.md)** - GitHub/Jira integration setup and configuration
- **[.claude/TASK_PROMPT_DEFAULTS.md](.claude/TASK_PROMPT_DEFAULTS.md)** - Agent prompt templates (reference)
- **Individual agent `.md` files** - Complete specifications for each agent

### Quick Reference
Use artifacts from this conversation:
- **Quick Reference Card** - Common commands cheat sheet
- **Implementation Checklist** - Deployment verification
- **Deployment Summary** - What files go where

## ⚠️ SECURITY WARNING

**CRITICAL: Never commit API credentials to version control!**

The MCP configuration files in `.claude/mcp-servers/` are templates that use environment variables for credentials:

```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}",
    "JIRA_API_TOKEN": "${JIRA_API_TOKEN}"
  }
}
```

**Credential Storage Options:**

*Option 1: Secrets Manager (Recommended)*
- Use a secrets management solution for enhanced security
- Provides automatic rotation, audit logs, and team access control

*Option 2: Environment Variables (Simpler)*
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc)
export GITHUB_TOKEN="ghp_your_token_here"
export JIRA_API_TOKEN="your_jira_token_here"
export JIRA_EMAIL="your-email@company.com"
```

See [.claude/mcp-servers/SECURITY_README.md](.claude/mcp-servers/SECURITY_README.md) for security best practices.

## 🧪 Example Project

This template includes a working Python CLI task manager as a demonstration:

- **Source**: `src/task_manager.py` - Simple task management CLI
- **Tests**: `tests/test_task_manager.py` - Comprehensive test suite
- **Demo Enhancement**: `enhancements/demo-test/` - Minimal test for verification
- **Full Enhancement**: `enhancements/add-json-export/` - Complete workflow example

Run the example:

```bash
# Try the task manager
python src/task_manager.py add "Test task" -d "Testing the app"
python src/task_manager.py list

# Run tests
python -m unittest discover tests
```

## 🎓 Learning Resources

### For First-Time Users

1. **Read** [.claude/README.md](.claude/README.md) - Understand the system
2. **Review** [.claude/AGENT_CONTRACTS.json](.claude/AGENT_CONTRACTS.json) - See agent specifications
3. **Study** [.claude/WORKFLOW_GUIDE.md](.claude/WORKFLOW_GUIDE.md) - Learn workflow patterns
4. **Try** `enhancements/demo-test/` - Simple test enhancement
5. **Explore** `enhancements/add-json-export/` - Full workflow example
6. **Customize** [CUSTOMIZATION.md](CUSTOMIZATION.md) - Adapt to your project

### Key Concepts

- **Agent Contracts**: Formal specifications (JSON) define agent behavior
- **Output Validation**: System validates outputs before chaining to next agent
- **Metadata Headers**: Every document is self-documenting with YAML frontmatter
- **Status Codes**: Trigger workflow transitions and next agent selection
- **State Machine**: Defines valid workflow states and transitions
- **Hook Automation**: Detects completion, validates, and suggests next steps
- **Enhancement-First**: Start with clear requirements document

### Understanding the Contract System

The system is driven by **AGENT_CONTRACTS.json**, which defines for each agent:

```json
{
  "inputs": {
    "required": [{"name": "...", "pattern": "...", "description": "..."}]
  },
  "outputs": {
    "root_document": "analysis_summary.md",
    "output_directory": "requirements-analyst",
    "additional_required": []
  },
  "statuses": {
    "success": [{"code": "READY_FOR_DEVELOPMENT", "next_agents": ["architect"]}],
    "failure": [{"code": "BLOCKED", "pattern": "BLOCKED: {reason}"}]
  },
  "metadata_required": true
}
```

This contract:
- Validates that `analysis_summary.md` exists
- Checks for metadata header (5 required fields)
- Determines `architect` is the next agent
- Builds the correct source path for the next task

**Single Source of Truth**: All workflow logic derives from these contracts.

## 🛠️ Requirements

- **Claude Code** - This template is designed for use with Claude Code
- **bash** - For hook scripts and queue management
- **jq** - For JSON processing (install via `brew install jq` or package manager)

Optional:
- **Python 3.7+** - For the example project (not required for template itself)
- **Node.js 16+** - For MCP servers (GitHub/Jira integration)

## 🔧 System Components

### Core Files

| File | Purpose |
|------|---------|
| `AGENT_CONTRACTS.json` | **Source of truth** - Agent specifications |
| `WORKFLOW_STATES.json` | State machine with valid transitions |
| `WORKFLOW_GUIDE.md` | Human-readable workflow patterns |
| `queue_manager.sh` | Task management with contract validation |
| `on-subagent-stop.sh` | Workflow orchestration with validation |

### Agent Definitions

Each agent has a `.md` file in `.claude/agents/` with:
- Role and purpose
- When to use / not use
- Workflow position
- Output requirements
- Success/failure statuses
- Contract reference

### Configuration

- `settings.local.json` - Claude Code hook configuration
- `task_queue.json` - Active task queue database
- `workflow_templates.json` - Predefined workflow patterns

## 📖 How It Works

### Real Example: demo-test Enhancement

Starting from `enhancements/demo-test/demo-test.md`, the system automatically:

#### 1. Requirements Analyst Creates Output

```markdown
---
enhancement: demo-test
agent: requirements-analyst
task_id: task_1234567890_12345
timestamp: 2025-10-21T14:30:00Z
status: READY_FOR_DEVELOPMENT
---

# Analysis Summary
[Requirements analysis content...]
```

Location: `enhancements/demo-test/requirements-analyst/analysis_summary.md`

#### 2. System Validates

```bash
🔍 Validating outputs from requirements-analyst...
  ✓ Root document exists: analysis_summary.md
  ✓ Metadata header present
  ✓ Required fields: enhancement, agent, task_id, timestamp, status
✅ Output validation passed
```

#### 3. System Determines Next Agent

```bash
📋 Consulting AGENT_CONTRACTS.json:
  Current agent: requirements-analyst
  Current status: READY_FOR_DEVELOPMENT
  Next agent: architect (from contract)

✅ Auto-chained to architect: task_1234567890_12346
   Source: enhancements/demo-test/requirements-analyst/analysis_summary.md
   Inherited automation: auto_complete=true, auto_chain=true

🚀 Auto-starting next task...
```

#### 4. Workflow Continues Automatically

Process repeats:
- **Architect** → `implementation_plan.md` → `READY_FOR_IMPLEMENTATION`
- **Implementer** → `test_plan.md` → `READY_FOR_TESTING`
- **Tester** → `test_summary.md` → `TESTING_COMPLETE`
- **Documenter** → `documentation_summary.md` → `DOCUMENTATION_COMPLETE`

Each step includes validation before proceeding.

#### 5. Final Result

```
enhancements/demo-test/
├── demo-test.md                              # Original spec
├── requirements-analyst/
│   └── analysis_summary.md                   # ✓ With metadata
├── architect/
│   └── implementation_plan.md                # ✓ With metadata
├── implementer/
│   └── test_plan.md                          # ✓ With metadata
├── tester/
│   └── test_summary.md                       # ✓ With metadata
├── documenter/
│   └── documentation_summary.md              # ✓ With metadata
└── logs/                                     # All agent logs in one place
    ├── requirements-analyst_task_..._*.log
    ├── architect_task_..._*.log
    ├── implementer_task_..._*.log
    ├── tester_task_..._*.log
    └── documenter_task_..._*.log
```

All files have metadata headers, all validated, complete workflow trace in logs.

## 🎯 Complete Walkthrough: demo-test

### Step-by-Step: Running the Demo Enhancement

**Prerequisites**:
```bash
# Ensure you're in project root
pwd  # Should show your project directory

# Check queue manager works
.claude/queues/queue_manager.sh version
# Should show: Queue Manager v2.0.0

# Check contracts file exists
ls -la .claude/AGENT_CONTRACTS.json
```

**Run the Full Workflow**:

```bash
# 1. Configure for full automation
export AUTO_INTEGRATE="never"

# 2. Create the first task (fully automated)
TASK_ID=$(.claude/queues/queue_manager.sh add \
  "Demo test - requirements analysis" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Analyze requirements for demo test enhancement" \
  true \
  true)

# Output: task_1761091368_XXXXX (your task ID)

# 3. Start the workflow
.claude/queues/queue_manager.sh start $TASK_ID

# Now watch as the system:
# - Runs requirements-analyst
# - Validates output
# - Auto-chains to architect
# - Auto-starts architect
# - Continues through implementer → tester → documenter
# - All automatically with zero prompts!

# 4. When complete, verify results
tree enhancements/demo-test/

# Output:
# enhancements/demo-test/
# ├── demo-test.md
# ├── requirements-analyst/
# │   └── analysis_summary.md
# ├── architect/
# │   └── implementation_plan.md
# ├── implementer/
# │   └── test_plan.md
# ├── tester/
# │   └── test_summary.md
# ├── documenter/
# │   └── documentation_summary.md
# └── logs/
#     ├── requirements-analyst_task_*_*.log
#     ├── architect_task_*_*.log
#     ├── implementer_task_*_*.log
#     ├── tester_task_*_*.log
#     └── documenter_task_*_*.log

# 5. Check queue status
.claude/queues/queue_manager.sh status

# All agents should be idle
# All tasks should be in completed_tasks
```

**Verify Metadata Headers**:

```bash
# Each output should have proper metadata
head -10 enhancements/demo-test/requirements-analyst/analysis_summary.md

# Expected:
# ---
# enhancement: demo-test
# agent: requirements-analyst
# task_id: task_1234567890_12345
# timestamp: 2025-10-21T14:30:00Z
# status: READY_FOR_DEVELOPMENT
# ---
```

**Review Agent Logs**:

```bash
# See what each agent did
cat enhancements/demo-test/logs/requirements-analyst_*.log
cat enhancements/demo-test/logs/architect_*.log
# etc.
```

### Troubleshooting the Demo

**If validation fails**:
```bash
# Check what was created
ls -la enhancements/demo-test/requirements-analyst/

# If file missing:
# - Check agent logs for errors
# - Verify agent understood output directory requirements

# If metadata missing:
# - Check file content
# - Verify YAML frontmatter present
```

**If auto-chain doesn't work**:
```bash
# Verify task has auto_chain=true
jq '.completed_tasks[-1] | {auto_complete, auto_chain}' .claude/queues/task_queue.json

# Should show:
# {
#   "auto_complete": true,
#   "auto_chain": true
# }
```

**If wrong agent suggested**:
```bash
# Check contract
jq '.agents."requirements-analyst".statuses.success[0]' .claude/AGENT_CONTRACTS.json

# Should show architect as next_agents
```

## 🤝 Contributing

This template is designed to be adapted to your needs. Suggested improvements:

- Additional specialized agents for your domain
- Custom workflow templates
- Project-specific automation
- Integration with CI/CD systems
- Additional example projects in other languages

## 📝 License

This template is provided as-is for use in your projects. Adapt and modify freely.

## 🙏 Acknowledgments

This template demonstrates contract-based multi-agent development workflows with Claude Code, showcasing how formal specifications, automated validation, and intelligent chaining create reliable, repeatable development processes.

## 🔗 Links

- **Claude Code**: https://claude.ai/code
- **Documentation**: See `.claude/README.md` for complete system documentation
- **Example Enhancement**: See `enhancements/add-json-export/` for full workflow
- **Demo Enhancement**: See `enhancements/demo-test/` for quick test

---

**Ready to get started?** See [INSTALLATION.md](INSTALLATION.md) for step-by-step setup instructions.

**Need to customize?** See [CUSTOMIZATION.md](CUSTOMIZATION.md) for adapting to your project.

**Want to understand workflows?** See [.claude/WORKFLOW_GUIDE.md](.claude/WORKFLOW_GUIDE.md) for patterns and queue commands.

**Need integration?** See [.claude/INTEGRATION_GUIDE.md](.claude/INTEGRATION_GUIDE.md) for GitHub/Jira setup.

---
