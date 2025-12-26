# Queue System Guide

Complete guide to the task queue system in CMAT.

**Version**: 8.8.0

## Overview

The queue system manages the lifecycle of all agent tasks. It provides:

- **Task Organization**: Tracks tasks by status (pending, active, completed, failed)
- **Agent Coordination**: Monitors which agents are busy or available
- **Workflow Support**: Carries workflow context for auto-chaining
- **Cost Tracking**: Records token usage and costs per task
- **Learnings Integration**: Tracks which learnings were used/created

---

## Queue Architecture

### Data Storage

All queue data is stored in `.claude/data/task_queue.json`.

### Task Structure

```json
{
  "id": "task_1702345678_12345",
  "title": "Workflow: new-feature - step 0",
  "assigned_agent": "requirements-analyst",
  "priority": "high",
  "task_type": "analysis",
  "description": "Analyze feature requirements",
  "source_file": "enhancements/feature/feature.md",
  "status": "pending",
  "created": "2024-12-12T10:00:00Z",
  "started": null,
  "completed": null,
  "result": null,
  "auto_complete": true,
  "auto_chain": true,
  "metadata": {
    "workflow_name": "new-feature-development",
    "workflow_step": "0",
    "enhancement_title": "feature",
    "cost_input_tokens": "12345",
    "cost_output_tokens": "3456",
    "cost_cache_creation_tokens": "0",
    "cost_cache_read_tokens": "8901",
    "cost_usd": "0.0789",
    "cost_model": "claude-sonnet-4-20250514",
    "session_id": "abc123",
    "learnings_retrieved": ["learn_123", "learn_456"],
    "learnings_created": ["learn_789"]
  }
}
```

### Task Properties

**Core Properties**:
| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique ID: `task_<timestamp>_<pid>` |
| `title` | string | Short descriptive title |
| `assigned_agent` | string | Agent responsible for execution |
| `priority` | enum | `critical`, `high`, `normal`, `low` |
| `task_type` | string | Type: `analysis`, `implementation`, `testing`, etc. |
| `description` | string | Detailed task description |
| `source_file` | string | Path to input file |
| `status` | enum | `pending`, `active`, `completed`, `failed`, `cancelled` |
| `created` | string | ISO 8601 creation timestamp |
| `started` | string | ISO 8601 start timestamp |
| `completed` | string | ISO 8601 completion timestamp |
| `result` | string | Completion status code or error |

**Automation Properties**:
| Property | Type | Description |
|----------|------|-------------|
| `auto_complete` | boolean | Auto-complete without user prompt |
| `auto_chain` | boolean | Auto-chain to next workflow step |

**Metadata Properties**:
| Property | Type | Description |
|----------|------|-------------|
| `workflow_name` | string | Name of workflow template |
| `workflow_step` | string | Current step index |
| `enhancement_title` | string | Enhancement being worked on |
| `requested_model` | string | Model requested for this task execution |
| `cost_input_tokens` | string | Input tokens used |
| `cost_output_tokens` | string | Output tokens generated |
| `cost_cache_creation_tokens` | string | Cache creation tokens |
| `cost_cache_read_tokens` | string | Cache read tokens |
| `cost_usd` | string | Total cost in USD |
| `cost_model` | string | Model actually used (from cost extraction) |
| `session_id` | string | Claude session ID |
| `learnings_retrieved` | array | Learning IDs used in prompt |
| `learnings_created` | array | Learning IDs extracted from output |

---

## Task Lifecycle

### State Transitions

```
┌─────────┐
│ Created │
└────┬────┘
     │
     ↓
┌─────────┐     ┌───────────┐
│ Pending │────→│ Cancelled │
└────┬────┘     └───────────┘
     │ start
     ↓
┌─────────┐     ┌───────────┐
│ Active  │────→│ Cancelled │
└────┬────┘     └───────────┘
     │
     ├──→ fail ──→ ┌────────┐
     │             │ Failed │──┐
     │             └────────┘  │
     │                         │ rerun
     ↓ complete                │
┌───────────┐                  │
│ Completed │──────────────────┘
└─────┬─────┘
      │ auto-chain (if enabled)
      ↓
┌─────────────┐
│ Next Task   │
│ (Pending)   │
└─────────────┘
```

### Lifecycle Steps

#### 1. Task Creation

A task is created when:
- User manually adds a task
- Workflow is started
- Auto-chain creates follow-up task

**Initial State**:
- `status`: `pending`
- `created`: Current timestamp
- `started`, `completed`, `result`: null

#### 2. Task Start

When a task starts:
- `status` changes to `active`
- `started` set to current timestamp
- Agent status updated to `active`

#### 3. Task Execution

The assigned agent processes the task:
- Reads input from `source_file`
- Retrieves relevant learnings
- Executes work
- Creates output in `required_output/`
- Reports status via completion block

#### 4. Task Completion

When task completes successfully:
- `status` changes to `completed`
- `completed` set to current timestamp
- `result` contains status code (e.g., `READY_FOR_TESTING`)
- Agent status updated to `idle`
- Cost metadata updated (via hook)

#### 5. Auto-Chain (Optional)

If `auto_chain` is true and status has a transition:
- Next task is created based on workflow template
- New task enters pending state
- Workflow continues automatically

---

## CLI Commands

### queue status

Show summary counts.

```bash
python -m cmat queue status
```

**Output**:
```
Queue Status:
  Pending:   2
  Active:    1
  Completed: 15
  Failed:    0
  Total:     18
```

### queue list

List tasks by status.

```bash
python -m cmat queue list [pending|active|completed|failed|all]
```

**Examples**:
```bash
# List pending tasks
python -m cmat queue list pending

# List all tasks
python -m cmat queue list all

# List failed tasks
python -m cmat queue list failed
```

