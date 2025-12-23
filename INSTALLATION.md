# Installation Guide

This guide will walk you through installing and configuring the Claude Multi-Agent Template in your project.

## Prerequisites

Before you begin, ensure you have:

- **Claude Code** installed and working
- **Python 3.10+** with pip
- Your project directory ready

Optional (for integrations):
- Node.js 16+ (for MCP servers - GitHub/Jira integration)

## Installation Steps

### Step 1: Copy Template Files

```bash
# Navigate to your project root
cd /path/to/your/project

# Copy the .claude directory
cp -r /path/to/ClaudeMultiAgentTemplate/.claude ./

# Verify Python package is accessible
cd .claude
python -m cmat version
# Should show: CMAT version 8.2.0
```

### Step 2: Create Enhancements Directory

```bash
# Create enhancements directory structure
mkdir -p enhancements

# Optional: Copy example enhancements for reference
cp -r /path/to/ClaudeMultiAgentTemplate/enhancements/demo-test ./enhancements/
```

### Step 3: Configure Claude Code Hook

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

This hook tracks token usage and costs for each task.

### Step 4: Verify Installation

```bash
# Check CMAT version
cd /path/to/your/project/.claude
python -m cmat version
# Should show: CMAT version 8.2.0

# Check queue status
python -m cmat queue status
# Should show queue counts (likely all zeros for new install)

# List available agents
python -m cmat agents list
# Should show 8+ agents with roles and skills
```

### Step 5: Verify Data Files

```bash
# Check data directory
ls .claude/data/

# Should contain:
# - task_queue.json     (task queue state)
# - workflow_templates.json (workflow definitions)
# - learnings.json      (RAG learnings - may be empty)
# - models.json         (Claude model definitions)
# - tools.json          (tool definitions)
```

### Step 6: Customize for Your Project

Before using the template, customize it:

1. **Edit agent files** in `.claude/agents/` to specify:
   - Your programming language(s)
   - Your testing framework
   - Your coding standards
   - Your documentation format

2. **Create custom workflows** for your common patterns

3. **Add custom skills** for your domain

4. **Add project learnings** to prime the RAG system:
   ```bash
   python -m cmat learnings add "This project uses pytest for testing" --tags testing,python
   python -m cmat learnings add "Use snake_case for Python functions" --tags python,style
   ```

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed instructions.

---

## Verification

### Test 1: Basic CLI Operations

```bash
# All commands should work without errors
python -m cmat version          # Version info
python -m cmat queue status     # Queue counts
python -m cmat agents list      # Agent list
python -m cmat models list      # Model list with pricing
```

### Test 2: Learnings System

```bash
# Add a test learning
python -m cmat learnings add "Test learning for verification" --tags test

# List learnings
python -m cmat learnings list
# Should show the learning you just added

# Search learnings
python -m cmat learnings search "verification"
# Should return the test learning
```

### Test 3: Agent Configuration

```bash
# Generate agents.json from markdown files
python -m cmat agents generate

# List agents with details
python -m cmat agents list
# Should show agents with:
#   - Name
#   - Role
#   - Skills assigned
```

---

## Directory Structure After Installation

```
your-project/
├── .claude/
│   ├── cmat/              # Python package
│   │   ├── __init__.py
│   │   ├── __main__.py    # CLI entry point
│   │   ├── cmat.py        # Main CMAT class
│   │   ├── models/        # Data models
│   │   ├── services/      # Service classes
│   │   └── utils.py
│   ├── agents/            # Agent definitions
│   │   ├── *.md          # Agent markdown files
│   │   └── agents.json   # Generated registry
│   ├── skills/            # Skills system
│   │   ├── skills.json   # Skills registry
│   │   └── */SKILL.md    # Skill definitions
│   ├── data/              # JSON data files
│   │   ├── task_queue.json
│   │   ├── workflow_templates.json
│   │   ├── learnings.json
│   │   ├── models.json
│   │   └── tools.json
│   ├── hooks/             # Automation hooks
│   │   └── on-session-end-cost.sh
│   ├── docs/              # Documentation
│   └── tests/             # Python tests
├── enhancements/          # Your enhancement specs
└── [your project files]
```

---

## Common Issues

### "No module named 'cmat'"

**Cause**: Running from wrong directory or Python path issues.

**Solution**: Run from the `.claude` directory:
```bash
cd /path/to/your/project/.claude
python -m cmat version
```

Or use full path:
```bash
python -m /path/to/your/project/.claude/cmat version
```

### "ModuleNotFoundError: No module named 'pyyaml'"

**Cause**: Missing optional dependency.

**Solution**: Install pyyaml (only needed for some features):
```bash
pip install pyyaml
```

### "Task queue file not found"

**Cause**: Data files not initialized.

**Solution**: Check data directory exists:
```bash
ls .claude/data/
# If empty or missing, copy from template
```

### "Agent not found"

**Cause**: agents.json out of sync with markdown files.

**Solution**: Regenerate agents.json:
```bash
python -m cmat agents generate
```

### Permission Denied on Hook

**Cause**: Hook script not executable.

**Solution**: Make hook executable:
```bash
chmod +x .claude/hooks/on-session-end-cost.sh
```

---

## What's Next?

Now that installation is verified:

### Learn the System

- **Read** [README.md](README.md) - System overview
- **Study** [.claude/docs/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) - Workflow patterns
- **Review** [.claude/docs/CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md) - Command reference

### Customize

- **Edit** agent definitions in `.claude/agents/`
- **Add** learnings for your project patterns
- **Create** custom workflows for your needs
- **Configure** integrations (optional)

### Try Real Work

- **Create** your first enhancement specification
- **Use** Claude Code with CMAT agents via Task tool
- **Review** outputs from each agent
- **Track** costs with `python -m cmat costs show <task_id>`

---

## Quick Command Reference

```bash
# Core commands (run from .claude directory)
python -m cmat version              # Version info
python -m cmat queue status         # Queue summary
python -m cmat agents list          # List agents
python -m cmat models list          # List models

# Learnings management
python -m cmat learnings list       # All learnings
python -m cmat learnings add "..."  # Add learning
python -m cmat learnings search "." # Search

# Cost tracking
python -m cmat costs show <task_id>
python -m cmat costs enhancement <name>
```

For complete documentation, see [.claude/docs/CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md).

---

**Installation complete!** You're ready to use the multi-agent development system.

Start by adding some learnings about your project, then use Claude Code with CMAT agents to work on your enhancements.
