# Installation Guide

This guide will walk you through installing and configuring the Claude Multi-Agent Template v5.0 in your project.

## Prerequisites

Before you begin, ensure you have:

- ✅ **Claude Code** installed and working
- ✅ **bash** shell (macOS/Linux/WSL)
- ✅ **jq** JSON processor: `brew install jq` (macOS) or `apt-get install jq` (Linux)
- ✅ Your project directory ready

Optional (for testing the example):
- Python 3.7 or higher

## Installation Steps

### Step 1: Copy Template Files

```bash
# Navigate to your project root
cd /path/to/your/project

# Copy the .claude directory
cp -r /path/to/ClaudeMultiAgentTemplate/.claude ./

# Make scripts executable
chmod +x .claude/scripts/*.sh
chmod +x .claude/hooks/*.sh
chmod +x .claude/agents/generate_agents_json.sh
```

### Step 2: Create enhancements Directory

```bash
# Create enhancements directory structure
mkdir -p enhancements

# Optional: Copy example enhancements for reference
cp -r /path/to/ClaudeMultiAgentTemplate/enhancements/demo-test ./enhancements/
```

### Step 3: Configure Claude Code

Create `.claude/settings.json` (or `.claude/settings.local.json`):
```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/on-subagent-stop.sh"
          }
        ]
      }
    ],
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

### Step 4: Verify Installation

```bash
# Check that scripts are executable
ls -l .claude/scripts/

# Should show: -rwxr-xr-x for *.sh files

# Verify cmat command works
.claude/scripts/cmat version

# Should show:
# cmat v5.0.0
# Dependencies: ✓ jq, ✓ claude, ✓ bash
```

### Step 5: Verify Agents and Workflows

```bash
# Check agents
cmat agents list | jq '.agents[] | {name, role, validations}'

# Should show 7 agents with role and validations

# Check workflows
cmat workflow list

# Should show 6 built-in workflows
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

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed instructions.

---

## Verification

### Test 1: Basic Workflow

```bash
# Create simple test workflow
cmat workflow create test-install "Installation test"

cmat workflow add-step test-install requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "test.md"

cmat workflow add-transition test-install 0 READY_FOR_DEVELOPMENT null false

# Validate
cmat workflow validate test-install

# Create test enhancement
mkdir -p enhancements/test-install
cat > enhancements/test-install/test-install.md << 'EOF'
# Test Installation

## Description
Verify system is working.

## Acceptance Criteria
- Agent processes this file
- Creates required_output/ directory
- Generates test.md with metadata
EOF

# Run workflow
cmat workflow start test-install test-install
```

### Test 2: Verify Output Structure

```bash
# Check directory structure
ls -la enhancements/test-install/requirements-analyst/

# Should see:
# required_output/
# optional_output/ (maybe)

# Check required file
cat enhancements/test-install/requirements-analyst/required_output/test.md

# Should have metadata header:
# ---
# enhancement: test-install
# agent: requirements-analyst
# ...
# ---
```

### Test 3: Verify Skills

```bash
# Check skills available
cmat skills list | jq '.skills | length'
# Should show 14

# Check agent skills
cmat skills get requirements-analyst
# Should show: ["requirements-elicitation", "user-story-writing", "bug-triage"]
```

---

## Common First-Time Issues

### "Command not found: cmat"

**Solution**: Use full path or create alias
```bash
# Use full path
.claude/scripts/cmat version

# Or create alias
alias cmat='.claude/scripts/cmat'
```

### "jq: command not found"

**Solution**: Install jq
```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq
```

### "Workflow template not found"

**Solution**: Check workflow_templates.json is present
```bash
ls .claude/queues/workflow_templates.json
cmat workflow list
```

### "Agent not found in agents.json"

**Solution**: Regenerate agents.json
```bash
cd .claude/agents
./generate_agents_json.sh
```

### "Permission denied"

**Solution**: Make scripts executable
```bash
chmod +x .claude/scripts/*.sh
chmod +x .claude/hooks/*.sh
```

---

## What's Next?

Now that installation is verified:

### Learn the System

- **Read** [README.md](README.md) - System overview
- **Study** [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Workflow patterns
- **Review** [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) - Command reference
- **Explore** [WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md) - Template management

### Customize

- **Edit** agent definitions
- **Create** custom workflows
- **Add** custom skills
- **Configure** integrations (optional)

### Try Real Work

- **Create** your first enhancement
- **Run** a complete workflow
- **Review** outputs from each agent

---

## Quick Command Reference

```bash
# Workflow operations
cmat workflow list
cmat workflow start <workflow> <enhancement>
cmat workflow validate <workflow>

# Queue operations
cmat queue status
cmat queue list <type>

# Skills operations
cmat skills list
cmat skills get <agent>

# Utilities
cmat version
cmat help
```

For complete documentation, see [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md).

---

**Installation complete!** You're ready to use the multi-agent development system.

Start with a simple test workflow, then create your own custom workflows for your project patterns.