# Customization Guide

This guide shows you how to adapt the Claude Multi-Agent Template v2.0 for your specific project.

## Overview

The template is designed to be **language-agnostic** and **project-flexible**. Customization involves updating agent definitions, agent contracts, workflow patterns, and project-specific documentation to match your needs.

**v2.0 Key Principle**: The system is driven by **agent_contracts.json** (machine-readable) with human-friendly guides that reference it.

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

**File**: `.claude/agents/agent_contracts.json`

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

**Agent Contract**: See `agent_contracts.json → agents.security-reviewer`

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

**File**: `.claude/agents/agent_contracts.json`

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

**File**: `.claude/queues/workflow_states.json`

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

## Adding Custom Skills

Custom skills allow you to add domain-specific expertise to your agents.

### Step 1: Create Skill Directory and File
````bash
# Create skill directory
mkdir -p .claude/skills/my-custom-skill

# Copy template
cp SKILL_TEMPLATE.md .claude/skills/my-custom-skill/SKILL.md
````

### Step 2: Define Your Skill

Edit `.claude/skills/my-custom-skill/SKILL.md` following the template structure:
````markdown
---
name: "My Custom Skill"
description: "Concise description of what this skill does (max 1024 chars)"
category: "implementation"  # or analysis, architecture, testing, documentation, etc.
required_tools: ["Read", "Write", "Bash"]
---

# My Custom Skill

## Purpose
[2-3 sentences explaining what this skill enables the agent to do]

## When to Use
[List 3-5 scenarios where this skill is appropriate]
- [Scenario 1]
- [Scenario 2]
- [Scenario 3]

## Key Capabilities
[3-5 main capabilities this skill provides]

1. **[Capability 1]** - [Brief description]
2. **[Capability 2]** - [Brief description]
3. **[Capability 3]** - [Brief description]

## Approach
[Step-by-step methodology, typically 3-7 steps]

1. [Step 1 with brief explanation]
2. [Step 2 with brief explanation]
3. [Step 3 with brief explanation]

