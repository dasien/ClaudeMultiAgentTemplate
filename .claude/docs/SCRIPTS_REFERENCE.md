# Scripts Reference Guide

Complete reference for all `cmat` commands in the Claude Multi-Agent Template.

## Command Structure

```bash
cmat <category> <command> [options]
```

**Categories**:
- `queue` - Task queue management
- `workflow` - Workflow template management and orchestration
- `skills` - Skills management
- `integration` - External system integration
- `agents` - Agent operations
- `version` - Show version information
- `help` - Show help message

## Quick Reference

```bash
# Common operations
cmat queue status                       # View queue status
cmat queue add "..." "..." ...          # Add task
cmat queue start <task_id>              # Start task
cmat skills list                        # List all skills
cmat workflow validate <template>       # Validate workflow template
cmat workflow start <workflow> <enh>    # Start workflow
cmat integration sync <task_id>         # Sync to external systems
cmat version                            # Show version info
```

---

## Queue Commands

Task lifecycle management operations.

### queue add

Add a new task to the pending queue.

```bash
cmat queue add <title> <agent> <priority> <type> <source> <description> [auto_complete] [auto_chain] [enhancement_title]
```

**Parameters**:
- `title` (required) - Short descriptive title for the task
- `agent` (required) - Agent name (must exist in agents.json)
- `priority` (required) - Task priority: `critical`, `high`, `normal`, `low`
- `type` (required) - Task type: `analysis`, `technical_analysis`, `implementation`, `testing`, `documentation`, `integration`
- `source` (optional) - Path to source file or directory. Can be empty string `""` for ad-hoc tasks without a specific input file. When empty, output goes to `enhancements/{task_id}/`
- `description` (required) - Detailed task description
- `auto_complete` (optional) - Auto-complete without prompt: `true`|`false` (default: `false`)
- `auto_chain` (optional) - Auto-chain to next step: `true`|`false` (default: `false`)
- `enhancement_title` (optional) - Enhancement title (extracted from source if not provided)

**Returns**: Task ID (e.g., `task_1234567890_12345`)

**Examples**:
```bash
# Manual task (prompts for everything)
TASK_ID=$(cmat queue add \
  "Analyze feature requirements" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/my-feature/my-feature.md" \
  "Initial requirements analysis" \
  false \
  false)

# Fully automated (runs entire workflow hands-off)
TASK_ID=$(cmat queue add \
  "Full workflow" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/my-feature/my-feature.md" \
  "Complete feature development" \
  true \
  true)

# Ad-hoc task without source file (quick one-off task)
TASK_ID=$(cmat queue add \
  "Review authentication code" \
  "code-reviewer" \
  "high" \
  "analysis" \
  "" \
  "Review the src/auth module for security vulnerabilities" \
  true \
  false)
# Output will be in: enhancements/task_1234567890_12345/code-reviewer/required_output/output.md
```

---

### queue start

Move task from pending to active and invoke the agent.

```bash
cmat queue start <task_id>
```

**Parameters**:
- `task_id` (required) - Task ID to start

**Behavior**:
1. Moves task from `pending_tasks` to `active_workflows`
2. Sets `status` to "active"
3. Records `started` timestamp
4. Updates agent status
5. Invokes agent with task parameters
6. Logs execution to `enhancements/{name}/logs/`

---

### queue complete

Mark active task as completed.

```bash
cmat queue complete <task_id> [result] [--auto-chain|true|false]
```

**Parameters**:
- `task_id` (required) - Task ID to complete
- `result` (optional) - Result message or status code (default: "completed successfully")
- `--auto-chain` or `true` (optional) - Automatically chain to next step if workflow

---

### queue status

Display current queue status and agent states.

```bash
cmat queue status
```

**Output**:
```
=== Multi-Agent Queue Status ===

📋 Agent Status:
  • requirements-analyst: idle
  • architect: active
  • implementer: idle

⏳ Pending Tasks:
  • [high] Implement feature X → implementer (ID: task_123...)

🔄 Active Workflows:
  • Design architecture for X → architect (Started: 2025-11-17T14:45:00Z)

✅ Recently Completed:
  • Analyze requirements → requirements-analyst
```

---

### queue list

List tasks from a specific queue.

```bash
cmat queue list <queue_type> [format]
```

**Parameters**:
- `queue_type` (required) - Queue: `pending`, `active`, `completed`, `failed`, `all`
- `format` (optional) - Format: `json` (default), `compact`

---

### queue metadata

Update task metadata field.

```bash
cmat queue metadata <task_id> <key> <value>
```

**Common Metadata Fields**:
- `workflow_name` - Which workflow template is executing
- `workflow_step` - Current step index in workflow
- `github_issue` - GitHub issue number
- `jira_ticket` - Jira ticket key
- `parent_task_id` - Parent task reference

---

### queue show-task-cost

Display cost in USD for a specific task.

```bash
cmat queue show-task-cost <task_id>
```

**Returns**: Cost in USD (e.g., `0.0234`)

---

### queue show-enhancement-cost

