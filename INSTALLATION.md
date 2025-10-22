# Installation Guide

This guide will walk you through installing and configuring the Claude Multi-Agent Template in your project.

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
chmod +x .claude/hooks/*.sh
chmod +x .claude/queues/*.sh
chmod +x .claude/agents/*.sh
```

### Step 2: Create enhancements Directory

```bash
# Create enhancements directory structure
mkdir -p enhancements

# Optional: Copy example enhancement for reference
cp -r /path/to/ClaudeMultiAgentTemplate/enhancements/add-json-export ./enhancements/
```

### Step 3: Configure Claude Code

Create or update `.claude/settings.local.json`:

```json
{
  "hooks": {
    "on_subagent_stop": ".claude/hooks/on-subagent-stop.sh"
  }
}
```

**Note**: Some projects may use a different settings file location. Consult Claude Code documentation for your version.

### Step 4: Verify Installation

```bash
# Check that hooks are executable
ls -l .claude/hooks/

# Should show: -rwxr-xr-x for .sh files

# Verify queue manager works
.claude/queues/queue_manager.sh status

# This creates initial queue files if they don't exist
# Should show: agent statuses and empty queues
```

### Step 5: Customize the Agents for your project

## Customization

Before using the template, customize it for your project. See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed instructions.

**Minimum customization required**:

1. **Edit agent files** in `.claude/agents/` to specify:
   - Your programming language(s)
   - Your testing framework
   - Your coding standards
   - Your documentation format

2. **Update project-specific sections** in each agent file (search for `[**NOTE TO TEMPLATE USER**]`)

## Verification

Test that everything is working:

### Test Queue System

```bash
# Add a test task (note: requires a valid source file)
# First create a test file
echo "# Test Enhancement" > enhancements/test.md

# Add the test task
.claude/queues/queue_manager.sh add \
  "Test task" \
  "requirements-analyst" \
  "normal" \
  "analysis" \
  "enhancements/test.md" \
  "Testing queue system"

# Check status
.claude/queues/queue_manager.sh status

# You should see the task in pending_tasks

# Clean up
.claude/queues/queue_manager.sh cancel <task_id> 

# Alternatively you can type 
.claude/queues/queue_manager.sh cancel-all
# This will cancel all tasks.  Since you only have the one this is safe.
```

## Understanding Queue-Based Launch 

Use the queue system to organize and track work:

```bash
# Add task to queue
.claude/queues/queue_manager.sh add \
  "Task name" \
  "agent-name" \
  "priority" \
  "task_type" \
  "source_file" \
  "description"

# Start task
.claude/queues/queue_manager.sh start task_id

# Then launch agent in Claude Code with task context

# Complete task after agent finishes
.claude/queues/queue_manager.sh complete task_id "status message"
```

**For learning the system, start with Direct Launch.** Once comfortable, add the Queue System for project management.

## Example Workflow

Try the complete workflow with the sample enhancement using **Direct Launch**:

### 1. Launch Requirements Analyst

**In Claude Code, simply type:**

```
Launch a requirements-analyst agent to analyze the requirements
for the JSON export feature described in
enhancements/add-json-export/add-json-export.md
```

**Alternative (if you prefer explicit Task tool syntax):**
```
Use Task tool with:
- subagent_type: "requirements-analyst"
- description: "Analyze JSON export feature"
- prompt: "Analyze the requirements for the JSON export feature
  described in enhancements/add-json-export/add-json-export.md"
```

Both approaches work the same way. Natural language is simpler.

### 2. Review Output

The agent should:
- Analyze the requirements
- Create an implementation plan
- Output: `READY_FOR_DEVELOPMENT` status

### 3. Follow Hook Suggestion

The hook will suggest launching the Architect next. **Simply type:**

```
Launch an architect agent to design the JSON export feature
based on the requirements analysis above
```

Or with explicit syntax:
```
Use Task tool with:
- subagent_type: "architect"
- description: "Design JSON export architecture"
- prompt: "Design the architecture for the JSON export feature
  based on the requirements analysis from the previous agent."
```

### 4. Continue Workflow

Follow this pattern through:
- Architect → `READY_FOR_IMPLEMENTATION`
- Implementer → `READY_FOR_TESTING`
- Tester → `TESTING_COMPLETE`
- Documenter → `DOCUMENTATION_COMPLETE`

## Troubleshooting

### Hooks Not Executing

**Problem**: Hooks don't trigger after agent completion

**Solutions**:
1. Verify hooks are executable: `ls -l .claude/hooks/`
2. Check `settings.local.json` has correct paths
3. Look for error messages in Claude Code console
4. Verify bash is available: `which bash`

### Queue Manager Errors

**Problem**: Queue manager script fails

**Solutions**:
1. Check jq is installed: `which jq`
2. Verify queue files exist: `ls .claude/queues/`
3. Check file permissions: `ls -l .claude/queues/`
4. Try reinitializing: delete `.claude/queues/*.json` and run `queue_manager.sh status`

### Agent Not Found

**Problem**: "Agent not found" error

**Solutions**:
1. Verify agent file exists: `ls .claude/agents/`
2. Check agents.json is up to date: `cat .claude/agents/agents.json`
3. Verify agent name matches exactly (case-sensitive)
4. Check YAML frontmatter in agent .md file is valid

### Permission Errors

**Problem**: "Permission denied" errors

**Solutions**:
```bash
# Make all scripts executable
chmod +x .claude/hooks/*.sh
chmod +x .claude/queues/*.sh
chmod +x .claude/agents/*.sh

# Verify
ls -l .claude/**/*.sh
```

## Advanced Configuration

### Custom Agents

To add a custom agent:

1. Create `.claude/agents/my-custom-agent.md`
2. Add YAML frontmatter with name, description, tools
3. Regenerate agents.json (if using): `.claude/agents/generate_agents_json.sh`
4. Add agent to workflow templates if needed

### Custom Workflows

Edit `.claude/queues/workflow_templates.json` to add custom workflow patterns for your project.

### Custom Hooks

Create additional hooks in `.claude/hooks/` for custom automation:
- `on-commit.sh` - Trigger on git commits
- `on-build.sh` - Trigger on builds
- `on-test.sh` - Trigger on test runs

Add to `settings.local.json`:
```json
{
  "hooks": {
    "on_subagent_stop": ".claude/hooks/on-subagent-stop.sh",
    "on_commit": ".claude/hooks/on-commit.sh"
  }
}
```

## Maintenance

### Updating Agents

When updating agent definitions:
1. Edit agent .md files
2. Test with a simple task
3. Update `agents.json` if needed
4. Document changes for your team

### Log Cleanup

Agent logs accumulate in `enhancements/*/logs/`:

```bash
# Clean old logs (older than 30 days)
find enhancements/*/logs -name "*.log" -mtime +30 -delete

# Archive important logs before cleaning
tar -czf logs-archive-$(date +%Y%m%d).tar.gz enhancements/*/logs/
```

### Queue Maintenance

```bash
# View completed tasks
.claude/queues/queue_manager.sh status

# Archive old queue data
cp .claude/queues/task_queue.json task_queue_backup_$(date +%Y%m%d).json

# Clear completed tasks (edit JSON manually or script it)
```

## Next Steps

1. ✅ Read [CUSTOMIZATION.md](CUSTOMIZATION.md) - Adapt template to your project
2. ✅ Review [.claude/README.md](.claude/README.md) - Understand the system
3. ✅ Study [enhancements/add-json-export/](enhancements/add-json-export/) - Example workflow
4. ✅ Create your first enhancement!

## Getting Help

- **Documentation**: Check `.claude/*.md` files for detailed information
- **Example**: Study `enhancements/add-json-export/` for working example
- **Logs**: Review `enhancements/*/logs/` for agent execution details
- **Queue Logs**: Check `.claude/logs/queue_operations.log` for queue system activity

---

**Installation complete!** You're ready to start using the multi-agent development system.
