# Scripts Reference Guide

Complete reference for all `cmat.sh` commands in the Claude Multi-Agent Template v3.0.

## Command Structure

```bash
cmat.sh <category> <command> [options]
```

**Categories**:
- `queue` - Task queue management
- `workflow` - Workflow orchestration
- `skills` - Skills management
- `integration` - External system integration
- `agents` - Agent operations
- `version` - Show version information
- `help` - Show help message

## Quick Reference

```bash
# Common operations
cmat.sh queue status                    # View queue status
cmat.sh queue add "..." "..." ...       # Add task
cmat.sh queue start <task_id>           # Start task
cmat.sh skills list                     # List all skills
cmat.sh workflow validate ...           # Validate outputs
cmat.sh integration sync <task_id>      # Sync to external systems
cmat.sh version                         # Show version info
```

---

## Queue Commands

Task lifecycle management operations.

### queue add

Add a new task to the pending queue.

```bash
cmat.sh queue add <title> <agent> <priority> <type> <source> <description> [auto_complete] [auto_chain]
```

**Parameters**:
- `title` (required) - Short descriptive title for the task
- `agent` (required) - Agent name (must exist in agents.json)
- `priority` (required) - Task priority: `critical`, `high`, `normal`, `low`
- `type` (required) - Task type: `analysis`, `technical_analysis`, `implementation`, `testing`, `documentation`, `integration`
- `source` (required) - Path to source file (e.g., `enhancements/feature/feature.md`)
- `description` (required) - Detailed task description
- `auto_complete` (optional) - Auto-complete without prompt: `true`|`false` (default: `false`)
- `auto_chain` (optional) - Auto-chain to next agent: `true`|`false` (default: `false`)

**Returns**: Task ID (e.g., `task_1234567890_12345`)

**Examples**:
```bash
# Manual task (prompts for everything)
TASK_ID=$(cmat.sh queue add \
  "Analyze feature requirements" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/my-feature/my-feature.md" \
  "Initial requirements analysis" \
  false \
  false)

# Semi-automated (auto-complete but manual chain)
TASK_ID=$(cmat.sh queue add \
  "Design architecture" \
  "architect" \
  "high" \
  "technical_analysis" \
  "enhancements/my-feature/requirements-analyst/analysis_summary.md" \
  "Create technical design" \
  true \
  false)

# Fully automated (runs entire workflow hands-off)
TASK_ID=$(cmat.sh queue add \
  "Full workflow" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/my-feature/my-feature.md" \
  "Complete feature development" \
  true \
  true)
```

**Automation Levels**:
- `false, false` - Manual: Prompts to complete, prompts to chain
- `true, false` - Semi-auto: Auto-completes, prompts to chain
- `true, true` - Full-auto: Auto-completes and auto-chains through entire workflow

---

### queue start

Move task from pending to active and invoke the agent.

```bash
cmat.sh queue start <task_id>
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

**Examples**:
```bash
# Start a task
cmat.sh queue start task_1234567890_12345

# The agent will:
# - Read role definition from .claude/agents/{agent}.md
# - Receive assigned skills automatically
# - Process source file
# - Create outputs in enhancements/{name}/{agent}/
# - Return completion status
```

**Output**: Agent execution log and status

---

### queue complete

Mark active task as completed.

```bash
cmat.sh queue complete <task_id> [result] [--auto-chain]
```

**Parameters**:
- `task_id` (required) - Task ID to complete
- `result` (optional) - Result message or status code (default: "completed successfully")
- `--auto-chain` or `true` (optional) - Automatically chain to next agent if applicable

**Status Codes** (common):
- `READY_FOR_DEVELOPMENT` - Requirements complete, ready for architecture
- `READY_FOR_IMPLEMENTATION` - Architecture complete, ready for coding
- `READY_FOR_TESTING` - Implementation complete, ready for testing
- `TESTING_COMPLETE` - Tests complete, ready for documentation
- `DOCUMENTATION_COMPLETE` - Documentation complete, workflow finished
- `INTEGRATION_COMPLETE` - Integration task complete
- `BLOCKED: <reason>` - Task blocked, cannot proceed

**Examples**:
```bash
# Complete with default status
cmat.sh queue complete task_1234567890_12345

