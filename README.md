# Claude Multi-Agent Development Template

A template for implementing a multi-agent development workflow using Claude Code. This template provides specialized AI agents for requirements analysis, architecture, implementation, testing, and documentation.

## 🎯 What Is This?

This template provides a multi-agent system that breaks down software development into specialized roles, each handled by a dedicated Claude agent:

- **Requirements Analyst**: Analyzes user needs and creates implementation plans
- **Architect**: Designs system architecture and technical specifications
- **Implementer**: Writes production-quality code
- **Tester**: Creates comprehensive test suites
- **Documenter**: Maintains project documentation

## ✨ Features

- 🤖 **5 Specialized Agents** - Each with clear responsibilities and boundaries
- 🔄 **Automated Workflows** - If desired, hooks manage transitions between development phases.  The user has the option to allow automatic task chaining or intervene and set up tasks manually.
- 📋 **Task Queue System** - Organize and track work across agents
- 📊 **Workflow Templates** - Predefined patterns for common scenarios
- 📝 **Complete Documentation** - Guides for every aspect of the system
- 🧪 **Logging System** - Agent thinking is logged so that analysis can be done on what the agent was pondering as it did work
- 🐍 **Example Application** - Sample Python CLI app with full enhancement workflow

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

Add to your project's Claude Code settings or create `.claude/settings.local.json`:

```json
{
  "hooks": {
    "on_subagent_stop": ".claude/hooks/on-subagent-stop.sh",
    "on_stop": ".claude/hooks/on-stop.sh"
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

**Step 1: Add task to queue**
```bash
.claude/queues/queue_manager.sh add \
  "Analyze JSON export feature" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/add-json-export/add-json-export.md" \
  "Analyze requirements from enhancements/add-json-export/add-json-export.md"
```

This returns a task ID like `task_1234567890_12345`

**Step 2: Check queue status**
```bash
.claude/queues/queue_manager.sh status
```

You'll see:
```
📋 PENDING TASKS:
task_1234567890_12345: Analyze JSON export feature (requirements-analyst, priority: high)

🤖 AGENT STATUS:
requirements-analyst: idle
architect: idle
implementer: idle
tester: idle
documenter: idle
```

**Step 3: Start the task**
```bash
.claude/queues/queue_manager.sh start task_id (where task_id is the id from the add request above)
```

This will:
- Mark the task as active
- Show you the task description
- Run the prompt using the agent and source file provided

**Step 5: After agent completes, the queue manager will ask you if you want to mark the task complete.  
Alternatively, you can complete the task manually by passing in the task id and a final status**

```bash
.claude/queues/queue_manager.sh complete task_1234567890_12345 "READY_FOR_DEVELOPMENT"
```


#### Complete Example:

**Queue-Based Method:**

```bash
# Terminal: Add first task
$ .claude/queues/queue_manager.sh add "Analyze requirements" "requirements-analyst" "high" "..."

# Terminal: Start first task
$ .claude/queues/queue_manager.sh start task_123
Task started: task_123 (Analyze requirements)
Agent: [Works on task]

# Terminal: Mark complete, see what's next
$ .claude/queues/queue_manager.sh complete task_123 "READY_FOR_DEVELOPMENT"
✅ Task completed
📋 Next pending task: Design architecture (architect)

# Terminal: Add second task
$ .claude/queues/queue_manager.sh add "Design architecture" "architect" "high" "..."

# Terminal: Start next task
$ .claude/queues/queue_manager.sh start task_456

