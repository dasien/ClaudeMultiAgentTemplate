# Customization Guide

This guide shows you how to adapt the Claude Multi-Agent Template for your specific project.

## Overview

The template is designed to be **language-agnostic** and **project-flexible**. Customization involves updating agent definitions, workflow patterns, and project-specific documentation to match your needs.

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

### 2. Workflow Templates

**File**: `.claude/queues/workflow_templates.json`

Add project-specific workflows:

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

### 3. Hook Customization

**File**: `.claude/hooks/on-subagent-stop.sh`

Customize status detection and suggestions:

```bash
# Add project-specific status markers
case "$output" in
    *"READY_FOR_DEPLOYMENT"*)
        echo "🚀 Ready for deployment phase"
        echo "Suggested: Launch deployment-agent or manually deploy"
        ;;
    *"NEEDS_SECURITY_REVIEW"*)
        echo "🔒 Security review required"
        echo "Suggested: Launch security-reviewer agent"
        ;;
esac
```

### 4. Task Prompt Defaults

**File**: `.claude/TASK_PROMPT_DEFAULTS.md`

Add project-specific prompt templates:

```markdown
## Database Migration Prompts

### Create Migration
\```
Design and implement a database migration for [CHANGE_DESCRIPTION].

Current schema: [REFERENCE_FILE]
Migration tool: Alembic

Tasks:
1. Design migration strategy
2. Create migration scripts
3. Test upgrade and downgrade
4. Document migration notes
\```
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

Create specialized agents for your domain:

### Example: Security Reviewer Agent

**File**: `.claude/agents/security-reviewer.md`

```markdown
---
name: "Security Reviewer"
description: "Reviews code for security vulnerabilities and compliance"
tools: ["Read", "Grep", "Glob", "WebSearch"]
---

# Security Reviewer Agent

## Role
Review code for security vulnerabilities and ensure compliance with security standards.

## Responsibilities
- Check for common vulnerabilities (OWASP Top 10)
- Review authentication and authorization
- Check for hardcoded secrets
- Validate input sanitization
- Review cryptography usage
- Check dependency vulnerabilities

## Output Status
`SECURITY_REVIEW_COMPLETE`
```

### Example: Database Expert Agent

**File**: `.claude/agents/database-expert.md`

```markdown
---
name: "Database Expert"
description: "Designs database schemas and optimizes queries"
tools: ["Read", "Write", "Edit", "Bash"]
---

# Database Expert Agent

## Role
Design efficient database schemas and optimize database performance.

## Responsibilities
- Design normalized schemas
- Plan indexing strategies
- Optimize queries
- Design migrations
- Plan backup strategies
- Consider scalability

## Output Status
`DATABASE_DESIGN_COMPLETE`
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

### 2. Test Agent Launch

Launch each agent with a simple task to verify customizations are accessible.

### 3. Test Workflow

Run through a complete workflow with a small enhancement to verify all customizations work together.

## Documentation Updates

After customizing, update:

1. **README.md** - Reflect your project specifics
2. **.claude/README.md** - Update project examples
3. **INSTALLATION.md** - Add any project-specific setup steps
4. **This file (CUSTOMIZATION.md)** - Document your specific customizations for your team

## Sharing Customizations

If you create useful customizations:

1. Document them clearly
2. Share with your team
3. Consider contributing back to the template
4. Create team-specific fork if needed

## Best Practices

### DO:
- ✅ Customize all "Project-Specific Customization" sections
- ✅ Add project-specific workflow templates
- ✅ Document your customizations
- ✅ Test customizations thoroughly
- ✅ Update as project evolves

### DON'T:
- ❌ Remove agent boundaries (keep separation of concerns)
- ❌ Make agents too specific (maintain flexibility)
- ❌ Skip documentation of customizations
- ❌ Forget to update team members on changes

## Examples of Well-Customized Projects

### Microservices Project

```markdown
- Added API-specific workflows
- Created separate agents for frontend/backend
- Customized for Docker + Kubernetes deployment
- Added service mesh integration steps
- Documented API contracts in architect role
```

### Mobile App Project

```markdown
- Added platform-specific agents (iOS/Android)
- Customized for Swift and Kotlin
- Added UI/UX review agent
- Included app store submission workflow
- Added device testing requirements
```

### Data Pipeline Project

```markdown
- Added data engineering agent
- Customized for PySpark/Airflow
- Added data quality testing
- Included pipeline monitoring
- Documented data schemas
```

---

**Remember**: The template is a starting point. Customize it to fit your team's workflow, not the other way around.
