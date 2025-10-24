# Quick Start Guide

This document describes the process to get up and running with the Claude Multi-Agent Template v3.0.

## Step 1: Verify Installation
```bash
# Navigate to your project root
cd /path/to/your/project

# Verify cmat.sh is installed
.claude/scripts/cmat.sh version

# Should show:
# cmat v3.0.0
# Dependencies: ✓ jq, ✓ claude, ✓ bash
# Environment info with paths and counts
```

## Step 2: Verify Skills System
```bash
# Check skills are available
.claude/scripts/cmat.sh skills list

# Should show 14 skills

# Verify agents have skills
.claude/scripts/cmat.sh skills get requirements-analyst
# Should show: ["requirements-elicitation", "user-story-writing", "bug-triage"]
```

## Step 3: Test the Queue System
```bash
# Check queue status (creates initial queue files if needed)
.claude/scripts/cmat.sh queue status

# Should show:
# - Agent statuses (all idle)
# - Empty pending/active/completed queues
```

## Step 4: Try It Out!

### Create Your First Task
```bash
# Set environment to skip integration prompts
export AUTO_INTEGRATE="never"

# Create a simple manual task
TASK_ID=$(cmat.sh queue add \
  "Test the system" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Testing the multi-agent system" \
  false \
  false)

echo "Created task: $TASK_ID"
```

### Start the Task
```bash
# Start the task
cmat.sh queue start $TASK_ID

# The agent will:
# 1. Read its role definition
# 2. Receive specialized skills (requirements-elicitation, user-story-writing, bug-triage)
# 3. Process the enhancement specification
# 4. Create analysis output
# 5. Output READY_FOR_DEVELOPMENT status
```

### Monitor Progress
```bash
# Check queue status
cmat.sh queue status

# When complete, verify output was created
ls enhancements/demo-test/requirements-analyst/

# Should show: analysis_summary.md

# Check if skills were used
grep "Skills Applied" enhancements/demo-test/requirements-analyst/analysis_summary.md
```

### View the Log
```bash
# Find the log file
ls enhancements/demo-test/logs/

# View the log
cat enhancements/demo-test/logs/requirements-analyst_*.log

# Check for:
# - Skills section in prompt
# - Agent applying skills
# - Status: READY_FOR_DEVELOPMENT
```

## Step 5: Try Automated Workflow

Now try with full automation:
```bash
# Create fully automated task (auto-complete + auto-chain)
TASK_ID=$(cmat.sh queue add \
  "Automated workflow test" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Test automated workflow with skills" \
  true \
  true)

# Start it and let it run
cmat.sh queue start $TASK_ID

# The system will automatically:
# 1. Run requirements-analyst with skills → READY_FOR_DEVELOPMENT
# 2. Validate outputs
# 3. Create architect task (inherits automation)
# 4. Auto-start architect with skills → READY_FOR_IMPLEMENTATION
# 5. Continue through implementer → tester → documenter
# 6. Complete entire workflow hands-free!

# Monitor progress
watch -n 5 'cmat.sh queue status'
# Press Ctrl+C to exit watch

# After completion, verify all phases
ls enhancements/demo-test/
# Should show: requirements-analyst/, architect/, implementer/, tester/, documenter/, logs/
```

## Step 6: Explore Skills
```bash
# View all available skills
cmat.sh skills list

# Load and read a specific skill
cmat.sh skills load api-design

# See which skills an agent uses
cmat.sh skills get architect
# Shows: ["api-design", "architecture-patterns", "desktop-ui-design", "web-ui-design"]

# Preview what gets injected into architect's prompt
cmat.sh skills prompt architect | head -50
```

## Common First-Time Issues

### "Command not found: cmat.sh"

**Solution**: Use full path from project root
```bash
# Make sure you're in project root
pwd
# Should show: /path/to/your/project

# Use full path
.claude/scripts/cmat.sh queue status

# Not just: cmat.sh queue status
```

### "jq: command not found"

**Solution**: Install jq
```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq

# Verify
jq --version
```

### "Queue file not found"

**Solution**: Run status to initialize
```bash
# This creates the queue file
cmat.sh queue status

# Or copy empty template
cp .claude/queues/task_queue_empty.json .claude/queues/task_queue.json
```

