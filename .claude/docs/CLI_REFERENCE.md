# CMAT CLI Reference

Complete reference for the CMAT command-line interface.

**Version**: 8.7.0

## Overview

CMAT provides a Python-based CLI for managing the multi-agent system. All commands are run as Python module:

```bash
cd /path/to/your/project/.claude
python -m cmat <command> [subcommand] [options]
```

---

## Command Summary

| Command | Description |
|---------|-------------|
| `version` | Show CMAT version |
| `workflow` | Manage and start workflows |
| `queue` | Manage task queue |
| `skills` | View skills and assignments |
| `learnings` | Manage RAG learnings |
| `agents` | Manage agent definitions |
| `models` | Manage Claude model configuration |
| `costs` | Track token usage and costs |

---

## Version

Show the current CMAT version.

```bash
python -m cmat version
# Output: CMAT version 8.2.0
```

---

## Workflow Commands

Manage workflow templates and start workflow executions.

### workflow list

List all available workflow templates.

```bash
python -m cmat workflow list
```

**Output**:
```
Available workflows (7):

  new-feature-development
    Name: New Feature Development
    Description: Complete workflow for implementing a new feature
    Steps: 5
  ...
```

### workflow show

Show detailed information about a workflow.

```bash
python -m cmat workflow show <name>
```

**Example**:
```bash
python -m cmat workflow show new-feature-development
```

**Output**:
```
Workflow: new-feature-development
  Name: New Feature Development
  Description: Complete workflow for implementing a new feature

  Steps (5):

    [0] requirements-analyst
        Input: enhancements/{enhancement_name}/{enhancement_name}.md
        Required Output: analysis_summary.md
        Status Transitions:
          READY_FOR_DEVELOPMENT -> architect (auto)
          BLOCKED -> (end) (manual)
    ...
```

### workflow start

Start a workflow for an enhancement.

```bash
python -m cmat workflow start <workflow_name> <enhancement_name> [--model <model_id>]
```

**Arguments**:
- `workflow_name` - Name of the workflow template
- `enhancement_name` - Name of the enhancement to process
- `--model <model_id>` - (Optional) Override the model for the first workflow step

**Example**:
```bash
python -m cmat workflow start new-feature-development my-feature

# With model override
python -m cmat workflow start new-feature-development my-feature --model claude-sonnet-4-20250514
```

**Output**:
```
Workflow started: new-feature-development
Enhancement: my-feature
Task: task_1702345678_12345
Agent: requirements-analyst
Status: active
Model: claude-sonnet-4-20250514
```

This creates the first task in the workflow and adds it to the pending queue.

### workflow validate

Validate a workflow template for errors.

```bash
python -m cmat workflow validate <name>
```

**Example**:
```bash
python -m cmat workflow validate new-feature-development
```

**Output** (if valid):
```
Workflow 'new-feature-development' is valid.
```

**Output** (if errors):
```
Validation errors for 'new-feature-development':
  - Step 0: Agent 'unknown-agent' not found
  - Step 2: Missing required_output
```

### workflow add

Create a new workflow template.

```bash
python -m cmat workflow add <id> <name> <description>
```

**Example**:
```bash
python -m cmat workflow add api-endpoint "API Endpoint" "Development workflow for REST endpoints"
```

### workflow remove

Delete a workflow template.

```bash
python -m cmat workflow remove <id>
```

**Example**:
```bash
python -m cmat workflow remove api-endpoint
```

### workflow update

Update workflow metadata (name or description).

```bash
python -m cmat workflow update <id> [--name <name>] [--description <desc>]
```

**Example**:
```bash
python -m cmat workflow update api-endpoint --name "REST API Development" --description "Updated description"
```

### workflow add-step

Add a step to a workflow.

```bash
python -m cmat workflow add-step <workflow_id> <agent> <input> <output> [--model <model>] [--index <n>]
```

**Arguments**:
- `workflow_id` - ID of the workflow to modify
- `agent` - Agent to assign (e.g., `implementer`)
- `input` - Input path pattern (e.g., `enhancements/{enhancement_name}/{enhancement_name}.md`)
- `output` - Required output filename (e.g., `analysis.md`)
- `--model <model>` - (Optional) Claude model for this step
- `--index <n>` - (Optional) Position to insert (appends if not specified)

**Example**:
```bash
python -m cmat workflow add-step api-endpoint requirements-analyst "enhancements/{enhancement_name}/{enhancement_name}.md" "requirements.md"

# Add with specific model
python -m cmat workflow add-step api-endpoint architect "{previous_step}/required_output/" "design.md" --model claude-opus-4-20250514
```

### workflow remove-step

