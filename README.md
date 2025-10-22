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

- **Agent Contracts**: Formal JSON specifications replace implicit behavior
- **Output Validation**: Automated validation against contracts before chaining
- **Metadata Headers**: All documents include YAML frontmatter for traceability
- **Smart Auto-Chaining**: Contract-based next agent determination
- **Workflow State Machine**: Formal state definitions with valid transitions
- **Simplified Documentation**: Single source of truth (contracts) with human guides
- **Enhanced Error Messages**: Clear feedback when validation fails

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

### 3. Customize Agents

Edit agent files in `.claude/agents/` to customize for your project:
- Programming languages and frameworks
- Coding standards and conventions
- Testing requirements
- Documentation standards

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions.

### 4. Start Building

```bash
# Create enhancement specification
mkdir -p enhancements/my-feature
cat > enhancements/my-feature/my-feature.md << 'EOF'
# My Feature

## Goal
Add feature X to improve Y

## Requirements
- Must: Do X
- Must: Handle Y
EOF

# Add task to queue
.claude/queues/queue_manager.sh add \
  "Analyze my-feature" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/my-feature/my-feature.md" \
  "Analyze requirements for my-feature"

# Start task
.claude/queues/queue_manager.sh start <task_id>

# System will:
# 1. Run requirements-analyst
# 2. Validate outputs (analysis_summary.md with metadata header)
# 3. Suggest next agent (architect)
# 4. Optionally auto-chain to next phase
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
│   ├── AGENT_CONTRACTS.json      # Source of truth
│   ├── WORKFLOW_STATES.json      # State machine
│   ├── WORKFLOW_GUIDE.md         # Workflow patterns
│   ├── README.md                 # System documentation
│   ├── TASK_PROMPT_DEFAULTS.md   # Prompt templates
│   └── QUEUE_SYSTEM_GUIDE.md     # Queue usage guide
├── enhancements/                 # Feature requests
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
│       └── logs/                     # Agent execution logs
└── [your project files]
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

### Getting Started
- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation and setup
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapting template to your project
- **[.claude/README.md](.claude/README.md)** - Multi-agent system overview

### Reference Documentation
- **[.claude/AGENT_CONTRACTS.json](.claude/AGENT_CONTRACTS.json)** - **Source of truth** for agent specifications
- **[.claude/WORKFLOW_GUIDE.md](.claude/WORKFLOW_GUIDE.md)** - Workflow patterns and best practices
- **[.claude/WORKFLOW_STATES.json](.claude/WORKFLOW_STATES.json)** - State machine definitions
- **[.claude/TASK_PROMPT_DEFAULTS.md](.claude/TASK_PROMPT_DEFAULTS.md)** - Agent prompt templates
- **[.claude/QUEUE_SYSTEM_GUIDE.md](.claude/QUEUE_SYSTEM_GUIDE.md)** - Task queue usage

### Agent Documentation
- Individual agent `.md` files in `.claude/agents/` - Each agent's complete specification

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

### 1. Agent Completes Work

```markdown
---
enhancement: add-json-export
agent: requirements-analyst
task_id: task_1234567890_12345
timestamp: 2025-10-21T10:30:00Z
status: READY_FOR_DEVELOPMENT
---

# Analysis Summary
...
```

### 2. Hook Validates Outputs

```bash
🔍 Validating outputs from requirements-analyst...
✅ Output validation passed: enhancements/add-json-export/requirements-analyst/analysis_summary.md
  ✓ Root document exists
  ✓ Metadata header present (5 fields)
  ✓ All required files present
```

### 3. System Determines Next Agent

```bash
🔗 Next Agent Suggestion:
   Agent: architect
   Source: enhancements/add-json-export/requirements-analyst/analysis_summary.md

Create next task? [y/N]:
```

### 4. Workflow Continues

Process repeats through architect → implementer → tester → documenter with validation at each step.

## 🎯 Quick Example: Using demo-test

Test the system with the included demo enhancement:

```bash
# 1. Add requirements task
TASK_ID=$(.claude/queues/queue_manager.sh add \
  "Demo test - requirements analysis" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Analyze the requirements for this simple demo feature")

# 2. Start the task
.claude/queues/queue_manager.sh start $TASK_ID

# 3. After completion, system validates and suggests next agent
# Follow prompts to continue through workflow

# 4. Check final results
ls enhancements/demo-test/
# Should see:
# - requirements-analyst/analysis_summary.md
# - architect/implementation_plan.md
# - implementer/test_plan.md
# - tester/test_summary.md
# - logs/
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

**Want to understand the system?** See [.claude/WORKFLOW_GUIDE.md](.claude/WORKFLOW_GUIDE.md) for workflow patterns.