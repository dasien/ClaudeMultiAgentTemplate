# Queue System Guide

Complete guide to the task queue system in Claude Multi-Agent Template v3.0.

## Table of Contents

- [Overview](#overview)
- [Queue Architecture](#queue-architecture)
- [Task Lifecycle](#task-lifecycle)
- [Queue Operations](#queue-operations)
- [Automation Modes](#automation-modes)
- [Task Metadata](#task-metadata)
- [Queue Management](#queue-management)
- [Integration with Workflows](#integration-with-workflows)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The queue system manages the lifecycle of all agent tasks in the multi-agent workflow. It provides:

- **Task Organization**: Pending, active, completed, and failed queues
- **Agent Coordination**: Tracks which agents are available or busy
- **Workflow Automation**: Supports manual, semi-automated, and fully automated workflows
- **State Tracking**: Complete history of task execution
- **Integration Hooks**: Triggers for external system synchronization

### Key Components

**task_queue.json**: Central data store containing:
- `pending_tasks` - Tasks waiting to be started
- `active_workflows` - Currently executing tasks
- `completed_tasks` - Successfully finished tasks
- `failed_tasks` - Tasks that encountered errors
- `agent_status` - Current state of each agent

**queue-commands.sh**: Queue operations script
**workflow-commands.sh**: Workflow orchestration
**on-subagent-stop.sh**: Hook for automatic workflow progression

---

## Queue Architecture

### Queue Structure

```json
{
  "pending_tasks": [
    {
      "id": "task_1234567890_12345",
      "title": "Analyze requirements",
      "assigned_agent": "requirements-analyst",
      "priority": "high",
      "task_type": "analysis",
      "description": "Analyze feature requirements",
      "source_file": "enhancements/feature/feature.md",
      "created": "2025-10-24T14:00:00Z",
      "status": "pending",
      "started": null,
      "completed": null,
      "result": null,
      "auto_complete": false,
      "auto_chain": false,
      "metadata": {
        "github_issue": null,
        "jira_ticket": null,
        "github_pr": null,
        "confluence_page": null,
        "parent_task_id": null,
        "workflow_status": null
      }
    }
  ],
  "active_workflows": [],
  "completed_tasks": [],
  "failed_tasks": [],
  "agent_status": {
    "requirements-analyst": {
      "status": "idle",
      "last_activity": "2025-10-24T13:30:00Z",
      "current_task": null
    },
    "architect": {
      "status": "active",
      "last_activity": "2025-10-24T14:30:00Z",
      "current_task": "task_1234567890_12346"
    }
  }
}
```

### Task Properties

**Core Properties**:
- `id` - Unique task identifier (format: `task_<timestamp>_<pid>`)
- `title` - Short descriptive title
- `assigned_agent` - Agent responsible for execution
- `priority` - Task priority (critical, high, normal, low)
- `task_type` - Type of work (analysis, technical_analysis, implementation, testing, documentation, integration)
- `description` - Detailed task description
- `source_file` - Path to input file for agent
- `status` - Current state (pending, active, completed, failed)
- `created` - Task creation timestamp (ISO 8601)
- `started` - Execution start timestamp
- `completed` - Completion timestamp
- `result` - Completion status or error message

**Automation Properties**:
- `auto_complete` - Automatically complete without user prompt
- `auto_chain` - Automatically chain to next agent

**Metadata Properties**:
- `github_issue` - Linked GitHub issue number
- `github_pr` - Linked GitHub PR number
- `jira_ticket` - Linked Jira ticket key
- `confluence_page` - Linked Confluence page ID
- `parent_task_id` - Parent task reference
- `workflow_status` - Current workflow state

### Agent Status

Each agent maintains status:
- `status` - Current state (idle, active)
- `last_activity` - Last status update timestamp
- `current_task` - Currently executing task ID (if active)

---

## Task Lifecycle

### Standard Lifecycle Flow

```
1. CREATE (pending_tasks)
   ↓
2. START (moved to active_workflows)
   ↓
3. EXECUTE (agent processes task)
   ↓
4. COMPLETE (moved to completed_tasks)
   ↓
5. CHAIN (optional - create next task)
```

### State Diagram

```
┌─────────┐
│ Created │
└────┬────┘
     │
     ↓
┌─────────┐     ┌──────────┐
│ Pending │────→│ Canceled │
└────┬────┘     └──────────┘
     │
     ↓ start
┌─────────┐     ┌──────────┐
│ Active  │────→│ Canceled │
└────┬────┘     └──────────┘
     │
     ├──→ fail ────→ ┌────────┐
     │               │ Failed │
     │               └────────┘
     │
     ↓ complete
┌───────────┐
│ Completed │
└─────┬─────┘
      │
      ↓ auto-chain
┌─────────────┐
│ Next Task   │
│ (Pending)   │
└─────────────┘
```

### Detailed Lifecycle Steps

#### 1. Task Creation

```bash
cmat.sh queue add <title> <agent> <priority> <type> <source> <description> [auto_complete] [auto_chain]
```

**Actions**:
1. Generate unique task ID
2. Create task object with properties
3. Add to `pending_tasks` array
4. Log creation operation
5. Return task ID

**Output**:
```
task_1234567890_12345
```

#### 2. Task Start

```bash
cmat.sh queue start task_1234567890_12345
```

**Actions**:
1. Find task in `pending_tasks`
2. Set `status` to "active"
3. Record `started` timestamp
4. Move to `active_workflows`
5. Update agent status to "active"
6. Load agent configuration
7. Load agent skills
8. Build prompt with task details and skills
9. Invoke Claude with agent prompt
10. Stream output to console and log file

**Output**:
```
=== Starting Agent Execution ===
Start Time: 2025-10-24T14:30:00Z
Agent: requirements-analyst
Task ID: task_1234567890_12345
Source File: enhancements/feature/feature.md
Enhancement: feature
Output Directory: requirements-analyst
Root Document: analysis_summary.md
Log: enhancements/feature/logs/requirements-analyst_task_123_20251024_143000.log

[Agent execution output...]

=== Agent Execution Complete ===
End Time: 2025-10-24T14:45:00Z
Duration: 900s
Exit Code: 0
Exit Status: READY_FOR_DEVELOPMENT
```

#### 3. Task Completion

**Automatic** (if `auto_complete: true`):
```bash
# System automatically extracts status from agent output
# and completes task without user prompt
```

**Manual** (if `auto_complete: false`):
```bash
# System shows detected status
Detected Status: READY_FOR_DEVELOPMENT
Auto-completing task with status: READY_FOR_DEVELOPMENT
Proceed? [Y/n]:

# User confirms or manually completes:
cmat.sh queue complete task_1234567890_12345 "READY_FOR_DEVELOPMENT" --auto-chain
```

**Actions**:
1. Find task in `active_workflows`
2. Set `status` to "completed"
3. Set `result` to completion status
4. Record `completed` timestamp
5. Move to `completed_tasks`
6. Update agent status to "idle"
7. Log completion operation
8. Trigger auto-chain if enabled

#### 4. Auto-Chaining (Optional)

**If `auto_chain: true`**:

```bash
# System automatically:
# 1. Validates current agent outputs
# 2. Determines next agent from contract
# 3. Builds source path
# 4. Creates next task (inherits automation flags)
# 5. Starts next task
```

**Output**:
```
🔍 Validating outputs from requirements-analyst...
✅ Output validation passed: analysis_summary.md
📋 Next agent: architect (from contract)
✅ Auto-chained to architect: task_1234567890_12346
   Source: enhancements/feature/requirements-analyst/analysis_summary.md
   Inherited automation: auto_complete=true, auto_chain=true
🚀 Auto-starting next task...
```

---

## Queue Operations

### Adding Tasks

#### Basic Task
```bash
TASK_ID=$(cmat.sh queue add \
  "Task title" \
  "agent-name" \
  "priority" \
  "task-type" \
  "source-file" \
  "Description")

echo "Created: $TASK_ID"
```

#### With Automation
```bash
# Semi-automated (auto-complete only)
TASK_ID=$(cmat.sh queue add \
  "Design architecture" \
  "architect" \
  "high" \
  "technical_analysis" \
  "enhancements/feature/requirements-analyst/analysis_summary.md" \
  "Create technical design" \
  true \
  false)

# Fully automated (auto-complete + auto-chain)
TASK_ID=$(cmat.sh queue add \
  "Complete workflow" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/feature/feature.md" \
  "Full feature development" \
  true \
  true)
```

### Starting Tasks

```bash
# Start single task
cmat.sh queue start task_1234567890_12345

# Start next pending task (first in queue)
NEXT_TASK=$(cmat.sh queue list pending | jq -r '.[0].id')
cmat.sh queue start $NEXT_TASK
```

### Completing Tasks

```bash
# With default status
cmat.sh queue complete task_1234567890_12345

# With specific status
cmat.sh queue complete task_1234567890_12345 "READY_FOR_DEVELOPMENT"

# With auto-chain
cmat.sh queue complete task_1234567890_12345 "READY_FOR_DEVELOPMENT" --auto-chain

# With blocking reason
cmat.sh queue complete task_1234567890_12345 "BLOCKED: Missing API specification"
```

### Canceling Tasks

```bash
# Cancel specific task
cmat.sh queue cancel task_1234567890_12345 "Requirements changed"

# Cancel all pending and active
cmat.sh queue cancel-all "Project scope changed"
```

### Failing Tasks

```bash
# Mark task as failed
cmat.sh queue fail task_1234567890_12345 "Agent execution timeout"
```

### Viewing Queue Status

```bash
# Full status display
cmat.sh queue status

# List specific queue
cmat.sh queue list pending
cmat.sh queue list active
cmat.sh queue list completed
cmat.sh queue list failed
cmat.sh queue list all

# Compact format
cmat.sh queue list pending compact
```

### Updating Metadata

```bash
# Add GitHub issue
cmat.sh queue metadata task_123 github_issue "145"

# Add Jira ticket
cmat.sh queue metadata task_123 jira_ticket "PROJ-456"

# Link parent task
cmat.sh queue metadata task_456 parent_task_id "task_123"

# Update workflow status
cmat.sh queue metadata task_123 workflow_status "READY_FOR_TESTING"
```

---

## Automation Modes

The queue system supports three automation levels:

### 1. Manual Mode (Default)

**Settings**: `auto_complete: false`, `auto_chain: false`

**Behavior**:
- Agent executes and outputs status
- System prompts: "Complete with status X? [Y/n]"
- User must confirm completion
- System prompts: "Chain to next agent? [Y/n]"
- User must confirm chaining

**Use When**:
- Learning the system
- Uncertain about agent output quality
- Need to review results before proceeding
- Want full control over workflow

**Example**:
```bash
TASK_ID=$(cmat.sh queue add \
  "Analyze feature" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/feature/feature.md" \
  "Manual analysis" \
  false \
  false)

cmat.sh queue start $TASK_ID
# ... agent runs ...
# Detected Status: READY_FOR_DEVELOPMENT
# Auto-completing task with status: READY_FOR_DEVELOPMENT
# Proceed? [Y/n]: █
```

### 2. Semi-Automated Mode

**Settings**: `auto_complete: true`, `auto_chain: false`

**Behavior**:
- Agent executes and outputs status
- System automatically completes task
- System prompts: "Chain to next agent? [Y/n]"
- User must confirm chaining

**Use When**:
- Trust agent output quality
- Want to review before chaining
- Selective workflow progression
- Testing specific agents

**Example**:
```bash
TASK_ID=$(cmat.sh queue add \
  "Design architecture" \
  "architect" \
  "high" \
  "technical_analysis" \
  "enhancements/feature/requirements-analyst/analysis_summary.md" \
  "Semi-auto design" \
  true \
  false)

cmat.sh queue start $TASK_ID
# ... agent runs ...
# Detected Status: READY_FOR_IMPLEMENTATION
# ✅ Task completed automatically
# Create next task for implementer? [Y/n]: █
```

### 3. Fully Automated Mode

**Settings**: `auto_complete: true`, `auto_chain: true`

**Behavior**:
- Agent executes and outputs status
- System automatically completes task
- System automatically chains to next agent
- System automatically starts next task
- Entire workflow runs hands-off

**Use When**:
- Standard workflows you trust
- Batch processing multiple features
- Overnight/unattended execution
- Production workflow runs

**Example**:
```bash
TASK_ID=$(cmat.sh queue add \
  "Full feature workflow" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/feature/feature.md" \
  "Complete automated workflow" \
  true \
  true)

cmat.sh queue start $TASK_ID
# ... runs entire workflow automatically ...
# Requirements → Architecture → Implementation → Testing → Documentation
# ✅ Workflow complete: 5 agents, 2 hours
```

### Automation Inheritance

Child tasks inherit automation settings from parent:

```bash
# Parent task: auto_complete=true, auto_chain=true
PARENT=$(cmat.sh queue add "Feature" "requirements-analyst" ... true true)
cmat.sh queue start $PARENT

# Child tasks automatically created with SAME automation:
# - Architect task: auto_complete=true, auto_chain=true
# - Implementer task: auto_complete=true, auto_chain=true
# - Tester task: auto_complete=true, auto_chain=true
# - Documenter task: auto_complete=true, auto_chain=true
```

**Override inheritance** (manual):
```bash
# Create child without automation
CHILD=$(cmat.sh queue add "Child" "architect" ... false false)
```

---

## Task Metadata

Task metadata stores cross-references to external systems and workflow context.

### Standard Metadata Fields

**GitHub Integration**:
- `github_issue` - Issue number (e.g., "145")
- `github_issue_url` - Full issue URL
- `github_pr` - Pull request number
- `github_pr_url` - Full PR URL
- `github_synced_at` - Last sync timestamp

**Jira Integration**:
- `jira_ticket` - Ticket key (e.g., "PROJ-456")
- `jira_ticket_url` - Full ticket URL
- `jira_synced_at` - Last sync timestamp

**Confluence Integration**:
- `confluence_page` - Page ID
- `confluence_url` - Full page URL

**Workflow Context**:
- `parent_task_id` - Parent task reference
- `workflow_status` - Current workflow state
- `previous_agent` - Agent that created this task

### Working with Metadata

#### View Task Metadata
```bash
# View specific task
cmat.sh queue list completed | jq '.[] | select(.id == "task_123") | .metadata'

# View all tasks with GitHub issues
cmat.sh queue list all | jq '.completed[] | select(.metadata.github_issue != null) | {id, title, github_issue: .metadata.github_issue}'
```

#### Update Metadata
```bash
# Single field
cmat.sh queue metadata task_123 github_issue "145"

# Multiple fields (via script)
cmat.sh queue metadata task_123 github_issue "145"
cmat.sh queue metadata task_123 github_issue_url "https://github.com/owner/repo/issues/145"
cmat.sh queue metadata task_123 github_synced_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

#### Query by Metadata
```bash
# Find tasks linked to GitHub issue
cmat.sh queue list all | jq '.completed[] | select(.metadata.github_issue == "145")'

# Find tasks without Jira ticket
cmat.sh queue list completed | jq '.[] | select(.metadata.jira_ticket == null) | {id, title, status: .result}'

# Find integration tasks
cmat.sh queue list all | jq '.completed[] | select(.assigned_agent | contains("integration"))'
```

### Metadata Best Practices

**DO**:
- ✅ Update metadata immediately after external sync
- ✅ Store URLs for easy access
- ✅ Use metadata for cross-system traceability
- ✅ Query metadata to find related work
- ✅ Include parent_task_id for task relationships

**DON'T**:
- ❌ Store sensitive data in metadata
- ❌ Assume metadata fields exist (check for null)
- ❌ Forget to sync after external changes
- ❌ Use metadata for large data (use files instead)

---

## Queue Management

### Monitoring Queue Health

```bash
# Check queue status regularly
cmat.sh queue status

# Watch for changes (Linux/Mac)
watch -n 5 'cmat.sh queue status'

# Count tasks by status
cmat.sh queue list all | jq '{
  pending: .pending | length,
  active: .active | length,
  completed: .completed | length,
  failed: .failed | length
}'

# Find stuck active tasks (running > 1 hour)
cmat.sh queue list active | jq --arg now "$(date -u +%s)" '.[] | 
  select(($now | tonumber) - (.started | fromdateiso8601) > 3600) | 
  {id, title, agent: .assigned_agent, started}'
```

### Queue Cleanup

```bash
# Archive old completed tasks (manual backup)
cmat.sh queue list completed | jq '.' > archive/completed_$(date +%Y%m%d).json

# Clear completed tasks (careful!)
# First backup:
cp .claude/queues/task_queue.json .claude/queues/task_queue_backup.json
# Then edit manually or use jq:
jq '.completed_tasks = []' .claude/queues/task_queue.json > temp.json && mv temp.json .claude/queues/task_queue.json
```

### Recovering from Errors

#### Stuck Active Task
```bash
# Cancel stuck task
cmat.sh queue cancel task_123 "Agent hung, restarting"

# Re-create task
TASK_ID=$(cmat.sh queue add ...)
cmat.sh queue start $TASK_ID
```

#### Failed Task Retry
```bash
# Find failed task details
cmat.sh queue list failed | jq '.[] | {id, title, result}'

# Re-create task with same parameters
# (Extract from failed task metadata)
TASK_ID=$(cmat.sh queue add \
  "$(jq -r '.failed[0].title' .claude/queues/task_queue.json)" \
  "$(jq -r '.failed[0].assigned_agent' .claude/queues/task_queue.json)" \
  "$(jq -r '.failed[0].priority' .claude/queues/task_queue.json)" \
  "$(jq -r '.failed[0].task_type' .claude/queues/task_queue.json)" \
  "$(jq -r '.failed[0].source_file' .claude/queues/task_queue.json)" \
  "$(jq -r '.failed[0].description' .claude/queues/task_queue.json)")
```

#### Queue Corruption
```bash
# Validate queue JSON
jq '.' .claude/queues/task_queue.json

# If invalid, restore from backup
cp .claude/queues/task_queue_backup.json .claude/queues/task_queue.json

# Or reset to empty queue
cp .claude/queues/task_queue_empty.json .claude/queues/task_queue.json
```

---

## Integration with Workflows

### Contract-Based Workflow

The queue system integrates with the contract-based workflow system:

```bash
# 1. Task completes with status
cmat.sh queue complete task_123 "READY_FOR_DEVELOPMENT"

# 2. Hook validates outputs
workflow validate requirements-analyst enhancements/feature

# 3. Hook determines next agent
NEXT_AGENT=$(workflow next-agent requirements-analyst "READY_FOR_DEVELOPMENT")
# Returns: architect

# 4. Hook builds source path
SOURCE=$(workflow next-source feature architect requirements-analyst)
# Returns: enhancements/feature/requirements-analyst/analysis_summary.md

# 5. Hook creates next task
NEXT_ID=$(queue add "Design $FEATURE" "$NEXT_AGENT" ...)

# 6. If auto-chain enabled, start next task
queue start $NEXT_ID
```

### Integration Tasks

Integration tasks sync workflow state to external systems:

```bash
# Automatically created by hook when status needs integration
# For status: READY_FOR_DEVELOPMENT
integration add \
  "READY_FOR_DEVELOPMENT" \
  "enhancements/feature/requirements-analyst/analysis_summary.md" \
  "requirements-analyst" \
  "task_123"

# Creates task assigned to:
# - github-integration-coordinator (creates issue)
# - atlassian-integration-coordinator (creates Jira ticket)
```

### Hook Execution Flow

**on-subagent-stop.sh**:
```bash
#!/bin/bash

# 1. Extract task ID and status from completion
TASK_ID="$1"
STATUS="$2"

# 2. If integration enabled and status needs sync
if needs_integration "$STATUS"; then
    # Create integration task
    integration add "$STATUS" "$SOURCE" "$AGENT" "$TASK_ID"
fi

# 3. If auto-chain enabled
if [ "$AUTO_CHAIN" = "true" ]; then
    # Validate outputs
    workflow validate "$AGENT" "$ENHANCEMENT_DIR"
    
    # Chain to next agent
    workflow auto-chain "$TASK_ID" "$STATUS"
fi
```

---

## Best Practices

### Task Organization

**DO**:
- ✅ Use descriptive task titles
- ✅ Include enhancement name in title
- ✅ Set appropriate priority
- ✅ Use correct task_type
- ✅ Provide detailed descriptions
- ✅ Use auto-chain for standard workflows
- ✅ Monitor queue regularly

**DON'T**:
- ❌ Use generic titles ("Task 1", "Test")
- ❌ Mark everything as critical
- ❌ Skip source_file specification
- ❌ Use wrong task_type
- ❌ Leave tasks stuck in active state
- ❌ Ignore failed tasks

### Automation Strategy

**Start with Manual**:
```bash
# First time with new enhancement type
TASK_ID=$(cmat.sh queue add ... false false)
cmat.sh queue start $TASK_ID
# Review each step carefully
```

**Transition to Semi-Auto**:
```bash
# Once confident in output quality
TASK_ID=$(cmat.sh queue add ... true false)
cmat.sh queue start $TASK_ID
# Review before chaining
```

**Use Full-Auto for Production**:
```bash
# For well-tested workflows
export AUTO_INTEGRATE="always"
TASK_ID=$(cmat.sh queue add ... true true)
cmat.sh queue start $TASK_ID
# Let it run completely
```

### Queue Maintenance

**Daily**:
```bash
# Check queue status
cmat.sh queue status

# Review completed tasks
cmat.sh queue list completed | jq '.[-5:] | .[] | {title, agent: .assigned_agent, status: .result}'

# Check for failed tasks
cmat.sh queue list failed | jq 'length'
```

**Weekly**:
```bash
# Archive completed tasks
cmat.sh queue list completed | jq '.' > archive/completed_$(date +%Y%m%d).json

# Review integration sync status
cmat.sh queue list completed | jq '.[] | select(.metadata.github_issue == null) | {id, title}'
```

**Monthly**:
```bash
# Analyze workflow performance
cmat.sh queue list completed | jq '.[] | {
  agent: .assigned_agent,
  duration: ((.completed | fromdateiso8601) - (.started | fromdateiso8601))
}' | jq -s 'group_by(.agent) | map({
  agent: .[0].agent,
  avg_duration: (map(.duration) | add / length)
})'

# Clean up very old completed tasks (manual backup first)
```

### Error Handling

**Immediate Response**:
```bash
# Task fails
cmat.sh queue list failed | tail -1 | jq .

# Investigate log
tail -100 enhancements/*/logs/*_task_123_*.log

# If recoverable, retry
cmat.sh queue add ... # recreate with same params
```

**Systematic Review**:
```bash
# List all failures in last week
cmat.sh queue list failed | jq '.[] | 
  select(.completed > "'$(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%SZ)'") |
  {title, agent: .assigned_agent, error: .result}'

# Categorize by error type
# Fix root causes
# Update agent definitions or workflows
```

---

## Troubleshooting

### Task Won't Start

**Symptoms**: `cmat.sh queue start` fails

**Causes & Solutions**:

1. **Task not in pending queue**
   ```bash
   cmat.sh queue list pending | grep task_123
   # If not found, task may be in wrong queue
   cmat.sh queue list all | jq '.[] | .[] | select(.id == "task_123")'
   ```

2. **Source file missing**
   ```bash
   # Check task source file
   SOURCE=$(cmat.sh queue list pending | jq -r '.[] | select(.id == "task_123") | .source_file')
   ls -la "$SOURCE"
   # If missing, cancel and recreate with correct path
   ```

3. **Agent config missing**
   ```bash
   # Check agent exists
   ls .claude/agents/my-agent.md
   jq '.agents | keys' .claude/AGENT_CONTRACTS.json
   ```

### Task Stuck in Active

**Symptoms**: Task remains in active_workflows for hours

**Solutions**:

1. **Check if agent actually running**
   ```bash
   # Look for Claude process
   ps aux | grep claude
   
   # Check log for current activity
   tail -f enhancements/*/logs/*_task_123_*.log
   ```

2. **Cancel if truly stuck**
   ```bash
   cmat.sh queue cancel task_123 "Agent hung"
   
   # Check agent is released
   cmat.sh queue status | grep agent-name
   # Should show: idle
   ```

3. **Restart task**
   ```bash
   # Recreate and start
   TASK_ID=$(cmat.sh queue add ...)
   cmat.sh queue start $TASK_ID
   ```

### Auto-Chain Not Working

**Symptoms**: Task completes but doesn't chain

**Causes & Solutions**:

1. **auto_chain flag not set**
   ```bash
   cmat.sh queue list completed | jq '.[-1] | .auto_chain'
   # Should show: true
   # If false, that's why it didn't chain
   ```

2. **Output validation failed**
   ```bash
   # Check validation
   AGENT=$(jq -r '.completed[-1].assigned_agent' .claude/queues/task_queue.json)
   ENHANCEMENT=$(jq -r '.completed[-1].source_file' .claude/queues/task_queue.json | sed 's|enhancements/\([^/]*\)/.*|\1|')
   
   cmat.sh workflow validate "$AGENT" "enhancements/$ENHANCEMENT"
   # Look for validation errors
   ```

3. **No next agent for status**
   ```bash
   AGENT=$(jq -r '.completed[-1].assigned_agent' .claude/queues/task_queue.json)
   STATUS=$(jq -r '.completed[-1].result' .claude/queues/task_queue.json)
   
   cmat.sh workflow next-agent "$AGENT" "$STATUS"
   # If UNKNOWN, status doesn't have next agent defined
   ```

### Queue File Corrupted

**Symptoms**: jq errors when accessing queue

**Recovery**:

1. **Validate JSON**
   ```bash
   jq '.' .claude/queues/task_queue.json
   # Shows syntax errors if corrupted
   ```

2. **Restore from backup**
   ```bash
   # If you have backup
   cp .claude/queues/task_queue_backup.json .claude/queues/task_queue.json
   
   # Or reset to empty
   cp .claude/queues/task_queue_empty.json .claude/queues/task_queue.json
   ```

3. **Prevent future corruption**
   ```bash
   # Always backup before manual edits
   cp .claude/queues/task_queue.json .claude/queues/task_queue_backup.json
   
   # Use tools instead of manual edit
   cmat.sh queue metadata ...  # Not: vim task_queue.json
   ```

### Integration Not Triggering

**Symptoms**: External systems not updated

**Solutions**:

1. **Check AUTO_INTEGRATE setting**
   ```bash
   echo $AUTO_INTEGRATE
   # Should be: always, prompt, or never
   
   # If never, that's why
   export AUTO_INTEGRATE="prompt"
   ```

2. **Verify status needs integration**
   ```bash
   # Check if status triggers integration
   grep needs_integration .claude/scripts/common-commands.sh
   # Should match your status
   ```

3. **Check integration tasks created**
   ```bash
   cmat.sh queue list all | jq '.pending[] | select(.assigned_agent | contains("integration"))'
   # Should show integration tasks
   ```

---

## Further Reading

- **[SCRIPTS_REFERENCE.md](../SCRIPTS_REFERENCE.md)** - Complete command reference
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow patterns and orchestration
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - External system integration
- **[AGENT_CONTRACTS.json](../AGENT_CONTRACTS.json)** - Agent specifications

---

**Version**: 3.0.0  
**Last Updated**: 2025-10-24