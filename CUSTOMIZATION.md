# Customization Guide

How to adapt the Claude Multi-Agent Template for your specific project.

**Version**: 8.2.0

## Overview

The template is designed to be **language-agnostic** and **project-flexible**. Customization involves:

1. **Agent definitions** - Project-specific context in `.claude/agents/*.md`
2. **Workflow templates** - Custom workflows in `.claude/data/workflow_templates.json`
3. **Skills** - Domain-specific skills in `.claude/skills/`
4. **Learnings** - Project knowledge via RAG system

**Key Principle**: The system is driven by **workflow templates** (orchestration) and **agents.json** (capabilities).

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

### 2. Add Project Learnings

Prime the RAG system with project knowledge:

```bash
cd .claude
python -m cmat learnings add "This project uses Python 3.11 with FastAPI" --tags python,api
python -m cmat learnings add "Tests use pytest with pytest-asyncio for async tests" --tags testing
python -m cmat learnings add "Use snake_case for all Python functions and variables" --tags python,style
python -m cmat learnings add "API responses must return ISO 8601 timestamps" --tags api,python
```

### 3. Regenerate Agent Registry

After modifying agent files:

```bash
python -m cmat agents generate
```

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

Add learnings:
```bash
python -m cmat learnings add "Use type hints for all function parameters and return values" --tags python
python -m cmat learnings add "Run black formatter before committing" --tags python,style
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

Add learnings:
```bash
python -m cmat learnings add "Use strict TypeScript mode for all new files" --tags typescript
python -m cmat learnings add "Run eslint --fix before committing" --tags javascript,style
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

### Status Output

At the end of your response, output a completion block:

\`\`\`yaml
---
agent: security-reviewer
task_id: ${task_id}
status: <status>
---
\`\`\`

**Completion Statuses**:
- SECURITY_APPROVED - No issues found, ready for testing

**Halt Statuses**:
- SECURITY_ISSUES: <details> - Vulnerabilities found, needs fixes
```

### Step 2: Regenerate agents.json

```bash
python -m cmat agents generate
```

### Step 3: Verify Agent

```bash
python -m cmat agents list
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
python -m cmat agents generate

# 5. Verify
python -m cmat agents list
# Should show "react-hooks" in implementer's skills
```

---

## Workflow Customization

### Creating Custom Workflows

Workflow templates are stored in `.claude/data/workflow_templates.json`. You can create custom workflows by editing this file directly.

**Example: API Endpoint Workflow**

```json
{
  "name": "api-endpoint",
  "description": "REST API endpoint development",
  "steps": [
    {
      "agent": "requirements-analyst",
      "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
      "required_output": "endpoint_requirements.md",
      "on_status": {
        "READY_FOR_DEVELOPMENT": {
          "next_step": "architect",
          "auto_chain": true,
          "description": "Requirements complete"
        },
        "BLOCKED": {
          "next_step": null,
          "auto_chain": false,
          "description": "Cannot proceed"
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
          "auto_chain": true,
          "description": "Design complete"
        }
      }
    },
    {
      "agent": "implementer",
      "input": "{previous_step}/required_output/",
      "required_output": "endpoint_implementation.md",
      "on_status": {
        "READY_FOR_TESTING": {
          "next_step": "tester",
          "auto_chain": true,
          "description": "Implementation complete"
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
          "auto_chain": false,
          "description": "Workflow complete"
        }
      }
    }
  ]
}
```

### Workflow Patterns

#### Skip Requirements
For well-defined changes, start directly with architect:

```json
{
  "steps": [
    {
      "agent": "architect",
      "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
      "required_output": "design.md"
    }
  ]
}
```

#### Multiple Success Paths
Allow different statuses to branch differently:

```json
{
  "on_status": {
    "READY_FOR_IMPLEMENTATION": {
      "next_step": "implementer",
      "auto_chain": true
    },
    "NEEDS_RESEARCH": {
      "next_step": null,
      "auto_chain": false,
      "description": "Requires additional research"
    },
    "NEEDS_APPROVAL": {
      "next_step": null,
      "auto_chain": false,
      "description": "Requires stakeholder approval"
    }
  }
}
```

---

## Testing Customizations

### Validate Agent Definitions

```bash
# List all agents
python -m cmat agents list

# Should show agent with correct:
# - Name
# - Role
# - Skills assigned
```

### Verify Learnings

```bash
# List learnings
python -m cmat learnings list

# Search for specific topics
python -m cmat learnings search "testing"
```

### Check Queue Status

```bash
python -m cmat queue status
```

---

## Best Practices

### DO:
- Update all "Project-Specific Customization" sections in agent files
- Add learnings for project conventions and patterns
- Create workflows for repeated development patterns
- Add domain-specific skills for your tech stack
- Test customizations with simple enhancements first
- Keep `validations.metadata_required = true` for workflow agents

### DON'T:
- Remove agent role boundaries
- Make agents too project-specific (keep them reusable)
- Create too many similar workflows (consolidate)
- Skip regenerating agents.json after changes
- Forget to add learnings for important project patterns

---

## Customization Checklist

- [ ] Updated agent project context sections
- [ ] Added project learnings (5-10 minimum)
- [ ] Regenerated agents.json
- [ ] Created custom workflows (if needed)
- [ ] Added domain-specific skills (if needed)
- [ ] Verified with `agents list` and `learnings list`
- [ ] Tested with a simple enhancement

---

## See Also

- **[.claude/docs/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md)** - Workflow patterns
- **[.claude/docs/WORKFLOW_TEMPLATE_GUIDE.md](.claude/docs/WORKFLOW_TEMPLATE_GUIDE.md)** - Template management
- **[.claude/docs/SKILLS_GUIDE.md](.claude/docs/SKILLS_GUIDE.md)** - Skills system
- **[.claude/docs/LEARNINGS_GUIDE.md](.claude/docs/LEARNINGS_GUIDE.md)** - RAG memory system
- **[.claude/docs/CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md)** - Command reference