# Complete with custom status
cmat.sh queue complete task_1234567890_12345 "READY_FOR_DEVELOPMENT"

# Complete and auto-chain to next agent
cmat.sh queue complete task_1234567890_12345 "READY_FOR_DEVELOPMENT" --auto-chain

# Complete with blocking reason
cmat.sh queue complete task_1234567890_12345 "BLOCKED: Missing database schema"
```

**Auto-chaining**: When `--auto-chain` is used, the system will:
1. Validate current agent outputs
2. Determine next agent from contract
3. Build source path for next agent
4. Create and start next task automatically

---

### queue cancel

Cancel a pending or active task.

```bash
cmat.sh queue cancel <task_id> [reason]
```

**Parameters**:
- `task_id` (required) - Task ID to cancel
- `reason` (optional) - Cancellation reason (default: "task cancelled")

**Examples**:
```bash
# Cancel with default reason
cmat.sh queue cancel task_1234567890_12345

# Cancel with specific reason
cmat.sh queue cancel task_1234567890_12345 "Requirements changed"
```

**Behavior**:
- Removes task from queue (pending or active)
- Sets agent to idle (if active)
- Logs cancellation reason

---

### queue cancel-all

Cancel all pending and active tasks.

```bash
cmat.sh queue cancel-all [reason]
```

**Parameters**:
- `reason` (optional) - Cancellation reason (default: "bulk cancellation")

**Examples**:
```bash
# Cancel all tasks
cmat.sh queue cancel-all

# Cancel with reason
cmat.sh queue cancel-all "Project scope changed"
```

**Use Cases**:
- Reset queue when priorities change
- Clear queue before major refactoring
- Emergency stop of all workflows

---

### queue fail

Mark active task as failed.

```bash
cmat.sh queue fail <task_id> [error]
```

**Parameters**:
- `task_id` (required) - Task ID to fail
- `error` (optional) - Error message (default: "task failed")

**Examples**:
```bash
# Fail with default error
cmat.sh queue fail task_1234567890_12345

# Fail with specific error
cmat.sh queue fail task_1234567890_12345 "Agent execution timeout"
```

**Behavior**:
- Moves task to `failed_tasks`
- Sets agent to idle
- Logs error message

---

### queue status

Display current queue status and agent states.

```bash
cmat.sh queue status
```

**Output**:
```
=== Multi-Agent Queue Status ===

📋 Agent Status:
  • requirements-analyst: idle (Last: 2025-10-24T14:30:00Z)
  • architect: active (Last: 2025-10-24T14:45:00Z)
  • implementer: idle (Last: never)
  • tester: idle (Last: never)
  • documenter: idle (Last: never)

⏳ Pending Tasks:
  • [high] Implement feature X → implementer (ID: task_123...)
  • [normal] Document feature Y → documenter (ID: task_456...)

🔄 Active Workflows:
  • Design architecture for X → architect (Started: 2025-10-24T14:45:00Z, ID: task_789...)

🔗 Integration Tasks:
  • Sync with GitHub (Status: pending, ID: task_012...)

✅ Recently Completed:
  • Analyze requirements → requirements-analyst (2025-10-24T14:30:00Z)
  • Test feature Y → tester (2025-10-24T13:15:00Z)
```

**Use Cases**:
- Monitor workflow progress
- Check agent availability
- Review recent completions
- Identify bottlenecks

---

### queue list

List tasks from a specific queue.

```bash
cmat.sh queue list <queue_type> [format]
```

**Parameters**:
- `queue_type` (required) - Queue to list: `pending`, `active`, `completed`, `failed`, `all`
- `format` (optional) - Output format: `json` (default), `compact`

**Examples**:
```bash
# List pending tasks (full JSON)
cmat.sh queue list pending

# List active tasks (compact)
cmat.sh queue list active compact

# List all completed tasks
cmat.sh queue list completed

