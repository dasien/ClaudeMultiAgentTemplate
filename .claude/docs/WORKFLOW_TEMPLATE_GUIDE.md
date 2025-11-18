# Workflow Template Management Guide

Guide to creating and managing custom workflow templates in Claude Multi-Agent Template v5.0.

## Table of Contents

- [Overview](#overview)
- [Template Structure](#template-structure)
- [Managing Templates](#managing-templates)
- [Step Management](#step-management)
- [Transition Management](#transition-management)
- [Using Templates](#using-templates)
- [Built-in Templates](#built-in-templates)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)

---

## Overview

Workflow templates define reusable sequences of agents with explicit input/output specifications and status transitions.

### Key Benefits (v5.0)

- **Complete Orchestration** - Workflows specify everything: agents, inputs, outputs, transitions
- **Agent Reusability** - Same agent in different workflows with different inputs/outputs
- **Flexible Status Handling** - Workflows define what status codes mean
- **Self-Contained** - Template has all information needed to execute
- **User Control** - Easy to create and modify workflows via CLI

---

## Template Structure

### Complete Template Example

```json
{
  "workflows": {
    "my-workflow": {
      "name": "My Custom Workflow",
      "description": "Custom workflow for specific feature type",
      "steps": [
        {
          "agent": "requirements-analyst",
          "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
          "required_output": "analysis.md",
          "on_status": {
            "READY_FOR_DEVELOPMENT": {
              "next_step": "architect",
              "auto_chain": true
            }
          }
        },
        {
          "agent": "architect",
          "input": "{previous_step}/required_output/",
          "required_output": "design.md",
          "on_status": {
            "READY_FOR_IMPLEMENTATION": {
              "next_step": "implementer",
              "auto_chain": true
            },
            "NEEDS_RESEARCH": {
              "next_step": null,
              "auto_chain": false
            }
          }
        },
        {
          "agent": "implementer",
          "input": "{previous_step}/required_output/",
          "required_output": "implementation.md",
          "on_status": {
            "READY_FOR_TESTING": {
              "next_step": null,
              "auto_chain": false
            }
          }
        }
      ]
    }
  }
}
```

### Field Definitions

**Workflow Level**:
- `name` - Human-readable workflow name
- `description` - What this workflow is for
- `steps` - Array of agent steps (execution order)

**Step Level**:
- `agent` - Agent name (must exist in agents.json)
- `input` - File path or directory path (supports placeholders)
- `required_output` - Filename to create in `required_output/`
- `on_status` - Map of status codes to transitions

**Transition Level**:
- `next_step` - Next agent name or `null` for end
- `auto_chain` - Whether to automatically start next step

### Input Path Placeholders

- `{enhancement_name}` - Replaced with actual enhancement name
- `{previous_step}` - Replaced with previous agent's directory path

**Examples**:
```json
// First step - reads spec file
"input": "enhancements/{enhancement_name}/{enhancement_name}.md"
// Becomes: enhancements/user-profiles/user-profiles.md

// Later step - reads previous agent's output
"input": "{previous_step}/required_output/"
// Becomes: enhancements/user-profiles/architect/required_output/
```

---

## Managing Templates

### Create Template

```bash
cmat workflow create <template_name> <description>
```

**Example**:
```bash
cmat workflow create api-dev "REST API development workflow"
```

---

### List Templates

```bash
cmat workflow list
```

---

### Show Template

```bash
cmat workflow show <template_name>
```

---

### Delete Template

```bash
cmat workflow delete <template_name>
```

---

### Validate Template

```bash
cmat workflow validate <template_name>
```

**Checks**:
- All agents exist in agents.json
- All steps have input and required_output
- All transition targets exist (or are null)
- No missing fields

---

## Step Management

### Add Step

```bash
cmat workflow add-step <template> <agent> <input> <o> [position]
```

**Examples**:
```bash
# Add to end
cmat workflow add-step my-workflow architect \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "design.md"

# Insert at position 0
cmat workflow add-step my-workflow requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "analysis.md" \
    0
```

---

### Edit Step

```bash
cmat workflow edit-step <template> <step_num> [input] [output]
```

---

### Remove Step

```bash
cmat workflow remove-step <template> <step_number>
```

---

### List Steps

```bash
cmat workflow list-steps <template>
```

**Output**:
```
Steps in 'my-workflow':
  0. requirements-analyst
  1. architect
  2. implementer
```

---

### Show Step

```bash
cmat workflow show-step <template> <step_number>
```

---

## Transition Management

### Add Transition

```bash
cmat workflow add-transition <template> <step> <status> <next> [auto_chain]
```

**Examples**:
```bash
# Success transition with auto-chain
cmat workflow add-transition my-workflow 0 READY_FOR_DEVELOPMENT architect true

# Workflow end (no next step)
cmat workflow add-transition my-workflow 2 TESTING_COMPLETE null false

# Multiple transitions for same step
cmat workflow add-transition my-workflow 1 READY_FOR_IMPLEMENTATION implementer true
cmat workflow add-transition my-workflow 1 NEEDS_RESEARCH null false
```

---

### Remove Transition

```bash
cmat workflow remove-transition <template> <step> <status>
```

---

### List Transitions

```bash
cmat workflow list-transitions <template> <step>
```

**Output**:
```
Transitions for step 1:
  READY_FOR_IMPLEMENTATION → implementer (auto_chain: true)
  NEEDS_RESEARCH → END (auto_chain: false)
```

---

## Using Templates

### Start a Workflow

```bash
cmat workflow start <workflow_name> <enhancement_name>
```

**What Happens**:
1. Validates workflow template
2. Verifies enhancement spec file exists
3. Creates first task with metadata:
   - `workflow_name`: template name
   - `workflow_step`: 0
4. Auto-starts first task
5. Workflow progresses automatically based on status transitions

**Example**:
```bash
# Create enhancement spec
mkdir -p enhancements/my-feature
echo "# My Feature" > enhancements/my-feature/my-feature.md

# Start workflow
cmat workflow start new_feature_development my-feature
```

---

## Built-in Templates

### new_feature_development (5 steps)

```
requirements-analyst → architect → implementer → tester → documenter
```

**Transitions**:
- Step 0: `READY_FOR_DEVELOPMENT` → architect
- Step 1: `READY_FOR_IMPLEMENTATION` → implementer
- Step 2: `READY_FOR_TESTING` or `READY_FOR_INTEGRATION` → tester
- Step 3: `TESTING_COMPLETE` → documenter
- Step 4: `DOCUMENTATION_COMPLETE` → END

---

### bugfix_workflow (4 steps)

```
requirements-analyst → architect → implementer → tester
```

---

### hotfix_workflow (2 steps)

```
implementer → tester
```

---

### performance_optimization (4 steps)

```
tester → architect → implementer → tester
```

---

### documentation_update (3 steps)

```
requirements-analyst → documenter → tester
```

---

### refactoring_workflow (4 steps)

```
architect → implementer → tester → documenter
```

---

## Common Patterns

### Pattern: Skip Requirements

```bash
cmat workflow create no-req "Skip requirements"
cmat workflow add-step no-req architect \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "design.md"
cmat workflow add-transition no-req 0 READY_FOR_IMPLEMENTATION implementer true
# ... add remaining steps
```

---

### Pattern: Add Security Review

```bash
cmat workflow create secure-feature "Feature with security review"
cmat workflow add-step secure-feature requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "analysis.md"
cmat workflow add-step secure-feature architect \
    "{previous_step}/required_output/" \
    "design.md"
cmat workflow add-step secure-feature implementer \
    "{previous_step}/required_output/" \
    "implementation.md"
cmat workflow add-step secure-feature security-reviewer \
    "{previous_step}/required_output/" \
    "security_review.md"
cmat workflow add-step secure-feature tester \
    "{previous_step}/required_output/" \
    "tests.md"

# Add all transitions
cmat workflow add-transition secure-feature 0 READY_FOR_DEVELOPMENT architect true
cmat workflow add-transition secure-feature 1 READY_FOR_IMPLEMENTATION implementer true
cmat workflow add-transition secure-feature 2 READY_FOR_TESTING security-reviewer true
cmat workflow add-transition secure-feature 3 SECURITY_APPROVED tester true
cmat workflow add-transition secure-feature 4 TESTING_COMPLETE null false
```

---

## Best Practices

### Template Design

**DO**:
- ✅ Keep workflows focused (one purpose)
- ✅ Use descriptive template names
- ✅ Include transitions for expected statuses
- ✅ Document when to use the workflow
- ✅ Validate template before using

**DON'T**:
- ❌ Create too many similar templates
- ❌ Skip validation steps
- ❌ Use hardcoded paths (use placeholders)
- ❌ Forget to add transitions

### Status Handling

**DO**:
- ✅ Use standard status patterns (`READY_FOR_*`, `*_COMPLETE`)
- ✅ Add transitions for all expected success statuses
- ✅ Let unexpected statuses stop workflow naturally
- ✅ Use descriptive status codes

**DON'T**:
- ❌ Add transitions for every possible status
- ❌ Use vague status codes
- ❌ Forget that missing status = workflow stops

---

## Quick Reference

```bash
# Template CRUD
cmat workflow create <n> <desc>
cmat workflow list
cmat workflow show <n>
cmat workflow delete <n>
cmat workflow validate <n>

# Step management
cmat workflow add-step <n> <agent> <input> <o> [pos]
cmat workflow edit-step <n> <step> [input] [output]
cmat workflow remove-step <n> <step>
cmat workflow list-steps <n>

# Transition management
cmat workflow add-transition <n> <step> <status> <next> [auto]
cmat workflow remove-transition <n> <step> <status>
cmat workflow list-transitions <n> <step>

# Execution
cmat workflow start <workflow> <enhancement>
```

---

## See Also

- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow patterns and orchestration
- **[SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md)** - Complete command reference
- **[agents.json](.claude/agents/agents.json)** - Agent definitions

---