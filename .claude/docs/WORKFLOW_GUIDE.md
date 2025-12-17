# Workflow Guide

Complete guide to workflow orchestration and template management in CMAT.

**Version**: 8.2.0

## Table of Contents

- [Overview](#overview)
- [Workflow Architecture](#workflow-architecture)
- [Template Structure](#template-structure)
- [CLI Commands](#cli-commands)
- [Built-in Workflows](#built-in-workflows)
- [Creating Custom Workflows](#creating-custom-workflows)
- [Status Transitions](#status-transitions)
- [Output Structure](#output-structure)
- [Common Patterns](#common-patterns)
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

### Key Benefits

- **Complete Orchestration** - Workflows specify everything: agents, inputs, outputs, transitions
- **Agent Reusability** - Same agent in different workflows with different inputs/outputs
- **Flexible Status Handling** - Workflows define what status codes mean
- **Self-Contained** - Template has all information needed to execute
- **User Control** - Easy to create and modify workflows via CLI

---

## Workflow Architecture

### Design Overview

```
Workflow Template (workflow_templates.json)
  |
  +- Step 0: requirements-analyst
  |    +- input: "enhancements/{name}/{name}.md"
  |    +- required_output: "analysis.md"
  |    +- on_status:
  |         +- READY_FOR_DEVELOPMENT -> Step 1
  |
  +- Step 1: architect
  |    +- input: "{previous_step}/required_output/"
  |    +- required_output: "design.md"
  |    +- on_status:
  |         +- READY_FOR_IMPLEMENTATION -> Step 2
  |
  +- Step 2: implementer
       +- input: "{previous_step}/required_output/"
       +- required_output: "implementation.md"
       +- on_status:
            +- READY_FOR_TESTING -> null (end)
```

### Task Metadata

Each task carries workflow context:

```json
{
  "workflow_name": "new-feature-development",
  "workflow_step": 0
}
```

### Auto-Chain Process

When an agent completes:
1. System reads `workflow_name` and `workflow_step` from task metadata
2. Loads workflow template
3. Checks if output status exists in current step's `on_status`
4. If found and `auto_chain: true` -> creates and starts next task
5. If not found -> stops workflow

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
| Field | Description |
|-------|-------------|
| `name` | Human-readable workflow name |
| `description` | What this workflow is for |
| `steps` | Array of agent steps (execution order) |

**Step Level**:
| Field | Description |
|-------|-------------|
| `agent` | Agent name (must exist in agents.json) |
| `input` | File or directory path (supports placeholders) |
| `required_output` | Filename to create in `required_output/` |
| `on_status` | Map of status codes to transitions |

**Transition Level**:
| Field | Description |
|-------|-------------|
| `next_step` | Next agent name or `null` for end |
| `auto_chain` | Whether to automatically start next step |

### Input Path Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{enhancement_name}` | Enhancement directory name | `user-profiles` |
| `{previous_step}` | Previous agent's directory path | `enhancements/user-profiles/architect` |

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

## CLI Commands

### Workflow Operations

```bash
# List all workflows
python -m cmat workflow list

# Show workflow details
python -m cmat workflow show <workflow_name>

# Start a workflow
python -m cmat workflow start <workflow_name> <enhancement_name>

# Validate a workflow template
python -m cmat workflow validate <workflow_name>
```

### Example Session

```bash
# See available workflows
python -m cmat workflow list

# Examine a workflow
python -m cmat workflow show new-feature-development

# Start the workflow
python -m cmat workflow start new-feature-development my-feature

# Monitor progress
python -m cmat queue status
python -m cmat queue list active
```

---

## Built-in Workflows

### new-feature-development (5 steps)

```
requirements-analyst -> architect -> implementer -> tester -> documenter
```

**Use For**:
- New features
- Major enhancements
- User-facing changes requiring documentation

**Transitions**:
- Step 0: `READY_FOR_DEVELOPMENT` -> architect
- Step 1: `READY_FOR_IMPLEMENTATION` -> implementer
- Step 2: `READY_FOR_TESTING` -> tester
- Step 3: `TESTING_COMPLETE` -> documenter
- Step 4: `DOCUMENTATION_COMPLETE` -> END

**Start Command**:
```bash
python -m cmat workflow start new-feature-development feature-name
```

---

### bugfix-workflow (4 steps)

```
requirements-analyst -> architect -> implementer -> tester
```

**Use For**:
- Bug fixes requiring analysis
- Issues needing design consideration

---

### hotfix-workflow (2 steps)

```
implementer -> tester
```

**Use For**:
- Critical production issues
- Emergency fixes
- Simple, obvious bugs

---

### performance-optimization (4 steps)

```
tester -> architect -> implementer -> tester
```

**Use For**:
- Performance improvements
- Optimization work

**Note**: Starts with tester to establish baseline metrics.

---

### documentation-update (3 steps)

```
requirements-analyst -> documenter -> tester
```

**Use For**:
- Documentation-only updates
- Guide creation

---

### refactoring-workflow (4 steps)

```
architect -> implementer -> tester -> documenter
```

**Use For**:
- Code refactoring
- Technical debt reduction

---

## Creating Custom Workflows

### Step-by-Step Guide

1. **Plan your workflow** - Decide which agents in which order
2. **Create the template** - Add to `workflow_templates.json`
3. **Define steps** - Specify input/output for each agent
4. **Add transitions** - Map status codes to next steps
5. **Validate** - Check for errors
6. **Test** - Run with a sample enhancement

### Example: API Development Workflow

Edit `.claude/data/workflow_templates.json`:

```json
{
  "workflows": {
    "api-development": {
      "name": "API Development",
      "description": "REST API endpoint development workflow",
      "steps": [
        {
          "agent": "requirements-analyst",
          "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
          "required_output": "endpoint_spec.md",
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
          "required_output": "api_design.md",
          "on_status": {
            "READY_FOR_IMPLEMENTATION": {
              "next_step": "implementer",
              "auto_chain": true
            }
          }
        },
        {
          "agent": "implementer",
          "input": "{previous_step}/required_output/",
          "required_output": "endpoint_impl.md",
          "on_status": {
            "READY_FOR_TESTING": {
              "next_step": "tester",
              "auto_chain": true
            }
          }
        },
        {
          "agent": "tester",
          "input": "{previous_step}/required_output/",
          "required_output": "api_tests.md",
          "on_status": {
            "TESTING_COMPLETE": {
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

Then validate and use:

```bash
python -m cmat workflow validate api-development
python -m cmat workflow start api-development add-payment-endpoint
```

---

## Status Transitions

### How Transitions Work

1. Agent outputs a completion block with status code
2. System reads workflow template and current step
3. System checks if status exists in step's `on_status` map
4. If **found** -> Get `next_step` and `auto_chain` settings
5. If **not found** -> Stop workflow

**Simple Rule**: Status in `on_status` -> continue. Status not in `on_status` -> stop.

### Standard Status Codes

**Completion Statuses** (workflow continues):
| Status | Description | Typical Next Step |
|--------|-------------|-------------------|
| `READY_FOR_DEVELOPMENT` | Requirements analysis complete | architect |
| `READY_FOR_IMPLEMENTATION` | Architecture/design complete | implementer |
| `READY_FOR_TESTING` | Code complete | tester |
| `TESTING_COMPLETE` | Tests passed | documenter or END |
| `DOCUMENTATION_COMPLETE` | Docs finished | END |

**Halt Statuses** (workflow stops):
| Status | Description | Action Required |
|--------|-------------|-----------------|
| `BLOCKED: <reason>` | Cannot proceed | Resolve blocker |
| `NEEDS_CLARIFICATION: <what>` | Need more info | Provide clarification |
| `TESTS_FAILED: <details>` | Tests didn't pass | Fix failures |
| `BUILD_FAILED` | Build errors | Fix build |

### Defining Transitions

Each step can have multiple transitions for different outcomes:

```json
{
  "agent": "architect",
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
}
```

---

## Output Structure

### Directory Convention

All agents use standardized output structure:

```
enhancements/{enhancement_name}/{agent}/
+-- required_output/
|   +-- {workflow-specified-filename}
+-- optional_output/
    +-- [agent's additional files]
```

**Workflow Specifies**:
- Input path (file or directory)
- Required output filename

**Agent Creates**:
- `required_output/` directory
- Required file in that directory
- Optional files in `optional_output/`

### Example Flow

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

## Common Patterns

### Skip Requirements Analysis

For well-defined features where requirements are already clear:

```json
{
  "skip-analysis": {
    "name": "Skip Analysis Workflow",
    "description": "Start directly with architecture",
    "steps": [
      {
        "agent": "architect",
        "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
        "required_output": "design.md",
        "on_status": {
          "READY_FOR_IMPLEMENTATION": {
            "next_step": "implementer",
            "auto_chain": true
          }
        }
      }
    ]
  }
}
```

### Add Security Review

Insert a security review step before testing:

```json
{
  "agent": "implementer",
  "on_status": {
    "READY_FOR_TESTING": {
      "next_step": "code-reviewer",
      "auto_chain": true
    }
  }
},
{
  "agent": "code-reviewer",
  "input": "{previous_step}/required_output/",
  "required_output": "security_review.md",
  "on_status": {
    "SECURITY_APPROVED": {
      "next_step": "tester",
      "auto_chain": true
    }
  }
}
```

### Multiple Outcomes

Handle different agent outcomes:

```json
{
  "agent": "tester",
  "on_status": {
    "TESTING_COMPLETE": {
      "next_step": "documenter",
      "auto_chain": true
    },
    "TESTS_FAILED": {
      "next_step": null,
      "auto_chain": false
    }
  }
}
```

---

## Best Practices

### Workflow Design

**DO**:
- Keep workflows focused (single purpose)
- Include minimum necessary steps
- Use standard status codes
- Always include a testing step
- Document when to use the workflow

**DON'T**:
- Create too many similar workflows
- Skip testing steps
- Use vague status codes
- Make workflows too generic

### Status Handling

**DO**:
- Use standard status patterns (`READY_FOR_*`, `*_COMPLETE`)
- Add transitions for all expected success statuses
- Let unexpected statuses stop workflow naturally
- Use descriptive status codes

**DON'T**:
- Add transitions for every possible status
- Use vague status codes
- Forget that missing status = workflow stops

### Choosing the Right Workflow

| Scenario | Recommended Workflow |
|----------|---------------------|
| New feature, unclear requirements | new-feature-development |
| Bug with known fix | hotfix-workflow |
| Bug needing investigation | bugfix-workflow |
| Performance issue | performance-optimization |
| Documentation only | documentation-update |
| Code cleanup | refactoring-workflow |

---

## Troubleshooting

### Workflow Won't Start

**Check**:
```bash
# Workflow exists?
python -m cmat workflow list

# Template valid?
python -m cmat workflow validate <workflow>

# Enhancement spec exists?
ls enhancements/<name>/<name>.md
```

### Workflow Stops Unexpectedly

**Diagnosis**:
```bash
# Check last task status
python -m cmat queue list completed

# View task details
python -m cmat queue show <task_id>
```

**Common Causes**:
- Agent output status not in `on_status` map
- Validation failed (missing required output)
- Agent output `BLOCKED` or error status

### Output Validation Fails

**Check**:
```bash
# Verify directory structure
ls -la enhancements/<feature>/<agent>/

# Should see: required_output/ directory

# Check required file exists
ls enhancements/<feature>/<agent>/required_output/
```

---

## Quick Reference

```bash
# Workflow operations
python -m cmat workflow list
python -m cmat workflow show <name>
python -m cmat workflow start <name> <enhancement>
python -m cmat workflow validate <name>

# Queue monitoring
python -m cmat queue status
python -m cmat queue list active
python -m cmat queue list completed
```

---

## See Also

- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** - Complete command reference
- **[QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md)** - Task queue management
- **[PROMPT_SYSTEM_GUIDE.md](PROMPT_SYSTEM_GUIDE.md)** - Prompt construction and status reporting
- **[ENHANCEMENT_GUIDE.md](ENHANCEMENT_GUIDE.md)** - Creating enhancement specs