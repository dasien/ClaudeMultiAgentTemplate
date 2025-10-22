# Customization Guide

This guide shows you how to adapt the Claude Multi-Agent Template v2.0 for your specific project.

## Overview

The template is designed to be **language-agnostic** and **project-flexible**. Customization involves updating agent definitions, agent contracts, workflow patterns, and project-specific documentation to match your needs.

**v2.0 Key Principle**: The system is driven by **AGENT_CONTRACTS.json** (machine-readable) with human-friendly guides that reference it.

## Essential Customizations

These customizations should be done **before** using the template:

### 1. Agent Project Context

Each agent file (`.claude/agents/*.md`) has a "Project-Specific Customization" section. Update these sections with your project details:

#### Requirements Analyst

**File**: `.claude/agents/requirements-analyst.md`

**Customize**:
```markdown
## Project-Specific Customization

**Project Type**: [Web app / CLI / Library / Mobile app / etc.]
**Primary Language(s)**: [Python / JavaScript / Java / etc.]
**Key Technologies**: [React / Django / Spring / etc.]
**Existing Architecture**: [Microservices / Monolith / etc.]
**Team Conventions**: [Link to style guide or conventions doc]
**Project Constraints**: [Performance / Memory / Compatibility requirements]
```

#### Architect

**File**: `.claude/agents/architect.md`

**Customize**:
```markdown
## Project-Specific Customization

**Primary Language(s)**: Python 3.9+
**Preferred Frameworks**: FastAPI for APIs, pytest for testing
**Architecture Pattern**: Clean Architecture / Layered / MVC
**Coding Standards**: PEP 8, type hints required
**Testing Frameworks**: pytest, unittest
**Documentation Style**: Google-style docstrings
**Performance Requirements**: API response < 200ms
**Security Requirements**: OWASP Top 10 compliance
```

#### Implementer

**File**: `.claude/agents/implementer.md`

**Customize**:
```markdown
## Project-Specific Customization

**Primary Language(s)**: Python 3.9+
**Coding Style Guide**: PEP 8 (enforced via black formatter)
**Naming Conventions**:
- snake_case for functions/variables
- PascalCase for classes
- UPPER_CASE for constants

**Comment Style**: Google-style docstrings
**Error Handling**: Custom exceptions in exceptions.py
**Logging Standards**: Python logging module, INFO level
**File Organization**: Feature-based modules
**Import Ordering**: stdlib, third-party, local (sorted by isort)
**Documentation Style**: Docstrings for all public APIs
**Performance Requirements**: O(n) acceptable, O(n²) needs justification
```

#### Tester

**File**: `.claude/agents/tester.md`

**Customize**:
```markdown
## Project-Specific Customization

**Testing Framework**: pytest with pytest-cov
**Coverage Tools**: coverage.py with 80% minimum
**Test Organization**: Mirror src/ structure in tests/
**Naming Conventions**: test_<function>_<scenario>_<expected>
**Mock/Stub Libraries**: pytest-mock, unittest.mock
**Test Data Management**: fixtures/ directory
**Performance Testing**: pytest-benchmark for critical paths
**CI/CD Integration**: GitHub Actions
**Test Environment**: Docker containers for integration tests
**Documentation Standards**: Docstrings in test files
```

#### Documenter

**File**: `.claude/agents/documenter.md`

**Customize**:
```markdown
## Project-Specific Customization

**Documentation Format**: Markdown
**Documentation Location**: docs/ directory + README.md
**Docstring Format**: Google-style (parsed by Sphinx)
**Documentation Generator**: Sphinx + autodoc
**Target Audience**: Developers and end-users (separate docs)
**Style Guide**: Write the Docs style guide
**Examples Format**: Code blocks with language hints
**Version Documentation**: CHANGELOG.md following Keep a Changelog
```

### 2. Agent Contracts (NEW in v2.0)

**File**: `.claude/AGENT_CONTRACTS.json`

The agent contracts file is the **source of truth** for the system. You typically don't need to modify it unless you're adding custom agents or changing workflow patterns.

**When to modify**:
- Adding a new custom agent
- Changing required output filenames
- Adding additional required files for an agent
- Modifying success/failure status codes
- Changing next agent in workflow

**Example - Adding a custom status**:
```json
"implementer": {
  "statuses": {
    "success": [
      {
        "code": "READY_FOR_TESTING",
        "description": "Implementation complete, needs testing",
        "next_agents": ["tester"]
      },
      {
        "code": "READY_FOR_CODE_REVIEW",
        "description": "Implementation complete, needs review before testing",
        "next_agents": ["code-reviewer"]
      }
    ]
  }
}
```