Display total cost in USD for all tasks in an enhancement.

```bash
cmat queue show-enhancement-cost <enhancement_name>
```

**Returns**: Total cost in USD (e.g., `0.1567`)

---

### queue rerun

Re-queue a completed or failed task for re-execution.

```bash
cmat queue rerun <task_id> [--start]
```

**Parameters**:
- `task_id` (required) - Task ID to re-run
- `--start` (optional) - Start the task immediately after re-queuing

**Behavior**:
1. Finds task in `completed_tasks` or `failed_tasks`
2. Resets task state (`status`, `started`, `completed`, `result`)
3. Moves task back to `pending_tasks`
4. Preserves workflow metadata for auto-chain continuation
5. Optionally starts task immediately

**Use Cases**:
- Re-run a task that completed with `BLOCKED:` status after resolving the blocker
- Retry a failed task after fixing the underlying issue
- Re-execute a task to get updated output

**Examples**:
```bash
# Re-queue task (requires manual start)
cmat queue rerun task_1234567890_12345

# Re-queue and start immediately
cmat queue rerun task_1234567890_12345 --start
```

---

## Workflow Commands

Workflow template management and execution.

### workflow create

Create a new workflow template.

```bash
cmat workflow create <template_name> <description>
```

**Examples**:
```bash
cmat workflow create api-dev "REST API development workflow"
```

---

### workflow list

List all available workflow templates.

```bash
cmat workflow list
```

**Output**:
```
new_feature_development - Complete workflow (5 steps)
bugfix_workflow - Bug fix workflow (4 steps)
hotfix_workflow - Fast-track critical issues (2 steps)
api-dev - REST API development (4 steps)
```

---

### workflow show

Display detailed workflow template information.

```bash
cmat workflow show <template_name>
```

**Output**:
```
Template: api-dev
Description: REST API development workflow
Steps: 4

Workflow:
  Step 0: requirements-analyst
    Input: enhancements/{enhancement_name}/{enhancement_name}.md
    Output: analysis.md
    Transitions:
      READY_FOR_DEVELOPMENT → architect (auto: true)

  Step 1: architect
    Input: {previous_step}/required_output/
    Output: design.md
    Transitions:
      READY_FOR_IMPLEMENTATION → implementer (auto: true)
```

---

### workflow delete

Delete a workflow template.

```bash
cmat workflow delete <template_name>
```

---

### workflow add-step

Add a step to a workflow template.

```bash
cmat workflow add-step <template_name> <agent> <input> <output> [position]
```

**Parameters**:
- `template_name` (required) - Template to modify
- `agent` (required) - Agent name (must exist in agents.json)
- `input` (required) - Input path (supports `{enhancement_name}` and `{previous_step}` placeholders)
- `output` (required) - Required output filename
- `position` (optional) - Step position (0-indexed), default appends to end

**Examples**:
```bash
# Add first step
cmat workflow add-step my-workflow requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "analysis.md"

# Add second step (reads from previous)
cmat workflow add-step my-workflow architect \
    "{previous_step}/required_output/" \
    "design.md"

# Insert at specific position
cmat workflow add-step my-workflow security-reviewer \
    "{previous_step}/required_output/" \
    "security_review.md" \
    3
```

---

### workflow edit-step

Edit a step's input or output.

```bash
cmat workflow edit-step <template_name> <step_number> [input] [output]
```

**Parameters**:
- `template_name` (required) - Template to modify
- `step_number` (required) - Step number (0-indexed)
- `input` (optional) - New input path
- `output` (optional) - New output filename

---

### workflow remove-step

Remove a step from workflow.

```bash
cmat workflow remove-step <template_name> <step_number>
```

---

### workflow add-transition

Add a status transition to a step.

```bash
cmat workflow add-transition <template_name> <step_number> <status> <next_step> [auto_chain]
```

**Parameters**:
- `template_name` (required) - Template to modify
- `step_number` (required) - Step number (0-indexed)
- `status` (required) - Status code to match
- `next_step` (required) - Next agent name or `null` for workflow end
- `auto_chain` (optional) - Auto-chain: `true`|`false` (default: `true`)

**Examples**:
```bash
# Add success transition
cmat workflow add-transition my-workflow 0 READY_FOR_DEVELOPMENT architect true

# Add workflow end transition
cmat workflow add-transition my-workflow 2 TESTING_COMPLETE null false
```

---

### workflow remove-transition

Remove a status transition from a step.

```bash
cmat workflow remove-transition <template_name> <step_number> <status>
```

---

### workflow list-transitions

List all transitions for a step.

```bash
cmat workflow list-transitions <template_name> <step_number>
```

**Output**:
```
Transitions for step 0:
  READY_FOR_DEVELOPMENT → architect (auto_chain: true)
  BLOCKED:* → END (auto_chain: false)
```

---

### workflow validate

Validate a workflow template.

```bash
cmat workflow validate <template_name>
```

**Checks**:
- All agents exist in agents.json
- All steps have input and required_output defined
- All transition targets exist
- No circular dependencies

---

