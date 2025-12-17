# Status Completion Guide

How agents report task completion status using YAML completion blocks.

**Version**: 8.2.0

## Overview

CMAT agents report their completion status using structured YAML blocks at the end of their output. This enables reliable status extraction and workflow orchestration.

---

## Completion Block Format

Every agent must output a YAML completion block at the end of their response:

```yaml
---
agent: <agent-name>
task_id: <task-id>
status: <STATUS_CODE>
---
```

**Fields**:
- `agent` - The agent's identifier (e.g., `implementer`, `tester`)
- `task_id` - The task being completed (e.g., `task_1702345678_12345`)
- `status` - The completion status code (see below)

**Example**:
```yaml
---
agent: implementer
task_id: task_1702345678_12345
status: READY_FOR_TESTING
---
```

---

## Status Types

### Completion Statuses

Completion statuses indicate the agent has finished successfully and the workflow should continue to the next step.

| Status | Description | Typical Next Step |
|--------|-------------|-------------------|
| `READY_FOR_DEVELOPMENT` | Requirements analysis complete | architect |
| `READY_FOR_IMPLEMENTATION` | Architecture/design complete | implementer |
| `READY_FOR_TESTING` | Implementation complete | tester |
| `READY_FOR_REVIEW` | Ready for code review | code-reviewer |
| `TESTING_COMPLETE` | All tests passed | documenter |
| `DOCUMENTATION_COMPLETE` | Documentation updated | (workflow end) |

### Halt Statuses

Halt statuses indicate the agent cannot proceed and requires intervention. These pause the workflow.

| Status | Description | Resolution |
|--------|-------------|------------|
| `BLOCKED: <reason>` | Cannot proceed due to external dependency | Address blocking issue |
| `NEEDS_CLARIFICATION: <question>` | Requirements unclear | Provide clarification |
| `TESTS_FAILED: <details>` | Tests did not pass | Fix failing tests |
| `BUILD_FAILED: <details>` | Build process failed | Fix build errors |
| `NEEDS_RESEARCH: <topic>` | Additional research needed | Conduct research |

**Example halt status**:
```yaml
---
agent: implementer
task_id: task_1702345678_12345
status: BLOCKED: Missing API specification for payment endpoint
---
```

---

## How Status Extraction Works

### Primary Method: YAML Block

The `TaskService.extract_status()` method looks for YAML completion blocks using this pattern:

```python
COMPLETION_BLOCK_PATTERN = re.compile(
    r'^---\s*\n'           # Opening ---
    r'agent:\s*\S+\s*\n'   # agent field
    r'task_id:\s*\S+\s*\n' # task_id field
    r'status:\s*(.+?)\s*\n'# status field (captured)
    r'---\s*$',            # Closing ---
    re.MULTILINE
)
```

### Legacy Fallback

For backward compatibility, the system also supports legacy status patterns:

```python
LEGACY_STATUS_PATTERNS = [
    r'^Status:\s*(READY_FOR_\w+|.*_COMPLETE)\s*$',
    r'^##\s*Status\s*\n+\s*(READY_FOR_\w+|.*_COMPLETE)',
    r'^(BLOCKED|NEEDS_CLARIFICATION|TESTS_FAILED|BUILD_FAILED|NEEDS_RESEARCH):\s*(.+)$',
]
```

**Priority**: If both YAML block and legacy patterns are found, the YAML block takes precedence.

---

## Workflow Integration

### on_status Configuration

Workflows define how to handle each status in their step configuration:

```json
{
  "steps": [
    {
      "agent": "implementer",
      "on_status": {
        "READY_FOR_TESTING": {
          "next_step": "tester",
          "auto_chain": true,
          "description": "Implementation complete, ready for testing"
        },
        "BLOCKED": {
          "next_step": null,
          "auto_chain": false,
          "description": "Cannot proceed - requires manual intervention"
        },
        "TESTS_FAILED": {
          "next_step": null,
          "auto_chain": false,
          "description": "Tests failed - fix and re-run"
        }
      }
    }
  ]
}
```

### Status Transition Logic

