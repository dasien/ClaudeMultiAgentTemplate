# Installation Guide

This guide will walk you through installing and configuring the Claude Multi-Agent Template v2.0 in your project.

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
```

### Step 2: Create enhancements Directory

```bash
# Create enhancements directory structure
mkdir -p enhancements

# Copy demo enhancement for testing
cp -r /path/to/ClaudeMultiAgentTemplate/enhancements/demo-test ./enhancements/
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

**Note**: v2.0 no longer uses `on-stop` hook. All workflow management is handled by the queue system.

### Step 4: Verify Installation

```bash
# Check that scripts are executable
ls -l .claude/hooks/*.sh .claude/queues/*.sh

# Verify queue manager works
.claude/queues/queue_manager.sh version

# Should show:
# Queue Manager v2.0.0
# ✓ jq v1.x
# ✓ claude
# Contracts: 7 agents defined in contracts

# Verify contracts file exists
ls -la .claude/AGENT_CONTRACTS.json

# Check queue status
.claude/queues/queue_manager.sh status

# Should show:
# === Multi-Agent Queue Status ===
# 📋 Agent Status:
#   • requirements-analyst: idle
#   • architect: idle
#   • implementer: idle
#   • tester: idle
#   • documenter: idle
#   • github-integration-coordinator: idle
#   • atlassian-integration-coordinator: idle
```

### Step 5: Test with Demo Enhancement

Run the demo-test enhancement to verify everything works:

```bash
# Set integration mode (skip for testing)
export AUTO_INTEGRATE="never"

# Create fully automated task
TASK_ID=$(.claude/queues/queue_manager.sh add \
  "Demo test - requirements analysis" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Analyze requirements for demo test enhancement" \
  true \
  true)

echo "Created task: $TASK_ID"

# Start the workflow and let it run
.claude/queues/queue_manager.sh start $TASK_ID

# The system will automatically:
# 1. Run requirements-analyst
# 2. Validate outputs
# 3. Create architect task
# 4. Auto-start architect
# 5. Continue through implementer → tester → documenter
# 6. Complete with all outputs validated

# This may take 10-30 minutes depending on agent speed
```

**Verify Success**:

```bash
# Check all outputs were created
ls -la enhancements/demo-test/

# Should see:
# demo-test.md
# requirements-analyst/
# architect/
# implementer/
# tester/
# documenter/
# logs/

# Verify metadata headers
head -10 enhancements/demo-test/requirements-analyst/analysis_summary.md

# Should show:
# ---
# enhancement: demo-test
# agent: requirements-analyst
# task_id: task_...
# timestamp: 2025-...
# status: READY_FOR_DEVELOPMENT
# ---

# Check queue status
.claude/queues/queue_manager.sh status

# Should show all agents idle, 5+ tasks completed
```

### Step 6: Customize for Your Project

Now that you've verified the system works, customize it for your project:

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed instructions.

**Minimum customization required**:

1. **Edit agent files** in `.claude/agents/` to specify:
   - Your programming language(s)
   - Your testing framework
   - Your coding standards
   - Your documentation format

2. **Update project-specific sections** in each agent file (search for `[**NOTE TO TEMPLATE USER**]`)

## Understanding the Task Creation Command

The `add` command has 7-9 parameters:

```bash
.claude/queues/queue_manager.sh add \
  "Task title" \                    # 1. Short description
  "agent-name" \                    # 2. Which agent to use
  "priority" \                      # 3. low|normal|high|critical
  "task_type" \                     # 4. analysis|technical_analysis|implementation|testing|documentation
  "source_file" \                   # 5. Input file path
  "description" \                   # 6. Detailed description
  auto_complete \                   # 7. true|false (skip completion prompt)
  auto_chain                        # 8. true|false (auto-create and auto-start next task)
```

**Automation Modes**:

```bash
# Fully Manual - prompts for everything
false false

# Auto-Complete - completes without prompt, but stops
true false

# Auto-Chain - prompts to complete, then auto-chains
false true

# Fully Automated - no prompts, runs entire workflow ⭐
true true
```

## Troubleshooting

### Installation Issues

#### jq Not Found

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Verify
jq --version
```

#### Hooks Not Executing

**Problem**: Hooks don't trigger after agent completion

**Solutions**:
1. Verify hooks are executable: `ls -l .claude/hooks/`
2. Check `settings.local.json` has correct path
3. Ensure you're using queue_manager.sh to start tasks
4. Look for error messages in Claude Code console

#### Queue Manager Errors

**Problem**: Queue manager script fails with jq errors

**Solutions**:
1. Check jq is installed: `which jq`
2. Verify queue files exist: `ls .claude/queues/`
3. Check JSON syntax: `jq '.' .claude/queues/task_queue.json`
4. Check contracts syntax: `jq '.' .claude/AGENT_CONTRACTS.json`

#### Agent Not Found in Contract

**Problem**: "Agent not found in contracts" error

**Solutions**:
1. Verify contracts file exists: `ls .claude/AGENT_CONTRACTS.json`
2. Check agent name matches exactly (case-sensitive)
3. Verify agent exists in contracts:
   ```bash
   jq '.agents | keys' .claude/AGENT_CONTRACTS.json
   ```

#### Validation Always Fails

**Problem**: Output validation fails even when files exist

**Solutions**:
```bash
# Check what contract expects
jq '.agents."requirements-analyst".outputs' .claude/AGENT_CONTRACTS.json

