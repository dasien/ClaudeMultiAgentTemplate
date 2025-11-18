# Quick Start Guide

Get up and running with the Claude Multi-Agent Template v5.0 in 5 minutes.

## 1. Verify Installation

```bash
# Navigate to project root
cd /path/to/your/project

# Check version
cmat version

# Should show: cmat v5.0.0
```

## 2. List Available Workflows

```bash
cmat workflow list
```

**Output**:
```
new_feature_development - Complete workflow (5 steps)
bugfix_workflow - Bug fix workflow (4 steps)
hotfix_workflow - Fast-track critical issues (2 steps)
```

## 3. Create Enhancement Spec

```bash
mkdir -p enhancements/my-feature
cat > enhancements/my-feature/my-feature.md << 'EOF'
# My Feature

## Description
Add new functionality.

## Acceptance Criteria
- Feature implemented
- Tests passing
- Documented

## Notes
Testing the multi-agent system.
EOF
```

## 4. Start Workflow

```bash
cmat workflow start new_feature_development my-feature
```

**The system will**:
1. Create first task (requirements-analyst, step 0)
2. Add workflow metadata to task
3. Auto-start task
4. After completion, auto-chain to next step
5. Continue through all 5 steps automatically

## 5. Monitor Progress

```bash
# Check status
cmat queue status

# View logs
tail -f enhancements/my-feature/logs/*.log
```

## 6. Verify Results

```bash
# Check output structure
ls enhancements/my-feature/

# Should see:
# requirements-analyst/required_output/
# architect/required_output/
# implementer/required_output/
# tester/required_output/
# documenter/required_output/
# logs/
```

---

## Create Custom Workflow

```bash
# 1. Create template
cmat workflow create my-workflow "My custom workflow"

# 2. Add steps
cmat workflow add-step my-workflow requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "analysis.md"

cmat workflow add-step my-workflow implementer \
    "{previous_step}/required_output/" \
    "code.md"

# 3. Add transitions
cmat workflow add-transition my-workflow 0 READY_FOR_DEVELOPMENT implementer true
cmat workflow add-transition my-workflow 1 READY_FOR_TESTING null false

# 4. Use it
cmat workflow start my-workflow test-feature
```

---

## Quick Commands

```bash
# Workflows
cmat workflow list                      # Show all workflows
cmat workflow show <name>               # Show workflow details
cmat workflow start <workflow> <enh>    # Start workflow

# Queue
cmat queue status                       # Show current status
cmat queue list completed               # Show completed tasks

# Skills
cmat skills list                        # Show all skills
cmat skills get <agent>                 # Show agent's skills
```

---

## Next Steps

- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Learn workflow patterns
- **[WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md)** - Template management
- **[SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md)** - All commands
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapt to your project

---

**You're ready!** Start with `cmat workflow start` and let the system guide you through development.