---

## QueueService API

The `QueueService` class provides programmatic access to queue operations.

### Core Methods

```python
# Get task by ID
task = queue_service.get(task_id)

# Add new task
task = queue_service.add(task_data)

# Start a task
queue_service.start(task_id)

# Complete a task
queue_service.complete(task_id, result)

# Fail a task
queue_service.fail(task_id, error)

# Cancel a task
queue_service.cancel(task_id, reason)

# Rerun a task
queue_service.rerun(task_id)
```

### Listing Methods

```python
# List by status
pending = queue_service.list_pending()
active = queue_service.list_active()
completed = queue_service.list_completed()
failed = queue_service.list_failed()
cancelled = queue_service.list_cancelled()
all_tasks = queue_service.list_tasks()  # All tasks

# Get status summary
status = queue_service.status()
# Returns: {"pending": 2, "active": 1, "completed": 15, "failed": 0, "total": 18}
```

### Cleanup Methods

```python
# Remove specific tasks by ID (permanently deletes from queue)
count = queue_service.clear_tasks([task_id1, task_id2])

# Clear all completed tasks
count = queue_service.clear_completed()

# Clear all failed tasks
count = queue_service.clear_failed()
```

**Note**: `cancel()` marks a task as cancelled but keeps it in the queue. Use `clear_tasks()` to permanently remove tasks from the queue.

### Metadata Methods

```python
# Update single metadata field
queue_service.update_single_metadata(task_id, "cost_usd", "0.0789")

# Get task cost info
cost_info = queue_service.show_task_cost(task_id)

# Get enhancement total cost
total = queue_service.show_enhancement_cost("my-feature")
```

---

## Integration with Workflows

### Workflow Context

When tasks are created from workflows, they carry context in metadata:

```json
{
  "metadata": {
    "workflow_name": "new-feature-development",
    "workflow_step": "0",
    "enhancement_title": "my-feature"
  }
}
```

### Auto-Chain Process

1. Task completes with status (e.g., `READY_FOR_TESTING`)
2. System checks task's `auto_chain` flag
3. If true, looks up workflow template
4. Finds current step's `on_status` transitions
5. If status matches and `auto_chain: true`:
   - Creates new task for next step
   - Copies workflow context
   - Increments step number
   - New task enters pending state

### Workflow Metadata Preservation

The following metadata is preserved during auto-chain:
- `workflow_name`
- `enhancement_title`

Updated during auto-chain:
- `workflow_step` (incremented)

---

## Cost Tracking

### How Costs Are Recorded

1. Task completes and session ends
2. `on-session-end-cost.sh` hook fires
3. Hook calls `python -m cmat costs extract`
4. `ModelService` parses transcript for usage
5. Cost metadata updated on task

### Cost Metadata Fields

```json
{
  "metadata": {
    "cost_input_tokens": "12345",
    "cost_output_tokens": "3456",
    "cost_cache_creation_tokens": "0",
    "cost_cache_read_tokens": "8901",
    "cost_usd": "0.0789",
    "cost_model": "claude-sonnet-4-20250514",
    "session_id": "abc123"
  }
}
```

### Viewing Costs

```bash
# Single task cost
python -m cmat costs show task_1702345678_12345

# Enhancement total
python -m cmat costs enhancement my-feature
```

---

## Learnings Integration

### Learnings Metadata

Tasks track which learnings were used and created:

```json
{
  "metadata": {
    "learnings_retrieved": ["learn_123", "learn_456"],
    "learnings_created": ["learn_789"]
  }
}
```

### Flow

1. **Before execution**: Relevant learnings retrieved based on task context
2. **During execution**: Learnings injected into agent prompt
3. **After execution**: New learnings extracted from output
4. **Metadata updated**: Learning IDs recorded on task

---

## Best Practices

### Task Management

1. **Clear titles**: Use descriptive titles that identify the work
2. **Proper priority**: Set appropriate priority for ordering
3. **Source files**: Always specify valid source file paths
4. **Workflow context**: Preserve workflow metadata for traceability

### Cost Management

1. **Monitor costs**: Regularly check enhancement costs
2. **Review high-cost tasks**: Investigate unusually expensive tasks
3. **Model selection**: Use appropriate model for task complexity

### Debugging

1. **Check queue status**: Start with `queue status` for overview
2. **List by state**: Use `queue list <state>` to find issues
3. **Review metadata**: Check workflow metadata for stuck tasks
4. **Verify agent status**: Ensure agents aren't stuck in active state

---

## Troubleshooting

### Task Stuck in Active State

**Symptoms**: Task shows as active but agent isn't running

**Causes**:
- Agent crashed without completing
- Hook failed to process completion

**Resolution**:
1. Check agent logs
2. Manually complete or fail the task
3. Verify hook configuration

### Tasks Not Auto-Chaining

**Symptoms**: Workflow stops after task completion

**Causes**:
- `auto_chain` is false
- Status not in workflow's `on_status`
- Transition's `auto_chain` is false

**Resolution**:
1. Check task's `auto_chain` flag
2. Check workflow template's `on_status`
3. Verify status code matches exactly

### Missing Cost Data

**Symptoms**: Cost metadata is null/empty

**Causes**:
- Hook not configured
- Transcript not available
- Model not recognized

**Resolution**:
1. Verify hook in settings.json
2. Check transcript path
3. Verify model in models.json

---

## See Also

- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Complete CLI commands
- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Workflow configuration
- [PROMPT_SYSTEM_GUIDE.md](PROMPT_SYSTEM_GUIDE.md) - Prompt construction and status reporting
- [COST_TRACKING.md](COST_TRACKING.md) - Cost management details
