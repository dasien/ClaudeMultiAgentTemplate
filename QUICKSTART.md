# Quick Start Guide

Get up and running with the Claude Multi-Agent Template in 5 minutes.

## 1. Verify Installation

```bash
# Navigate to project's .claude directory
cd /path/to/your/project/.claude

# Check version
python -m cmat version

# Should show: CMAT version 8.2.0
```

## 2. Explore the System

```bash
# View queue status
python -m cmat queue status

# List available agents
python -m cmat agents list

# List Claude models and pricing
python -m cmat models list
```

## 3. Add Your First Learning

Prime the RAG system with knowledge about your project:

```bash
# Add project-specific learnings
python -m cmat learnings add "This project uses Python 3.10+ with pytest for testing"

python -m cmat learnings add "API responses should use snake_case for JSON keys"

# View stored learnings
python -m cmat learnings list
```

## 4. Create Enhancement Spec

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

## Notes
Testing the multi-agent system.
EOF
```

## 5. Use CMAT Agents

CMAT agents are designed to work with Claude Code's Task tool. In Claude Code, you can invoke CMAT agents like:

```
Use the Task tool with a specialized agent (requirements-analyst, architect,
implementer, tester, documenter) to work on the enhancement at
enhancements/my-feature/my-feature.md
```

The agent will:
1. Read your enhancement spec
2. Retrieve relevant learnings from the RAG system
3. Apply specialized skills
4. Create output in `required_output/` directory
5. Report completion status via YAML block

## 6. Track Costs

After agent tasks complete, view costs:

```bash
# Show cost for a specific task
python -m cmat costs show <task_id>

# Show total cost for an enhancement
python -m cmat costs enhancement my-feature
```

## 7. Verify Results

```bash
# Check output structure
ls enhancements/my-feature/

# After agents run, should see:
# requirements-analyst/required_output/
# architect/required_output/
# implementer/required_output/
# tester/required_output/
# documenter/required_output/
# logs/
```

---

## Quick Commands

```bash
# Run from .claude directory
cd /path/to/your/project/.claude

# System status
python -m cmat version              # Version info
python -m cmat queue status         # Queue summary
python -m cmat agents list          # List agents
python -m cmat models list          # List models with pricing

# Learnings (RAG memory)
python -m cmat learnings list       # Show all learnings
python -m cmat learnings add "..."  # Add learning
python -m cmat learnings search "." # Search learnings

# Cost tracking
python -m cmat costs show <id>      # Task cost details
python -m cmat costs enhancement <n># Enhancement total
```

---

## Understanding Agent Output

Agents report completion using YAML blocks:

```yaml
---
agent: implementer
task_id: task_1234567890_12345
status: READY_FOR_TESTING
---
```

**Completion statuses** (workflow continues):
- `READY_FOR_DEVELOPMENT` - Requirements analysis complete
- `READY_FOR_IMPLEMENTATION` - Architecture/design complete
- `READY_FOR_TESTING` - Implementation complete
- `TESTING_COMPLETE` - Tests passed
- `DOCUMENTATION_COMPLETE` - Docs updated

**Halt statuses** (workflow pauses):
- `BLOCKED: <reason>` - Cannot proceed
- `NEEDS_CLARIFICATION: <question>` - Requires input
- `TESTS_FAILED: <details>` - Tests need attention

---

## Common Workflows

### Feature Development
1. **Requirements Analyst** - Analyzes spec, creates implementation plan
2. **Architect** - Designs solution, creates technical spec
3. **Implementer** - Writes code
4. **Tester** - Creates and runs tests
5. **Documenter** - Updates documentation

### Bug Fix
1. **Requirements Analyst** - Triages bug, identifies root cause
2. **Implementer** - Creates fix
3. **Tester** - Validates fix
4. **Documenter** - Updates docs if needed

---

## Next Steps

- **[DEMO.md](DEMO.md)** - Hands-on demo with the calculator project
- **[.claude/docs/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md)** - Workflow patterns
- **[.claude/docs/CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md)** - Complete command reference
- **[.claude/docs/LEARNINGS_GUIDE.md](.claude/docs/LEARNINGS_GUIDE.md)** - RAG memory system
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapt to your project

---

**You're ready!** Try the [DEMO.md](DEMO.md) walkthrough, then start using CMAT agents on your own enhancements.