# List all queues
cmat.sh queue list all
```

**Output Formats**:

**JSON** (default):
```json
[
  {
    "id": "task_1234567890_12345",
    "title": "Analyze requirements",
    "assigned_agent": "requirements-analyst",
    "priority": "high",
    "task_type": "analysis",
    "status": "pending",
    "created": "2025-10-24T14:00:00Z",
    "started": null,
    "completed": null,
    "runtime_seconds": null,
    "metadata": {...}
  }
]
```

**Compact**:
```
task_1234567890_12345|Analyze requirements|requirements-analyst|high|pending
task_1234567890_12346|Design architecture|architect|high|active
```

---

### queue metadata

Update task metadata field.

```bash
cmat.sh queue metadata <task_id> <key> <value>
```

**Parameters**:
- `task_id` (required) - Task ID to update
- `key` (required) - Metadata field name
- `value` (required) - New value for field

**Common Metadata Fields**:
- `github_issue` - GitHub issue number
- `github_pr` - GitHub PR number
- `jira_ticket` - Jira ticket key
- `confluence_page` - Confluence page ID
- `parent_task_id` - Parent task reference
- `workflow_status` - Current workflow state

**Examples**:
```bash
# Link to GitHub issue
cmat.sh queue metadata task_123 github_issue "145"

# Add Jira ticket
cmat.sh queue metadata task_123 jira_ticket "PROJ-456"

# Link to parent task
cmat.sh queue metadata task_456 parent_task_id "task_123"
```

---

## Workflow Commands

Workflow orchestration and contract validation.

### workflow validate

Validate agent outputs against contract requirements.

```bash
cmat.sh workflow validate <agent> <enhancement_dir>
```

**Parameters**:
- `agent` (required) - Agent name to validate
- `enhancement_dir` (required) - Path to enhancement directory

**Validation Checks**:
1. ✅ Root document exists (from contract)
2. ✅ Output directory exists
3. ✅ Additional required files present
4. ✅ Metadata header present (if required)
5. ✅ All required metadata fields exist

**Examples**:
```bash
# Validate requirements analyst output
cmat.sh workflow validate requirements-analyst enhancements/my-feature

# Output:
# ✅ Required root document: enhancements/my-feature/requirements-analyst/analysis_summary.md
# ✅ Metadata header present
# ✅ Required fields: enhancement, agent, task_id, timestamp, status
# ✅ Output validation passed

# Validate architect output
cmat.sh workflow validate architect enhancements/my-feature
```

**Exit Codes**:
- `0` - Validation passed
- `1` - Validation failed (missing files or invalid metadata)

---

### workflow next-agent

Determine next agent based on current agent and status.

```bash
cmat.sh workflow next-agent <agent> <status>
```

**Parameters**:
- `agent` (required) - Current agent name
- `status` (required) - Completion status code

**Returns**: Next agent name or "UNKNOWN"

**Examples**:
```bash
# After requirements analyst completes
cmat.sh workflow next-agent requirements-analyst READY_FOR_DEVELOPMENT
# Output: architect

# After architect completes
cmat.sh workflow next-agent architect READY_FOR_IMPLEMENTATION
# Output: implementer

# After implementer completes
cmat.sh workflow next-agent implementer READY_FOR_TESTING
# Output: tester

# Blocked status
cmat.sh workflow next-agent architect "BLOCKED: Missing API specification"
# Output: UNKNOWN
```

**Uses**: Contract-based workflow chaining

---

### workflow next-source

Build source file path for next agent.

```bash
cmat.sh workflow next-source <enhancement> <next_agent> <current_agent>
```

**Parameters**:
- `enhancement` (required) - Enhancement name
- `next_agent` (required) - Next agent in workflow
- `current_agent` (required) - Current agent

**Returns**: Source file path for next agent

**Examples**:
```bash
# Build path for architect (after requirements-analyst)
cmat.sh workflow next-source my-feature architect requirements-analyst
# Output: enhancements/my-feature/requirements-analyst/analysis_summary.md

# Build path for implementer (after architect)
cmat.sh workflow next-source my-feature implementer architect
# Output: enhancements/my-feature/architect/implementation_plan.md
```

**Uses**: Automatic source path construction for chaining

---

### workflow auto-chain

Automatically create and start next workflow task.

```bash
cmat.sh workflow auto-chain <task_id> <status>
```

**Parameters**:
- `task_id` (required) - Completed task ID
- `status` (required) - Completion status

**Process**:
1. Validates current agent outputs
2. Determines next agent from contract
3. Builds source path for next agent
4. Creates next task with inherited automation
5. Auto-starts next task

**Examples**:
```bash
# Chain after requirements analyst
cmat.sh workflow auto-chain task_123 READY_FOR_DEVELOPMENT

