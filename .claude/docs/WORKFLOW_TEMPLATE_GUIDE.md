# Workflow Template Management Guide

Guide to creating and managing custom workflow templates in Claude Multi-Agent Template v4.1.

## Table of Contents

- [Overview](#overview)
- [What Are Workflow Templates](#what-are-workflow-templates)
- [Template Structure](#template-structure)
- [Managing Templates](#managing-templates)
- [Using Templates](#using-templates)
- [Built-in Templates](#built-in-templates)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Workflow templates define reusable sequences of agents that can be applied to different enhancements. Instead of manually creating each task in a workflow, you define the sequence once and reference it when needed.

### Key Benefits

- **Reusability**: Define once, use many times
- **Consistency**: Same workflow for similar features
- **Simplicity**: Just reference template name instead of creating multiple tasks
- **Discovery**: List available workflows to find appropriate pattern
- **Customization**: Create project-specific workflows

---

## What Are Workflow Templates

A workflow template is a named sequence of agent steps stored in `workflow_templates.json`.

### Template Components

**Basic Structure**:
```json
{
  "my-workflow": {
    "name": "My Custom Workflow",
    "description": "Custom workflow for specific feature type",
    "steps": [
      {
        "agent": "architect",
        "task": "Design architecture",
        "description": "Design system architecture"
      },
      {
        "agent": "implementer",
        "task": "Implement code",
        "description": "Write production code"
      }
    ],
    "created": "2025-11-15T10:00:00Z"
  }
}
```

**Fields**:
- `name` - Human-readable workflow name
- `description` - What this workflow is for
- `steps` - Array of agent steps
- `created` - When template was created

**Step Fields**:
- `agent` - Agent name (must exist in agent_contracts.json)
- `task` - Task title for this step
- `description` - What this step does
- `estimated_duration` - (optional) How long step typically takes
- `deliverables` - (optional) What this step produces

---

## Managing Templates

### Create New Template

```bash
cmat workflow create <template_name> <description>
```

**Example**:
```bash
cmat workflow create api-dev "REST API development workflow"
```

**Output**:
```
✅ Created workflow template: api-dev
```

**Result**: Empty template created in `workflow_templates.json`

---

### Add Steps to Template

```bash
cmat workflow add-step <template_name> <agent> [--position=N]
```

**Examples**:
```bash
# Add steps in order (appends to end by default)
cmat workflow add-step api-dev requirements-analyst
cmat workflow add-step api-dev architect
cmat workflow add-step api-dev implementer
cmat workflow add-step api-dev tester

# Insert at specific position (0-indexed)
cmat workflow add-step api-dev documenter --position=4

# Insert at beginning
cmat workflow add-step my-workflow requirements-analyst --position=0
```

**Validation**:
- Agent must exist in `agent_contracts.json`
- Position must be valid (0 to current step count)

---

### Remove Steps from Template

```bash
cmat workflow remove-step <template_name> <step_number>
```

**Examples**:
```bash
# View current steps
cmat workflow list-steps api-dev
# Output:
# Steps in 'api-dev':
#   1. requirements-analyst
#   2. architect
#   3. implementer
#   4. tester
#   5. documenter

# Remove step 5 (documenter)
cmat workflow remove-step api-dev 5

# Verify
cmat workflow list-steps api-dev
# Now shows only steps 1-4
```

**Notes**:
- Steps numbered 1-N for user display (1-indexed)
- Remaining steps automatically renumber after removal

---

### List All Templates

```bash
cmat workflow list
```

**Output**:
```
new_feature_development - Complete workflow for implementing a new feature (5 steps)
bugfix_workflow - Workflow for fixing bugs (4 steps)
hotfix_workflow - Fast-track workflow for critical issues (2 steps)
api-dev - REST API development workflow (4 steps)
```

---

### Show Template Details

```bash
cmat workflow show <template_name>
```

**Example**:
```bash
cmat workflow show api-dev
```

**Output**:
```
Template: api-dev
Description: REST API development workflow
Steps: 4
Created: 2025-11-15T10:00:00Z

Steps:
  requirements-analyst → architect → implementer → tester
```

---

### List Template Steps

```bash
cmat workflow list-steps <template_name>
```

**Example**:
```bash
cmat workflow list-steps api-dev
```

**Output**:
```
Steps in 'api-dev':
  1. requirements-analyst
  2. architect
  3. implementer
  4. tester
```

---

### Show Step Details

```bash
cmat workflow show-step <template_name> <step_number>
```

**Example**:
```bash
cmat workflow show-step api-dev 2
```

**Output**:
```
Step 2 of 'api-dev':
  AGENT: architect
  TASK: Execute architect
  DESCRIPTION: Designs system architecture and technical specifications
```

---

### Delete Template

```bash
cmat workflow delete <template_name>
```

**Example**:
```bash
cmat workflow delete api-dev
```

**Output**:
```
✅ Deleted workflow template: api-dev
```

**Warning**: Deletion is permanent!

---

## Using Templates

### Current Usage (v4.1)

Templates are metadata that external systems (like MultiAgentUI) use to create task sequences.

**UI Integration**:
1. UI calls `cmat workflow list` to populate dropdown
2. User selects template
3. UI calls `cmat workflow show <template>` to preview steps
4. UI creates individual tasks for each step
5. User starts first task, workflow chains automatically

### Example: UI Using Templates

```javascript
// 1. Get available templates
const templates = await exec('cmat workflow list');

// 2. User selects "api-dev"
const template = await exec('cmat workflow show api-dev');

// 3. Parse steps
const steps = parseSteps(template); // ["requirements-analyst", "architect", "implementer", "tester"]

// 4. Create first task with auto-chain enabled
const taskId = await exec(`cmat queue add 
  "API Feature" 
  "${steps[0]}" 
  "high" 
  "analysis" 
  "enhancements/api-feature/api-feature.md" 
  "Start API workflow" 
  true 
  true`);

// 5. Start task - workflow will auto-chain through all steps
await exec(`cmat queue start ${taskId}`);
```

### Future: Direct Execution (Planned)

```bash
# Not yet implemented - planned for future version
cmat workflow execute <template_name> <enhancement_name> [--auto-complete] [--auto-chain]

# Would automatically:
# 1. Validate template
# 2. Create first task
# 3. Start workflow
# 4. Chain through all steps
```

---

## Built-in Templates

The system includes several predefined templates in `workflow_templates.json`:

### new_feature_development

**Steps**: requirements-analyst → architect → implementer → tester → documenter (5 steps)

**Use For**:
- New features with unclear requirements
- Complex changes needing architectural design
- User-facing changes requiring documentation

**Duration**: 6-12 hours total

---

### bugfix_workflow

**Steps**: requirements-analyst → architect → implementer → tester (4 steps)

**Use For**:
- Bug fixes requiring analysis
- Issues needing design consideration
- Bugs affecting multiple components

**Duration**: 2-4 hours total

**Note**: Documentation usually skipped for bugs

---

### hotfix_workflow

**Steps**: implementer → tester (2 steps)

**Use For**:
- Critical production issues
- Emergency fixes
- Simple, obvious bugs

**Duration**: 1-2 hours total

**Note**: Requirements and architecture skipped for speed

---

### performance_optimization

**Steps**: tester → architect → implementer → tester (4 steps)

**Use For**:
- Performance improvements
- Optimization work
- Profiling-driven changes

**Duration**: 3-5 hours total

**Note**: Starts with tester to establish baseline

---

### documentation_update

**Steps**: requirements-analyst → documenter → tester (3 steps)

**Use For**:
- Documentation-only updates
- Guide creation
- Example updates

**Duration**: 2-3 hours total

**Note**: Tester validates examples work

---

### refactoring_workflow

**Steps**: architect → implementer → tester → documenter (4 steps)

**Use For**:
- Code refactoring
- Technical debt reduction
- Structural improvements

**Duration**: 4-8 hours total

**Note**: Requirements skipped since functionality doesn't change

---

## Common Patterns

### Pattern 1: Skip Requirements

For well-understood changes, start with architect:

```bash
cmat workflow create no-req "Skip requirements workflow"
cmat workflow add-step no-req architect
cmat workflow add-step no-req implementer
cmat workflow add-step no-req tester
```

**Use When**:
- Requirements are crystal clear
- Following established patterns
- Small, focused changes

---

### Pattern 2: Skip Documentation

For internal-only changes:

```bash
cmat workflow create no-docs "Internal changes workflow"
cmat workflow add-step no-docs requirements-analyst
cmat workflow add-step no-docs architect
cmat workflow add-step no-docs implementer
cmat workflow add-step no-docs tester
```

**Use When**:
- Internal refactoring
- No API changes
- Technical debt work

---

### Pattern 3: Documentation Focus

For docs-only updates:

```bash
cmat workflow create docs-focus "Documentation workflow"
cmat workflow add-step docs-focus requirements-analyst
cmat workflow add-step docs-focus documenter
cmat workflow add-step docs-focus tester  # Validates examples work
```

**Use When**:
- Updating guides
- Adding examples
- Documentation improvements

---

### Pattern 4: Security Review

Add security step to standard workflow:

```bash
cmat workflow create secure-feature "Feature with security review"
cmat workflow add-step secure-feature requirements-analyst
cmat workflow add-step secure-feature architect
cmat workflow add-step secure-feature implementer
cmat workflow add-step secure-feature security-reviewer  # Custom agent
cmat workflow add-step secure-feature tester
cmat workflow add-step secure-feature documenter
```

**Use When**:
- Authentication/authorization changes
- Sensitive data handling
- Cryptography implementation

**Note**: Requires custom `security-reviewer` agent

---

## Best Practices

### Template Naming

**DO**:
- ✅ Use lowercase-with-hyphens: `api-development`, `quick-fix`
- ✅ Be descriptive: `secure-feature` not `workflow1`
- ✅ Indicate purpose: `docs-only`, `no-requirements`

**DON'T**:
- ❌ Use spaces: `my workflow` (use `my-workflow`)
- ❌ Use generic names: `workflow1`, `custom`
- ❌ Use special characters: `my_workflow#1`

### Template Design

**DO**:
- ✅ Keep templates focused (one purpose)
- ✅ Include minimum necessary steps
- ✅ Order steps logically
- ✅ Document when to use template (in description)

**DON'T**:
- ❌ Create too many similar templates
- ❌ Include unnecessary steps
- ❌ Make templates too generic
- ❌ Skip validation (tester) steps

### Template Organization

**Recommended Approach**:
```bash
# General-purpose (built-in)
- new_feature_development
- bugfix_workflow
- hotfix_workflow

# Domain-specific (custom)
- api-endpoint-dev
- ui-component-dev
- database-migration
- security-feature

# Special-purpose (custom)
- docs-only
- performance-tuning
- refactoring-only
```

**Strategy**:
1. Start with built-in templates
2. Identify patterns in your work
3. Create templates for repeated workflows
4. Keep template count manageable (5-10 max)

---

## Workflow Template Examples

### Example 1: API Endpoint Development

```bash
# Create template
cmat workflow create api-endpoint "REST API endpoint development"

# Add steps
cmat workflow add-step api-endpoint requirements-analyst  # Define endpoint contract
cmat workflow add-step api-endpoint architect             # Design API structure
cmat workflow add-step api-endpoint implementer           # Implement endpoint
cmat workflow add-step api-endpoint tester               # Test endpoint
cmat workflow add-step api-endpoint documenter           # Document API

# View result
cmat workflow show api-endpoint

# Output:
# Template: api-endpoint
# Description: REST API endpoint development
# Steps: 5
# Steps:
#   requirements-analyst → architect → implementer → tester → documenter
```

**Use For**: Adding new REST API endpoints

---

### Example 2: UI Component Development

```bash
# Create template
cmat workflow create ui-component "UI component development"

# Add steps
cmat workflow add-step ui-component requirements-analyst  # Define component requirements
cmat workflow add-step ui-component architect             # Design component structure
cmat workflow add-step ui-component implementer           # Build component
cmat workflow add-step ui-component tester               # Test component
cmat workflow add-step ui-component documenter           # Document usage

# View
cmat workflow show ui-component
```

**Use For**: Creating reusable UI components

---

### Example 3: Database Migration

```bash
# Create template
cmat workflow create db-migration "Database schema migration"

# Add steps (skip requirements for schema changes)
cmat workflow add-step db-migration architect      # Design migration strategy
cmat workflow add-step db-migration implementer    # Write migration scripts
cmat workflow add-step db-migration tester        # Test migration up/down
cmat workflow add-step db-migration documenter    # Document schema changes

# View
cmat workflow show db-migration
```

**Use For**: Database schema changes, migrations

---

### Example 4: Quick Bug Fix

```bash
# Create template
cmat workflow create quick-bugfix "Fast bug fix workflow"

# Add minimal steps
cmat workflow add-step quick-bugfix implementer  # Fix the bug
cmat workflow add-step quick-bugfix tester      # Verify fix works

# View
cmat workflow show quick-bugfix
```

**Use For**: Simple, obvious bugs that don't need analysis or architecture

---

### Example 5: Documentation Update

```bash
# Create template
cmat workflow create doc-update "Documentation update workflow"

# Add steps
cmat workflow add-step doc-update requirements-analyst  # Identify what needs documenting
cmat workflow add-step doc-update documenter           # Write/update docs
cmat workflow add-step doc-update tester              # Validate examples work

# View
cmat workflow show doc-update
```

**Use For**: Documentation improvements, guide creation

---

## Template Modification

### Inspecting Templates

```bash
# List all available templates
cmat workflow list

# Show template overview
cmat workflow show api-endpoint

# List steps with numbers
cmat workflow list-steps api-endpoint

# Show specific step details
cmat workflow show-step api-endpoint 3
```

### Modifying Existing Templates

```bash
# Clone built-in template for customization
# (Currently: manually copy in workflow_templates.json)

# Remove unwanted step
cmat workflow remove-step api-endpoint 5  # Remove documenter

# Add step at specific position
cmat workflow add-step api-endpoint security-reviewer --position=3

# Verify changes
cmat workflow list-steps api-endpoint
```

### Cleaning Up Templates

```bash
# List templates to find unused ones
cmat workflow list

# Delete template
cmat workflow delete old-template
```

---

## Using Templates

### In MultiAgentUI (Primary Use Case)

**Workflow**:
1. User clicks "New Enhancement"
2. UI shows dropdown of templates from `cmat workflow list`
3. User selects template (e.g., "api-endpoint")
4. UI calls `cmat workflow show api-endpoint` to get steps
5. UI creates task queue based on steps
6. UI starts first task with auto-chain enabled
7. Workflow executes automatically through all steps

### Manual Task Creation

Reference template in task metadata:

```bash
# Create first task referencing template
TASK_ID=$(cmat queue add \
  "Add user profile endpoint" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/user-profile/user-profile.md" \
  "Start API endpoint workflow" \
  true \
  true)

# Store template reference (optional, for tracking)
cmat queue metadata $TASK_ID workflow_template "api-endpoint"

# Start workflow
cmat queue start $TASK_ID
```

---

## Built-in Templates Reference

### Viewing Built-in Templates

```bash
# See what's available
cmat workflow list

# Inspect template structure
cmat workflow show new_feature_development

# See all steps
cmat workflow list-steps new_feature_development

# View specific step
cmat workflow show-step new_feature_development 3
```

### Template Details

#### new_feature_development
- **Steps**: 5 (requirements-analyst → architect → implementer → tester → documenter)
- **Duration**: 6-12 hours
- **Use For**: New features, major enhancements

#### bugfix_workflow
- **Steps**: 4 (requirements-analyst → architect → implementer → tester)
- **Duration**: 2-4 hours
- **Use For**: Bug fixes needing analysis

#### hotfix_workflow
- **Steps**: 2 (implementer → tester)
- **Duration**: 1-2 hours
- **Use For**: Emergency fixes

#### performance_optimization
- **Steps**: 4 (tester → architect → implementer → tester)
- **Duration**: 3-5 hours
- **Use For**: Performance improvements

#### documentation_update
- **Steps**: 3 (requirements-analyst → documenter → tester)
- **Duration**: 2-3 hours
- **Use For**: Documentation work

#### refactoring_workflow
- **Steps**: 4 (architect → implementer → tester → documenter)
- **Duration**: 4-8 hours
- **Use For**: Code refactoring

---

## Best Practices

### When to Create Templates

**Create templates for**:
- ✅ Repeated workflow patterns (3+ uses)
- ✅ Project-specific workflows
- ✅ Team-standard processes
- ✅ Domain-specific patterns (API dev, UI work, etc.)

**Don't create templates for**:
- ❌ One-off workflows
- ❌ Highly variable workflows
- ❌ Experimental workflows still being refined

### Template Quality

**Good Templates**:
- Clear purpose in description
- Logical step sequence
- Appropriate for multiple enhancements
- 2-6 steps (focused scope)

**Poor Templates**:
- Vague description
- Too many steps (>7)
- Too specific to one enhancement
- Missing critical steps (like testing)

### Template Maintenance

**Regular Review** (quarterly):
```bash
# List all templates
cmat workflow list

# Review each for usage
# Delete unused templates
# Update descriptions as needed
# Add new patterns discovered
```

**Version Control**:
- Commit `workflow_templates.json` to git
- Document template changes in commit messages
- Review template modifications in PRs
- Keep team aligned on available templates

---

## Integration with Queue System

### Template Metadata in Tasks

When UI creates tasks from templates, it should store template reference:

```bash
# Create task
TASK_ID=$(cmat queue add ...)

# Store template reference
cmat queue metadata $TASK_ID workflow_template "api-endpoint"

# Query later
cmat queue list completed | jq '.[] | 
  select(.metadata.workflow_template == "api-endpoint")'
```

**Benefits**:
- Track which templates are most used
- Analyze template effectiveness
- Find all enhancements using a template

---

## Troubleshooting

### Template Not Found

**Problem**: `cmat workflow show my-template` fails

**Solution**:
```bash
# List all templates
cmat workflow list

# Check exact name (case-sensitive)
jq '.templates | keys' .claude/queues/workflow_templates.json

# Verify file exists
ls -la .claude/queues/workflow_templates.json
```

### Cannot Add Step - Agent Not Found

**Problem**: `Agent 'xyz' not found in agent_contracts.json`

**Solution**:
```bash
# List valid agents
jq '.agents | keys' .claude/agents/agent_contracts.json

# Check spelling (case-sensitive)
# Use exact agent name from contracts
```

### Step Number Out of Range

**Problem**: `Step number N is out of range`

**Solution**:
```bash
# Check how many steps exist
cmat workflow list-steps my-template

# Use valid step number (1 to step_count)
```

### Template File Corrupted

**Problem**: JSON parse errors

**Solution**:
```bash
# Validate JSON syntax
jq '.' .claude/queues/workflow_templates.json

# If invalid, restore from backup
cp .claude/queues/workflow_templates_backup.json .claude/queues/workflow_templates.json

# Or restore from git
git checkout .claude/queues/workflow_templates.json
```

---

## Advanced Usage

### Backing Up Templates

```bash
# Create backup before major changes
cp .claude/queues/workflow_templates.json \
   .claude/queues/workflow_templates_backup.json

# Or commit to git
git add .claude/queues/workflow_templates.json
git commit -m "Add custom workflow templates"
```

### Exporting Templates

```bash
# Export single template
jq '.templates."my-template"' .claude/queues/workflow_templates.json \
  > my-template.json

# Share with team
```

### Importing Templates

```bash
# Manually add to workflow_templates.json
# (Automated import planned for future version)
```

### Template Analytics

```bash
# Count templates
jq '.templates | length' .claude/queues/workflow_templates.json

# List by step count
jq -r '.templates | to_entries[] | 
  "\(.value.steps | length) steps: \(.key)"' \
  .claude/queues/workflow_templates.json | sort -n

# Find templates using specific agent
jq -r '.templates | to_entries[] | 
  select(.value.steps[].agent == "architect") | 
  .key' .claude/queues/workflow_templates.json
```

---

## Migration Notes

### From v4.0 to v4.1

Templates were always stored in `workflow_templates.json`, but v4.1 adds:
- CRUD commands for template management
- Step-level inspection commands
- Validation when adding steps

**No migration needed** - existing templates work as-is.

### Adding Templates to Existing Projects

If your `workflow_templates.json` only has basic templates:

```bash
# Add your common workflows
cmat workflow create api-dev "API development"
cmat workflow add-step api-dev requirements-analyst
cmat workflow add-step api-dev architect
cmat workflow add-step api-dev implementer
cmat workflow add-step api-dev tester
cmat workflow add-step api-dev documenter

# Save additional templates
# Commit to version control
```

---

## Future Enhancements

**Planned for v4.2+**:
- `cmat workflow execute <template> <enhancement>` - Direct execution
- `cmat workflow clone <source> <new_name>` - Clone templates
- `cmat workflow export/import` - Share templates between projects
- `cmat workflow validate <template>` - Check template is valid
- Step-level conditions and branching
- Parallel step execution
- Template versioning

---

## Quick Reference

```bash
# Template CRUD
cmat workflow create <name> <description>
cmat workflow list
cmat workflow show <name>
cmat workflow delete <name>

# Step management
cmat workflow add-step <template> <agent> [--position=N]
cmat workflow remove-step <template> <step_num>
cmat workflow list-steps <template>
cmat workflow show-step <template> <step_num>

# Using templates (via UI or manual task creation)
# UI reads template and creates task sequence
```

---

## See Also

- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow patterns and orchestration
- **[SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md)** - Complete command reference
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Customizing for your project
- **[workflow_templates.json](.claude/queues/workflow_templates.json)** - Template storage

---