# Repeat...
```

## 📁 Project Structure

```
your-project/
├── .claude/                      # Multi-agent system
│   ├── agents/                   # Agent definitions
│   │   ├── requirements-analyst.md
│   │   ├── architect.md
│   │   ├── implementer.md
│   │   ├── tester.md
│   │   └── documenter.md
│   ├── hooks/                    # Workflow automation
│   │   ├── on-subagent-stop.sh
│   │   └── on-stop.sh
│   ├── queues/                   # Task management
│   │   ├── queue_manager.sh
│   │   ├── task_queue.json
│   │   └── workflow_templates.json
│   ├── README.md                 # System documentation
│   ├── AGENT_ROLE_MAPPING.md     # Role descriptions
│   ├── TASK_PROMPT_DEFAULTS.md   # Prompt templates
│   └── QUEUE_SYSTEM_GUIDE.md     # Queue usage guide
├── enhancements/                 # Feature requests
│   └── feature-name/
│       ├── feature.md           # Enhancement spec
│       └── logs/                # Agent logs
└── [your project files]
```

## 🔄 Development Workflow

### Standard Feature Development

```
1. Requirements Analyst
   └─> Analyzes requirements, creates plan
       └─> Status: READY_FOR_DEVELOPMENT

2. Architect
   └─> Designs architecture and technical specs
       └─> Status: READY_FOR_IMPLEMENTATION

3. Implementer
   └─> Writes production code
       └─> Status: READY_FOR_TESTING

4. Tester
   └─> Creates and runs test suite
       └─> Status: TESTING_COMPLETE

5. Documenter (optional)
   └─> Updates documentation
       └─> Status: DOCUMENTATION_COMPLETE
```

See [.claude/AGENT_ROLE_MAPPING.md](.claude/AGENT_ROLE_MAPPING.md) for other workflow patterns.

## 📚 Documentation

- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation and setup
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapting template to your project
- **[.claude/README.md](.claude/README.md)** - Multi-agent system overview
- **[.claude/AGENT_ROLE_MAPPING.md](.claude/AGENT_ROLE_MAPPING.md)** - Agent responsibilities
- **[.claude/TASK_PROMPT_DEFAULTS.md](.claude/TASK_PROMPT_DEFAULTS.md)** - Prompt templates
- **[.claude/QUEUE_SYSTEM_GUIDE.md](.claude/QUEUE_SYSTEM_GUIDE.md)** - Task queue usage

## 🧪 Example Project

This template includes a working Python CLI task manager as a demonstration:

- **Source**: `src/task_manager.py` - Simple task management CLI
- **Tests**: `tests/test_task_manager.py` - Comprehensive test suite
- **Enhancement**: `enhancements/add-json-export/` - Example enhancement with full workflow

Run the example:

```bash
# Install (Python 3.7+ required)
cd ClaudeMultiAgentTemplate

# Try the task manager
python src/task_manager.py add "Test task" -d "Testing the app"
python src/task_manager.py list

# Run tests
python -m unittest discover tests
```

## 🎓 Learning Resources

### For First-Time Users

1. Read [.claude/README.md](.claude/README.md) - Understand the system
2. Review [enhancements/add-json-export/add-json-export.md](enhancements/add-json-export/add-json-export.md) - See a complete enhancement
3. Try the example workflow in [INSTALLATION.md](INSTALLATION.md)
4. Customize agents for your project using [CUSTOMIZATION.md](CUSTOMIZATION.md)

### Key Concepts

- **Agent Specialization**: Each agent has a specific role and doesn't overstep
- **Status Markers**: Agents output status to trigger next workflow step
- **Hook Automation**: Hooks detect status and suggest next actions
- **Task Queue**: Optional system for managing multiple enhancements
- **Enhancement-First**: Start with clear requirements document

## 🛠️ Requirements

- **Claude Code** - This template is designed for use with Claude Code
- **bash** - For hook scripts and queue management
- **jq** - For JSON processing in queue system (install via `brew install jq` or package manager)

Optional:
- **Python 3.7+** - For the example project (not required for template itself)

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

This template was created to demonstrate multi-agent development workflows with Claude Code, showcasing how specialized AI agents can work together through a structured workflow system.

## 🔗 Links

- **Claude Code**: https://claude.ai/code
- **Documentation**: See `.claude/README.md` for complete system documentation
- **Example Enhancement**: See `enhancements/add-json-export/` for workflow demonstration

---

**Ready to get started?** See [INSTALLATION.md](INSTALLATION.md) for step-by-step setup instructions.
