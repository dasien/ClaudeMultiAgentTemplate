# Customization Guide

This guide shows you how to adapt the Claude Multi-Agent Template v5.0 for your specific project.

## Overview

The template is designed to be **language-agnostic** and **project-flexible**. Customization involves updating agent definitions, workflow templates, and project-specific documentation to match your needs.

**v5.0 Key Principle**: The system is driven by **workflow templates** (orchestration) and **agents.json** (capabilities).

---

## Essential Customizations

These customizations should be done **before** using the template:

### 1. Agent Project Context

Each agent file (`.claude/agents/*.md`) has a "Project-Specific Customization" section. Update these sections with your project details.

#### Example: Implementer Customization

**File**: `.claude/agents/implementer.md`

```markdown
## Project-Specific Customization

**Primary Language(s)**: Python 3.11+
**Coding Style Guide**: PEP 8 (enforced via black formatter)
**Naming Conventions**:
- snake_case for functions/variables
- PascalCase for classes
- UPPER_CASE for constants

**Error Handling**: Custom exceptions in exceptions.py
**Logging Standards**: Python logging module, INFO level
**Testing Framework**: pytest with pytest-cov
**Documentation Style**: Google-style docstrings
```

### 2. Workflow Templates

**File**: `.claude/queues/workflow_templates.json`

Add project-specific workflow templates for repeated patterns:

```bash
# Create custom workflow
cmat workflow create api-endpoint "REST API endpoint development"

# Add steps with project-specific outputs
cmat workflow add-step api-endpoint requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "endpoint_requirements.md"

cmat workflow add-step api-endpoint architect \
    "{previous_step}/required_output/" \
    "api_design.md"

cmat workflow add-step api-endpoint implementer \
    "{previous_step}/required_output/" \
    "endpoint_implementation.md"

cmat workflow add-step api-endpoint tester \
    "{previous_step}/required_output/" \
    "api_tests.md"

# Add transitions
cmat workflow add-transition api-endpoint 0 READY_FOR_DEVELOPMENT architect true
cmat workflow add-transition api-endpoint 1 READY_FOR_IMPLEMENTATION implementer true
cmat workflow add-transition api-endpoint 2 READY_FOR_TESTING tester true
cmat workflow add-transition api-endpoint 3 TESTING_COMPLETE null false
```

### 3. Skills System

Add domain-specific skills for your project:

```bash
# Create custom skill
mkdir -p .claude/skills/react-component-dev
# Edit SKILL.md with your domain knowledge

# Register in skills.json
# Assign to appropriate agents
# Regenerate: cmat agents generate-json
```

See [SKILLS_GUIDE.md](SKILLS_GUIDE.md) for complete instructions.

---

## Language-Specific Customizations

### Python Projects

Update `.claude/agents/implementer.md`:
```markdown
**Type Hints**: Required for all function signatures
**Formatter**: black (line length 88)
**Linter**: pylint + mypy for type checking
**Package Manager**: poetry or pip
**Testing**: pytest with fixtures
```

### JavaScript/TypeScript Projects

Update `.claude/agents/implementer.md`:
```markdown
**Type System**: TypeScript strict mode
**Formatter**: Prettier
**Linter**: ESLint with Airbnb config
**Package Manager**: npm or yarn
**Testing**: Jest + React Testing Library
```

### Java Projects

Update `.claude/agents/implementer.md`:
```markdown
**Version**: Java 17 LTS
**Build Tool**: Maven or Gradle
**Testing**: JUnit 5 + Mockito
**Formatter**: Google Java Format
```

---

## Adding Custom Agents

### Step 1: Create Agent Definition

**File**: `.claude/agents/security-reviewer.md`

```markdown
---
name: "Security Reviewer"
role: "security_review"
description: "Reviews code for security vulnerabilities"
tools: ["Read", "Grep", "Glob"]
skills: []
validations:
  metadata_required: true
---

# Security Reviewer Agent

## Role and Purpose
Review code for security vulnerabilities and ensure compliance.

## Core Responsibilities
- Check for OWASP Top 10 vulnerabilities
- Review authentication and authorization
- Validate input sanitization

## When to Use This Agent
- After implementation, before testing
- High-security features
```