## Example
**Context**: [When you'd use this skill]

**Approach**:
````
[Code snippet, process description, or example of applying the skill]
````

**Expected Result**: [What should happen]

## Best Practices
- ✅ [Do this]
- ✅ [Do this]
- ✅ [Do this]
- ❌ Avoid: [Don't do this]
- ❌ Avoid: [Don't do this]
````

### Step 3: Register in skills.json

Add your skill to `.claude/skills/skills.json`:
````json
{
  "skills": [
    {
      "name": "My Custom Skill",
      "skill-directory": "my-custom-skill",
      "category": "implementation",
      "required_tools": ["Read", "Write", "Bash"],
      "description": "Concise description matching SKILL.md frontmatter"
    }
  ]
}
````

**Important**: Keep `description` consistent between skills.json and SKILL.md.

### Step 4: Assign to Agents

Edit relevant agent `.md` files in `.claude/agents/`:

**Example - Add to implementer**:
````markdown
---
name: "Implementer"
description: "Implements features based on architectural specifications"
tools: ["Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep", "Task"]
skills: ["error-handling", "code-refactoring", "sql-development", "my-custom-skill"]
---
````

**Best Practices for Assignment**:
- ✅ Assign 2-4 skills per agent (not too many)
- ✅ Choose skills directly relevant to agent's role
- ✅ Ensure agent has required tools for the skill
- ❌ Don't assign all skills to all agents
- ❌ Don't assign irrelevant skills

### Step 5: Regenerate agents.json
````bash
cmat.sh agents generate-json
````

This updates `.claude/agents/agents.json` with the new skill assignments.

### Step 6: Test Your Skill
````bash
# Verify skill is registered
cmat.sh skills list | grep "my-custom-skill"

# Check agent has the skill
cmat.sh skills get implementer
# Should include "my-custom-skill"

# Preview what gets injected
cmat.sh skills prompt implementer | grep -A 20 "My Custom Skill"

# Test with actual task
TASK_ID=$(cmat.sh queue add \
  "Test custom skill" \
  "implementer" \
  "normal" \
  "implementation" \
  "test-file.md" \
  "Testing my custom skill")

cmat.sh queue start $TASK_ID

# Verify skill appeared in logs
grep "My Custom Skill" enhancements/*/logs/implementer_*.log
````

## Skill Customization Examples

### Domain-Specific Skills

**Example: React Component Development**
````markdown
---
name: "React Component Development"
description: "Best practices for building React components with hooks, proper state management, and TypeScript"
category: "implementation"
required_tools: ["Read", "Write", "Edit"]
---

# React Component Development

## Purpose
Build React components following modern best practices using hooks, TypeScript, and proper component patterns.

## When to Use
- Creating new React components
- Refactoring class components to functional
- Implementing complex state logic
- Building reusable UI components

## Key Capabilities
1. **Functional Components** - Use hooks over classes
2. **TypeScript Integration** - Proper typing for props and state
3. **Component Composition** - Build from smaller pieces

## Approach
1. Define component interface with TypeScript
2. Use functional component with hooks
3. Implement proper prop validation
4. Apply composition over inheritance
5. Add proper error boundaries
6. Ensure accessibility

## Example
**Context**: Creating a user profile card

**Code**:
```typescript
interface ProfileCardProps {
  name: string;
  email: string;
  avatar?: string;
  onEdit?: () => void;
}

export const ProfileCard: React.FC<ProfileCardProps> = ({
  name,
  email,
  avatar,
  onEdit
}) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className="profile-card"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="article"
      aria-label={`Profile for ${name}`}
    >
      {avatar && <Avatar src={avatar} alt={name} />}
      <h2>{name}</h2>
      <p>{email}</p>
      {onEdit && (
        <Button
          onClick={onEdit}
          aria-label="Edit profile"
        >
          Edit
        </Button>
      )}
    </div>
  );
};
```

## Best Practices
- ✅ Use TypeScript for all components
- ✅ Destructure props in function signature
- ✅ Use semantic HTML and ARIA labels
- ✅ Keep components small and focused
- ✅ Use composition over inheritance
- ❌ Avoid: Prop drilling (use context instead)
- ❌ Avoid: Inline function definitions in JSX
- ❌ Avoid: Missing key props in lists
````

**Assignment**: Add to `implementer` agent for React projects.

### Infrastructure Skills

**Example: Docker Deployment**
````markdown
---
name: "Docker Deployment"
description: "Containerize applications with Docker, write efficient Dockerfiles, and manage multi-container setups with docker-compose"
category: "devops"
required_tools: ["Read", "Write", "Bash"]
---

# Docker Deployment

## Purpose
Containerize applications effectively using Docker best practices for efficient, reproducible deployments.

## When to Use
- Creating Dockerfiles for applications
- Setting up development environments
- Preparing production deployments
- Defining multi-service architectures

## Key Capabilities
1. **Efficient Dockerfiles** - Multi-stage builds, layer caching
2. **Docker Compose** - Multi-container orchestration
3. **Security** - Non-root users, minimal base images

## Approach
1. Choose appropriate base image
2. Use multi-stage builds
3. Optimize layer caching
4. Run as non-root user
5. Define health checks
6. Document environment variables

## Example
**Context**: Containerizing a Python Flask application

**Dockerfile**:
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application
COPY --chown=appuser:appuser . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run
EXPOSE 5000
CMD ["python", "app.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://db:5432/app
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

## Best Practices
- ✅ Use official base images
- ✅ Multi-stage builds for smaller images
- ✅ Run as non-root user
- ✅ .dockerignore to exclude unnecessary files
- ✅ Health checks for all services
- ✅ Secrets management (not in environment variables)
- ❌ Avoid: COPY . . before dependencies
- ❌ Avoid: Running as root
- ❌ Avoid: Large base images (use alpine/slim)
````

**Assignment**: Add to custom `devops-engineer` agent.

## Skill Categories

Choose the appropriate category for your skill:

**Built-in Categories**:
- `analysis` - Requirements, planning, problem analysis
- `architecture` - System design, API design, patterns
- `implementation` - Coding practices, refactoring, specific languages/frameworks
- `testing` - Test strategies, coverage, quality assurance
- `documentation` - Writing, API docs, user guides
- `ui-design` - Interface design, UX patterns
- `database` - Schema design, queries, optimization

**Custom Categories**:
- `security` - Security practices, auditing
- `devops` - Deployment, CI/CD, infrastructure
- `performance` - Optimization, profiling, scaling
- `data-science` - ML, data analysis, visualization
- `mobile` - iOS, Android, mobile-specific practices

## Skill Quality Checklist

Before finalizing a custom skill, verify:

- [ ] Frontmatter has all required fields
- [ ] Description is clear and concise (< 1024 chars)
- [ ] Category is appropriate
- [ ] Required tools listed accurately
- [ ] Purpose section is 2-3 sentences
- [ ] "When to Use" has 3-5 specific scenarios
- [ ] Key capabilities listed (3-5 items)
- [ ] Approach has clear steps (3-7)
- [ ] Example is practical and complete
- [ ] Best practices include DOs and DON'Ts
- [ ] Content is 1-2 pages (not too long)
- [ ] Language is clear, no unexplained jargon
- [ ] Registered in skills.json
- [ ] Assigned to appropriate agents
- [ ] Tested with actual task

## Skills Maintenance

### Updating Skills

To update a skill:

1. Edit `.claude/skills/{skill-directory}/SKILL.md`
2. No regeneration needed (changes take effect immediately)
3. Test with: `cmat.sh skills load {skill-directory}`

### Adding Skills to More Agents

1. Edit agent `.md` files to add skill to `skills` array
2. Run: `cmat.sh agents generate-json`
3. Verify: `cmat.sh skills get {agent-name}`

### Removing Skills

1. Remove from agent `.md` files
2. Run: `cmat.sh agents generate-json`
3. Optionally delete skill directory and entry in skills.json

### Version Control

**Recommended**:
- ✅ Commit all changes to `.claude/skills/`
- ✅ Include skills.json and agents.json in version control
- ✅ Document skill updates in CHANGELOG
- ✅ Review skill changes in pull requests

**Be Careful**:
- Don't commit sensitive information in skills
- Test skills before committing
- Coordinate skill changes across team

---

## Skills Best Practices Summary

### DO:
- ✅ Create focused, single-purpose skills
- ✅ Provide concrete, practical examples
- ✅ Keep skills concise (1-2 pages)
- ✅ Assign 2-4 skills per agent
- ✅ Test skills with real tasks
- ✅ Update skills as practices evolve
- ✅ Use clear, simple language
- ✅ Include both positive and negative examples

### DON'T:
- ❌ Make skills too broad or generic
- ❌ Duplicate content across skills
- ❌ Assign all skills to all agents
- ❌ Include sensitive or proprietary information
- ❌ Forget to regenerate agents.json after changes
- ❌ Create skills without testing them

---

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
jq '.' .claude/agents/agent_contracts.json

# Check specific agent contract
jq '.agents."requirements-analyst"' .claude/agents/agent_contracts.json

# Verify all agents have required fields
jq '.agents | to_entries[] | select(.value.outputs.root_document == null) | .key' .claude/agents/agent_contracts.json
# Should return empty (all agents have root_document)
```

### 3. Test Agent Launch

Launch each agent with a simple task to verify customizations are accessible:

```bash
# Test requirements analyst
.claude/scripts/cmat.sh queue add \
  "Test task" \
  "requirements-analyst" \
  "normal" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Test agent customization"

.claude/scripts/cmat.sh queue start <task_id>
```

### 4. Test Contract Validation

```bash
# Test output validation
.claude/scripts/cmat.sh workflow validate \
  "requirements-analyst" \
  "enhancements/demo-test"

# Test next agent determination
.claude/scripts/cmat.sh workflow next-agent \
  "requirements-analyst" \
  "READY_FOR_DEVELOPMENT"
# Should output: architect

# Test path building
.claude/scripts/cmat.sh workflow next-source \
  "demo-test" \
  "architect" \
  "requirements-analyst"
# Should output: enhancements/demo-test/requirements-analyst/analysis_summary.md
```

### 5. Test Complete Workflow

Run through a complete workflow with the demo enhancement to verify all customizations work together:

```bash
# Use demo-test enhancement as validation
.claude/scripts/cmat.sh queue add \
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

Add project-specific states to `workflow_states.json`:

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

**To add custom fields**, modify validation in `.claude/scripts/workflow-commands.sh`:

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
- [ ] JSON syntax is valid: `jq '.' .claude/agents/agent_contracts.json`

### Workflow Validation Checklist

- [ ] All states in workflow_states.json are reachable
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
jq '.' .claude/agents/agent_contracts.json

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
jq '.agents | keys' .claude/agents/agent_contracts.json

# Verify agent name matches exactly (case-sensitive)
# Check agent .md file name matches contract key
```

### Validation Always Fails

**Problem**: Output validation fails even when files exist

**Solution**:
```bash
# Check what contract expects
jq '.agents."your-agent".outputs' .claude/agents/agent_contracts.json

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
jq '.agents."current-agent".statuses.success' .claude/agents/agent_contracts.json

# Verify status code exactly matches
# Check next_agents array contains expected agent
```

---

## Migration from v1.0

If you're upgrading from the original template:

### 1. Add agent_contracts.json

Create the contracts file with your 5 core agents plus any custom agents.

### 2. Enhance Agent .md Files

Add the new sections to each agent:
- Contract reference
- When to Use This Agent
- Workflow Position
- Output Requirements

### 3. Create WORKFLOW_GUIDE.md

Move content from old `AGENT_ROLE_MAPPING.md` to the new guide.

### 4. Update Scripts (v4.0)

The modular script system in `.claude/scripts/` includes all necessary contract validation functions. No replacement needed - the v3.0 system is already up to date.

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