Remove a step from a workflow.

```bash
python -m cmat workflow remove-step <workflow_id> <step_index>
```

**Example**:
```bash
python -m cmat workflow remove-step api-endpoint 2
```

### workflow update-step

Update an existing workflow step.

```bash
python -m cmat workflow update-step <workflow_id> <step_index> [--agent <a>] [--input <i>] [--output <o>] [--model <m>]
```

**Example**:
```bash
python -m cmat workflow update-step api-endpoint 0 --model claude-sonnet-4-20250514
```

### workflow add-transition

Add a status transition to a workflow step.

```bash
python -m cmat workflow add-transition <workflow_id> <step_index> <status> [--next-step <agent>] [--no-auto-chain] [--description <desc>]
```

**Arguments**:
- `workflow_id` - ID of the workflow to modify
- `step_index` - Index of the step to add transition to
- `status` - Status name (e.g., `READY_FOR_DEVELOPMENT`)
- `--next-step <agent>` - (Optional) Next agent to chain to (omit for workflow end)
- `--no-auto-chain` - Halt workflow on this status (for statuses like BLOCKED)
- `--description <desc>` - (Optional) Description of this transition

**Example**:
```bash
# Auto-chain to next agent
python -m cmat workflow add-transition api-endpoint 0 READY_FOR_DEVELOPMENT --next-step architect

# Halt status (no auto-chain)
python -m cmat workflow add-transition api-endpoint 0 BLOCKED --no-auto-chain --description "Cannot proceed"
```

### workflow remove-transition

Remove a status transition from a workflow step.

```bash
python -m cmat workflow remove-transition <workflow_id> <step_index> <status>
```

**Example**:
```bash
python -m cmat workflow remove-transition api-endpoint 0 BLOCKED
```

---

## Queue Commands

Manage the task queue.

### queue status

Show queue summary with counts by status.

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
python -m cmat queue list [pending|active|completed|failed|cancelled|all]
```

**Arguments**:
- `pending` - Tasks waiting to start
- `active` - Currently running tasks
- `completed` - Successfully finished tasks
- `failed` - Tasks that failed
- `cancelled` - Tasks that were cancelled
- `all` - All tasks (default)

**Example**:
```bash
python -m cmat queue list pending
```

### queue add

Add a new task to the queue.

```bash
python -m cmat queue add <agent> <title> <source_file> [--auto-chain] [--model <model_id>]
```

**Arguments**:
- `agent` - Agent to assign (e.g., `implementer`)
- `title` - Task title
- `source_file` - Path to input file
- `--auto-chain` - Enable auto-chaining to next workflow step
- `--model <model_id>` - (Optional) Specify the Claude model to use for this task

**Example**:
```bash
python -m cmat queue add implementer "Fix login bug" enhancements/bugfix/bugfix.md --auto-chain

# With model specification
python -m cmat queue add architect "Design system" spec.md --model claude-opus-4-20250514
```

### queue start

Start a pending task (mark as active).

```bash
python -m cmat queue start <task_id>
```

**Example**:
```bash
python -m cmat queue start task_1702345678_12345
```

### queue complete

Mark an active task as completed.

```bash
python -m cmat queue complete <task_id> <result>
```

**Arguments**:
- `task_id` - Task to complete
- `result` - Completion status (e.g., `READY_FOR_TESTING`)

**Example**:
```bash
python -m cmat queue complete task_1702345678_12345 READY_FOR_TESTING
```

### queue fail

Mark an active task as failed.

```bash
python -m cmat queue fail <task_id> <reason>
```

**Example**:
```bash
python -m cmat queue fail task_1702345678_12345 "Build failed: missing dependency"
```

### queue cancel

Cancel a pending or active task. The task remains in the queue with `cancelled` status.

```bash
python -m cmat queue cancel <task_id> [reason]
```

**Example**:
```bash
python -m cmat queue cancel task_1702345678_12345 "No longer needed"
```

**Note**: To permanently remove tasks from the queue, use the `QueueService.clear_tasks()` API method. See [QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md) for details.

### queue rerun

Re-queue a completed or failed task.

```bash
python -m cmat queue rerun <task_id>
```

This resets the task to pending status for re-execution.

**Example**:
```bash
python -m cmat queue rerun task_1702345678_12345
```

---

## Skills Commands

View skills and their assignments.

### skills list

List all available skills, grouped by category.

```bash
python -m cmat skills list
```

**Output**:
```
Available skills (16):

  [analysis]
    requirements-elicitation
      Name: Requirements Elicitation
      Description: Extract and clarify requirements from specifications...
    user-story-writing
      Name: User Story Writing
      Description: Create clear user stories with acceptance criteria

  [architecture]
    api-design
      Name: API Design
      Description: Design RESTful APIs with proper contracts...
  ...