# Verify output location matches
ls -la enhancements/demo-test/requirements-analyst/

# Common issues:
# - Wrong directory name (check output_directory in contract)
# - Wrong filename (check root_document in contract)
# - Missing metadata header
# - Metadata missing required fields
```

#### Permission Errors

**Problem**: "Permission denied" errors

**Solutions**:
```bash
# Make all scripts executable
chmod +x .claude/hooks/*.sh
chmod +x .claude/queues/*.sh

# Verify
ls -l .claude/hooks/*.sh .claude/queues/*.sh
```

### Runtime Issues

#### Auto-Chain Not Working

**Problem**: Next task created but not started automatically

**Solution**: This was fixed in v2.0. Update to latest queue_manager.sh.

**Verify fix**:
```bash
.claude/queues/queue_manager.sh version
# Should show v2.0.0 or higher
```

#### Tasks Not Inheriting Automation Flags

**Problem**: Each task prompts even when parent had auto_complete=true

**Solution**: This was fixed in v2.0 - tasks now inherit parent's flags.

**Verify**:
```bash
# Check completed tasks
jq '.completed_tasks[-2:] | .[] | {id, auto_complete, auto_chain}' .claude/queues/task_queue.json

# All should have same auto_complete and auto_chain values
```

## Advanced Configuration

### GitHub/Jira Integration

To enable external system integration:

1. Follow setup in `.claude/mcp-servers/MCP_INTEGRATION_QUICKSTART.md`
2. Set `AUTO_INTEGRATE` environment variable:
   ```bash
   export AUTO_INTEGRATE="always"  # Auto-create integration tasks
   export AUTO_INTEGRATE="never"   # Skip integration (for testing)
   export AUTO_INTEGRATE="prompt"  # Ask before creating (default)
   ```

### Custom Agents

To add a custom agent:

1. Create `.claude/agents/my-custom-agent.md`
2. Add YAML frontmatter with name, description, tools
3. Add agent to `.claude/AGENT_CONTRACTS.json`
4. Add to `.claude/WORKFLOW_STATES.json` if using custom states
5. Test with a simple enhancement

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed instructions.

## Maintenance

### Updating the System

When updating to newer template versions:

1. **Backup your customizations**:
   ```bash
   cp .claude/agents/requirements-analyst.md requirements-analyst.md.backup
   # Repeat for each customized agent
   ```

2. **Copy new system files**:
   ```bash
   cp /path/to/template/.claude/AGENT_CONTRACTS.json .claude/
   cp /path/to/template/.claude/WORKFLOW_STATES.json .claude/
   cp /path/to/template/.claude/queues/queue_manager.sh .claude/queues/
   ```

3. **Restore your customizations**: Re-apply to "Project-Specific Customization" sections

4. **Test with demo-test**: Verify system still works

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
# View queue status
.claude/queues/queue_manager.sh status

# Archive old queue data
cp .claude/queues/task_queue.json task_queue_backup_$(date +%Y%m%d).json

# Clean up old completed tasks (edit JSON or use jq)
jq '.completed_tasks = .completed_tasks[-20:]' .claude/queues/task_queue.json > temp.json
mv temp.json .claude/queues/task_queue.json
```

## Next Steps

1. ✅ **Test System**: Run demo-test enhancement (as shown in Step 5)
2. ✅ **Review Results**: Examine outputs in `enhancements/demo-test/`
3. ✅ **Understand Contracts**: Read `.claude/AGENT_CONTRACTS.json`
4. ✅ **Read Workflow Guide**: Study `.claude/WORKFLOW_GUIDE.md`
5. ✅ **Customize**: Follow [CUSTOMIZATION.md](CUSTOMIZATION.md) for your project
6. ✅ **Create First Real Enhancement**: Use your own feature

## Getting Help

- **System Documentation**: `.claude/README.md` - Complete system overview
- **Agent Contracts**: `.claude/AGENT_CONTRACTS.json` - Source of truth
- **Workflow Patterns**: `.claude/WORKFLOW_GUIDE.md` - Common patterns
- **Queue System**: `.claude/QUEUE_SYSTEM_GUIDE.md` - Task management
- **Example Enhancement**: `enhancements/demo-test/` - Working example
- **Logs**: `enhancements/*/logs/` - Agent execution details
- **Queue Logs**: `.claude/logs/queue_operations.log` - Queue activity

## Common Questions

**Q: Do I need to use the queue system?**
A: Yes, in v2.0 the queue system provides all workflow management, validation, and auto-chaining.

**Q: Can I skip agents in the workflow?**
A: Yes, see `.claude/WORKFLOW_GUIDE.md` for patterns like hotfix (skip requirements/architecture) or bug fix (skip documentation).

**Q: How do I make it fully automated?**
A: Set `auto_complete=true` and `auto_chain=true` when creating tasks, plus `export AUTO_INTEGRATE="never"` to skip integration prompts.

**Q: What if validation fails?**
A: Check the error message - it will tell you what's missing (file, metadata header, specific field). Fix the issue and the workflow can continue.

**Q: Can I use this without GitHub/Jira?**
A: Yes! Set `AUTO_INTEGRATE="never"` and the system works perfectly without external integrations.

---

**Installation complete!** You're ready to start using the multi-agent development system.

**Next**: Run the demo-test enhancement to verify everything works, then customize for your project.