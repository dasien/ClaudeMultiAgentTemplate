# Workflow Guide

This guide describes workflow patterns and orchestration in the multi-agent system v5.0.

## Table of Contents

- [Overview](#overview)
- [Workflow Architecture](#workflow-architecture)
- [Command Reference](#command-reference)
- [Standard Workflows](#standard-workflows)
- [Creating Custom Workflows](#creating-custom-workflows)
- [Output Structure](#output-structure)
- [Status Transitions](#status-transitions)
- [Integration with External Systems](#integration-with-external-systems)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The multi-agent system uses **workflow templates** to orchestrate agent sequences. Workflows define:
- Which agents execute in which order
- What inputs each agent receives
- What outputs each agent must produce
- How status codes trigger transitions

**Key Principle**: Workflows are the source of truth for orchestration. Agents are reusable components that workflows connect together.

---

## Workflow Architecture

### Workflow-Based Design (v5.0)

```
Workflow Template (workflow_templates.json)
  ├─ Step 0: requirements-analyst
  │    ├─ input: "enhancements/{name}/{name}.md"
  │    ├─ required_output: "analysis.md"
  │    └─ on_status:
  │         └─ READY_FOR_DEVELOPMENT → Step 1
  │
  ├─ Step 1: architect
  │    ├─ input: "{previous_step}/required_output/"
  │    ├─ required_output: "design.md"
  │    └─ on_status:
  │         └─ READY_FOR_IMPLEMENTATION → Step 2
  │
  └─ Step 2: implementer
       ├─ input: "{previous_step}/required_output/"
       ├─ required_output: "implementation.md"
       └─ on_status:
            └─ READY_FOR_TESTING → null (end)
```

**Task Metadata** carries workflow context:
```json
{
  "workflow_name": "new_feature_development",
  "workflow_step": 0
}
```

**Hook** uses workflow to determine next steps:
1. Get workflow_name and workflow_step from task metadata
2. Load workflow template
3. Check if status exists in current step's `on_status`
4. If yes → create next task with step+1
5. If no → stop workflow

---

## Command Reference

### Starting Workflows

```bash
# Start a workflow from the beginning
cmat workflow start <workflow_name> <enhancement_name>

# Example
cmat workflow start new_feature_development user-profiles
```

### Managing Templates

```bash
# Create new template
cmat workflow create <name> <description>

# Add steps
cmat workflow add-step <name> <agent> <input> <output> [position]

# Add transitions
cmat workflow add-transition <name> <step> <status> <next_agent> [auto_chain]

# Validate template
cmat workflow validate <name>

# View template
cmat workflow show <name>
```

### Example: Creating a Custom Workflow

```bash
# 1. Create template
cmat workflow create quick-impl "Quick implementation workflow"

# 2. Add steps
cmat workflow add-step quick-impl architect \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "design.md"

cmat workflow add-step quick-impl implementer \
    "{previous_step}/required_output/" \
    "code.md"

cmat workflow add-step quick-impl tester \
    "{previous_step}/required_output/" \
    "tests.md"

# 3. Add transitions
cmat workflow add-transition quick-impl 0 READY_FOR_IMPLEMENTATION implementer true
cmat workflow add-transition quick-impl 1 READY_FOR_TESTING tester true
cmat workflow add-transition quick-impl 2 TESTING_COMPLETE null false

# 4. Validate
cmat workflow validate quick-impl

# 5. Use it
cmat workflow start quick-impl my-feature
```

---

## Standard Workflows

### new_feature_development

**Steps**: requirements-analyst → architect → implementer → tester → documenter (5 steps)

**Use For**:
- New features
- Major enhancements
- User-facing changes requiring documentation

**Duration**: 6-12 hours total

**Start Command**:
```bash
cmat workflow start new_feature_development feature-name
```

---

### bugfix_workflow

**Steps**: requirements-analyst → architect → implementer → tester (4 steps)

**Use For**:
- Bug fixes requiring analysis
- Issues needing design consideration

**Duration**: 2-4 hours total

---

### hotfix_workflow

**Steps**: implementer → tester (2 steps)

**Use For**:
- Critical production issues
- Emergency fixes
- Simple, obvious bugs

**Duration**: 1-2 hours total

---

### performance_optimization

**Steps**: tester → architect → implementer → tester (4 steps)

**Use For**:
- Performance improvements
- Optimization work

**Duration**: 3-5 hours total

**Note**: Starts with tester to establish baseline

---

### documentation_update

**Steps**: requirements-analyst → documenter → tester (3 steps)

**Use For**:
- Documentation-only updates
- Guide creation

**Duration**: 2-3 hours total

---

### refactoring_workflow

**Steps**: architect → implementer → tester → documenter (4 steps)

**Use For**:
- Code refactoring
- Technical debt reduction

**Duration**: 4-8 hours total

---

## Creating Custom Workflows

See complete guide: [WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md)

Quick example:
```bash
# Create API-focused workflow
cmat workflow create api-endpoint "REST API endpoint development"

cmat workflow add-step api-endpoint requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "endpoint_spec.md"

cmat workflow add-step api-endpoint architect \
    "{previous_step}/required_output/" \
    "api_design.md"

cmat workflow add-step api-endpoint implementer \
    "{previous_step}/required_output/" \
    "endpoint_impl.md"

cmat workflow add-step api-endpoint tester \
    "{previous_step}/required_output/" \
    "api_tests.md"

# Add transitions
cmat workflow add-transition api-endpoint 0 READY_FOR_DEVELOPMENT architect true
cmat workflow add-transition api-endpoint 1 READY_FOR_IMPLEMENTATION implementer true
cmat workflow add-transition api-endpoint 2 READY_FOR_TESTING tester true
cmat workflow add-transition api-endpoint 3 TESTING_COMPLETE null false

# Use it
cmat workflow start api-endpoint add-payment-endpoint
```

---

## Output Structure

### Directory Convention (v5.0)

All agents use standardized output structure:

```
enhancements/{enhancement_name}/{agent}/
├── required_output/
│   └── {workflow-specified-filename}
└── optional_output/
    └── [agent's additional files]
```

**Workflow Specifies**:
- Input path (file or directory)
- Required output filename

**Agent Creates**:
- `required_output/` directory
- Required file in that directory
- Optional files in `optional_output/`

**Example Flow**:
```
Step 0: requirements-analyst
  Input:  enhancements/my-feature/my-feature.md (file)
  Output: enhancements/my-feature/requirements-analyst/required_output/analysis.md

Step 1: architect
  Input:  enhancements/my-feature/requirements-analyst/required_output/ (directory)
  Output: enhancements/my-feature/architect/required_output/design.md

Step 2: implementer
  Input:  enhancements/my-feature/architect/required_output/ (directory)
  Output: enhancements/my-feature/implementer/required_output/implementation.md
```

---

## Status Transitions

### How Status Transitions Work

1. Agent outputs a status code (e.g., `READY_FOR_IMPLEMENTATION`)
2. Hook reads workflow template and current step
3. Hook checks if status exists in step's `on_status` map
4. If **found** → Get `next_step` and `auto_chain` settings
5. If **not found** → Stop workflow

**Simple Rule**: Status in `on_status` → continue. Status not in `on_status` → stop.

### Common Status Patterns

**Success Statuses**:
- `READY_FOR_DEVELOPMENT` - Requirements complete
- `READY_FOR_IMPLEMENTATION` - Architecture complete
- `READY_FOR_TESTING` - Code complete
- `TESTING_COMPLETE` - Tests passed
- `DOCUMENTATION_COMPLETE` - Docs finished

**Blocking Statuses**:
- `BLOCKED: <reason>` - Cannot proceed
- `NEEDS_CLARIFICATION: <what>` - Need more info
- `TESTS_FAILED: <details>` - Tests didn't pass

**Example Workflow Step**:
```json
{
  "agent": "architect",
  "input": "{previous_step}/required_output/",
  "required_output": "design.md",
  "on_status": {
    "READY_FOR_IMPLEMENTATION": {
      "next_step": "implementer",
      "auto_chain": true
    }
  }
}
```

If architect outputs anything other than `READY_FOR_IMPLEMENTATION`, workflow stops.

---

## Integration with External Systems

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for complete setup.

**Quick Overview**:
```bash
# Control integration behavior
export AUTO_INTEGRATE="always"  # Auto-create integration tasks
export AUTO_INTEGRATE="never"   # Skip integration
export AUTO_INTEGRATE="prompt"  # Ask each time (default)

# Manual sync
cmat integration sync <task_id>
cmat integration sync-all
```

---

## Best Practices

### Starting a New Feature

1. **Create Enhancement Spec**: `enhancements/feature/feature.md`
2. **Choose Workflow**: Use built-in or create custom
3. **Start Workflow**: `cmat workflow start <workflow> <feature>`
4. **Monitor**: `cmat queue status`

### Choosing the Right Workflow

**Use new_feature_development** when:
- Requirements unclear
- Complex architecture needed
- User-facing changes
- Need comprehensive documentation

**Use hotfix_workflow** when:
- Production emergency
- Fix is simple and obvious
- Speed is critical

**Create custom workflow** when:
- Repeated pattern specific to your domain
- Need specialized agent sequence
- Built-in workflows don't fit

### Workflow Design Principles

**DO**:
- ✅ Keep workflows focused (single purpose)
- ✅ Include minimum necessary steps
- ✅ Use standard status codes
- ✅ Always include testing step
- ✅ Document when to use the workflow

**DON'T**:
- ❌ Create too many similar workflows
- ❌ Skip testing steps
- ❌ Use vague status codes
- ❌ Make workflows too generic

---

## Troubleshooting

### Workflow Won't Start

**Check**:
```bash
# Workflow exists?
cmat workflow list

# Template valid?
cmat workflow validate <workflow>

# Enhancement spec exists?
ls enhancements/<name>/<name>.md
```

### Workflow Stops Unexpectedly

**Diagnosis**:
```bash
# Check last task status
cmat queue list completed | jq '.[-1]'

# View task log
tail -100 enhancements/*/logs/*.log

# Check if status in workflow
cmat workflow show <workflow> | grep "status-code"
```

**Common Causes**:
- Agent output status not in `on_status` map
- Validation failed (missing required output)
- Agent output `BLOCKED` or error status

### Output Validation Fails

**Check**:
```bash
# Verify directory structure
ls -la enhancements/feature/agent/

# Should see: required_output/ directory

# Check required file
ls enhancements/feature/agent/required_output/

# Check metadata header
head -10 enhancements/feature/agent/required_output/file.md
```

---


## Quick Reference

```bash
# Workflow template management
cmat workflow create <n> <desc>
cmat workflow list
cmat workflow show <name>
cmat workflow validate <name>
cmat workflow start <name> <enhancement>

# Step management
cmat workflow add-step <n> <agent> <input> <output>
cmat workflow edit-step <n> <step> [input] [output]
cmat workflow remove-step <n> <step>

# Transition management
cmat workflow add-transition <n> <step> <status> <next> [auto]
cmat workflow list-transitions <n> <step>

# Queue operations
cmat queue status
cmat queue list <type>
```

---

**For complete workflow template documentation, see [WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md)**