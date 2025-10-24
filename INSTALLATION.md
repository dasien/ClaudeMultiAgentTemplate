# Installation Guide

This guide will walk you through installing and configuring the Claude Multi-Agent Template v3.0 in your project.

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
```

### Step 2: Create enhancements Directory
```bash
# Create enhancements directory structure
mkdir -p enhancements

# Optional: Copy example enhancements for reference
cp -r /path/to/ClaudeMultiAgentTemplate/enhancements/demo-test ./enhancements/
cp -r /path/to/ClaudeMultiAgentTemplate/enhancements/add-json-export ./enhancements/
```

### Step 3: Configure Claude Code

Create `.claude/settings.local.json`:
```json
{
  "hooks": {
    "on_subagent_stop": ".claude/hooks/on-subagent-stop.sh"
  }
}
```

**Note**: Hook configuration may vary by Claude Code version. Consult Claude Code documentation if this doesn't work.

### Step 4: Verify Installation
```bash
# Check that scripts are executable
ls -l .claude/scripts/

# Should show: -rwxr-xr-x for *.sh files

# Verify cmat command works
.claude/scripts/cmat.sh version

# Should show:
# cmat v3.0.0
# Claude Multi-Agent Template System
# Dependencies: ✓ jq, ✓ claude, ✓ bash
# Project paths and counts

# Check queue system
.claude/scripts/cmat.sh queue status

# Should show: agent statuses and empty queues
```

### Step 5: Verify Skills System
```bash
# List available skills
.claude/scripts/cmat.sh skills list

# Should show 14 skills

# Test skills system
.claude/scripts/cmat.sh skills test

# Should show:
# - Skills data
# - Requirements analyst skills
# - Sample skill content
# - Skills prompt preview
```

### Step 6: Customize for Your Project

Before using the template, customize it for your project:

1. **Edit agent files** in `.claude/agents/` to specify:
   - Your programming language(s)
   - Your testing framework
   - Your coding standards
   - Your documentation format

2. **Update project-specific sections** in each agent file (search for `[**NOTE TO TEMPLATE USER**]`)

3. **Customize or add skills** as needed for your domain

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed instructions.

## Verification

Test that everything is working:

### Test Queue System
```bash
# Create a test file
echo "# Test Enhancement" > enhancements/test.md

# Add a test task
TASK_ID=$(cmat.sh queue add \
  "Test task" \
  "requirements-analyst" \
  "normal" \
  "analysis" \
  "enhancements/test.md" \
  "Testing queue system" \
  false \
  false)

echo "Created task: $TASK_ID"

# Check status
cmat.sh queue status

# You should see the task in pending_tasks

# Clean up
cmat.sh queue cancel $TASK_ID
```

### Test Skills Integration
```bash
# Verify skills are assigned to agents
cmat.sh skills get requirements-analyst
# Should show: ["requirements-elicitation", "user-story-writing", "bug-triage"]

cmat.sh skills get architect
# Should show: ["api-design", "architecture-patterns", "desktop-ui-design", "web-ui-design"]

# Test skills prompt generation
cmat.sh skills prompt requirements-analyst | head -30
# Should show skills section with all assigned skills
```

### Test Complete Workflow

Run the demo enhancement to verify the entire system:
```bash
# Set environment to skip integration prompts
export AUTO_INTEGRATE="never"