```
Task completes with status
    │
    ▼
Status in workflow's on_status? ──No──▶ UNEXPECTED (stop)
    │ Yes
    ▼
transition.next_step defined? ──null─▶ WORKFLOW COMPLETE or HALT
    │ Has value
    ▼
transition.auto_chain = true? ──False─▶ STOP (manual intervention)
    │ True
    ▼
CREATE NEXT TASK AND RUN IT
```

---

## Agent Implementation

### Adding Completion Block to Agents

Each agent's markdown file should include instructions for the completion block in its "Status Output" section:

```markdown
### Status Output

At the end of your response, output a completion block:

\`\`\`yaml
---
agent: implementer
task_id: ${task_id}
status: <status>
---
\`\`\`

**Completion Statuses** (workflow continues):
- READY_FOR_TESTING - Implementation complete, all requirements met

**Halt Statuses** (workflow pauses for intervention):
- BLOCKED: <reason> - Cannot proceed due to external dependency
- TESTS_FAILED: <details> - Tests did not pass
```

### Status Selection Guidelines

Agents should select status based on:

1. **COMPLETION STATUS** when:
   - All required outputs are created
   - Quality criteria are met
   - No blockers exist
   - Ready for next phase

2. **HALT STATUS** when:
   - Missing required information
   - External dependencies not met
   - Quality issues found
   - Manual intervention needed

---

## Prompt Template Integration

The `${expected_statuses}` variable in prompt templates is populated by `WorkflowService.format_statuses_for_prompt()`:

```python
def format_statuses_for_prompt(self, on_status: dict) -> str:
    completion = []
    halt = []

    for status, transition in on_status.items():
        desc = transition.get("description", "")
        if transition.get("auto_chain") and transition.get("next_step"):
            completion.append(f"- {status} - {desc}")
        else:
            halt.append(f"- {status} - {desc}")

    return f"""**Completion Statuses** (workflow continues):
{chr(10).join(completion)}

**Halt Statuses** (workflow pauses for intervention):
{chr(10).join(halt)}"""
```

---

## Examples

### Successful Implementation

```yaml
---
agent: implementer
task_id: task_1702345678_12345
status: READY_FOR_TESTING
---
```

Result: Workflow creates tester task and continues.

### Blocked by Dependency

```yaml
---
agent: architect
task_id: task_1702345678_12346
status: BLOCKED: Waiting for database schema decision from team lead
---
```

Result: Workflow pauses. User must resolve blocker and manually restart.

### Tests Failed

```yaml
---
agent: tester
task_id: task_1702345678_12347
status: TESTS_FAILED: 3 unit tests failing in auth module - see test_summary.md for details
---
```

Result: Workflow pauses. User/agent must fix tests and re-run.

### Needs Clarification

```yaml
---
agent: requirements-analyst
task_id: task_1702345678_12348
status: NEEDS_CLARIFICATION: Should user authentication use OAuth2 or API keys?
---
```

Result: Workflow pauses. User must provide clarification.

---

## Debugging

### Status Not Extracted

If status extraction fails:

1. **Check YAML format**: Ensure exact format with `---` delimiters
2. **Check field order**: Must be `agent`, `task_id`, `status`
3. **Check whitespace**: No extra blank lines within block
4. **Check status value**: Must be on single line

### Unexpected Status

If workflow stops with "Status not defined in workflow":

1. Check workflow template's `on_status` dictionary
2. Verify status code matches exactly (case-sensitive)
3. Add missing status to workflow if needed

### Legacy Status Still Used

If agents are outputting legacy format:

1. Update agent markdown with completion block instructions
2. Legacy patterns still work but YAML is preferred
3. Both formats can coexist during transition

---

## Best Practices

1. **Always include completion block** - Even for halt statuses
2. **Be specific in halt reasons** - Help users understand what's needed
3. **Use consistent status codes** - Match workflow expectations
4. **Include context in halt statuses** - `BLOCKED: <specific reason>` not just `BLOCKED`
5. **Validate against workflow** - Check that status exists in workflow's `on_status`

---

## See Also

- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Workflow configuration
- [WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md) - Template management
- [TASK_PROMPT_DEFAULTS.md](TASK_PROMPT_DEFAULTS.md) - Prompt templates