### workflow start

Start a workflow from the beginning.

```bash
cmat workflow start <workflow_name> <enhancement_name>
```

**Parameters**:
- `workflow_name` (required) - Template identifier
- `enhancement_name` (required) - Enhancement name (must have spec file)

**Examples**:
```bash
# Start standard feature workflow
cmat workflow start new_feature_development user-profiles

# Start custom workflow
cmat workflow start api-dev payment-endpoint
```

**Behavior**:
1. Validates workflow template
2. Verifies input file exists
3. Creates first task with workflow metadata
4. Sets `workflow_name` and `workflow_step: 0` in metadata
5. Auto-starts first task

---

### workflow validate-output

Validate agent output structure (used internally by hook).

```bash
cmat workflow validate-output <agent> <enhancement_dir> <required_output>
```

---

### workflow get-task-type

Get task type for an agent based on its role.

```bash
cmat workflow get-task-type <agent>
```

**Returns**: Task type (`analysis`, `technical_analysis`, `implementation`, `testing`, `documentation`, `integration`)

---

## Skills Commands

Skills management and prompt generation.

### skills list

Display all available skills.

```bash
cmat skills list
```

---

### skills get

Get skills assigned to a specific agent.

```bash
cmat skills get <agent-name>
```

**Returns**: JSON array of skill directories

---

### skills load

Load and display a skill's content.

```bash
cmat skills load <skill-directory>
```

---

### skills prompt

Build complete skills section for agent prompt.

```bash
cmat skills prompt <agent-name>
```

---

## Integration Commands

External system synchronization.

### integration add

Create integration task for external system sync.

```bash
cmat integration add <workflow_status> <source_file> <previous_agent> [parent_task_id]
```

---

### integration sync

Synchronize specific completed task to external systems.

```bash
cmat integration sync <task_id>
```

---

### integration sync-all

Synchronize all unsynced completed tasks.

```bash
cmat integration sync-all
```

---

## Agent Commands

Agent operations and configuration.

### agents list

List all available agents from agents.json.

```bash
cmat agents list
```

---

### agents generate-json

Generate agents.json from agent markdown frontmatter.

```bash
cmat agents generate-json
```

**When to Use**:
- After editing agent .md files
- After adding new agents
- After changing agent skills assignments

---

## Common Workflows

### Create and Start a Workflow

```bash
# 1. Create workflow template
cmat workflow create my-workflow "Custom development workflow"

# 2. Add steps
cmat workflow add-step my-workflow requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "analysis.md"

cmat workflow add-step my-workflow architect \
    "{previous_step}/required_output/" \
    "design.md"

cmat workflow add-step my-workflow implementer \
    "{previous_step}/required_output/" \
    "implementation.md"

# 3. Add transitions
cmat workflow add-transition my-workflow 0 READY_FOR_DEVELOPMENT architect true
cmat workflow add-transition my-workflow 1 READY_FOR_IMPLEMENTATION implementer true
cmat workflow add-transition my-workflow 2 READY_FOR_TESTING null false

# 4. Validate
cmat workflow validate my-workflow

# 5. Create enhancement spec
mkdir -p enhancements/my-feature
cat > enhancements/my-feature/my-feature.md << 'EOF'
# My Feature
## Description
Feature description here
EOF

# 6. Start workflow
cmat workflow start my-workflow my-feature
```

### Monitor Running Workflow

```bash
# Check status
cmat queue status

# View logs
tail -f enhancements/my-feature/logs/*.log

# Check completed tasks
cmat queue list completed | jq '.[-3:]'
```

---

## Environment Variables

### AUTO_INTEGRATE

Control automatic integration task creation.

**Values**:
- `always` - Always create integration tasks automatically
- `never` - Never create integration tasks
- `prompt` - Prompt user for each integration (default)

**Examples**:
```bash
export AUTO_INTEGRATE="never"   # Disable during testing
export AUTO_INTEGRATE="always"  # Full automation
```

---

## Exit Codes

All commands follow standard exit code conventions:

- `0` - Success
- `1` - Error (invalid arguments, task not found, validation failed, etc.)

---

## Output Structure (v5.0)

Agents now use standardized directory structure:

```
enhancements/{enhancement_name}/{agent}/
├── required_output/
│   └── {workflow-specified-filename}
└── optional_output/
    └── [any additional files]
```

**Key Changes**:
- Workflows specify the required output filename
- Agents write to `required_output/` and `optional_output/` directories
- No hardcoded filenames in agent definitions

---

## Quick Tips

1. **Always run from project root** (directory containing `.claude/`)
2. **Use workflows** (`cmat workflow start`) for structured development
3. **Validate templates** before using them
4. **Check logs** in `enhancements/*/logs/` when debugging
5. **Use `watch`** to monitor long-running workflows
6. **Set AUTO_INTEGRATE** to avoid repeated prompts

---

## Further Reading

- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow patterns and best practices
- **[WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md)** - Template management
- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Skills system documentation
- **[INSTALLATION.md](INSTALLATION.md)** - Setup and installation

---