```

### skills show

Show detailed information about a skill.

```bash
python -m cmat skills show <skill_directory>
```

**Example**:
```bash
python -m cmat skills show api-design
```

**Output**:
```
Skill: api-design
  Name: API Design
  Description: Design RESTful APIs with proper contracts and specifications
  Category: architecture
  Required Tools: Read, Write, Grep

  Content Preview:
    ---
    name: "API Design"
    ...
```

### skills get

Get skills assigned to a specific agent.

```bash
python -m cmat skills get <agent_name>
```

**Example**:
```bash
python -m cmat skills get implementer
```

**Output**:
```
Skills for agent 'implementer':

  error-handling
    Name: Error Handling Strategies
    Category: implementation

  code-refactoring
    Name: Code Refactoring
    Category: implementation
```

---

## Learnings Commands

Manage the RAG-based learnings system.

### learnings list

List all stored learnings.

```bash
python -m cmat learnings list
```

### learnings add

Add a new learning manually.

```bash
python -m cmat learnings add "<content>" [--tags tag1,tag2]
```

**Examples**:
```bash
python -m cmat learnings add "Always use snake_case for Python function names"

python -m cmat learnings add "Use pytest fixtures for database tests" --tags testing,python
```

### learnings delete

Delete a learning by ID.

```bash
python -m cmat learnings delete <id>
```

### learnings show

Show full details of a specific learning.

```bash
python -m cmat learnings show <id>
```

### learnings search

Search for relevant learnings using Claude.

```bash
python -m cmat learnings search "<query>"
```

**Example**:
```bash
python -m cmat learnings search "database testing patterns"
```

### learnings count

Show the total number of stored learnings.

```bash
python -m cmat learnings count
```

---

## Agents Commands

Manage agent definitions and registry.

### agents list

List all registered agents.

```bash
python -m cmat agents list
```

**Output**:
```
Found 8 agent(s):

  requirements-analyst.md
    Name: Requirements Analyst
    Role: analysis
    Skills: requirements-elicitation, user-story-writing, bug-triage
  ...
```

### agents generate

Regenerate `agents.json` from agent markdown files.

```bash
python -m cmat agents generate
```

---

## Models Commands

Manage Claude model configuration and pricing.

### models list

List all configured Claude models.

```bash
python -m cmat models list
```

### models show

Show detailed information about a specific model.

```bash
python -m cmat models show <id>
```

### models set-default

Set the default model for task execution and cost calculations. When tasks run without an explicit model (via `--model` flag or workflow step configuration), CMAT uses this default model.

```bash
python -m cmat models set-default <id>
```

---

## Costs Commands

Track and display token usage and costs.

### costs extract

Extract costs from a Claude transcript and store in task metadata.

```bash
python -m cmat costs extract <task_id> <transcript_path> [session_id]
```

This is typically called automatically by the `on-session-end-cost.sh` hook.

### costs show

Show cost breakdown for a specific task.

```bash
python -m cmat costs show <task_id>
```

### costs enhancement

Show total costs for all tasks in an enhancement.

```bash
python -m cmat costs enhancement <name>
```

---

## Help

Show CLI usage information.

```bash
python -m cmat --help
python -m cmat -h
python -m cmat help
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid arguments, not found, etc.) |

---

## Examples

### Starting a New Feature

```bash
# 1. Create enhancement spec
mkdir -p enhancements/my-feature
cat > enhancements/my-feature/my-feature.md << 'EOF'
# My Feature
Description of what to build...
EOF

# 2. Start workflow
python -m cmat workflow start new-feature-development my-feature

# 3. Monitor progress
python -m cmat queue status
python -m cmat queue list pending
```

### Daily Workflow

```bash
# Check status
python -m cmat queue status

# List active tasks
python -m cmat queue list active

# Check costs
python -m cmat costs enhancement my-feature
```

### Debugging Issues

```bash
# Check if agents are registered
python -m cmat agents list

# Regenerate agents if needed
python -m cmat agents generate

# Check for stuck tasks
python -m cmat queue list active

# Re-run a failed task
python -m cmat queue rerun <task_id>
```

---

## See Also

- [README.md](../../README.md) - System overview
- [DEMO.md](../../DEMO.md) - Hands-on demo walkthrough
- [LEARNINGS_GUIDE.md](LEARNINGS_GUIDE.md) - RAG memory system details
- [COST_TRACKING.md](COST_TRACKING.md) - Cost tracking details
- [QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md) - Task queue operations