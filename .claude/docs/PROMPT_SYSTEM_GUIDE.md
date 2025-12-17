# Prompt System Guide

Complete guide to how CMAT builds prompts for agents and how agents report completion status.

**Version**: 8.2.0

## Table of Contents

- [Overview](#overview)
- [Prompt Construction Pipeline](#prompt-construction-pipeline)
- [Prompt Components](#prompt-components)
  - [Base Templates](#base-templates)
  - [Skills Section](#skills-section)
  - [Workflow Context](#workflow-context)
  - [Variable Substitution](#variable-substitution)
- [User Input](#user-input)
- [Status Completion System](#status-completion-system)
  - [Completion Block Format](#completion-block-format)
  - [Status Types](#status-types)
  - [Status Extraction](#status-extraction)
  - [Workflow Integration](#workflow-integration)
- [Customizing Prompts](#customizing-prompts)
- [Debugging](#debugging)
- [Best Practices](#best-practices)

---

## Overview

When you start a task, CMAT automatically constructs a comprehensive prompt that includes:

1. **Base task template** (from TASK_PROMPT_DEFAULTS.md)
2. **Workflow context** (expected statuses, input/output specs)
3. **Skills** (domain expertise for the agent)
4. **Variable substitutions** (task-specific details)
5. **User input** (enhancement spec file and task description)

Agents respond with their work and a **completion block** that reports their status, enabling workflow orchestration.

---

## Prompt Construction Pipeline

### Step-by-Step Process

```
1. User starts workflow
   |
   v
2. System creates task with workflow metadata
   |
   v
3. Load base template (by task_type)
   |
   v
4. Inject skills section
   |
   v
5. Get workflow context (expected statuses, required output)
   |
   v
6. Substitute all variables
   |
   v
7. Send final prompt to Claude
   |
   v
8. Agent completes work and outputs completion block
   |
   v
9. System extracts status and triggers next step
```

---

## Prompt Components

### Base Templates

**Source**: `.claude/docs/TASK_PROMPT_DEFAULTS.md`

Based on task type, one of these templates is loaded:

| Template | Task Type | Agent |
|----------|-----------|-------|
| `ANALYSIS_TEMPLATE` | analysis | requirements-analyst |
| `TECHNICAL_ANALYSIS_TEMPLATE` | architecture | architect |
| `IMPLEMENTATION_TEMPLATE` | implementation | implementer |
| `TESTING_TEMPLATE` | testing | tester |
| `DOCUMENTATION_TEMPLATE` | documentation | documenter |
| `INTEGRATION_TEMPLATE` | integration | integration coordinators |

### Example Template Structure

```markdown
You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

${enhancement_dir}/${agent}/
+-- required_output/
|   +-- ${required_output_filename}  (REQUIRED)
+-- optional_output/                  (OPTIONAL)

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

## Status Output

At the end of your response, output your completion status.

**Expected Statuses for This Workflow:**
${expected_statuses}

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions...
```

---

### Skills Section

**Source**: `.claude/skills/{skill-directory}/SKILL.md`

Skills are automatically injected based on agent configuration.

#### How Skills Are Selected

**From agent frontmatter** (`.claude/agents/requirements-analyst.md`):
```yaml
---
skills: ["requirements-elicitation", "user-story-writing", "bug-triage"]
---
```

**System loads these skills**:
1. `.claude/skills/requirements-elicitation/SKILL.md`
2. `.claude/skills/user-story-writing/SKILL.md`
3. `.claude/skills/bug-triage/SKILL.md`

#### Skills Section Structure

```markdown
################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

You have access to the following specialized skills that enhance your capabilities.
Use these skills when they are relevant to your task:

---

# Requirements Elicitation

## Purpose
Extract complete, unambiguous requirements from user specifications...

## When to Use
- Analyzing new feature requests
- Processing enhancement specifications
...

## Key Capabilities
1. **Extract Requirements** - Identify functional and non-functional requirements
2. **Clarify Ambiguities** - Flag unclear specifications
...

---

# User Story Writing
[Similar structure for next skill...]

---

**Using Skills**: Apply the above skills as appropriate to accomplish your objectives.

################################################################################
```

---

### Workflow Context

**Source**: Workflow template + task metadata

#### Workflow Context Extraction

**From task metadata**:
```json
{
  "workflow_name": "new-feature-development",
  "workflow_step": 0
}
```

**System looks up** in `workflow_templates.json`:
```json
{
  "steps": [
    {
      "agent": "requirements-analyst",
      "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
      "required_output": "analysis_summary.md",
      "on_status": {
        "READY_FOR_DEVELOPMENT": {
          "next_step": "architect",
          "auto_chain": true
        }
      }
    }
  ]
}
```

**Extracts**:
- `required_output_filename` = "analysis_summary.md"
- `expected_statuses` = "- `READY_FOR_DEVELOPMENT`"
- `input_instruction` = "Read and process this file: enhancements/user-auth/user-auth.md"

---

### Variable Substitution

All variables in templates are substituted before sending to Claude:

| Variable | Example Value | Source |
|----------|---------------|--------|
| `${agent}` | "requirements-analyst" | Task parameter |
| `${agent_config}` | ".claude/agents/requirements-analyst.md" | Derived from agent |
| `${task_id}` | "task_1732123456_12345" | Generated |
| `${task_description}` | "Workflow: new-feature-development, Step 0" | Task parameter |
| `${enhancement_name}` | "user-auth" | Extracted from source path |
| `${enhancement_dir}` | "enhancements/user-auth" | Derived |
| `${input_instruction}` | "Read and process this file: ..." | Workflow + file detection |
| `${required_output_filename}` | "analysis_summary.md" | Workflow step definition |
| `${expected_statuses}` | "- `READY_FOR_DEVELOPMENT`" | Workflow on_status keys |

---

## User Input

### Primary: Enhancement Specification File

**File**: `enhancements/{enhancement_name}/{enhancement_name}.md`

This is the **main user input** that agents process:

```markdown
# User Authentication Feature

## Description
Add user login and registration functionality with email verification.

## Acceptance Criteria
- Users can register with email/password
- Email verification required before login
- Password must meet strength requirements
- Login generates JWT token
- Logout invalidates token

## Technical Notes
- Use bcrypt for password hashing
- JWT tokens expire after 24 hours
```

The agent receives an instruction to read this file:
```markdown
## Input

Read and process this file: enhancements/user-auth/user-auth.md
```

### Secondary: Task Description

**When using workflows** (recommended):
```bash
python -m cmat workflow start new-feature-development user-auth
```

Task description is auto-generated: `"Workflow: new-feature-development, Step 0"`

**When creating manual tasks**:
```bash
python -m cmat queue add requirements-analyst "Custom instructions here" \
    enhancements/user-auth/user-auth.md
```

Task description appears in prompt:
```markdown
## Task: Custom instructions here
```

---

## Status Completion System

### Completion Block Format

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
- `status` - The completion status code

**Example**:
```yaml
---
agent: implementer
task_id: task_1702345678_12345
status: READY_FOR_TESTING
---
```

---

### Status Types

#### Completion Statuses

Completion statuses indicate the agent has finished successfully and the workflow should continue.

| Status | Description | Typical Next Step |
|--------|-------------|-------------------|
| `READY_FOR_DEVELOPMENT` | Requirements analysis complete | architect |
| `READY_FOR_IMPLEMENTATION` | Architecture/design complete | implementer |
| `READY_FOR_TESTING` | Implementation complete | tester |
| `READY_FOR_REVIEW` | Ready for code review | code-reviewer |
| `TESTING_COMPLETE` | All tests passed | documenter |
| `DOCUMENTATION_COMPLETE` | Documentation updated | (workflow end) |

#### Halt Statuses

Halt statuses indicate the agent cannot proceed and requires intervention.

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

### Status Extraction

#### Primary Method: YAML Block

The `TaskService.extract_status()` method looks for YAML completion blocks:

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

#### Legacy Fallback

For backward compatibility, the system also supports legacy status patterns:
- `Status: READY_FOR_TESTING`
- `## Status\n\nREADY_FOR_TESTING`

**Priority**: If both YAML block and legacy patterns are found, the YAML block takes precedence.

---

### Workflow Integration

#### on_status Configuration

Workflows define how to handle each status:

```json
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
    }
  }
}
```

#### Status Transition Logic

```
Task completes with status
    |
    v
Status in workflow's on_status? ──No──> UNEXPECTED (stop)
    | Yes
    v
transition.next_step defined? ──null─> WORKFLOW COMPLETE or HALT
    | Has value
    v
transition.auto_chain = true? ──False─> STOP (manual intervention)
    | True
    v
CREATE NEXT TASK AND RUN IT
```

---

## Customizing Prompts

### Method 1: Edit Base Templates

**File**: `.claude/docs/TASK_PROMPT_DEFAULTS.md`

Modify the base template for a task type. **Affects**: All tasks of that type.

### Method 2: Customize Agent Configuration

**File**: `.claude/agents/{agent}.md`

Update the agent .md file to change:
- Role description
- Core responsibilities
- Scope boundaries
- Best practices

**Affects**: All tasks for that agent.

### Method 3: Add/Modify Skills

**Files**: `.claude/skills/{skill}/SKILL.md`

Create new skills or edit existing ones. **Affects**: All agents with that skill assigned.

### Method 4: Workflow-Level Customization

**File**: `.claude/data/workflow_templates.json`

Change:
- Expected statuses (from `on_status` keys)
- Required output filename
- Input paths

**Affects**: Only workflows using that template.

### Method 5: Task-Level Customization

Use custom task description when creating manual tasks to add specific instructions.

---

## Debugging

### View Complete Prompt

**Before execution**:
```bash
python -m cmat queue preview-prompt <task_id>
```

**After execution**: Check agent logs in `enhancements/{feature}/logs/`

### Check Variable Substitution

```bash
python -m cmat queue preview-prompt <task_id> | grep "enhancement:"
python -m cmat queue preview-prompt <task_id> | grep "Expected Statuses"
```

### Verify Skills Injection

```bash
python -m cmat queue preview-prompt <task_id> | grep "SPECIALIZED SKILLS"
```

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

---

## Best Practices

### Prompt Design

**DO**:
- Preview prompts before execution
- Keep skills concise (300-800 tokens each)
- Assign 2-4 relevant skills per agent
- Use workflow templates to customize behavior
- Check logs to see actual prompts sent

**DON'T**:
- Edit generated prompts directly (they're rebuilt each time)
- Assign too many skills (bloats prompt)
- Make base templates too verbose
- Include sensitive data in templates or skills

### Status Reporting

**DO**:
- Always include completion block - Even for halt statuses
- Be specific in halt reasons - Help users understand what's needed
- Use consistent status codes - Match workflow expectations
- Include context in halt statuses - `BLOCKED: <specific reason>` not just `BLOCKED`
- Validate against workflow - Check that status exists in workflow's `on_status`

**DON'T**:
- Output multiple completion blocks
- Use status codes not in workflow's `on_status`
- Leave out the reason for halt statuses

### Prompt Size Considerations

**Approximate Sizes**:
- Base Template: ~500 tokens
- Per Skill: ~300-800 tokens each
- Example totals: 2000-3500 tokens

**If prompts too large**:
1. Reduce skills assigned to agents (keep 2-3 most relevant)
2. Shorten skill content (make more concise)
3. Simplify base templates

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
status: TESTS_FAILED: 3 unit tests failing in auth module - see test_summary.md
---
```

Result: Workflow pauses. User/agent must fix tests and re-run.

---

## See Also

- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow configuration
- **[TASK_PROMPT_DEFAULTS.md](TASK_PROMPT_DEFAULTS.md)** - Base prompt templates
- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Skills system
- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** - Command reference