### 3. Workflow Patterns

**File**: `.claude/WORKFLOW_GUIDE.md`

Add project-specific workflow patterns to the guide:

```markdown
## Custom: API Endpoint Development

**Flow**: Requirements → Architecture → Implementation → Security Review → Testing → Documentation

**When to Use**: New REST API endpoints requiring security validation

**Duration**: 8-10 hours total

**Notes**: Adds security-reviewer agent before testing phase
```

### 4. Workflow Templates

**File**: `.claude/queues/workflow_templates.json`

Add project-specific workflow templates:

```json
{
  "templates": {
    "api_endpoint_development": {
      "name": "API Endpoint Development",
      "description": "Add new REST API endpoint",
      "steps": [
        {
          "agent": "requirements-analyst",
          "task": "Analyze endpoint requirements",
          "estimated_duration": "30 minutes"
        },
        {
          "agent": "architect",
          "task": "Design endpoint architecture",
          "estimated_duration": "1 hour"
        },
        {
          "agent": "implementer",
          "task": "Implement endpoint",
          "estimated_duration": "2 hours"
        },
        {
          "agent": "tester",
          "task": "Test endpoint",
          "estimated_duration": "1 hour"
        },
        {
          "agent": "documenter",
          "task": "Document endpoint",
          "estimated_duration": "30 minutes"
        }
      ]
    }
  }
}
```

### 5. Task Prompt Defaults

**File**: `.claude/TASK_PROMPT_DEFAULTS.md`

Add project-specific prompt templates (advanced):

```markdown
## Database Migration Prompts

### Create Migration
Design and implement a database migration for [CHANGE_DESCRIPTION].

Current schema: [REFERENCE_FILE]
Migration tool: Alembic

Tasks:
1. Design migration strategy
2. Create migration scripts
3. Test upgrade and downgrade
4. Document migration notes
```

## Language-Specific Customizations

### Python Projects

```markdown
# .claude/agents/implementer.md additions

**Type Hints**: Required for all function signatures
**Formatter**: black (line length 88)
**Linter**: pylint + mypy for type checking
**Import Organization**: isort with black profile
**Virtual Environment**: poetry or venv
**Package Manager**: pip or poetry
**Testing**: pytest with fixtures
**Async**: asyncio for async code
```

### JavaScript/TypeScript Projects

```markdown
# .claude/agents/implementer.md additions

**Type System**: TypeScript strict mode
**Formatter**: Prettier
**Linter**: ESLint with Airbnb config
**Package Manager**: npm or yarn
**Testing**: Jest + React Testing Library
**Build Tool**: Webpack or Vite
**Module System**: ES6 modules
```

### Java Projects

```markdown
# .claude/agents/implementer.md additions

**Version**: Java 17 LTS
**Build Tool**: Maven or Gradle
**Testing**: JUnit 5 + Mockito
**Formatter**: Google Java Format
**Linter**: Checkstyle + SpotBugs
**Documentation**: Javadoc
**Package Structure**: Domain-driven
```

## Domain-Specific Customizations

### Web Application Projects

Add web-specific concerns:

```markdown
# .claude/agents/architect.md additions

**Frontend Framework**: React / Vue / Angular
**Backend Framework**: Express / FastAPI / Spring Boot
**API Design**: RESTful / GraphQL
**Authentication**: JWT / OAuth2
**Database**: PostgreSQL / MongoDB
**Caching**: Redis
**Deployment**: Docker + Kubernetes
**Monitoring**: Prometheus + Grafana
```

### Library/SDK Projects

Add library-specific concerns:

```markdown
# .claude/agents/architect.md additions

**API Design**: Public vs internal APIs
**Versioning**: Semantic versioning
**Backward Compatibility**: Required
**Dependencies**: Minimal external dependencies
**Documentation**: Comprehensive API docs required
**Examples**: Multiple usage examples required
**Testing**: 90%+ coverage required
```

### CLI Tool Projects

Add CLI-specific concerns:

```markdown
# .claude/agents/architect.md additions

**Argument Parsing**: argparse / Click / Commander
**Output Format**: JSON / YAML / Table
**Configuration**: Config file support
**Error Messages**: User-friendly errors
**Help System**: Comprehensive help text
**Installation**: pip / npm / homebrew
```

## Team-Specific Customizations

### Code Review Requirements

Add to `.claude/agents/implementer.md`:

```markdown
**Code Review Checklist**:
- [ ] Follows team coding standards
- [ ] All tests pass
- [ ] No compiler warnings
- [ ] Security best practices followed
- [ ] Performance considerations addressed
- [ ] Documentation updated
- [ ] Breaking changes noted
```

### Deployment Process

Add to `.claude/agents/documenter.md`:

```markdown
**Deployment Documentation**:
- Deployment checklist
- Rollback procedures
- Configuration changes
- Database migrations
- Environment variables
- Monitoring setup
```

## Adding Custom Agents

### Step 1: Create Agent Definition File

**File**: `.claude/agents/security-reviewer.md`

```markdown
---
name: "Security Reviewer"
description: "Reviews code for security vulnerabilities and compliance"
tools: ["Read", "Grep", "Glob", "WebSearch"]
---

# Security Reviewer Agent

## Role and Purpose
Review code for security vulnerabilities and ensure compliance with security standards.

**Agent Contract**: See `AGENT_CONTRACTS.json → agents.security-reviewer`

## Core Responsibilities
- Check for common vulnerabilities (OWASP Top 10)
- Review authentication and authorization
- Check for hardcoded secrets
- Validate input sanitization

## When to Use This Agent
### ✅ Use security-reviewer when:
- After implementation, before testing
- High-security features
- Authentication/authorization changes

## Workflow Position
**Input**: `enhancements/{name}/implementer/test_plan.md`
**Output Directory**: `security-reviewer/`
**Root Document**: `security_review.md`
**Success Status**: `SECURITY_REVIEW_COMPLETE`
**Next Agent**: tester

## Output Requirements
**Required**: `security_review.md` with findings and recommendations
**Success Status**: `SECURITY_REVIEW_COMPLETE`
**Failure Status**: `BLOCKED: <security issues found>`
```

### Step 2: Add to Agent Contracts

**File**: `.claude/AGENT_CONTRACTS.json`

Add new agent to the contracts:

```json
{
  "agents": {
    "security-reviewer": {
      "role": "security_review",
      "description": "Reviews code for security vulnerabilities and compliance",
      "inputs": {
        "required": [
          {
            "name": "implementation",
            "pattern": "enhancements/{enhancement_name}/implementer/test_plan.md",
            "description": "Implementation to review"
          }
        ]
      },
      "outputs": {
        "root_document": "security_review.md",
        "output_directory": "security-reviewer",
        "additional_required": []
      },
      "statuses": {
        "success": [
          {
            "code": "SECURITY_REVIEW_COMPLETE",
            "description": "Security review passed",
            "next_agents": ["tester"]
          }
        ],
        "failure": [
          {
            "code": "BLOCKED",
            "pattern": "BLOCKED: {reason}",
            "description": "Security issues found"
          }
        ]
      },
      "metadata_required": true
    }
  }
}
```

### Step 3: Update Workflow States (if needed)

**File**: `.claude/WORKFLOW_STATES.json`

Add new state if using custom status codes:

```json
{
  "states": {
    "SECURITY_REVIEW_COMPLETE": {
      "description": "Security review passed, ready for testing",
      "valid_agents": ["tester"],
      "next_states": ["TESTING_COMPLETE", "BLOCKED"],
      "is_terminal": false
    }
  }
}
```

### Step 4: Update Implementer's Next Agents

Modify implementer to chain to security-reviewer instead of tester:

```json
"implementer": {
  "statuses": {
    "success": [
      {
        "code": "READY_FOR_SECURITY_REVIEW",
        "description": "Implementation complete, needs security review",
        "next_agents": ["security-reviewer"]
      }
    ]
  }
}
```

### Step 5: Update WORKFLOW_GUIDE.md

Document the new workflow pattern:

```markdown
## Secure Feature Development

**Flow**: Requirements → Architecture → Implementation → Security Review → Testing → Documentation

**When to Use**: Features involving authentication, authorization, or sensitive data

**Duration**: 8-10 hours total
```

### Step 6: Add Prompt Template (Optional)

**File**: `.claude/TASK_PROMPT_DEFAULTS.md`

```markdown
# SECURITY_REVIEW_TEMPLATE

You are acting as the ${agent} agent performing security review.

Read your role definition from: ${agent_config}

Review the implementation in: ${source_file}

## SECURITY REVIEW OBJECTIVES:
- Identify security vulnerabilities
- Check for OWASP Top 10 issues
- Validate authentication and authorization
- Check for hardcoded secrets
...
```

## Testing Your Customizations

### 1. Verify Agent Definitions

```bash
# Check all agents have valid YAML
for file in .claude/agents/*.md; do
    echo "Checking $file"
    head -20 "$file" | grep -A 10 "^---$"
done
```

