# Workflow Patterns Guide

This guide describes common workflow patterns in the multi-agent system. All patterns are driven by the agent contracts defined in `AGENT_CONTRACTS.json`.

**Version**: 3.0.0 - Updated for modular cmat.sh command structure and skills system

## Table of Contents

- [Command Reference](#command-reference)
- [Standard Workflows](#standard-workflows)
- [Workflow States and Transitions](#workflow-states-and-transitions)
- [Skills System](#skills-system)
- [Branching Workflows](#branching-workflows)
- [Handling Special Cases](#handling-special-cases)
- [Integration with External Systems](#integration-with-external-systems)
- [Best Practices](#best-practices)
- [Customizing Workflows](#customizing-workflows)
- [Troubleshooting Workflows](#troubleshooting-workflows)

---

## Command Reference

The queue system manages tasks and orchestrates workflow transitions using the `cmat.sh` command.

### Basic Task Management
```bash
# Check queue status
cmat.sh queue status

# Add a task
cmat.sh queue add \
  "Task title" \
  "agent-name" \
  "priority" \
  "task_type" \
  "source_file" \
  "description" \
  auto_complete \
  auto_chain

# Start a task
cmat.sh queue start <task_id>

# Complete a task (basic)
cmat.sh queue complete <task_id> "completion_message"

# Complete a task with auto-chain
cmat.sh queue complete <task_id> "READY_FOR_DEVELOPMENT" --auto-chain

# Cancel a task
cmat.sh queue cancel <task_id> "cancellation_reason"

# Cancel all tasks
cmat.sh queue cancel-all "reason"

# Fail a task
cmat.sh queue fail <task_id> "error_message"

# Update task metadata
cmat.sh queue metadata <task_id> <key> <value>
```

### Contract-Based Commands
```bash
# Validate agent outputs against contract
cmat.sh workflow validate \
  "requirements-analyst" \
  "enhancements/feature"

# Determine next agent from contract
cmat.sh workflow next-agent \
  "requirements-analyst" \
  "READY_FOR_DEVELOPMENT"

# Build next source path
cmat.sh workflow next-source \
  "feature-name" \
  "architect" \
  "requirements-analyst"

# Auto-chain with validation
cmat.sh workflow auto-chain \
  <task_id> \
  "READY_FOR_DEVELOPMENT"
```

### List and Query Tasks
```bash
# List tasks by queue
cmat.sh queue list pending
cmat.sh queue list active
cmat.sh queue list completed
cmat.sh queue list failed
cmat.sh queue list all

# Compact format (one task per line)
cmat.sh queue list completed compact

# Check version
cmat.sh version
```

### Skills Commands
```bash
# List all available skills
cmat.sh skills list

# Get skills for specific agent
cmat.sh skills get requirements-analyst

# Load skill content
cmat.sh skills load requirements-elicitation

# Preview skills prompt for agent
cmat.sh skills prompt architect

# Test skills system
cmat.sh skills test
```

### Integration Commands
```bash
# Sync specific task to external systems
cmat.sh integration sync <task_id>

# Sync all unsynced completed tasks
cmat.sh integration sync-all

# Add integration task manually
cmat.sh integration add \
  "READY_FOR_DEVELOPMENT" \
  "enhancements/feature/requirements-analyst/analysis_summary.md" \
  "requirements-analyst" \
  "parent_task_id"
```

### Workflow Templates
```bash
# Start predefined workflow
cmat.sh workflow template sequential_development "Feature description"
cmat.sh workflow template bug_fix "Bug description"
cmat.sh workflow template hotfix_flow "Hotfix description"
cmat.sh workflow template refactoring "Refactoring description"
```

### Agent Commands
```bash
# List all agents
cmat.sh agents list

# Regenerate agents.json from .md files
cmat.sh agents generate-json
```

---

## Task Priorities

Control task execution order with priorities:

- **critical**: Emergency fixes, blocking issues (highest priority)
- **high**: Important features, significant bugs
- **normal**: Regular development tasks (default)
- **low**: Nice-to-have improvements, documentation updates

Tasks with higher priority are suggested first when selecting what to work on next.

---

## Automation Flags

### auto_complete Flag

Controls whether task completion requires confirmation:

- `false` - Prompt: "Proceed? [Y/n]" before marking complete
- `true` - Auto-complete without prompting

### auto_chain Flag

Controls whether next task is created and started automatically:

- `false` - Stop after completion
- `true` - Auto-create next task, inherit settings, and auto-start it

### Automation Matrix

| auto_complete | auto_chain | Behavior |
|---------------|------------|----------|
| `false` | `false` | **Manual**: Prompts for everything |
| `true` | `false` | **Auto-complete**: Completes without prompt, stops |
| `false` | `true` | **Auto-chain**: Prompts to complete, then auto-chains |
| `true` | `true` | **Fully Automated**: Zero prompts, runs entire workflow |

### Settings Inheritance

When `auto_chain=true`, the created task inherits parent's automation settings:
```
Parent Task: auto_complete=true, auto_chain=true
    ↓ [completes]
    ↓ [validates]
    ↓ [creates next task]
Child Task: auto_complete=true, auto_chain=true  ← Inherited
    ↓ [auto-starts]
    ↓ [completes]
    ↓ [validates]
    ↓ [creates next task]
Grandchild Task: auto_complete=true, auto_chain=true  ← Inherited
    ... workflow continues automatically
```

---

## Skills System

### Overview

The skills system provides specialized domain knowledge to agents. Skills are automatically injected into agent prompts based on agent configuration.

### Built-in Skills

**Analysis Skills** (3):
- **requirements-elicitation**: Extract and clarify requirements
- **user-story-writing**: Create user stories with acceptance criteria
- **bug-triage**: Reproduce, diagnose, and plan bug fixes

**Architecture Skills** (2):
- **api-design**: Design RESTful APIs
- **architecture-patterns**: Apply proven architectural patterns

**Implementation Skills** (2):
- **error-handling**: Implement robust error handling
- **code-refactoring**: Improve code structure

**Testing Skills** (2):
- **test-design-patterns**: Apply testing patterns (AAA, mocking, etc.)
- **test-coverage**: Analyze and improve test coverage

**Documentation Skills** (2):
- **technical-writing**: Write clear technical documentation
- **api-documentation**: Document APIs comprehensively

**UI Design Skills** (2):
- **desktop-ui-design**: Design desktop interfaces
- **web-ui-design**: Design responsive web interfaces

**Database Skills** (1):
- **sql-development**: Design schemas and optimize queries

### Skill Assignment

Skills are assigned in agent frontmatter:
```yaml
---
name: "Requirements Analyst"
tools: ["Read", "Write", "Glob", "Grep"]
skills: ["requirements-elicitation", "user-story-writing", "bug-triage"]
---
```

**Current assignments:**
- **requirements-analyst**: requirements-elicitation, user-story-writing, bug-triage
- **architect**: api-design, architecture-patterns, desktop-ui-design, web-ui-design
- **implementer**: error-handling, code-refactoring, sql-development
- **tester**: test-design-patterns, test-coverage, bug-triage
- **documenter**: technical-writing, api-documentation

### Managing Skills
```bash
# View all skills
cmat.sh skills list

# See agent's skills
cmat.sh skills get architect

# View skill content
cmat.sh skills load api-design

# Preview full skills section for agent
cmat.sh skills prompt requirements-analyst
```

### Adding Custom Skills

See [SKILLS_GUIDE.md](SKILLS_GUIDE.md) for complete documentation.

Quick steps:
1. Create skill directory: `.claude/skills/my-skill/`
2. Create `SKILL.md` using [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md)
3. Add to `skills.json` registry
4. Assign to agents in their frontmatter
5. Regenerate: `cmat.sh agents generate-json`

---

## Logging and Monitoring

### Agent Logs

Each agent execution creates a detailed log:

**Location**: `enhancements/{enhancement}/logs/{agent}_{task_id}_{timestamp}.log`

**Contents**:
- Agent execution start time
- Task details (ID, source file, enhancement)
- Skills injected into prompt
- Complete agent output
- Skill usage documentation
- Execution duration
- Exit code and status

**Example**:
```bash
# View most recent log
ls -t enhancements/demo-test/logs/*.log | head -1 | xargs cat

# Follow log in real-time
tail -f enhancements/demo-test/logs/architect_*.log

# Check if skills were applied
grep "Skills Applied" enhancements/demo-test/*/analysis_summary.md
grep "Skills Applied" enhancements/demo-test/*/implementation_plan.md
```

### Queue Operations Log

System-level operations logged to:

**Location**: `.claude/logs/queue_operations.log`

**Contents**:
- Task additions, starts, completions
- Agent status updates
- Metadata updates
- Workflow transitions

**Example**:
```bash
tail -f .claude/logs/queue_operations.log

# Sample output:
# [2025-10-24T14:30:00Z] TASK_ADDED: ID: task_123, Agent: requirements-analyst, Title: Demo test
# [2025-10-24T14:30:05Z] TASK_STARTED: ID: task_123, Agent: requirements-analyst
# [2025-10-24T14:35:00Z] TASK_COMPLETED: ID: task_123, Agent: requirements-analyst, Result: READY_FOR_DEVELOPMENT
```

### Monitoring Workflows
```bash
# Check overall queue status
cmat.sh queue status

# See recently completed tasks
jq '.completed_tasks[-5:]' .claude/queues/task_queue.json

# Check for failed tasks
jq '.failed_tasks' .claude/queues/task_queue.json

# Monitor active tasks
watch -n 5 'cmat.sh queue status'
```

---

## Standard Workflows

### Complete Feature Development

**Flow**: Requirements → Architecture → Implementation → Testing → Documentation

**Agents**:
1. **requirements-analyst** (skills: requirements-elicitation, user-story-writing) → `READY_FOR_DEVELOPMENT`
2. **architect** (skills: api-design, architecture-patterns) → `READY_FOR_IMPLEMENTATION`
3. **implementer** (skills: error-handling, code-refactoring) → `READY_FOR_TESTING`
4. **tester** (skills: test-design-patterns, test-coverage) → `TESTING_COMPLETE`
5. **documenter** (skills: technical-writing, api-documentation) → `DOCUMENTATION_COMPLETE`

**When to Use**: New features, major enhancements, user-facing changes

**Duration**: Typically 6-12 hours total across all phases

**Example**: Adding a new API endpoint with documentation

**Command**:
```bash
cmat.sh queue add \
  "Add new API endpoint" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/add-endpoint/add-endpoint.md" \
  "Analyze requirements for new API endpoint" \
  true \
  true
```

---

### Bug Fix Workflow

**Flow**: Requirements → Architecture → Implementation → Testing

**Agents**:
1. **requirements-analyst** (includes bug-triage skill) → `READY_FOR_DEVELOPMENT`
2. **architect** → `READY_FOR_IMPLEMENTATION`
3. **implementer** → `READY_FOR_TESTING`
4. **tester** (includes bug-triage skill) → `TESTING_COMPLETE`

**When to Use**: Bug fixes requiring analysis and design

**Duration**: Typically 2-4 hours total

**Note**: Documentation phase usually skipped for bug fixes unless API changes

**Example**: Fixing a calculation error requiring business logic understanding

---

### Hotfix Workflow

**Flow**: Implementation → Testing

**Agents**:
1. **implementer** → `READY_FOR_TESTING`
2. **tester** → `TESTING_COMPLETE`

**When to Use**: Critical bugs, emergency fixes, production incidents

**Duration**: 1-2 hours total

**Note**: Requirements and architecture skipped for speed

**Example**: Fixing a typo causing a crash

---

### Refactoring Workflow

**Flow**: Architecture → Implementation → Testing → Documentation

**Agents**:
1. **architect** (includes architecture-patterns, code-refactoring via cross-reference) → `READY_FOR_IMPLEMENTATION`
2. **implementer** (includes code-refactoring skill) → `READY_FOR_TESTING`
3. **tester** → `TESTING_COMPLETE`
4. **documenter** → `DOCUMENTATION_COMPLETE`

**When to Use**: Code refactoring, technical debt reduction

**Duration**: 4-8 hours total

**Note**: Requirements analysis skipped since functionality doesn't change

---

## Workflow States and Transitions

Each status code triggers a specific next agent according to agent contracts:

| Current Status | Next Agent | Skills Applied |
|----------------|------------|----------------|
| `READY_FOR_DEVELOPMENT` | architect | API Design, Architecture Patterns |
| `READY_FOR_IMPLEMENTATION` | implementer | Error Handling, Code Refactoring |
| `READY_FOR_TESTING` | tester | Test Design Patterns, Test Coverage |
| `READY_FOR_INTEGRATION` | tester | Test Design Patterns, Test Coverage |
| `TESTING_COMPLETE` | documenter | Technical Writing, API Documentation |
| `DOCUMENTATION_COMPLETE` | none | (workflow complete) |
| `BLOCKED: <reason>` | none | (manual intervention required) |

**State Machine**: See `WORKFLOW_STATES.json` for complete state machine definition.

---

## Integration with External Systems

The system can optionally sync with GitHub and Jira/Confluence. For detailed setup, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md).

### Quick Integration Overview

**Control via Environment Variable**:
```bash
export AUTO_INTEGRATE="never"   # Skip integration (testing)
export AUTO_INTEGRATE="prompt"  # Ask before creating (default)
export AUTO_INTEGRATE="always"  # Auto-create integration tasks
```

**Integration Triggers**:
- After `READY_FOR_DEVELOPMENT` → Create GitHub issue, Jira ticket
- After `READY_FOR_IMPLEMENTATION` → Update to "In Progress"
- After `READY_FOR_TESTING` → Create pull request
- After `TESTING_COMPLETE` → Post test results
- After `DOCUMENTATION_COMPLETE` → Close issue, merge PR

**Manual Integration**:
```bash
# Sync specific task
cmat.sh integration sync <task_id>

# Sync all unsynced tasks
cmat.sh integration sync-all
```

---

## Best Practices

### Starting a Workflow

1. **Create Enhancement Spec**: Document in `enhancements/<name>/<name>.md`
2. **Add First Task**: Create requirements-analyst task
```bash
   cmat.sh queue add \
     "Analyze feature X" \
     "requirements-analyst" \
     "high" \
     "analysis" \
     "enhancements/feature-x/feature-x.md" \
     "Analyze requirements for feature X" \
     true \
     true
```
3. **Start Task**: `cmat.sh queue start <task_id>`
4. **Monitor Progress**: `cmat.sh queue status`

### Choosing the Right Workflow

**Use Full Workflow** when:
- New feature with unclear requirements
- Complex changes needing architectural design
- User-facing changes requiring documentation
- Want comprehensive skill application across all phases

**Skip Requirements** when:
- Specifications are crystal clear
- Simple, well-understood changes
- Following existing patterns

**Skip Documentation** when:
- Internal refactoring only
- No API or behavior changes
- Technical debt reduction

**Use Hotfix** when:
- Production is broken
- Fix is obvious and low-risk
- Speed is critical

### Workflow Efficiency Tips

1. **Enable Auto-Chain**: Set `auto_chain: true` for automation
```bash
   cmat.sh queue add "Task" "agent" "high" "analysis" "file.md" "Description" false true
```

2. **Use Skills**: Ensure agents have appropriate skills assigned

3. **Review Failures Quickly**: Don't let blocked tasks pile up
```bash
   cmat.sh queue status  # Check regularly
```

4. **Clear Enhancement Specs**: Better specs = better skill application

5. **Validate Early**: Check outputs after each agent

### Monitoring Workflows
```bash
# Check current status
cmat.sh queue status

# View completed tasks
jq '.completed_tasks[-5:]' .claude/queues/task_queue.json

# Check for blocked tasks
jq '.failed_tasks' .claude/queues/task_queue.json

# Review agent logs
tail -f enhancements/*/logs/*.log

# Check skill usage
grep -r "Skills Applied" enhancements/feature-name/
```

---

## Handling Special Cases

### When Agent Gets Blocked

If an agent outputs `BLOCKED: <reason>`:

1. **Workflow Halts**: Automatic pause, no next agent triggered
2. **Task Status**: Marked as blocked in queue
3. **Manual Review**: Human reviews the blocking reason
4. **Resolution**: Fix the blocker
5. **Restart**: Create new task for same agent or appropriate agent

**Example**:
```
Agent Output: BLOCKED: API specification incomplete, needs stakeholder clarification
Action: Get stakeholder input, update requirements, restart architect
```

### When Output Validation Fails

If contract validation fails:

1. **Agent Completes**: Status detected normally
2. **Validation Runs**: Checks for required outputs
3. **Validation Fails**: Missing root document or required files
4. **Task Failed**: Marked as failed in queue
5. **Manual Fix**: Review logs, create missing files
6. **Retry**: Create new task or fix outputs

**Debug**:
```bash
# Check what was created
ls -la enhancements/feature-x/

# Check what contract expects
jq '.agents."requirements-analyst".outputs' .claude/AGENT_CONTRACTS.json

# Manually validate
cmat.sh workflow validate requirements-analyst enhancements/feature-x
```

### When Tests Fail

If tester outputs `BLOCKED: Tests failed`:

1. **Workflow Halts**: No automatic progression
2. **Review Failures**: Check test logs
3. **Fix Code**: Update implementation
4. **Retest**: Create new implementer task or restart tester

---

## Advanced Usage Examples

### Starting a New Feature
```bash
# Create enhancement file
mkdir -p enhancements/add-search
cat > enhancements/add-search/add-search.md << 'EOF'
# Add Search Feature

## Description
Add search functionality to filter tasks.

## Acceptance Criteria
- Search by title or description
- Case-insensitive matching
- Return relevant results
EOF

# Add initial task (automated)
TASK_ID=$(cmat.sh queue add \
  "Search feature - requirements" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/add-search/add-search.md" \
  "Analyze search feature requirements" \
  true \
  true)

# Start and let it run
cmat.sh queue start $TASK_ID

# Workflow will automatically progress through all phases
# Skills will be applied at each stage
```

### Monitoring Progress
```bash
# View queue status
cmat.sh queue status

# Check agent logs
tail -f enhancements/add-search/logs/*.log

# View workflow state
cat .claude/status/workflow_state.json | jq '.project_milestones'

# Check skill application
grep "Skills Applied" enhancements/add-search/*/
```

---

## Troubleshooting Workflows

### Workflow Stuck

**Symptoms**: No next agent suggested, workflow stopped unexpectedly

**Diagnosis**:
```bash
# Check task status
cmat.sh queue status

# Look for blocked/failed tasks
jq '.failed_tasks' .claude/queues/task_queue.json

# Check last agent's output
tail -100 enhancements/*/logs/*_$(date +%Y%m%d)*.log
```

**Solutions**:
- If blocked: Resolve blocker and restart agent
- If failed validation: Fix outputs and retry
- If no next agent: Check if workflow is complete
- If status unrecognized: Verify agent output correct status code

### Validation Always Failing

**Symptoms**: Every agent completion fails output validation

**Common Causes**:
- Root document wrong filename
- Output in wrong directory
- Missing metadata header
- Wrong agent subdirectory name

**Diagnosis**:
```bash
# Check what agent created
ls -la enhancements/feature-x/

# Check what contract expects
jq '.agents."requirements-analyst".outputs' .claude/AGENT_CONTRACTS.json

# Manually validate
cmat.sh workflow validate requirements-analyst enhancements/feature-x
```

### Auto-Chain Not Working

**Symptoms**: Manual prompt appears even with auto-chain enabled

**Diagnosis**:
```bash
# Check task settings
jq '.active_workflows[0].auto_chain' .claude/queues/task_queue.json

# Verify task created with auto-chain
jq '.pending_tasks[] | {id, auto_chain}' .claude/queues/task_queue.json

# Check logs
tail -20 .claude/logs/queue_operations.log | grep auto-chain
```

### Skills Not Appearing

**Symptoms**: Skills not in agent prompts or logs

**Diagnosis**:
```bash
# Check agent has skills defined
cmat.sh skills get requirements-analyst
# Should show array of skills

# Check skills.json exists
cmat.sh skills list

# Verify agents.json updated
jq '.agents[] | {name, skills}' .claude/agents/agents.json

# Test skills prompt generation
cmat.sh skills prompt requirements-analyst | grep "SPECIALIZED SKILLS"
```

**Solutions**:
- Add skills to agent frontmatter
- Regenerate: `cmat.sh agents generate-json`
- Verify skills.json has all skill definitions
- Check SKILL.md files exist in skill directories

---

## Quick Reference

### Command Cheatsheet
```bash
# Queue operations
cmat.sh queue add "Title" "agent" "priority" "type" "source" "desc" false true
cmat.sh queue start <task_id>
cmat.sh queue complete <task_id> "STATUS"
cmat.sh queue status

# Workflow operations
cmat.sh workflow validate "agent" "enhancement_dir"
cmat.sh workflow auto-chain <task_id> "STATUS"

# Skills operations
cmat.sh skills list
cmat.sh skills get <agent>
cmat.sh skills prompt <agent>

# Integration operations
cmat.sh integration sync <task_id>
cmat.sh integration sync-all
```

### Status Codes Quick Reference

- `READY_FOR_DEVELOPMENT` → architect
- `READY_FOR_IMPLEMENTATION` → implementer
- `READY_FOR_TESTING` → tester
- `TESTING_COMPLETE` → documenter (optional)
- `DOCUMENTATION_COMPLETE` → complete
- `BLOCKED: <reason>` → manual intervention

---

**This guide should be updated as new workflows are discovered or system capabilities expand.**

**Last Updated**: 10/24/2025
**Version**: 3.0.0