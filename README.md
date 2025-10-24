# Claude Multi-Agent Development Template

A contract-based multi-agent development workflow system using Claude Code. This template provides specialized AI agents with formal contracts, automated validation, intelligent workflow chaining, and a comprehensive skills system.

**Version**: 3.0.0 - Modular script architecture with skills system

## 🎯 What Is This?

This template provides a multi-agent system that breaks down software development into specialized roles, each handled by a dedicated Claude agent with formal contracts defining inputs, outputs, and workflow transitions:

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
- Organized by category (analysis, architecture, implementation, testing, documentation, ui-design, database)

## ✨ Features

### Core System
- 🤖 **7 Specialized Agents** - Clear responsibilities defined by formal contracts
- 📜 **Agent Contracts** - Formal specifications for inputs, outputs, and statuses
- ✅ **Output Validation** - Automatic validation before workflow progression
- 🔄 **Automated Workflows** - Contract-based intelligent task chaining
- 📋 **Task Queue System** - Organize and track work across agents
- 📊 **Workflow Patterns** - Predefined patterns for common scenarios
- 🔍 **State Machine** - Formal state definitions and valid transitions
- 🧠 **Skills System** - Domain expertise in reusable skill modules

### Quality & Tracking
- 📝 **Metadata Headers** - All outputs are self-documenting and traceable
- 🧪 **Comprehensive Logging** - Agent execution logged for analysis
- 🔗 **Cross-Platform Sync** - GitHub and Jira/Confluence integration
- 🎯 **Contract Validation** - Outputs validated against formal specifications
- 🏗️ **Modular Architecture** - Clean separation of concerns in script design

### Example & Documentation
- 🐍 **Example Application** - Sample Python CLI app with full enhancement workflow
- 📚 **Complete Documentation** - Guides for every aspect of the system

## 🆕 What's New in v3.0

### Modular Script Architecture ✅

Complete refactoring of the script system:

- **New Command Structure**: `cmat.sh <category> <command>` (git-like interface)
- **Organized Scripts**: Separated into queue, workflow, skills, integration, agent commands
- **Shared Utilities**: Common functions in reusable library
- **Better Maintainability**: Each script has single, clear responsibility

**Old**:
```bash
.claude/queues/queue_manager.sh add "Task" "agent" ...
.claude/queues/queue_manager.sh validate_agent_outputs ...
```

**New v3.0**:
```bash
cmat.sh queue add "Task" "agent" ...
cmat.sh workflow validate ...
cmat.sh skills list
```

### Skills System ✅

Comprehensive skills providing specialized knowledge to agents:

- **14 Built-in Skills**: Requirements elicitation, API design, code refactoring, test patterns, etc.
- **Auto-injection**: Skills automatically added to agent prompts
- **Category Organization**: Analysis, architecture, implementation, testing, documentation, UI design, database
- **Extensible**: Easy to add custom skills for your domain
- **Agent Assignment**: Each agent has appropriate skills for their role

### Script Organization ✅
```
.claude/scripts/
├── cmat.sh                    # Main command launcher
├── queue-commands.sh          # Task queue operations
├── workflow-commands.sh       # Workflow orchestration
├── skills-commands.sh         # Skills management
├── integration-commands.sh    # External system sync
├── agent-commands.sh          # Agent operations
└── common-commands.sh         # Shared utilities
```

### Key Improvements from v2.x

- ✅ **Single Command Entry Point**: `cmat.sh` for all operations
- ✅ **Skills System**: Domain expertise automatically available to agents
- ✅ **Modular Design**: Easy to maintain and extend
- ✅ **Better Organization**: Clear separation of concerns
- ✅ **Improved Testing**: Each component testable independently

## 🚀 Quick Start