### 2. Verify Contracts

```bash
# Validate contract JSON syntax
jq '.' .claude/AGENT_CONTRACTS.json

# Check specific agent contract
jq '.agents."requirements-analyst"' .claude/AGENT_CONTRACTS.json

# Verify all agents have required fields
jq '.agents | to_entries[] | select(.value.outputs.root_document == null) | .key' .claude/AGENT_CONTRACTS.json
# Should return empty (all agents have root_document)
```

### 3. Test Agent Launch

Launch each agent with a simple task to verify customizations are accessible:

```bash
# Test requirements analyst
.claude/queues/queue_manager.sh add \
  "Test task" \
  "requirements-analyst" \
  "normal" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Test agent customization"

.claude/queues/queue_manager.sh start <task_id>
```

### 4. Test Contract Validation

```bash
# Test output validation
.claude/queues/queue_manager.sh validate_agent_outputs \
  "requirements-analyst" \
  "enhancements/demo-test"

# Test next agent determination
.claude/queues/queue_manager.sh determine_next_agent_from_contract \
  "requirements-analyst" \
  "READY_FOR_DEVELOPMENT"
# Should output: architect

# Test path building
.claude/queues/queue_manager.sh build_next_source_path \
  "demo-test" \
  "architect" \
  "requirements-analyst"
# Should output: enhancements/demo-test/requirements-analyst/analysis_summary.md
```

### 5. Test Complete Workflow

Run through a complete workflow with the demo enhancement to verify all customizations work together:

```bash
# Use demo-test enhancement as validation
.claude/queues/queue_manager.sh add \
  "Demo validation" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Validate system with demo"

# Follow through entire workflow
# Verify each agent creates correct outputs
# Verify metadata headers are present
# Verify auto-chaining suggestions are correct
```

## Advanced Customizations

### Custom Output Structure

If you need different output file names, update the contract:

```json
"architect": {
  "outputs": {
    "root_document": "technical_design.md",  // Changed from implementation_plan.md
    "output_directory": "architect",
    "additional_required": [
      "architecture_diagram.md",  // Now required, not optional
      "api_specification.md"
    ]
  }
}
```

**Important**: If you change `root_document` names, also update:
- `TASK_PROMPT_DEFAULTS.md` variable examples
- Agent `.md` file "Output Requirements" section
- `WORKFLOW_GUIDE.md` documentation

### Custom Workflow States

Add project-specific states to `WORKFLOW_STATES.json`:

```json
{
  "states": {
    "READY_FOR_DEPLOYMENT": {
      "description": "Passed all checks, ready to deploy",
      "valid_agents": ["deployment-agent"],
      "next_states": ["DEPLOYED", "BLOCKED"],
      "is_terminal": false,
      "integration_trigger": true
    },
    "DEPLOYED": {
      "description": "Successfully deployed to production",
      "valid_agents": [],
      "next_states": [],
      "is_terminal": true
    }
  }
}
```

### Metadata Header Customization

The system requires 5 fields in metadata headers:
- `enhancement`
- `agent`
- `task_id`
- `timestamp`
- `status`

**To add custom fields**, modify validation in `queue_manager.sh`:

```bash
# Add optional field checking
if grep -q "^reviewer:" "$root_path"; then
    echo "  ✓ Reviewer field present"
fi
```

**Note**: Don't make custom fields required - keep the 5 standard fields for consistency.

## Documentation Updates

After customizing, update:

1. **README.md** - Reflect your project specifics
2. **.claude/README.md** - Update project examples
3. **.claude/WORKFLOW_GUIDE.md** - Document custom workflows
4. **INSTALLATION.md** - Add any project-specific setup steps
5. **This file (CUSTOMIZATION.md)** - Document your specific customizations for your team

## Sharing Customizations

If you create useful customizations:

1. Document them clearly in your project docs
2. Share with your team
3. Consider contributing back to the template
4. Create team-specific fork if needed

## Best Practices

### DO:
- ✅ Customize all "Project-Specific Customization" sections
- ✅ Update agent contracts when adding custom agents
- ✅ Add project-specific workflow templates
- ✅ Document your customizations clearly
- ✅ Test customizations thoroughly with demo-test
- ✅ Keep contracts and agent .md files in sync
- ✅ Update as project evolves

### DON'T:
- ❌ Remove agent boundaries (keep separation of concerns)
- ❌ Make agents too specific (maintain flexibility)
- ❌ Change core contract structure without understanding impact
- ❌ Skip documentation of customizations
- ❌ Modify contracts without testing
- ❌ Forget to update team members on changes
- ❌ Break the 5-field metadata header standard