# Output:
# 🔍 Validating outputs from requirements-analyst...
# ✅ Output validation passed
# 📋 Next agent: architect
# ✅ Auto-chained to architect: task_124
#    Source: enhancements/feature/requirements-analyst/analysis_summary.md
#    Inherited automation: auto_complete=true, auto_chain=true
# 🚀 Auto-starting next task...
```

**Automation**: Next task inherits `auto_complete` and `auto_chain` flags from parent

---

### workflow template

Execute predefined workflow template.

```bash
cmat.sh workflow template <template_name> [description]
```

**Parameters**:
- `template_name` (required) - Template name from workflow_templates.json
- `description` (optional) - Task description (default: "Workflow execution")

**Built-in Templates**:
- `standard_feature` - Full feature development workflow
- `bug_fix` - Bug fix workflow (skip documentation)
- `documentation_only` - Documentation update workflow

**Examples**:
```bash
# Run standard feature workflow
cmat.sh workflow template standard_feature "Implement user authentication"

# Run bug fix workflow
cmat.sh workflow template bug_fix "Fix login validation"
```

**Custom Templates**: Add to `.claude/queues/workflow_templates.json`

---

## Skills Commands

Skills management and prompt generation.

### skills list

Display all available skills.

```bash
cmat.sh skills list
```

**Output**: Complete skills.json content with all 14+ skills

**Example Output**:
```json
{
  "version": "1.0.0",
  "skills": [
    {
      "name": "Requirements Elicitation",
      "skill-directory": "requirements-elicitation",
      "category": "analysis",
      "required_tools": ["Read", "Write", "Grep"],
      "description": "Extract and clarify requirements..."
    },
    ...
  ]
}
```

---

### skills get

Get skills assigned to a specific agent.

```bash
cmat.sh skills get <agent-name>
```

**Parameters**:
- `agent-name` (required) - Agent name (e.g., "requirements-analyst")

**Returns**: JSON array of skill directories

**Examples**:
```bash
# Get requirements analyst skills
cmat.sh skills get requirements-analyst
# Output: ["requirements-elicitation", "user-story-writing", "bug-triage"]

# Get architect skills
cmat.sh skills get architect
# Output: ["api-design", "architecture-patterns", "desktop-ui-design", "web-ui-design"]

# Get implementer skills
cmat.sh skills get implementer
# Output: ["error-handling", "code-refactoring", "sql-development"]
```

---

### skills load

Load and display a skill's content.

```bash
cmat.sh skills load <skill-directory>
```

**Parameters**:
- `skill-directory` (required) - Skill directory name

**Returns**: Skill SKILL.md content (without frontmatter)

**Examples**:
```bash
# Load requirements elicitation skill
cmat.sh skills load requirements-elicitation

# Load API design skill
cmat.sh skills load api-design

# Load test patterns skill
cmat.sh skills load test-design-patterns
```

**Output**: Complete skill definition including:
- Purpose
- When to Use
- Key Capabilities
- Approach
- Examples
- Best Practices

---

### skills prompt

Build complete skills section for agent prompt.

```bash
cmat.sh skills prompt <agent-name>
```

**Parameters**:
- `agent-name` (required) - Agent name

**Returns**: Complete skills section ready for prompt injection

**Example**:
```bash
# Build skills section for requirements analyst
cmat.sh skills prompt requirements-analyst

# Output:
################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

You have access to the following specialized skills...

---

# Requirements Elicitation
[Complete skill content...]

---

# User Story Writing
[Complete skill content...]

---

# Bug Triage
[Complete skill content...]

---