# Create fully automated workflow task
TASK_ID=$(cmat.sh queue add \
  "Demo test - full workflow" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Test complete workflow with skills" \
  true \
  true)

# Start it
cmat.sh queue start $TASK_ID

# Watch it run through entire workflow:
# Requirements → Architecture → Implementation → Testing → Documentation

# Monitor progress
watch -n 5 'cmat.sh queue status'

# After completion, verify all outputs
ls enhancements/demo-test/
# Should show directories for all 5 agents plus logs/

# Verify skills were used
grep -r "Skills Applied" enhancements/demo-test/*/
```

## Common First-Time Issues

### "Command not found: cmat.sh"

**Solution**: Use full path or ensure you're in project root
```bash
# Check current directory
pwd

# Should show your project directory

# Use full path
.claude/scripts/cmat.sh version

# Or create alias (optional)
alias cmat='.claude/scripts/cmat.sh'
```

### "jq: command not found"

**Solution**: Install jq
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Verify
jq --version
```

### "Queue file not found"

**Solution**: Initialize queue by running status
```bash
# This creates initial queue files
cmat.sh queue status

# Or copy the empty template
cp .claude/queues/task_queue_empty.json .claude/queues/task_queue.json
```

### "Skills not loading"

**Solution**: Verify skills directory structure
```bash
# Check skills exist
ls .claude/skills/

# Verify skills.json
cat .claude/skills/skills.json | jq '.skills | length'
# Should show: 14

# Check individual skill
ls .claude/skills/requirements-elicitation/SKILL.md
```

### "Agent not found in contracts"

**Solution**: Verify AGENT_CONTRACTS.json
```bash
# Check contracts file exists
ls .claude/AGENT_CONTRACTS.json

# List all agents in contracts
jq '.agents | keys' .claude/AGENT_CONTRACTS.json
```

### "Hooks not executing"

**Solution**: 
1. Verify hooks are executable: `ls -l .claude/hooks/`
2. Check `settings.local.json` has correct paths
3. Verify bash is available: `which bash`

## Advanced Setup

### Creating an Alias

For convenience, add to your `~/.bashrc` or `~/.zshrc`:
```bash
# If you work on one project
alias cmat='/path/to/your/project/.claude/scripts/cmat.sh'

# If you work on multiple projects, use function
cmat() {
    if [ -f ".claude/scripts/cmat.sh" ]; then
        .claude/scripts/cmat.sh "$@"
    else
        echo "Error: Not in a CMAT project (no .claude/scripts/cmat.sh found)"
        return 1
    fi
}
```

Then reload: `source ~/.bashrc`

Now you can just use: `cmat queue status`

### Setting Up Integration

For GitHub/Jira integration:

1. Follow [.claude/mcp-servers/MCP_INTEGRATION_QUICKSTART.md](.claude/mcp-servers/MCP_INTEGRATION_QUICKSTART.md)
2. Configure MCP servers
3. Set environment variables for tokens
4. Test with: `cmat.sh integration sync-all`

### Custom Skills

To add domain-specific skills:

1. Use [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md) as guide
2. Create skill directory and SKILL.md
3. Add to `.claude/skills/skills.json`
4. Assign to relevant agents
5. Regenerate: `cmat.sh agents generate-json`

See [SKILLS_GUIDE.md](SKILLS_GUIDE.md) for complete instructions.

## Post-Installation Checklist

After installation, verify:

- [ ] `cmat.sh version` shows v3.0.0 and all dependencies
- [ ] `cmat.sh queue status` works without errors
- [ ] `cmat.sh skills list` shows 14 skills
- [ ] Agent files customized for your project
- [ ] Skills assigned appropriately to agents
- [ ] Hook configuration in settings.local.json
- [ ] Demo test enhancement runs successfully
- [ ] All 5 agent phases complete in workflow
- [ ] Skills appear in agent logs
- [ ] Agents document skill usage

## Troubleshooting Installation

### Permission Errors
```bash
# Make all scripts executable
chmod +x .claude/scripts/*.sh
chmod +x .claude/hooks/*.sh

# Verify
ls -l .claude/**/*.sh
```

### Path Issues

All commands must be run from **project root** (the directory containing `.claude/`):
```bash
# Check you're in the right place
ls .claude/
# Should show: scripts/ agents/ skills/ hooks/ queues/ etc.

# Always run cmat.sh from project root
.claude/scripts/cmat.sh queue status
```

### JSON Parse Errors
```bash
# Validate all JSON files
jq '.' .claude/queues/task_queue.json
jq '.' .claude/AGENT_CONTRACTS.json
jq '.' .claude/skills/skills.json
jq '.' .claude/agents/agents.json

# Any errors will show the line number
```

### Skills Not Appearing
```bash
# Verify agents.json has skills field
jq '.agents[0] | keys' .claude/agents/agents.json
# Should include "skills" in the list

# Regenerate agents.json from .md files
cmat.sh agents generate-json

# Verify skills field populated
jq '.agents[] | {name: .name, skills: .skills}' .claude/agents/agents.json
```

## Next Steps

1. ✅ Read [README.md](README.md) - Understand the system overview
2. ✅ Review [.claude/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) - Learn workflow patterns
3. ✅ Read [SKILLS_GUIDE.md](SKILLS_GUIDE.md) - Understand the skills system
4. ✅ Study [.claude/AGENT_CONTRACTS.json](.claude/AGENT_CONTRACTS.json) - See agent specifications
5. ✅ Review [CUSTOMIZATION.md](CUSTOMIZATION.md) - Adapt to your project
6. ✅ Try `enhancements/demo-test/` - Run simple test
7. ✅ Explore `enhancements/add-json-export/` - Full workflow example
8. ✅ Create your first enhancement!

## Getting Help

- **Command Reference**: [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) - All cmat.sh commands
- **Skills Guide**: [SKILLS_GUIDE.md](SKILLS_GUIDE.md) - Skills system documentation
- **Workflow Patterns**: [.claude/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) - Detailed workflows
- **Example Code**: Study `enhancements/add-json-export/` for working example
- **Logs**: Review `.claude/logs/` and `enhancements/*/logs/` for execution details

---

**Installation complete!** You're ready to start using the multi-agent development system with skills.

For your first task, try running the demo-test enhancement to see the complete workflow in action.