### Step 2: Regenerate agents.json

```bash
cmat agents generate-json
```

### Step 3: Add to Workflows

```bash
# Create workflow with security review
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
cmat workflow add-transition secure-feature 2 READY_FOR_SECURITY_REVIEW security-reviewer true
cmat workflow add-transition secure-feature 3 SECURITY_APPROVED tester true
cmat workflow add-transition secure-feature 4 TESTING_COMPLETE null false
```

---

## Adding Custom Skills

### Quick Example

```bash
# 1. Create skill directory and file
mkdir -p .claude/skills/react-hooks
cat > .claude/skills/react-hooks/SKILL.md << 'EOF'
---
name: "React Hooks Best Practices"
description: "Proper use of React hooks and custom hook development"
category: "implementation"
required_tools: ["Read", "Write"]
---

# React Hooks Best Practices

## Purpose
Guide proper use of React hooks and custom hook development.

## When to Use
- Creating React components
- Managing component state
- Building custom hooks

## Key Capabilities
1. **useState/useEffect** - Proper hook usage
2. **Custom Hooks** - Reusable stateful logic
3. **Hook Rules** - Avoid common mistakes
EOF

# 2. Register in skills.json
# Edit .claude/skills/skills.json to add entry

# 3. Assign to implementer
# Edit .claude/agents/implementer.md frontmatter:
# skills: ["error-handling", "code-refactoring", "react-hooks"]

# 4. Regenerate
cmat agents generate-json

# 5. Test
cmat skills get implementer
# Should include "react-hooks"
```

---

## Workflow Customization Patterns

### Pattern: Skip Requirements

For well-defined changes:
```bash
cmat workflow create no-req "Skip requirements"
cmat workflow add-step no-req architect \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "design.md"
# ... add remaining steps
```

### Pattern: Multiple Success Paths

For workflows with conditional branching:
```bash
cmat workflow add-transition my-workflow 1 READY_FOR_IMPLEMENTATION implementer true
cmat workflow add-transition my-workflow 1 NEEDS_RESEARCH null false
cmat workflow add-transition my-workflow 1 NEEDS_APPROVAL null false
```

Architect can output different statuses depending on situation.

---

## Testing Customizations

### Validate Agent Definitions

```bash
# Check agents.json structure
cmat agents list | jq '.agents[] | {name, role, validations}'

# Verify skills assigned
cmat skills get <agent-name>
```

### Validate Workflows

```bash
# Check all workflows
cmat workflow list

# Validate specific workflow
cmat workflow validate <workflow-name>

# Show workflow structure
cmat workflow show <workflow-name>
```

### Test with Simple Workflow

```bash
# Create minimal test
cmat workflow create test-custom "Test customizations"
cmat workflow add-step test-custom requirements-analyst \
    "enhancements/{enhancement_name}/{enhancement_name}.md" \
    "test.md"
cmat workflow add-transition test-custom 0 READY_FOR_DEVELOPMENT null false

# Run it
mkdir -p enhancements/test-1
echo "# Test" > enhancements/test-1/test-1.md
cmat workflow start test-custom test-1
```

---

## Best Practices

### DO:
- ✅ Customize all "Project-Specific Customization" sections
- ✅ Create workflows for repeated patterns
- ✅ Add domain-specific skills
- ✅ Test customizations with simple workflows first
- ✅ Document custom workflows in WORKFLOW_GUIDE.md
- ✅ Keep validations.metadata_required = true for workflow agents

### DON'T:
- ❌ Remove agent role boundaries
- ❌ Make agents too specific
- ❌ Create too many similar workflows
- ❌ Skip validation steps in workflows
- ❌ Forget to regenerate agents.json after changes

---

## See Also

- **[WORKFLOW_TEMPLATE_GUIDE.md](WORKFLOW_TEMPLATE_GUIDE.md)** - Workflow template management
- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Skills system
- **[agents.json](.claude/agents/agents.json)** - Agent definitions
- **[workflow_templates.json](.claude/queues/workflow_templates.json)** - Workflow storage

---