**Using Skills**: Apply the above skills as appropriate...
```

**Uses**: Automatically injected into agent prompts during task execution

---

### skills test

Test all skills system functions.

```bash
cmat.sh skills test
```

**Tests**:
1. Lists all skills from skills.json
2. Gets skills for requirements-analyst
3. Loads sample skill
4. Builds prompt section for requirements-analyst

**Output**: Test results showing system functionality

---

## Integration Commands

External system synchronization.

### integration add

Create integration task for external system sync.

```bash
cmat.sh integration add <workflow_status> <source_file> <previous_agent> [parent_task_id]
```

**Parameters**:
- `workflow_status` (required) - Status that triggered integration
- `source_file` (required) - Source file to sync
- `previous_agent` (required) - Agent that created the status
- `parent_task_id` (optional) - Parent task reference

**Trigger Statuses**:
- `READY_FOR_DEVELOPMENT` → Create GitHub issue, Jira ticket
- `READY_FOR_IMPLEMENTATION` → Update status, add labels
- `READY_FOR_TESTING` → Create pull request
- `TESTING_COMPLETE` → Post test results
- `DOCUMENTATION_COMPLETE` → Close issue, publish docs

**Examples**:
```bash
# Create integration after requirements
cmat.sh integration add \
  "READY_FOR_DEVELOPMENT" \
  "enhancements/feature/requirements-analyst/analysis_summary.md" \
  "requirements-analyst" \
  "task_123"

# Create integration after testing
cmat.sh integration add \
  "TESTING_COMPLETE" \
  "enhancements/feature/tester/test_summary.md" \
  "tester" \
  "task_456"
```

**Note**: Integration tasks are created automatically by the hook system when enabled

---

### integration sync

Synchronize specific completed task to external systems.

```bash
cmat.sh integration sync <task_id>
```

**Parameters**:
- `task_id` (required) - Completed task ID to sync

**Process**:
1. Retrieves task details
2. Creates integration task
3. Syncs to GitHub (if configured)
4. Syncs to Jira/Confluence (if configured)

**Examples**:
```bash
# Sync specific task
cmat.sh integration sync task_1234567890_12345

# Output:
# 🔗 Creating integration task for: task_1234567890_12345
# ✅ Integration task created: task_1234567890_67890
```

---

### integration sync-all

Synchronize all unsynced completed tasks.

```bash
cmat.sh integration sync-all
```

**Process**:
1. Scans completed tasks
2. Identifies tasks needing integration
3. Creates integration tasks for each

**Examples**:
```bash
# Sync all unsynced tasks
cmat.sh integration sync-all