### "Skills not appearing in prompts"

**Solution**: Verify skills setup
```bash
# Check skills.json exists
cat .claude/skills/skills.json | jq '.skills | length'
# Should show: 14

# Check agents have skills in frontmatter
grep "^skills:" .claude/agents/requirements-analyst.md

# Regenerate agents.json
cmat.sh agents generate-json

# Verify agents.json has skills
jq '.agents[0].skills' .claude/agents/agents.json
# Should show array, not null
```

### "Workflow not auto-chaining"

**Solution**: Check auto_chain flag
```bash
# Verify task has auto_chain: true
cmat.sh queue list pending | jq '.[] | {id, auto_chain}'

# Check hook is executing
tail -20 .claude/logs/queue_operations.log
# Should show TASK_COMPLETED and TASK_ADDED for chain
```

### "Permission denied" on Scripts

**Solution**: Make scripts executable
```bash
chmod +x .claude/scripts/*.sh
chmod +x .claude/hooks/*.sh

# Verify
ls -l .claude/scripts/*.sh
# Should show: -rwxr-xr-x
```

## What's Next?

Now that installation is verified, you can:

### Learn the System

- **Read** [README.md](README.md) - System overview
- **Study** [.claude/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) - Workflow patterns
- **Review** [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) - Complete command reference
- **Explore** [SKILLS_GUIDE.md](SKILLS_GUIDE.md) - Skills system documentation

### Customize for Your Project

- **Edit** agent definitions in `.claude/agents/`
- **Update** project-specific sections
- **Add** custom skills for your domain
- **Configure** workflows for your team

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed guidance.

### Try Real Work

- **Create** your first enhancement specification
- **Run** a full workflow
- **Review** outputs from each agent
- **Observe** how skills are applied

### Set Up Integration (Optional)

- **Configure** GitHub MCP server
- **Configure** Atlassian MCP server  
- **Test** external synchronization

See [.claude/INTEGRATION_GUIDE.md](.claude/docs/INTEGRATION_GUIDE.md) for setup.

## Quick Command Reference
```bash
# Queue operations
cmat.sh queue add <title> <agent> <priority> <type> <source> <desc> [auto_complete] [auto_chain]
cmat.sh queue start <task_id>
cmat.sh queue status
cmat.sh queue list <all|pending|active|completed|failed>

# Workflow operations
cmat.sh workflow validate <agent> <enhancement_dir>
cmat.sh workflow auto-chain <task_id> <status>

# Skills operations
cmat.sh skills list
cmat.sh skills get <agent>
cmat.sh skills prompt <agent>

# Integration operations
cmat.sh integration sync <task_id>
cmat.sh integration sync-all

# Utility
cmat.sh version
cmat.sh help
```

For complete command documentation, see [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md).

## Example: Complete Feature Development

Here's a complete example from start to finish:
```bash
# 1. Create enhancement specification
mkdir -p enhancements/add-search
cat > enhancements/add-search/add-search.md << 'EOF'
# Add Search Feature

## Description
Add search functionality to the task manager.

## Acceptance Criteria
- Search by title or description
- Case-insensitive search
- Return matching tasks

## Technical Notes
- Extend existing list command
- Add --search flag
EOF

# 2. Create initial requirements task (fully automated)
TASK_ID=$(cmat.sh queue add \
  "Add search - requirements" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/add-search/add-search.md" \
  "Analyze search feature requirements" \
  true \
  true)

# 3. Start and let it run
cmat.sh queue start $TASK_ID

# 4. Monitor progress
cmat.sh queue status

# 5. After completion, review outputs
tree enhancements/add-search/
# Should show all 5 agent outputs + logs

# 6. Check skill usage
grep -r "Skills Applied" enhancements/add-search/
```

## Need Help?

- **Documentation**: Check `.claude/*.md` files for detailed information
- **Examples**: Study `enhancements/demo-test/` and `enhancements/add-json-export/`
- **Logs**: Review `enhancements/*/logs/` for agent execution details
- **Queue Logs**: Check `.claude/logs/queue_operations.log` for system activity
- **Command Help**: Run `cmat.sh help` for usage

---

**Installation verified!** You're ready to use the multi-agent development system with skills.

Start with the demo-test enhancement, then create your own!