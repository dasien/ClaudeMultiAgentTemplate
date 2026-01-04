# System Reference

Technical reference for CMAT internals: task queue, prompt construction, cost tracking, skills, and learnings.

---

## Table of Contents

- [Task Queues](#task-queue-system)
- [Prompts](#prompt-system)
- [Cost Tracking](#cost-tracking)
- [Skills](#skills-system)
- [Learnings](#learnings-system)

---

## Task Queue System

The queue system manages the lifecycle of all agent tasks.

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
    "cost_usd": "0.0789",
    "session_id": "abc123"
  }
}
```

### Task Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique ID: `task_<timestamp>_<pid>` |
| `title` | string | Short descriptive title |
| `assigned_agent` | string | Agent responsible for execution |
| `priority` | enum | `critical`, `high`, `normal`, `low` |
| `task_type` | string | Type: `analysis`, `implementation`, `testing`, etc. |
| `status` | enum | `pending`, `active`, `completed`, `failed`, `cancelled` |
| `auto_complete` | boolean | Auto-complete without user prompt |
| `auto_chain` | boolean | Auto-chain to next workflow step |

### Task Lifecycle

```
Created → Pending → Active → Completed
                      ↓
                   Failed
```

1. **Created**: Task added to queue
2. **Pending**: Waiting to be started
3. **Active**: Agent is executing
4. **Completed**: Successfully finished with result status
5. **Failed**: Error occurred during execution

### Auto-Chain Process

When a task completes:
1. System checks `auto_chain` flag
2. Looks up workflow template for current step
3. Matches result status to `on_status` transitions
4. If transition has `auto_chain: true`, creates next task

---

## Prompt System

When you start a task, CMAT constructs a prompt that includes:

1. **Base task template** (from TASK_PROMPT_DEFAULTS.md)
2. **Workflow context** (expected statuses, input/output specs)
3. **Skills** (domain expertise for the agent)
4. **Variable substitutions** (task-specific details)
5. **User input** (enhancement spec file)

### Prompt Construction Pipeline

```
1. Load base template (by task_type)
2. Inject skills section
3. Get workflow context (expected statuses, required output)
4. Substitute all variables
5. Send final prompt to Claude
6. Agent outputs completion block
7. System extracts status and triggers next step
```

### Variable Substitution

| Variable | Description |
|----------|-------------|
| `${agent}` | Agent name |
| `${agent_config}` | Path to agent configuration file |
| `${task_id}` | Unique task identifier |
| `${task_description}` | Task description |
| `${enhancement_name}` | Enhancement name |
| `${enhancement_dir}` | Enhancement directory path |
| `${required_output_filename}` | Required output filename |
| `${expected_statuses}` | List of expected status codes |

### Completion Block Format

Every agent outputs a YAML completion block:

```yaml
---
agent: implementer
task_id: task_1702345678_12345
status: READY_FOR_TESTING
skills_used: [error-handling, code-refactoring]
---
```

### Status Types

**Completion Statuses** (workflow continues):
- `READY_FOR_DEVELOPMENT` - Requirements complete
- `READY_FOR_IMPLEMENTATION` - Architecture complete
- `READY_FOR_TESTING` - Implementation complete
- `TESTING_COMPLETE` - All tests passed
- `DOCUMENTATION_COMPLETE` - Documentation updated

**Halt Statuses** (requires intervention):
- `BLOCKED: <reason>` - Cannot proceed
- `NEEDS_CLARIFICATION: <question>` - Requirements unclear
- `TESTS_FAILED: <details>` - Tests did not pass

---

## Cost Tracking

CMAT tracks token usage and costs for each task via Claude Code hooks.

### How Costs Are Recorded

1. Task completes and session ends
2. `on-session-end-cost.sh` hook fires
3. Hook calls `python3 -m core costs extract`
4. Cost metadata updated on task

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

### Model Pricing

Costs are calculated based on model pricing defined in `models.json`:

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| claude-sonnet-4.5 | $3.00 | $15.00 |
| claude-sonnet-4 | $3.00 | $15.00 |
| claude-haiku-4.5 | $0.80 | $4.00 |
| claude-opus-4.5 | $15.00 | $75.00 |

### Viewing Costs

Costs are visible in the UI:
- Task details dialog shows per-task costs
- Enhancement totals aggregate all task costs

---

## Skills System

Skills provide specialized capabilities that agents can apply to their work.

### Skill Structure

Each skill has:
- **Directory**: `.claude/skills/{skill-name}/`
- **Definition**: `SKILL.md` file with frontmatter and content

```markdown
---
name: "Error Handling"
description: "Implement robust error handling patterns"
category: "implementation"
required_tools: ["Read", "Write", "Edit"]
---

# Error Handling

## Purpose
Guide implementation of robust error handling...

## When to Use
- Implementing new features
- Refactoring error-prone code

## Key Capabilities
1. **Exception Hierarchies** - Design custom exceptions
2. **Recovery Strategies** - Implement graceful degradation
```

### Skill Categories

- **analysis** - Requirements analysis skills
- **implementation** - Coding and development skills
- **testing** - Test design and execution skills
- **documentation** - Documentation writing skills

### Skills Assignment

Skills are assigned to agents in their frontmatter:

```yaml
---
name: "Implementer"
skills: ["error-handling", "code-refactoring", "test-design-patterns"]
---
```

### How Skills Are Used

1. When a task starts, system loads agent's assigned skills
2. Skills are injected into the prompt as guidance
3. Agent applies relevant skills to their work
4. Agent reports which skills were used in completion block

---

## Learnings System

The learnings system provides persistent memory via RAG (Retrieval-Augmented Generation).

### Learning Structure

```json
{
  "id": "learn_1702345678_12345",
  "summary": "Use pytest fixtures for database tests",
  "content": "When writing database tests, always use pytest fixtures...",
  "tags": ["testing", "python", "database"],
  "applies_to": ["implementation", "testing"],
  "source_type": "user_input",
  "confidence": 0.8,
  "created": "2024-12-12T10:30:00Z"
}
```

### Learning Properties

| Property | Description |
|----------|-------------|
| `summary` | 1-2 sentence description |
| `content` | Full learning content |
| `tags` | Categories for retrieval |
| `applies_to` | Task types where relevant |
| `source_type` | `user_input`, `agent_output`, `code_pattern` |
| `confidence` | 0.0-1.0, how universal vs project-specific |

### Learning Flow

```
Learning Sources (agent outputs, user input)
    ↓
Extraction (via Claude)
    ↓
Storage (learnings.json)
    ↓ (on new task)
Retrieval (context-aware)
    ↓
Prompt Injection
```

### Retrieval Context

When retrieving learnings, the system considers:
- Agent name and role
- Task type (analysis, implementation, etc.)
- Task description
- Source file being processed

### Adding Learnings

Learnings can be added through the UI's Learnings Browser dialog or extracted automatically from agent outputs.

### Best Practices

**Adding Effective Learnings**:
- Be specific and actionable
- Include reasoning (why, not just what)
- Use appropriate tags for discoverability
- Set applies_to for relevant task types

**Learning Categories**:
- Code style and conventions
- Architecture patterns
- Testing approaches
- Security practices
- Performance optimization

---

## Service APIs

### QueueService

```python
# Task operations
queue.add(title, agent, priority, task_type, source_file, description)
queue.get(task_id) -> Task
queue.start(task_id) -> Task
queue.complete(task_id, result) -> Task
queue.fail(task_id, reason) -> Task
queue.cancel(task_id) -> Task

# Listing
queue.list_pending() -> list[Task]
queue.list_active() -> list[Task]
queue.list_completed() -> list[Task]
queue.list_failed() -> list[Task]

# Status
queue.status() -> dict  # counts by status
```

### WorkflowService

```python
# Template CRUD
workflow.list_all() -> list[WorkflowTemplate]
workflow.get(workflow_id) -> WorkflowTemplate
workflow.add(template) -> WorkflowTemplate
workflow.update(template) -> WorkflowTemplate
workflow.delete(workflow_id) -> bool

# Orchestration
workflow.start_workflow(name, enhancement, description, auto_chain, model)
workflow.auto_chain(task_id, status) -> Optional[str]
```

### SkillsService

```python
skills.list_all() -> list[Skill]
skills.get(skill_directory) -> Skill
skills.get_by_category(category) -> list[Skill]
skills.get_skills_for_agent(skill_names) -> list[Skill]
```

### LearningsService

```python
learnings.list_all() -> list[Learning]
learnings.get(learning_id) -> Learning
learnings.store(learning) -> str
learnings.delete(learning_id) -> bool
learnings.count() -> int
```

---

## Troubleshooting

### Task Stuck in Active State

**Cause**: Agent crashed without completing

**Resolution**:
- Check task logs in enhancement directory
- Manually fail or cancel the task via UI

### Tasks Not Auto-Chaining

**Cause**: Status not in workflow's `on_status` or `auto_chain` is false

**Resolution**:
- Verify status code matches workflow definition exactly
- Check workflow template transitions

### Missing Cost Data

**Cause**: Hook not configured or transcript unavailable

**Resolution**:
- Verify hook is in `.claude/hooks/`
- Check CMAT_ROOT environment variable is set

### Learnings Not Being Retrieved

**Cause**: Tags don't match task context

**Resolution**:
- Check learning tags match task context
- Verify `applies_to` includes relevant task types