# Output:
# 🔍 Scanning for tasks requiring integration...
# 🔗 Creating integration for task_123 (READY_FOR_DEVELOPMENT)
# 🔗 Creating integration for task_456 (TESTING_COMPLETE)
# ✅ Created 2 integration tasks
```

**Use Cases**:
- Bulk sync after system setup
- Catch up on missed integrations
- Manual trigger when auto-integration disabled

---

## Agent Commands

Agent operations and configuration.

### agents list

List all available agents from agents.json.

```bash
cmat.sh agents list
```

**Output**: Complete agents.json content

**Example Output**:
```json
{
  "agents": [
    {
      "name": "Requirements Analyst",
      "agent-file": "requirements-analyst",
      "tools": ["Read", "Write", "Glob", "Grep", "WebSearch", "WebFetch"],
      "skills": ["requirements-elicitation", "user-story-writing", "bug-triage"],
      "description": "Analyzes project requirements..."
    },
    ...
  ]
}
```

---

### agents generate-json

Generate agents.json from agent markdown frontmatter.

```bash
cmat.sh agents generate-json
```

**Process**:
1. Scans all `.claude/agents/*.md` files
2. Extracts YAML frontmatter
3. Generates `.claude/agents/agents.json`

**Examples**:
```bash
# Regenerate after modifying agent files
cmat.sh agents generate-json

# Output:
# ✓ Generated .claude/agents/agents.json
```

**When to Use**:
- After editing agent .md files
- After adding new agents
- After changing agent skills assignments
- To sync agents.json with source files

---

## Utility Commands

### version

Show version and system information.

```bash
cmat.sh version
```

**Output**:
```
cmat v3.0.0
Claude Multi-Agent Template System

Dependencies:
  ✓ jq v1.7.1
  ✓ claude v0.8.5
  ✓ bash v5.2.26
  ○ git v2.43.0 (optional)

Environment:
  Project Root: /path/to/project
  Queue File: .claude/queues/task_queue.json
  Contracts: .claude/AGENT_CONTRACTS.json
  Skills: .claude/skills/skills.json
  Tasks: 2 pending, 1 active, 15 completed
  Agents: 7 defined
  Skills: 14 available
```

---

### help

Show help message with command overview.

```bash
cmat.sh help
```

**Output**: Command categories, common examples, and documentation links

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
# Disable integration prompts
export AUTO_INTEGRATE="never"
cmat.sh queue start task_123

# Always integrate automatically
export AUTO_INTEGRATE="always"
cmat.sh queue start task_456

# Prompt for each (default)
export AUTO_INTEGRATE="prompt"
cmat.sh queue start task_789
```

---

## Exit Codes

All commands follow standard exit code conventions:

- `0` - Success
- `1` - Error (invalid arguments, task not found, validation failed, etc.)

**Examples**:
```bash
# Check exit code
cmat.sh queue start task_123
if [ $? -eq 0 ]; then
    echo "Task started successfully"
else
    echo "Task start failed"
fi

# Use in conditional
if cmat.sh workflow validate architect enhancements/feature; then
    echo "Validation passed"
fi
```

---

## Common Workflows

### Manual Single-Agent Task
```bash
# 1. Create manual task
TASK_ID=$(cmat.sh queue add \
  "Analyze requirements" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/feature/feature.md" \
  "Initial analysis" \
  false \
  false)

# 2. Start task
cmat.sh queue start $TASK_ID

# 3. Monitor
cmat.sh queue status

# 4. Manual completion (prompted)
# Agent completes, you approve status, decide whether to chain
```

### Fully Automated Workflow
```bash
# 1. Create fully automated task
TASK_ID=$(cmat.sh queue add \
  "Complete feature" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/feature/feature.md" \
  "Full workflow" \
  true \
  true)

# 2. Start and let it run
cmat.sh queue start $TASK_ID

# 3. Monitor progress
watch -n 5 'cmat.sh queue status'

# System automatically:
# - Completes each agent
# - Validates outputs
# - Chains to next agent
# - Repeats until workflow done
```

### Integration Sync
```bash
# Enable integration
export AUTO_INTEGRATE="always"

# Create task (integration auto-triggered)
TASK_ID=$(cmat.sh queue add ...)
cmat.sh queue start $TASK_ID

# Or manually sync after
cmat.sh integration sync $TASK_ID
```

### Skills Exploration
```bash
# List all skills
cmat.sh skills list

# Check agent skills
cmat.sh skills get architect

# Read a skill
cmat.sh skills load api-design

# See what gets injected
cmat.sh skills prompt architect | less
```

### Validation and Debugging
```bash
# Validate outputs before chaining
cmat.sh workflow validate architect enhancements/feature

# Check what next agent would be
cmat.sh workflow next-agent architect READY_FOR_IMPLEMENTATION

# Check source path
cmat.sh workflow next-source feature implementer architect

# View logs
tail -f enhancements/feature/logs/architect_*.log
```

---

## Troubleshooting

### "Command not found: cmat.sh"
Use full path from project root: `.claude/scripts/cmat.sh`

### "jq: command not found"
Install jq: `brew install jq` (macOS) or `apt-get install jq` (Linux)

### "Queue file not found"
Initialize: `cmat.sh queue status`

### "Agent not found in contracts"
Verify: `jq '.agents | keys' .claude/AGENT_CONTRACTS.json`

### "Skills not loading"
Check: `cmat.sh skills test`

### "Validation failing"
Debug: `cmat.sh workflow validate <agent> <enhancement>`

### "Auto-chain not working"
Check task flags: `cmat.sh queue list active | jq '.[] | {id, auto_chain}'`

---

## Quick Tips

1. **Always run from project root** (directory containing `.claude/`)
2. **Use full automation** (`true true`) for standard workflows
3. **Validate outputs** before manual chaining
4. **Check logs** in `enhancements/*/logs/` when debugging
5. **Use `watch`** to monitor long-running workflows
6. **Set AUTO_INTEGRATE** to avoid repeated prompts
7. **Test skills** with `cmat.sh skills test`

---

## Further Reading

- **[INSTALLATION.md](INSTALLATION.md)** - Setup and installation
- **[.claude/WORKFLOW_GUIDE.md](.claude/WORKFLOW_GUIDE.md)** - Workflow patterns
- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Skills system documentation
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Adapting to your project
- **[.claude/AGENT_CONTRACTS.json](.claude/AGENT_CONTRACTS.json)** - Agent specifications

---

**Version**: 3.0.0  
**Last Updated**: 2025-10-24