### 1. Install the Template
```bash
# Copy .claude directory to your project
cp -r ClaudeMultiAgentTemplate/.claude /path/to/your/project/

# Make scripts executable
chmod +x /path/to/your/project/.claude/scripts/*.sh
chmod +x /path/to/your/project/.claude/hooks/*.sh
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

### 3. Customize for Your Project

Edit agent files in `.claude/agents/` and update skills in `.claude/skills/` to match your:
- Programming languages and frameworks
- Coding standards and conventions
- Testing requirements
- Documentation standards
- Domain-specific expertise

See [INSTALLATION.md](INSTALLATION.md) for detailed setup and [CUSTOMIZATION.md](CUSTOMIZATION.md) for adaptation guidance.

### 4. Test the System

**Quick Test with Demo Enhancement**:
```bash
# Navigate to project root
cd /path/to/your/project

# Set environment to skip integration prompts
export AUTO_INTEGRATE="never"

# Create fully automated task
TASK_ID=$(cmat.sh queue add \
  "Demo test - requirements analysis" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Analyze requirements for demo test enhancement" \
  true \
  true)

# Start and watch it run through entire workflow automatically
cmat.sh queue start $TASK_ID

# The system will:
# 1. Run requirements-analyst → Create analysis_summary.md
# 2. Validate output and metadata header
# 3. Auto-create architect task with skills
# 4. Auto-start architect → Create implementation_plan.md
# 5. Validate and auto-chain to implementer
# 6. Continue through tester → documenter
# 7. Complete with all outputs validated

# Verify results
ls enhancements/demo-test/
```

**Automation Levels**:
```bash
# Fully Manual (prompts for everything)
cmat.sh queue add "..." "..." "..." "..." "..." "..." false false

# Semi-Automated (auto-complete but manual chain)
cmat.sh queue add "..." "..." "..." "..." "..." "..." true false

# Fully Automated (runs entire workflow hands-off) ⭐
cmat.sh queue add "..." "..." "..." "..." "..." "..." true true
```

## 📁 Project Structure
```
your-project/
├── .claude/                      # Multi-agent system (v3.0)
│   ├── scripts/                  # Command scripts (NEW v3.0)
│   │   ├── cmat.sh              # Main command launcher
│   │   ├── queue-commands.sh     # Queue operations
│   │   ├── workflow-commands.sh  # Workflow orchestration
│   │   ├── skills-commands.sh    # Skills management
│   │   ├── integration-commands.sh # External sync
│   │   ├── agent-commands.sh     # Agent operations
│   │   └── common-commands.sh    # Shared utilities
│   ├── agents/                   # Agent definitions
│   │   ├── requirements-analyst.md
│   │   ├── architect.md
│   │   ├── implementer.md
│   │   ├── tester.md
│   │   ├── documenter.md
│   │   ├── github-integration-coordinator.md
│   │   ├── atlassian-integration-coordinator.md
│   │   └── agents.json
│   ├── skills/                   # Skills system (NEW v3.0)
│   │   ├── skills.json           # Skills registry
│   │   ├── requirements-elicitation/
│   │   ├── user-story-writing/
│   │   ├── bug-triage/
│   │   ├── api-design/
│   │   ├── architecture-patterns/
│   │   ├── error-handling/
│   │   ├── code-refactoring/
│   │   ├── test-design-patterns/
│   │   ├── test-coverage/
│   │   ├── technical-writing/
│   │   ├── api-documentation/
│   │   ├── desktop-ui-design/
│   │   ├── web-ui-design/
│   │   └── sql-development/
│   ├── hooks/                    # Workflow automation
│   │   └── on-subagent-stop.sh  # Enhanced with validation
│   ├── queues/                   # Task management
│   │   ├── task_queue.json
│   │   └── workflow_templates.json
│   ├── mcp-servers/             # MCP configuration (optional)
│   │   ├── github-config.json
│   │   ├── atlassian-config.json
│   │   └── [configuration guides]
│   ├── logs/                    # System logs
│   │   └── queue_operations.log
│   ├── status/                  # Workflow state
│   ├── AGENT_CONTRACTS.json     # Agent specifications
│   ├── WORKFLOW_STATES.json     # State machine definitions
│   ├── WORKFLOW_GUIDE.md        # Workflow patterns and commands
│   ├── INTEGRATION_GUIDE.md     # GitHub/Jira integration
│   ├── TASK_PROMPT_DEFAULTS.md  # Agent prompt templates
│   └── settings.local.json      # Claude Code configuration
├── enhancements/                # Feature requests
│   └── feature-name/
│       ├── feature-name.md           # Enhancement spec
│       ├── requirements-analyst/
│       ├── architect/
│       ├── implementer/
│       ├── tester/
│       ├── documenter/
│       └── logs/                     # All agent logs
├── README.md                    # This file
├── INSTALLATION.md              # Setup instructions
├── CUSTOMIZATION.md             # Customization guide
├── SKILL_TEMPLATE.md           # Template for creating skills (NEW v3.0)
└── [your project files]
```

## 🏗️ System Architecture

The multi-agent system follows a contract-based architecture where all behavior is formally specified.

### Core Components

**cmat.sh** (Command Launcher):
- Single entry point for all operations
- Routes commands to specialized subsystems
- Git-like command structure: `cmat.sh <category> <command>`

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

**Skills System** (Domain Expertise):
- 14 built-in skills covering common development tasks
- Automatically injected into agent prompts
- Organized by category for easy discovery
- Extensible for domain-specific knowledge

**Command Scripts** (Modular Operations):
- `queue-commands.sh` - Task lifecycle management
- `workflow-commands.sh` - Contract validation and chaining
- `skills-commands.sh` - Skills management
- `integration-commands.sh` - External system sync
- `agent-commands.sh` - Agent invocation

**on-subagent-stop.sh** (Hook Orchestration):
- Detects agent completion status
- Triggers output validation
- Handles integration task creation
- Manages auto-chaining

### Agent Specialization

Each agent has a **single, well-defined responsibility**:

| Agent | Role | Primary Function | Skills |
|-------|------|------------------|--------|
| requirements-analyst | analysis | What needs to be built | Requirements Elicitation, User Story Writing, Bug Triage |
| architect | technical_design | How to build it (design) | API Design, Architecture Patterns, UI Design |
| implementer | implementation | Build it (code) | Error Handling, Code Refactoring, SQL Development |
| tester | testing | Validate it works | Test Design Patterns, Test Coverage, Bug Triage |
| documenter | documentation | Explain how to use it | Technical Writing, API Documentation |
| github-integration-coordinator | integration | Sync with GitHub | (none) |
| atlassian-integration-coordinator | integration | Sync with Jira/Confluence | (none) |

## 🔄 Development Workflow

### Standard Feature Development
```
1. Requirements Analyst
   └─> Analyzes requirements, creates plan
       └─> Skills: Requirements Elicitation, User Story Writing
       └─> Status: READY_FOR_DEVELOPMENT
       └─> Output: requirements-analyst/analysis_summary.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

2. Architect
   └─> Designs architecture and technical specs
       └─> Skills: API Design, Architecture Patterns
       └─> Status: READY_FOR_IMPLEMENTATION
       └─> Output: architect/implementation_plan.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

3. Implementer
   └─> Writes production code
       └─> Skills: Error Handling, Code Refactoring
       └─> Status: READY_FOR_TESTING
       └─> Output: implementer/test_plan.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

4. Tester
   └─> Creates and runs test suite
       └─> Skills: Test Design Patterns, Test Coverage
       └─> Status: TESTING_COMPLETE
       └─> Output: tester/test_summary.md
       └─> Validation: ✓ File exists, ✓ Metadata header present

5. Documenter (optional)
   └─> Updates documentation
       └─> Skills: Technical Writing, API Documentation
       └─> Status: DOCUMENTATION_COMPLETE
       └─> Output: documenter/documentation_summary.md
       └─> Validation: ✓ File exists, ✓ Metadata header present
```

See [.claude/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) for other workflow patterns.

## 📚 Documentation

### Getting Started (Essential Reading)
- **[README.md](README.md)** - This file - Overview, architecture, quick start
- **[INSTALLATION.md](INSTALLATION.md)** - Step-by-step setup and verification
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapting template to your project
- **[SKILL_TEMPLATE.md](SKILL_TEMPLATE.md)** - Template for creating new skills

### System Reference (For Daily Use)
- **[.claude/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md)** - Workflow patterns, commands, best practices
- **[SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md)** - Complete cmat.sh command reference (NEW v3.0)
- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Skills system documentation (NEW v3.0)
- **[.claude/AGENT_CONTRACTS.json](.claude/AGENT_CONTRACTS.json)** - Agent specifications
- **[.claude/WORKFLOW_STATES.json](.claude/WORKFLOW_STATES.json)** - State machine definitions

### Advanced Topics (As Needed)
- **[.claude/INTEGRATION_GUIDE.md](.claude/docs/INTEGRATION_GUIDE.md)** - GitHub/Jira integration setup
- **[.claude/TASK_PROMPT_DEFAULTS.md](.claude/docs/TASK_PROMPT_DEFAULTS.md)** - Agent prompt templates
- **Individual agent `.md` files** - Complete specifications for each agent

## ⚠️ SECURITY WARNING

**CRITICAL: Never commit API credentials to version control!**

The MCP configuration files in `.claude/mcp-servers/` are templates that use environment variables for credentials.

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

1. **Read** this README - Understand the system
2. **Install** following [INSTALLATION.md](INSTALLATION.md) - Set up in your project
3. **Review** [.claude/AGENT_CONTRACTS.json](.claude/AGENT_CONTRACTS.json) - See agent specs
4. **Study** [.claude/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) - Learn workflow patterns
5. **Explore** [SKILLS_GUIDE.md](SKILLS_GUIDE.md) - Understand the skills system
6. **Try** `enhancements/demo-test/` - Simple test enhancement
7. **Explore** `enhancements/add-json-export/` - Full workflow example
8. **Customize** per [CUSTOMIZATION.md](CUSTOMIZATION.md) - Adapt to your needs

### Key Concepts

- **Agent Contracts**: Formal specifications (JSON) define agent behavior
- **Output Validation**: System validates outputs before chaining to next agent
- **Metadata Headers**: Every document is self-documenting with YAML frontmatter
- **Status Codes**: Trigger workflow transitions and next agent selection
- **State Machine**: Defines valid workflow states and transitions
- **Skills**: Domain expertise automatically provided to agents
- **Hook Automation**: Detects completion, validates, and suggests next steps
- **Enhancement-First**: Start with clear requirements document

## 🛠️ Requirements

- **Claude Code** - This template is designed for use with Claude Code
- **bash** - For scripts and queue management
- **jq** - For JSON processing (install via `brew install jq` or package manager)

Optional:
- **Python 3.7+** - For the example project (not required for template itself)
- **Node.js 16+** - For MCP servers (GitHub/Jira integration)

## 🔧 Command Reference

### Queue Commands
```bash
cmat.sh queue add <title> <agent> <priority> <type> <source> <desc> [auto_complete] [auto_chain]
cmat.sh queue start <task_id>
cmat.sh queue complete <task_id> [result] [--auto-chain]
cmat.sh queue cancel <task_id> [reason]
cmat.sh queue cancel-all [reason]
cmat.sh queue fail <task_id> [error]
cmat.sh queue status
cmat.sh queue list <pending|active|completed|failed|all> [json|compact]
cmat.sh queue metadata <task_id> <key> <value>
```

### Workflow Commands
```bash
cmat.sh workflow validate <agent> <enhancement_dir>
cmat.sh workflow next-agent <agent> <status>
cmat.sh workflow next-source <enhancement> <next_agent> <current_agent>
cmat.sh workflow auto-chain <task_id> <status>
cmat.sh workflow template <template_name> [description]
```

### Skills Commands
```bash
cmat.sh skills list
cmat.sh skills get <agent-name>
cmat.sh skills load <skill-directory>
cmat.sh skills prompt <agent-name>
cmat.sh skills test
```

### Integration Commands
```bash
cmat.sh integration add <status> <source> <agent> [parent_task_id]
cmat.sh integration sync <task_id>
cmat.sh integration sync-all
```

### Agent Commands
```bash
cmat.sh agents list
cmat.sh agents generate-json
```

### Utility Commands
```bash
cmat.sh version
cmat.sh help
```

See [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) for complete command documentation.

## 📖 How It Works

### Real Example: demo-test Enhancement

Starting from `enhancements/demo-test/demo-test.md`, the system automatically:

#### 1. Requirements Analyst Creates Output
```markdown
---
enhancement: demo-test
agent: requirements-analyst
task_id: task_1234567890_12345
timestamp: 2025-10-24T14:30:00Z
status: READY_FOR_DEVELOPMENT
---

# Analysis Summary
[Requirements analysis content...]

**Skills Applied**:
- ✅ requirements-elicitation: Extracted functional requirements
- ✅ user-story-writing: Created user stories with acceptance criteria
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

With skills injected at each phase:
- **Architect** (with API Design, Architecture Patterns skills) → `READY_FOR_IMPLEMENTATION`
- **Implementer** (with Error Handling, Code Refactoring skills) → `READY_FOR_TESTING`
- **Tester** (with Test Design Patterns, Test Coverage skills) → `TESTING_COMPLETE`
- **Documenter** (with Technical Writing, API Documentation skills) → `DOCUMENTATION_COMPLETE`

## 🎯 Skills System

### Built-in Skills

**Analysis** (3 skills):
- Requirements Elicitation
- User Story Writing
- Bug Triage

**Architecture** (2 skills):
- API Design
- System Architecture Patterns

**Implementation** (2 skills):
- Error Handling Strategies
- Code Refactoring

**Testing** (2 skills):
- Test Design Patterns
- Test Coverage Analysis

**Documentation** (2 skills):
- Technical Writing
- API Documentation

**UI Design** (2 skills):
- Desktop UI Design
- Web UI Design

**Database** (1 skill):
- SQL Development

### Managing Skills
```bash
# List all available skills
cmat.sh skills list

# See which skills an agent has
cmat.sh skills get requirements-analyst

# View a skill's content
cmat.sh skills load requirements-elicitation

# Test skills system
cmat.sh skills test
```

### Creating Custom Skills

See [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md) for the template and [SKILLS_GUIDE.md](SKILLS_GUIDE.md) for complete documentation.

Quick example:
```bash
# 1. Create skill directory
mkdir -p .claude/skills/my-custom-skill

# 2. Create SKILL.md using template
cp SKILL_TEMPLATE.md .claude/skills/my-custom-skill/SKILL.md
# Edit to define your skill

# 3. Add to skills.json
# Edit .claude/skills/skills.json

# 4. Assign to agents
# Edit agent .md frontmatter: skills: [..., "my-custom-skill"]

# 5. Regenerate agents.json
cmat.sh agents generate-json
```

## 🤝 Contributing

This template is designed to be adapted to your needs. Suggested improvements:

- Additional specialized agents for your domain
- Custom workflow templates
- Domain-specific skills
- Project-specific automation
- Integration with CI/CD systems
- Additional example projects in other languages

## 📝 License

This template is provided as-is for use in your projects. Adapt and modify freely.

## 🔗 Links

- **Claude Code**: https://claude.ai/code
- **Claude Skills Docs**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- **Skills Best Practices**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **Complete Documentation**: See `.claude/` directory for all guides

---

**Ready to get started?** See [INSTALLATION.md](INSTALLATION.md) for step-by-step setup.

**Need to customize?** See [CUSTOMIZATION.md](CUSTOMIZATION.md) for adapting to your project.

**Want to understand workflows?** See [.claude/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) for patterns and commands.

**Creating skills?** See [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md) and [SKILLS_GUIDE.md](SKILLS_GUIDE.md).

---