## Examples of Well-Customized Projects

### Microservices Project

```markdown
- Added API-specific workflows
- Created separate agents for frontend/backend
- Customized for Docker + Kubernetes deployment
- Added service mesh integration steps
- Documented API contracts in architect role
- Added contract for api-gateway-developer agent
```

### Mobile App Project

```markdown
- Added platform-specific agents (iOS/Android)
- Customized for Swift and Kotlin
- Added UI/UX review agent
- Included app store submission workflow
- Added device testing requirements
- Custom contracts for platform-specific implementers
```

### Data Pipeline Project

```markdown
- Added data engineering agent
- Customized for PySpark/Airflow
- Added data quality testing
- Included pipeline monitoring
- Documented data schemas
- Contract for data-validator agent
```

## Validating Your Customizations

### Contract Validation Checklist

Before using customized contracts:

- [ ] All agents have `role`, `description`, `inputs`, `outputs`, `statuses`
- [ ] All `root_document` values are valid filenames
- [ ] All `output_directory` values match agent names (recommended)
- [ ] All `next_agents` reference agents that exist
- [ ] All status codes are unique and descriptive
- [ ] `metadata_required` is set appropriately (true for workflow agents, false for integration)
- [ ] JSON syntax is valid: `jq '.' .claude/AGENT_CONTRACTS.json`

### Workflow Validation Checklist

- [ ] All states in WORKFLOW_STATES.json are reachable
- [ ] All agents mentioned in contracts exist in `.claude/agents/`
- [ ] All workflow patterns have clear documentation
- [ ] State transitions form valid paths (no dead ends except terminal states)
- [ ] Branching workflows have convergence states defined

### Agent File Validation Checklist

For each custom agent `.md` file:

- [ ] Has valid YAML frontmatter
- [ ] Includes "Agent Contract" reference
- [ ] Includes "When to Use This Agent" section
- [ ] Includes "Workflow Position" section
- [ ] Includes "Output Requirements" section
- [ ] Documents success and failure status codes
- [ ] References the agent's contract

## Troubleshooting Customizations

### Contract Parsing Errors

**Problem**: `jq` errors when loading contracts

**Solution**:
```bash
# Validate JSON syntax
jq '.' .claude/AGENT_CONTRACTS.json

# Check for common issues:
# - Missing commas
# - Trailing commas
# - Unescaped quotes
# - Unclosed brackets
```

### Agent Not Found in Contract

**Problem**: "Agent not found in contracts" error

**Solution**:
```bash
# List all agents in contract
jq '.agents | keys' .claude/AGENT_CONTRACTS.json

# Verify agent name matches exactly (case-sensitive)
# Check agent .md file name matches contract key
```

### Validation Always Fails

**Problem**: Output validation fails even when files exist

**Solution**:
```bash
# Check what contract expects
jq '.agents."your-agent".outputs' .claude/AGENT_CONTRACTS.json

# Compare with actual output location
ls -la enhancements/your-enhancement/your-agent/

# Common issues:
# - output_directory doesn't match actual directory name
# - root_document filename is wrong
# - Files in wrong location
```

### Wrong Next Agent

**Problem**: System suggests incorrect next agent

**Solution**:
```bash
# Check status code mapping
jq '.agents."current-agent".statuses.success' .claude/AGENT_CONTRACTS.json

# Verify status code exactly matches
# Check next_agents array contains expected agent
```

---

## Migration from v1.0

If you're upgrading from the original template:

### 1. Add AGENT_CONTRACTS.json

Create the contracts file with your 5 core agents plus any custom agents.

### 2. Enhance Agent .md Files

Add the new sections to each agent:
- Contract reference
- When to Use This Agent
- Workflow Position
- Output Requirements

### 3. Create WORKFLOW_GUIDE.md

Move content from old `AGENT_ROLE_MAPPING.md` to the new guide.

### 4. Update queue_manager.sh

Replace with v2.0 version that includes contract validation functions.

### 5. Update on-subagent-stop.sh

Replace with merged version that includes validation logic.

### 6. Update Existing Enhancements

Add metadata headers to existing output documents:

```bash
# Use the migration script from the analysis document
./migrate_enhancement.sh <enhancement-name>
```

### 7. Test Everything

Run through the demo-test enhancement to verify the upgrade worked.

---

**Remember**: The template is a starting point. Customize it to fit your team's workflow, not the other way around.

**The Contract System**: Provides structure and validation while remaining flexible for your needs.