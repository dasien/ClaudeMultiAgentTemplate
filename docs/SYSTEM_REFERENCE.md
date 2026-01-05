# System Reference

Technical reference for CMAT internals: task queue, agents, workflows, prompt construction, cost tracking, skills, and learnings.

---

## Table of Contents

- [Task Queue](#task-queue)
- [Agents](#agents)
- [Workflow Templates](#workflow-templates)
- [Enhancements](#enhancements)
- [Prompts](#prompts)
- [Cost Tracking](#cost-tracking)
- [Models](#models)
- [Skills](#skills)
- [Learnings](#learnings)
- [Service APIs](#service-apis)
- [Troubleshooting](#troubleshooting)

---

## Task Queue

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

## Agents

Agents are specialized capability definitions that execute tasks within workflows.

### Agent Structure

Each agent is defined by a markdown file with YAML frontmatter:

**Location**: `.claude/agents/{agent-slug}.md`

```markdown
---
name: "Implementer"
role: "implementation"
description: "Implements features based on architectural specifications"
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task"]
skills: ["error-handling", "code-refactoring", "sql-development"]
validations:
  metadata_required: true
---

# Implementer Agent

## Role and Purpose
[Agent instructions and guidelines...]
```

### Agent Frontmatter Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Display name (e.g., "Requirements Analyst") |
| `role` | string | Yes | Role category (see below) |
| `description` | string | Yes | Brief description of agent's purpose |
| `tools` | array | Yes | Claude Code tools agent can use |
| `skills` | array | No | Skill slugs assigned to this agent |
| `validations` | object | No | Validation settings |

### Agent Roles

| Role | Description | Typical Task Types |
|------|-------------|-------------------|
| `analysis` | Requirements and scope analysis | analysis |
| `technical_design` | Architecture and system design | technical_analysis |
| `implementation` | Code writing and development | implementation |
| `testing` | Test creation and execution | testing |
| `documentation` | Documentation writing | documentation |
| `integration` | External system integration | integration |

### Available Tools

| Tool | Description |
|------|-------------|
| `Read` | Read files from filesystem |
| `Write` | Create new files |
| `Edit` | Modify existing files |
| `MultiEdit` | Batch file modifications |
| `Bash` | Execute shell commands |
| `Glob` | Find files by pattern |
| `Grep` | Search file contents |
| `Task` | Spawn sub-agents |
| `WebSearch` | Search the web |
| `WebFetch` | Fetch web content |

### Agent Output Structure

Agents create outputs in a standard directory structure:

```
enhancements/{enhancement_name}/{agent-slug}/
├── required_output/
│   └── {workflow-specified-filename}.md
└── optional_output/
    └── [additional files]
```

### Completion Block

Every agent must output a completion block:

```yaml
---
agent: implementer
task_id: task_1702345678_12345
status: READY_FOR_TESTING
skills_used: [error-handling, code-refactoring]
---
```

---

## Workflow Templates

Workflow templates define how agents collaborate to process enhancements.

### Template Structure

**Location**: `.claude/data/workflow_templates.json`

```json
{
  "version": "2.0.0",
  "workflows": {
    "new-feature-development": {
      "name": "New Feature Development",
      "description": "Complete workflow for implementing a new feature",
      "steps": [
        {
          "agent": "requirements-analyst",
          "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
          "required_output": "analysis_summary.md",
          "on_status": {
            "READY_FOR_DEVELOPMENT": {
              "next_step": "architect",
              "auto_chain": true
            },
            "BLOCKED": {
              "next_step": null,
              "auto_chain": false,
              "description": "Cannot proceed without external input"
            }
          }
        }
      ]
    }
  }
}
```

### Workflow Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Display name |
| `description` | string | When to use this workflow |
| `steps` | array | Ordered list of workflow steps |

### Step Properties

| Property | Type | Description |
|----------|------|-------------|
| `agent` | string | Agent slug to execute this step |
| `input` | string | Input pattern (supports placeholders) |
| `required_output` | string | Filename agent must create |
| `on_status` | object | Status-to-transition mappings |

### Input Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{enhancement_name}` | Enhancement directory name | `user-auth` |
| `{previous_step}` | Previous agent's output directory | `requirements-analyst` |

### Status Transitions

Each transition defines what happens when an agent outputs a specific status:

```json
{
  "READY_FOR_DEVELOPMENT": {
    "next_step": "architect",
    "auto_chain": true,
    "auto_start": true
  },
  "READY_FOR_REVIEW": {
    "next_step": "implementer",
    "auto_chain": true,
    "auto_start": false,
    "description": "Pauses for human review before implementation"
  },
  "BLOCKED": {
    "next_step": null,
    "auto_chain": false,
    "description": "Requires user intervention"
  }
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `next_step` | string/null | - | Next agent slug, or null to end workflow |
| `auto_chain` | boolean | true | Automatically create next task when this status is output |
| `auto_start` | boolean | true | Immediately start the created task (false = leave pending for review) |
| `description` | string | - | (Optional) Explanation of this transition |

### Common Status Codes

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
- `BUILD_FAILED: <error>` - Code doesn't compile
- `NEEDS_RESEARCH: <topic>` - Technical unknowns

---

## Enhancements

Enhancements are structured specification documents that serve as workflow inputs.

### Enhancement Structure

**Location**: `enhancements/{enhancement-slug}/{enhancement-slug}.md`

```
enhancements/
└── user-authentication/
    ├── user-authentication.md          # Enhancement spec (input)
    ├── requirements-analyst/           # Step 1 outputs
    │   ├── required_output/
    │   │   └── analysis_summary.md
    │   └── optional_output/
    │       └── user_stories_detailed.md
    ├── architect/                      # Step 2 outputs
    │   └── required_output/
    │       └── implementation_plan.md
    ├── implementer/                    # Step 3 outputs
    │   └── required_output/
    │       └── implementation_summary.md
    ├── tester/                         # Step 4 outputs
    │   └── required_output/
    │       └── test_summary.md
    └── logs/                           # Task execution logs
        └── task_1702345678_12345.log
```

### Enhancement Spec Format

Enhancement specifications typically include:

- **Overview**: What is being built and why
- **Requirements**: Functional and non-functional requirements
- **Acceptance Criteria**: How success is measured
- **Technical Constraints**: Limitations and considerations
- **Dependencies**: Related systems or features

### Agent Output Files

Each agent creates a `required_output/` directory containing the file specified by the workflow template. Optional additional files go in `optional_output/`.

**Required output format** (includes metadata header):

```markdown
---
enhancement: user-authentication
agent: requirements-analyst
task_id: task_1702345678_12345
timestamp: 2024-12-12T10:30:00Z
status: READY_FOR_DEVELOPMENT
---

# Analysis Summary

[Agent's analysis content...]
```

---

## Prompts

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

### Viewing Costs

Costs are visible in the UI:
- Task details dialog shows per-task costs
- Enhancement totals aggregate all task costs

---

## Models

CMAT maintains model configurations for pricing calculations and selection.

### Model Configuration

**Location**: `.claude/data/models.json`

```json
{
  "models": {
    "claude-sonnet-4.5": {
      "pattern": "*sonnet-4-5*",
      "name": "Claude Sonnet 4.5",
      "api_id": "claude-sonnet-4-5-20250929",
      "description": "Balanced model for most tasks",
      "max_tokens": 200000,
      "pricing": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.3,
        "currency": "USD",
        "per_tokens": 1000000
      }
    }
  },
  "default_model": "claude-sonnet-4.5"
}
```

### Model Properties

| Property | Type | Description |
|----------|------|-------------|
| `pattern` | string | Glob pattern to match model strings |
| `name` | string | Display name |
| `api_id` | string | Anthropic API model identifier |
| `description` | string | Model capabilities summary |
| `max_tokens` | integer | Maximum context tokens |
| `pricing` | object | Cost per million tokens |

### Pricing Structure

| Field | Description |
|-------|-------------|
| `input` | Cost per 1M input tokens |
| `output` | Cost per 1M output tokens |
| `cache_write` | Cost per 1M cache creation tokens |
| `cache_read` | Cost per 1M cache read tokens |
| `currency` | Currency code (USD) |
| `per_tokens` | Token unit (1000000) |

### Current Model Pricing

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| claude-sonnet-4.5 | $3.00 | $15.00 |
| claude-sonnet-4 | $3.00 | $15.00 |
| claude-haiku-4.5 | $0.25 | $1.25 |
| claude-haiku-4 | $0.25 | $1.25 |
| claude-opus-4.5 | $5.00 | $25.00 |

---

## Skills

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

### Skill Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Display name |
| `description` | string | Brief purpose description |
| `category` | string | Skill category (see below) |
| `required_tools` | array | Tools needed to apply this skill |

### Skill Categories

- **analysis** - Requirements analysis skills
- **architecture** - System design skills
- **implementation** - Coding and development skills
- **testing** - Test design and execution skills
- **documentation** - Documentation writing skills
- **security** - Security analysis skills
- **performance** - Optimization skills

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

## Learnings

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

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier |
| `summary` | string | 1-2 sentence description |
| `content` | string | Full learning content |
| `tags` | array | Categories for retrieval |
| `applies_to` | array | Task types where relevant |
| `source_type` | string | `user_input`, `agent_output`, `code_pattern` |
| `confidence` | float | 0.0-1.0, how universal vs project-specific |

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

### AgentsService

```python
# Agent operations
agents.list_all() -> list[Agent]
agents.get(agent_slug) -> Agent
agents.get_by_role(role) -> list[Agent]
agents.create(agent_data) -> Agent
agents.update(agent_slug, agent_data) -> Agent
agents.delete(agent_slug) -> bool
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
skills.create(skill_data) -> Skill
skills.update(skill_directory, skill_data) -> Skill
skills.delete(skill_directory) -> bool
```

### LearningsService

```python
learnings.list_all() -> list[Learning]
learnings.get(learning_id) -> Learning
learnings.store(learning) -> str
learnings.delete(learning_id) -> bool
learnings.count() -> int
```

### ModelsService

```python
models.list_all() -> list[Model]
models.get(model_id) -> Model
models.get_default() -> Model
models.calculate_cost(model_id, tokens) -> float
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

### Agent Not Found

**Cause**: Agent file missing or malformed frontmatter

**Resolution**:
- Check `.claude/agents/{agent-slug}.md` exists
- Verify YAML frontmatter is valid
- Ensure required fields (name, role, description, tools) are present

### Workflow Validation Errors

**Cause**: Invalid workflow template configuration

**Resolution**:
- Check all referenced agents exist
- Verify input patterns use valid placeholders
- Ensure all transition targets exist in workflow
- Validate required_output filenames end with `.md`