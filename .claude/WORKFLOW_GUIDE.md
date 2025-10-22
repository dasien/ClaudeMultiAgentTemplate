# Workflow Patterns Guide

This guide describes common workflow patterns in the multi-agent system. All patterns are driven by the agent contracts defined in `AGENT_CONTRACTS.json`.

## Table of Contents

- [Standard Workflows](#standard-workflows)
- [Workflow States and Transitions](#workflow-states-and-transitions)
- [Branching Workflows](#branching-workflows)
- [Handling Special Cases](#handling-special-cases)
- [Integration with External Systems](#integration-with-external-systems)
- [Best Practices](#best-practices)
- [Customizing Workflows](#customizing-workflows)
- [Troubleshooting Workflows](#troubleshooting-workflows)

---

## Queue System Commands

The queue system manages tasks and orchestrates workflow transitions.

### Basic Task Management

```bash
# Check queue status
.claude/queues/queue_manager.sh status

# Add a task
.claude/queues/queue_manager.sh add \
  "Task title" \
  "agent-name" \
  "priority" \
  "task_type" \
  "source_file" \
  "description" \
  auto_complete \
  auto_chain

# Start a task
.claude/queues/queue_manager.sh start <task_id>

# Complete a task
.claude/queues/queue_manager.sh complete <task_id> "STATUS"

# Complete with auto-chain
.claude/queues/queue_manager.sh complete <task_id> "STATUS" --auto-chain

# Cancel a task
.claude/queues/queue_manager.sh cancel <task_id> "reason"

# Cancel all tasks
.claude/queues/queue_manager.sh cancel-all "reason"

# Fail a task
.claude/queues/queue_manager.sh fail <task_id> "error message"

# Update task metadata
.claude/queues/queue_manager.sh update-metadata <task_id> <key> <value>
```

### Contract-Based Commands

```bash
# Validate agent outputs against contract
.claude/queues/queue_manager.sh validate_agent_outputs \
  "requirements-analyst" \
  "enhancements/feature"

# Determine next agent from contract
.claude/queues/queue_manager.sh determine_next_agent_from_contract \
  "requirements-analyst" \
  "READY_FOR_DEVELOPMENT"

# Build next source path
.claude/queues/queue_manager.sh build_next_source_path \
  "feature-name" \
  "architect" \
  "requirements-analyst"

# Auto-chain with validation
.claude/queues/queue_manager.sh auto_chain_validated \
  <task_id> \
  "READY_FOR_DEVELOPMENT"
```

### List and Query Tasks

```bash
# List tasks by queue
.claude/queues/queue_manager.sh list_tasks pending
.claude/queues/queue_manager.sh list_tasks active
.claude/queues/queue_manager.sh list_tasks completed
.claude/queues/queue_manager.sh list_tasks failed
.claude/queues/queue_manager.sh list_tasks all

# Compact format (one task per line)
.claude/queues/queue_manager.sh list_tasks completed compact

# Check version
.claude/queues/queue_manager.sh version
```

### Integration Commands

```bash
# Sync specific task to external systems
.claude/queues/queue_manager.sh sync-external <task_id>

# Sync all unsynced completed tasks
.claude/queues/queue_manager.sh sync-all

# Add integration task manually
.claude/queues/queue_manager.sh add-integration \
  "READY_FOR_DEVELOPMENT" \
  "enhancements/feature/requirements-analyst/analysis_summary.md" \
  "requirements-analyst" \
  "parent_task_id"
```

### Workflow Templates

```bash
# Start predefined workflow
.claude/queues/queue_manager.sh workflow sequential_development "Feature description"
.claude/queues/queue_manager.sh workflow bug_fix "Bug description"
.claude/queues/queue_manager.sh workflow hotfix_flow "Hotfix description"
.claude/queues/queue_manager.sh workflow refactoring "Refactoring description"
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

## Logging and Monitoring

### Agent Logs

Each agent execution creates a detailed log:

**Location**: `enhancements/{enhancement}/logs/{agent}_{task_id}_{timestamp}.log`

**Contents**:
- Agent execution start time
- Task details (ID, source file, enhancement)
- Complete agent output
- Execution duration
- Exit code and status

**Example**:
```bash
# View most recent log
ls -t enhancements/demo-test/logs/*.log | head -1 | xargs cat

# Follow log in real-time
tail -f enhancements/demo-test/logs/architect_*.log

# View all logs for an enhancement
ls enhancements/demo-test/logs/
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
# [2025-10-21T14:30:00Z] TASK_ADDED: ID: task_123, Agent: requirements-analyst, Title: Demo test
# [2025-10-21T14:30:05Z] TASK_STARTED: ID: task_123, Agent: requirements-analyst
# [2025-10-21T14:35:00Z] TASK_COMPLETED: ID: task_123, Agent: requirements-analyst, Result: READY_FOR_DEVELOPMENT
```

### Monitoring Workflows

```bash
# Check overall queue status
.claude/queues/queue_manager.sh status

# See recently completed tasks
jq '.completed_tasks[-5:]' .claude/queues/task_queue.json

# Check for failed tasks
jq '.failed_tasks' .claude/queues/task_queue.json

# Monitor active tasks
watch -n 5 '.claude/queues/queue_manager.sh status'
```

---

## Integration with External Systems

The system can optionally sync with GitHub and Jira/Confluence. For detailed setup and configuration, see [INTEGRATION_GUIDE.md](.claude/INTEGRATION_GUIDE.md).

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
.claude/queues/queue_manager.sh sync-external <task_id>

# Sync all unsynced tasks
.claude/queues/queue_manager.sh sync-all
```

See [INTEGRATION_GUIDE.md](.claude/INTEGRATION_GUIDE.md) for complete integration documentation, MCP setup, and platform-specific details.

---

## Standard Workflows

### Complete Feature Development

**Flow**: Requirements → Architecture → Implementation → Testing → Documentation

**Agents**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **architect** → `READY_FOR_IMPLEMENTATION`
3. **implementer** → `READY_FOR_TESTING`
4. **tester** → `TESTING_COMPLETE`
5. **documenter** → `DOCUMENTATION_COMPLETE`

**When to Use**: New features, major enhancements, user-facing changes

**Duration**: Typically 6-12 hours total across all phases

**Example**: Adding a new API endpoint with documentation

---

### Bug Fix Workflow

**Flow**: Requirements → Architecture → Implementation → Testing

**Agents**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **architect** → `READY_FOR_IMPLEMENTATION`
3. **implementer** → `READY_FOR_TESTING`
4. **tester** → `TESTING_COMPLETE`

**When to Use**: Bug fixes requiring analysis and design

**Duration**: Typically 2-4 hours total

**Note**: Documentation phase usually skipped for bug fixes unless API changes or behavior modifications require documentation updates

**Example**: Fixing a calculation error that requires understanding the business logic

---

### Hotfix Workflow

**Flow**: Implementation → Testing

**Agents**:
1. **implementer** → `READY_FOR_TESTING`
2. **tester** → `TESTING_COMPLETE`

**When to Use**: Critical bugs, emergency fixes, production incidents

**Duration**: 1-2 hours total

**Note**: Requirements and architecture analysis skipped for speed. Use only for truly critical issues where the fix is obvious.

**Example**: Fixing a typo causing a crash, patching a security vulnerability with known solution

---

### Refactoring Workflow

**Flow**: Architecture → Implementation → Testing → Documentation

**Agents**:
1. **architect** → `READY_FOR_IMPLEMENTATION`
2. **implementer** → `READY_FOR_TESTING`
3. **tester** → `TESTING_COMPLETE`
4. **documenter** → `DOCUMENTATION_COMPLETE`

**When to Use**: Code refactoring, technical debt reduction, performance optimization

**Duration**: 4-8 hours total

**Note**: Requirements analysis skipped since functionality doesn't change

**Example**: Refactoring a module to use a better design pattern, optimizing database queries

---

### Documentation Update Workflow

**Flow**: Requirements → Documentation → Testing

**Agents**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **documenter** → `DOCUMENTATION_COMPLETE`
3. **tester** → `TESTING_COMPLETE` (validates examples work)

**When to Use**: Documentation improvements, guide updates, API documentation changes

**Duration**: 2-4 hours total

**Note**: Architecture and implementation skipped - just updating docs

**Example**: Updating README with new examples, creating user guides

---

## Workflow States and Transitions

Each status code triggers a specific next agent according to agent contracts:

| Current Status | Next Agent | Notes |
|----------------|------------|-------|
| `READY_FOR_DEVELOPMENT` | architect | Requirements complete, ready for design |
| `READY_FOR_IMPLEMENTATION` | implementer | Architecture complete, ready to code |
| `READY_FOR_TESTING` | tester | Implementation complete, needs validation |
| `READY_FOR_INTEGRATION` | tester | Implementation complete, needs integration testing |
| `TESTING_COMPLETE` | documenter | Tests passed, ready for docs (optional) |
| `DOCUMENTATION_COMPLETE` | none | Workflow complete |
| `BLOCKED: <reason>` | none | Manual intervention required |

**State Machine**: See `WORKFLOW_STATES.json` for the complete state machine definition with valid transitions.

### Status Code Meanings

- **READY_FOR_DEVELOPMENT**: Requirements analyzed, clear scope defined, ready for technical design
- **READY_FOR_IMPLEMENTATION**: Architecture designed, technical specs complete, ready to write code
- **READY_FOR_TESTING**: Code written, implementation complete, needs quality validation
- **READY_FOR_INTEGRATION**: Implementation complete, needs integration with other components
- **TESTING_COMPLETE**: Tests passed, quality validated, ready for documentation
- **DOCUMENTATION_COMPLETE**: Documentation finished, enhancement fully complete
- **BLOCKED: <reason>**: Workflow halted, manual intervention needed (e.g., "BLOCKED: Missing API credentials")

---

## Branching Workflows

### Parallel Development

**When to Use**: Independent components can be developed simultaneously

**Example**: Frontend and backend implementation can proceed in parallel

**Flow**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **architect** → `READY_FOR_IMPLEMENTATION`
3. **Parallel Execution**:
   - **implementer-frontend** → `READY_FOR_INTEGRATION`
   - **implementer-backend** → `READY_FOR_INTEGRATION`
4. **tester** → `TESTING_COMPLETE` (integration testing)
5. **documenter** → `DOCUMENTATION_COMPLETE`

**Configuration**: Requires custom workflow configuration in `WORKFLOW_STATES.json`

**Note**: Use when components are independent with clear interfaces. Requires coordination to ensure compatible implementations.

---

## Handling Special Cases

### When Agent Gets Blocked

If an agent outputs `BLOCKED: <reason>`:

1. **Workflow Halts**: Automatic pause, no next agent triggered
2. **Task Status**: Marked as blocked in queue
3. **Manual Review**: Human reviews the blocking reason
4. **Resolution**: Fix the blocker (gather missing info, resolve issue)
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
5. **Manual Fix**: Review logs, create missing files, validate structure
6. **Retry**: Create new task or fix outputs and manually mark complete

**Example**:
```
Validation Error: Required output missing: enhancements/feature/architect/implementation_plan.md
Action: Review agent log, identify why file wasn't created, fix and retry
```

### When Tests Fail

If tester outputs `BLOCKED: Tests failed`:

1. **Workflow Halts**: No automatic progression
2. **Review Failures**: Check test logs and failure reasons
3. **Fix Code**: Update implementation based on test failures
4. **Retest**: 
   - Option A: Create new implementer task to fix
   - Option B: Fix manually, restart tester directly

**Example**:
```
Tester Output: BLOCKED: 3 unit tests failed - validation logic incorrect
Action: Fix validation logic in implementer, re-run tester
```

---

## Integration with External Systems

### Integration Tasks

After each phase completion, optionally create integration tasks to sync with GitHub, Jira, and Confluence:

**Trigger Statuses and Actions**:

| Status | GitHub Action | Jira Action | Confluence Action |
|--------|--------------|-------------|-------------------|
| `READY_FOR_DEVELOPMENT` | Create issue with requirements | Create ticket (Story/Task) | - |
| `READY_FOR_IMPLEMENTATION` | Add "architecture-complete" label | Update to "In Progress" | Publish architecture doc |
| `READY_FOR_TESTING` | Create pull request | Update to "In Review" | - |
| `TESTING_COMPLETE` | Add "tests-passing" label | Update to "Testing" | - |
| `DOCUMENTATION_COMPLETE` | Close issue, merge PR | Update to "Done" | Publish user guide |

### Controlling Integration

Set `AUTO_INTEGRATE` environment variable:

```bash
export AUTO_INTEGRATE="always"   # Automatic integration task creation
export AUTO_INTEGRATE="prompt"   # Ask before creating (default)
export AUTO_INTEGRATE="never"    # Manual integration only
```

**Per-Task Control**:
- Add `--auto-integrate` flag when creating tasks
- Configure default per-agent in `.claude/config.json`

**Manual Integration**:
```bash
# Sync specific completed task
.claude/queues/queue_manager.sh sync-external <task_id>

# Sync all unsynced tasks
.claude/queues/queue_manager.sh sync-all
```

---

## Best Practices

### Starting a Workflow

1. **Create Enhancement Spec**: Document in `enhancements/<name>/<name>.md`
2. **Add First Task**: Create requirements-analyst task
   ```bash
   .claude/queues/queue_manager.sh add \
     "Analyze feature X" \
     "requirements-analyst" \
     "high" \
     "analysis" \
     "enhancements/feature-x/feature-x.md" \
     "Analyze requirements for feature X"
   ```
3. **Enable Auto-Chain**: Set `--auto-chain true` for fully automated flow
4. **Monitor Progress**: Check queue status regularly

### Choosing the Right Workflow

**Use Full Workflow** when:
- New feature with unclear requirements
- Complex changes needing architectural design
- User-facing changes requiring documentation

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

1. **Enable Auto-Chain**: Set `auto_chain: true` on tasks for automation
   ```bash
   .claude/queues/queue_manager.sh add ... --auto-chain true
   ```

2. **Enable Auto-Integration**: For fully automated external sync
   ```bash
   export AUTO_INTEGRATE="always"
   ```

3. **Review Failures Quickly**: Don't let blocked tasks pile up
   ```bash
   .claude/queues/queue_manager.sh status  # Check regularly
   ```

4. **Clear Enhancement Specs**: Better specs = faster requirements phase

5. **Validate Early**: Check outputs after each agent to catch issues

### Monitoring Workflows

```bash
# Check current status
.claude/queues/queue_manager.sh status

# View completed tasks
jq '.completed_tasks[-5:]' .claude/queues/task_queue.json

# Check for blocked tasks
jq '.failed_tasks' .claude/queues/task_queue.json

# Review agent logs
tail -f enhancements/*/logs/*.log
```

---

## Customizing Workflows

### Adding New Workflows

1. **Define Pattern**: Document the agent sequence
2. **Update WORKFLOW_STATES.json**: If special transitions needed
3. **Update Agent Contracts**: If new status codes required
4. **Document Here**: Add to this guide
5. **Test Thoroughly**: Validate before production use

### Example: Code Review Workflow

```markdown
**Flow**: Architect → Code Reviewer → Implementer

**Agents**:
1. architect → READY_FOR_REVIEW
2. code-reviewer → READY_FOR_IMPLEMENTATION
3. implementer → READY_FOR_TESTING
```

**Configuration**:
1. Create `code-reviewer` agent
2. Add to `AGENT_CONTRACTS.json`
3. Update architect's success statuses to include `READY_FOR_REVIEW`

### Creating Custom Agents

To add specialized agents:

1. **Create Agent File**: `.claude/agents/custom-agent.md`
2. **Add to Contracts**: Define in `AGENT_CONTRACTS.json`
3. **Update Workflows**: Reference in relevant workflow patterns
4. **Test**: Validate with example enhancement

---

## Troubleshooting Workflows

### Workflow Stuck

**Symptoms**: No next agent suggested, workflow stopped unexpectedly

**Diagnosis**:
```bash
# Check task status
.claude/queues/queue_manager.sh status

# Look for blocked/failed tasks
jq '.failed_tasks' .claude/queues/task_queue.json

# Check last agent's output
tail -100 enhancements/*/logs/*_$(date +%Y%m%d)*.log
```

**Solutions**:
- If blocked: Resolve blocker and restart agent
- If failed validation: Fix outputs and retry
- If no next agent: Check if workflow is actually complete
- If status unrecognized: Verify agent output correct status code

### Wrong Next Agent Suggested

**Symptoms**: System suggests incorrect or unexpected next agent

**Solutions**:
```bash
# Verify agent contract
jq '.agents.architect' .claude/AGENT_CONTRACTS.json

# Check next_agents for status
jq '.agents.architect.statuses.success[] | select(.code == "READY_FOR_IMPLEMENTATION")' .claude/AGENT_CONTRACTS.json

# Cancel automatic suggestion and create manually
.claude/queues/queue_manager.sh cancel <task_id>
.claude/queues/queue_manager.sh add "Correct task" "correct-agent" ...
```

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
.claude/queues/queue_manager.sh validate_agent_outputs "requirements-analyst" "enhancements/feature-x"
```

**Solutions**:
- Verify contract matches actual output structure
- Check prompt template gives correct instructions
- Ensure agent understands output requirements
- Update contract if agent behavior is correct but contract is wrong

### Auto-Chain Not Working

**Symptoms**: Manual prompt appears even with auto-chain enabled

**Diagnosis**:
```bash
# Check task settings
jq '.active_workflows[0].auto_chain' .claude/queues/task_queue.json

# Verify task created with auto-chain
jq '.pending_tasks[] | {id, auto_chain}' .claude/queues/task_queue.json
```

**Solutions**:
- Ensure task created with `--auto-chain true` flag
- Check hook is executing (look for "🔗 Auto-chaining enabled" message)
- Verify validation is passing (auto-chain requires valid outputs)

---

## Quick Reference

### Command Cheatsheet

```bash
# Create task with auto-chain
.claude/queues/queue_manager.sh add "Title" "agent" "priority" "type" "source" "desc" false true

# Start task
.claude/queues/queue_manager.sh start <task_id>

# Complete manually
.claude/queues/queue_manager.sh complete <task_id> "STATUS"

# Check status
.claude/queues/queue_manager.sh status

# Create integration task
.claude/queues/queue_manager.sh sync-external <task_id>
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

**Last Updated**: 10/22/2025
**Version**: 1.1