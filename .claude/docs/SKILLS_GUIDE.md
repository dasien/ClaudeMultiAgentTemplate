# Skills System Guide

Complete guide to the Skills System in Claude Multi-Agent Template v3.0.

## Table of Contents

- [Overview](#overview)
- [How Skills Work](#how-skills-work)
- [Built-in Skills](#built-in-skills)
- [Using Skills](#using-skills)
- [Creating Custom Skills](#creating-custom-skills)
- [Managing Skills](#managing-skills)
- [Skills by Category](#skills-by-category)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Skills System provides specialized domain expertise to agents through modular, reusable skill definitions. Skills are automatically injected into agent prompts, enhancing their capabilities with proven methodologies and best practices.

### What are Skills?

Skills are self-contained knowledge modules that provide:
- **Specific Expertise**: Focused knowledge on a particular domain or technique
- **Proven Methods**: Step-by-step approaches based on best practices
- **Practical Examples**: Concrete code and pattern examples
- **Clear Guidance**: When and how to apply the skill

### Key Benefits

- **Consistency**: All agents use the same proven approaches
- **Quality**: Expertise codified in reusable form
- **Extensibility**: Easy to add domain-specific knowledge
- **Maintainability**: Update skills once, applies to all agents
- **Modularity**: Mix and match skills per agent role

---

## How Skills Work

### 1. Skills Registration

Skills are registered in `.claude/skills/skills.json`:

```json
{
  "version": "1.0.0",
  "skills": [
    {
      "name": "Requirements Elicitation",
      "skill-directory": "requirements-elicitation",
      "category": "analysis",
      "required_tools": ["Read", "Write", "Grep"],
      "description": "Extract and clarify requirements from specifications"
    }
  ]
}
```

### 2. Skills Definition

Each skill has a `SKILL.md` file in its directory:

```
.claude/skills/
└── requirements-elicitation/
    └── SKILL.md         # Complete skill definition
```

The SKILL.md contains:
- YAML frontmatter (metadata)
- Purpose and when to use
- Key capabilities
- Step-by-step approach
- Practical examples
- Best practices

### 3. Agent Assignment

Agents are assigned skills in their frontmatter (`.claude/agents/*.md`):

```markdown
---
name: "Requirements Analyst"
skills: ["requirements-elicitation", "user-story-writing", "bug-triage"]
---
```

### 4. Automatic Injection

When an agent task starts:

1. System reads agent's assigned skills from agents.json
2. Loads each skill's SKILL.md content
3. Builds comprehensive skills section
4. Injects into agent's prompt automatically

**Example injection**:
```
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

---

# User Story Writing

## Purpose
Create well-structured user stories that clearly communicate user needs...

---

**Using Skills**: Apply the above skills as appropriate to accomplish your objectives.
```

### 5. Agent Application

The agent:
- Receives skills automatically in prompt
- Applies relevant skills to the task
- Documents which skills were used
- References skills in output

---

## Built-in Skills

The system includes 14 built-in skills organized by category:

### Analysis Skills (3)

**Requirements Elicitation** (`requirements-elicitation`)
- Extract functional and non-functional requirements
- Identify implicit requirements
- Clarify ambiguities
- Document acceptance criteria

**User Story Writing** (`user-story-writing`)
- Create "As a/I want/So that" format stories
- Write testable acceptance criteria
- Focus on user value
- Estimate complexity

**Bug Triage** (`bug-triage`)
- Reproduce bugs systematically
- Identify root causes
- Assess severity and impact
- Determine fix strategy

### Architecture Skills (2)

**API Design** (`api-design`)
- Design RESTful APIs
- Define resource models
- Choose HTTP methods correctly
- Design error responses

**System Architecture Patterns** (`architecture-patterns`)
- Apply proven patterns (MVC, layered, microservices)
- Define component boundaries
- Design for scalability and maintainability

### Implementation Skills (2)

**Error Handling Strategies** (`error-handling`)
- Implement robust error handling
- Validate inputs
- Provide clear error messages
- Design recovery mechanisms

**Code Refactoring** (`code-refactoring`)
- Improve code structure
- Extract methods
- Remove duplication
- Maintain testability

### Testing Skills (2)

**Test Design Patterns** (`test-design-patterns`)
- Apply AAA pattern (Arrange-Act-Assert)
- Create test fixtures
- Use mocking effectively
- Write maintainable tests

**Test Coverage Analysis** (`test-coverage`)
- Measure coverage effectively
- Identify critical untested code
- Prioritize testing efforts
- Improve coverage strategically

### Documentation Skills (2)

**Technical Writing** (`technical-writing`)
- Write clear, accessible documentation
- Organize information logically
- Provide practical examples
- Avoid jargon

**API Documentation** (`api-documentation`)
- Document function signatures
- Describe parameters and returns
- Provide usage examples
- Document error conditions

### UI Design Skills (2)

**Desktop UI Design** (`desktop-ui-design`)
- Design native desktop interfaces
- Follow platform conventions
- Organize layouts effectively
- Ensure keyboard accessibility

**Web UI Design** (`web-ui-design`)
- Design responsive web interfaces
- Follow modern UX principles
- Ensure accessibility (WCAG)
- Implement mobile-first design

### Database Skills (1)

**SQL Development** (`sql-development`)
- Design efficient schemas
- Write optimized queries
- Create appropriate indexes
- Follow normalization principles

---

## Using Skills

### Viewing Available Skills

```bash
# List all skills
cmat.sh skills list

# Output shows all 14 skills with metadata
```

### Checking Agent Skills

```bash
# See which skills an agent has
cmat.sh skills get requirements-analyst
# Output: ["requirements-elicitation", "user-story-writing", "bug-triage"]

cmat.sh skills get architect
# Output: ["api-design", "architecture-patterns", "desktop-ui-design", "web-ui-design"]

cmat.sh skills get implementer
# Output: ["error-handling", "code-refactoring", "sql-development"]
```

### Reading a Skill

```bash
# Load and view skill content
cmat.sh skills load requirements-elicitation

# Pipe to less for easier reading
cmat.sh skills load api-design | less
```

### Previewing Prompt Injection

```bash
# See complete skills section for an agent
cmat.sh skills prompt requirements-analyst

# Preview what architect receives
cmat.sh skills prompt architect | head -100
```

### Skills in Agent Execution

Skills are automatically used when agents run:

```bash
# Create task (skills auto-injected)
TASK_ID=$(cmat.sh queue add \
  "Analyze requirements" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/feature/feature.md" \
  "Initial analysis")

# Start task (agent receives skills automatically)
cmat.sh queue start $TASK_ID

# Agent's prompt includes:
# - Role definition
# - Task details
# - Skills section (all 3 analysis skills)
# - Source file content
```

### Skills in Agent Output

Agents should document which skills they applied:

**Example from analysis_summary.md**:
```markdown
---
enhancement: my-feature
agent: requirements-analyst
task_id: task_1234567890_12345
timestamp: 2025-10-24T14:30:00Z
status: READY_FOR_DEVELOPMENT
---

# Requirements Analysis Summary

[Analysis content...]

## Skills Applied

- ✅ **requirements-elicitation**: Extracted functional and non-functional requirements from specification
- ✅ **user-story-writing**: Created user stories with clear acceptance criteria
- 🔧 **bug-triage**: Not applicable for this task
```

---

## Creating Custom Skills

### Step 1: Use the Template

Copy the skill template:

```bash
cp SKILL_TEMPLATE.md .claude/skills/my-skill/SKILL.md
```

### Step 2: Define Your Skill

Edit `.claude/skills/my-skill/SKILL.md`:

```markdown
---
name: "My Custom Skill"
description: "One-line description (max 1024 chars)"
category: "implementation"
required_tools: ["Read", "Write", "Bash"]
---

# My Custom Skill

## Purpose
[2-3 sentences explaining what this enables]

## When to Use
[List of scenarios where appropriate]
- [Scenario 1]
- [Scenario 2]

## Key Capabilities
[3-5 main capabilities]

1. **[Capability 1]** - [Description]
2. **[Capability 2]** - [Description]

## Approach
[Step-by-step methodology]

1. [Step 1 with explanation]
2. [Step 2 with explanation]

## Example
**Context**: [When you'd use this]

**Approach**:
```
[Code or process example]
```

**Expected Result**: [What should happen]

## Best Practices
- ✅ [Do this]
- ❌ Avoid: [Don't do this]
```

### Step 3: Register the Skill

Add to `.claude/skills/skills.json`:

```json
{
  "skills": [
    {
      "name": "My Custom Skill",
      "skill-directory": "my-skill",
      "category": "implementation",
      "required_tools": ["Read", "Write", "Bash"],
      "description": "One-line description matching SKILL.md"
    }
  ]
}
```

### Step 4: Assign to Agents

Edit agent frontmatter in `.claude/agents/*.md`:

```markdown
---
name: "Implementer"
skills: ["error-handling", "code-refactoring", "sql-development", "my-skill"]
---
```

### Step 5: Regenerate agents.json

```bash
cmat.sh agents generate-json
```

### Step 6: Test the Skill

```bash
# Verify registration
cmat.sh skills list | grep "my-skill"

# Check agent assignment
cmat.sh skills get implementer
# Should include "my-skill"

# Preview injection
cmat.sh skills prompt implementer | grep -A 20 "My Custom Skill"
```

---

## Managing Skills

### Adding Skills to Agents

Edit the agent's .md file frontmatter:

```markdown
---
name: "Requirements Analyst"
skills: ["requirements-elicitation", "user-story-writing", "bug-triage", "new-skill"]
---
```

Then regenerate:
```bash
cmat.sh agents generate-json
```

### Removing Skills from Agents

Edit the agent's .md file frontmatter, remove skill from array, then regenerate.

### Updating Skill Content

Edit the skill's SKILL.md file directly. Changes take effect immediately (no regeneration needed).

### Organizing Custom Skills

**Recommended structure**:
```
.claude/skills/
├── skills.json                    # Registry (all skills)
├── requirements-elicitation/      # Built-in skills
├── ...
├── custom-domain-modeling/        # Your custom skills
├── custom-security-review/
└── custom-performance-tuning/
```

**Naming conventions**:
- Use lowercase with hyphens
- Be descriptive but concise
- Prefix custom skills with `custom-` to distinguish from built-ins

---

## Skills by Category

### When to Create Skills in Each Category

**Analysis** - Create when you need to:
- Define structured analysis methodologies
- Standardize requirements gathering approaches
- Codify bug investigation techniques

**Architecture** - Create when you need to:
- Document architecture patterns specific to your stack
- Define API design standards for your organization
- Codify infrastructure design approaches

**Implementation** - Create when you need to:
- Standardize coding patterns across team
- Document performance optimization techniques
- Define security implementation practices

**Testing** - Create when you need to:
- Standardize testing approaches
- Define coverage requirements
- Document testing patterns for specific frameworks

**Documentation** - Create when you need to:
- Define documentation standards
- Standardize formatting approaches
- Document style guides

**UI Design** - Create when you need to:
- Define design system guidelines
- Document component patterns
- Standardize accessibility practices

**Database** - Create when you need to:
- Define schema design patterns
- Document query optimization techniques
- Standardize migration approaches

**Custom Categories** - Create when:
- None of the above fit
- Define in skills.json: `"category": "security"`, `"category": "devops"`, etc.

---

## Best Practices

### Skill Design

**DO**:
- ✅ Keep skills focused on one specific domain/technique
- ✅ Provide concrete, practical examples
- ✅ Include step-by-step approaches
- ✅ Document when NOT to use the skill
- ✅ Use clear, simple language
- ✅ Include both DO and DON'T examples

**DON'T**:
- ❌ Make skills too broad or generic
- ❌ Include implementation-specific details (those belong in project docs)
- ❌ Duplicate content across skills
- ❌ Write overly long skills (target 1-2 pages)
- ❌ Use jargon without explanation

### Agent Assignment

**DO**:
- ✅ Assign 2-4 skills per agent (not too many)
- ✅ Choose skills directly relevant to agent's role
- ✅ Ensure skills complement each other
- ✅ Consider skill overlap between agents
- ✅ Review assignments periodically

**DON'T**:
- ❌ Assign all skills to all agents
- ❌ Assign irrelevant skills to pad numbers
- ❌ Forget to regenerate agents.json after changes
- ❌ Assign skills requiring tools the agent doesn't have

### Skill Maintenance

**DO**:
- ✅ Update skills when best practices change
- ✅ Add examples from real project use
- ✅ Incorporate team feedback
- ✅ Version skills.json when making major changes
- ✅ Document skill updates in CHANGELOG

**DON'T**:
- ❌ Change skill fundamentals without team review
- ❌ Remove skills still in use by agents
- ❌ Rename skill directories without updating all references
- ❌ Forget to test after major skill updates

### Skill Testing

```bash
# After creating/modifying a skill:

# 1. Test loading
cmat.sh skills load my-skill

# 2. Check agent assignment
cmat.sh skills get implementer

# 3. Preview prompt injection
cmat.sh skills prompt implementer | grep -A 30 "My Skill"

# 4. Run test task
TASK_ID=$(cmat.sh queue add \
  "Test skill" \
  "implementer" \
  "normal" \
  "implementation" \
  "test-file.md" \
  "Testing my-skill")
cmat.sh queue start $TASK_ID

# 5. Verify skill was used
grep "my-skill" enhancements/*/implementer/*.md
```

---

## Skills in Different Workflows

### Standard Feature Development

Each phase receives relevant skills:

1. **Requirements Analyst** + Analysis Skills
   - Requirements elicitation → Extract requirements
   - User story writing → Create user stories
   - Bug triage → (if applicable)

2. **Architect** + Architecture Skills
   - API design → Design endpoints
   - Architecture patterns → Choose patterns
   - UI design → Plan interface structure

3. **Implementer** + Implementation Skills
   - Error handling → Robust code
   - Code refactoring → Clean implementation
   - SQL development → (if database work)

4. **Tester** + Testing Skills
   - Test design patterns → Write tests
   - Test coverage → Measure coverage

5. **Documenter** + Documentation Skills
   - Technical writing → Clear docs
   - API documentation → Document APIs

### Bug Fix Workflow

Emphasizes diagnostic and implementation skills:

1. **Requirements Analyst** (triage focus)
   - **Bug triage** ← Primary skill
   - Requirements elicitation
   - User story writing

2. **Implementer** (fix focus)
   - **Error handling** ← Primary skill
   - Code refactoring
   - Testing patterns (if test needed)

### Architecture Review

Architecture-heavy workflow:

1. **Architect** (deep analysis)
   - **All architecture skills**
   - API design
   - Architecture patterns
   - UI design (all variants)

2. **Requirements Analyst** (validation)
   - Requirements elicitation
   - User story writing

---

## Example: Custom Security Skill

Here's a complete example of creating a domain-specific skill:

### 1. Create Directory and File

```bash
mkdir -p .claude/skills/security-audit
```

### 2. Write SKILL.md

**`.claude/skills/security-audit/SKILL.md`**:
```markdown
---
name: "Security Audit"
description: "Systematic security review of code and architecture for common vulnerabilities following OWASP Top 10"
category: "security"
required_tools: ["Read", "Grep", "WebSearch"]
---

# Security Audit

## Purpose
Conduct systematic security reviews to identify vulnerabilities, ensure secure coding practices, and verify compliance with security standards.

## When to Use
- Reviewing authentication/authorization code
- Auditing data handling and storage
- Evaluating API security
- Assessing cryptography usage
- Before production deployment

## Key Capabilities

1. **OWASP Top 10 Assessment** - Check for common web vulnerabilities
2. **Authentication Review** - Validate auth mechanisms
3. **Data Protection** - Ensure sensitive data is protected
4. **Input Validation** - Verify all inputs are sanitized

## Approach

1. **Identify Attack Surface**
   - List all entry points (APIs, forms, uploads)
   - Map data flows
   - Identify trust boundaries

2. **Check OWASP Top 10**
   - Injection flaws (SQL, XSS, etc.)
   - Broken authentication
   - Sensitive data exposure
   - XML external entities
   - Broken access control
   - Security misconfiguration
   - Cross-site scripting (XSS)
   - Insecure deserialization
   - Components with known vulnerabilities
   - Insufficient logging & monitoring

3. **Review Authentication**
   - Password requirements
   - Session management
   - Token generation and validation
   - Multi-factor authentication

4. **Validate Input Handling**
   - All inputs validated
   - Parameterized queries used
   - Output encoding applied
   - File uploads restricted

5. **Check Cryptography**
   - Strong algorithms used (no MD5, SHA1)
   - Proper key management
   - Secure random number generation
   - TLS/SSL configured correctly

6. **Document Findings**
   - Severity (Critical/High/Medium/Low)
   - Affected components
   - Exploitation risk
   - Remediation steps

## Example

**Context**: Reviewing a user login endpoint

**Security Checklist**:
```python
# ❌ VULNERABLE CODE
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    user = db.execute(query)
    if user:
        session['user_id'] = user.id
        return "Login successful"
    return "Invalid credentials"

# ✅ SECURE CODE
def login(username, password):
    # 1. Input validation
    if not username or not password:
        return "Missing credentials", 400
    
    # 2. Parameterized query (prevents SQL injection)
    query = "SELECT * FROM users WHERE username = ? AND password_hash = ?"
    user = db.execute(query, (username, hash_password(password)))
    
    # 3. Secure session management
    if user:
        session.regenerate()  # Prevent session fixation
        session['user_id'] = user.id
        audit_log("login_success", username)
        return "Login successful"
    
    # 4. Generic error (prevents username enumeration)
    audit_log("login_failed", username)
    return "Invalid credentials", 401
```

**Findings**:
- ✅ SQL injection prevented (parameterized query)
- ✅ Password hashing used
- ✅ Session regenerated on login
- ✅ Audit logging present
- ✅ Generic error messages

## Best Practices

- ✅ Always use parameterized queries or ORMs
- ✅ Hash passwords with bcrypt/argon2 (never store plaintext)
- ✅ Validate and sanitize ALL user inputs
- ✅ Use HTTPS for all sensitive operations
- ✅ Implement rate limiting on authentication
- ✅ Log security events
- ✅ Keep dependencies updated
- ❌ Avoid: Storing sensitive data in logs
- ❌ Avoid: Rolling your own cryptography
- ❌ Avoid: Trusting client-side validation alone
```

### 3. Register in skills.json

Add to `.claude/skills/skills.json`:
```json
{
  "skills": [
    {
      "name": "Security Audit",
      "skill-directory": "security-audit",
      "category": "security",
      "required_tools": ["Read", "Grep", "WebSearch"],
      "description": "Systematic security review following OWASP Top 10"
    }
  ]
}
```

### 4. Assign to Security-Reviewer Agent

Create or edit `.claude/agents/security-reviewer.md`:
```markdown
---
name: "Security Reviewer"
description: "Reviews code for security vulnerabilities"
tools: ["Read", "Grep", "WebSearch"]
skills: ["security-audit"]
---
```

### 5. Update Contracts

Add to `.claude/AGENT_CONTRACTS.json`:
```json
{
  "agents": {
    "security-reviewer": {
      "role": "security_review",
      "inputs": {...},
      "outputs": {...},
      "statuses": {...}
    }
  }
}
```

### 6. Test the Skill

```bash
# Generate agents.json
cmat.sh agents generate-json

# Verify skill exists
cmat.sh skills list | grep "security-audit"

# Check agent has skill
cmat.sh skills get security-reviewer

# Preview injection
cmat.sh skills prompt security-reviewer

# Use in workflow
cmat.sh queue add \
  "Security review" \
  "security-reviewer" \
  "critical" \
  "security_review" \
  "enhancements/feature/implementer/test_plan.md" \
  "Review authentication code"
```

---

## Troubleshooting

### Skill Not Appearing in List

**Problem**: `cmat.sh skills list` doesn't show my skill

**Solutions**:
```bash
# 1. Check skills.json syntax
jq '.' .claude/skills/skills.json

# 2. Verify skill entry exists
jq '.skills[] | select(.["skill-directory"] == "my-skill")' .claude/skills/skills.json

# 3. Check for typos in skill-directory name
ls .claude/skills/my-skill/SKILL.md
```

### Skill Not Assigned to Agent

**Problem**: Agent doesn't have skill in agents.json

**Solutions**:
```bash
# 1. Check agent .md frontmatter
head -20 .claude/agents/implementer.md

# 2. Verify skills array in frontmatter
grep "^skills:" .claude/agents/implementer.md

# 3. Regenerate agents.json
cmat.sh agents generate-json

# 4. Verify in agents.json
jq '.agents[] | select(.["agent-file"] == "implementer") | .skills' .claude/agents/agents.json
```

### Skill Not in Agent Prompt

**Problem**: Skills section not appearing in agent prompts

**Solutions**:
```bash
# 1. Test skills prompt generation
cmat.sh skills prompt implementer

# If empty output:
# 2. Check agent has skills in agents.json
cmat.sh skills get implementer

# 3. Verify SKILL.md files exist
ls .claude/skills/*/SKILL.md

# 4. Test skills system
cmat.sh skills test
```

### SKILL.md Not Loading

**Problem**: `cmat.sh skills load my-skill` fails

**Solutions**:
```bash
# 1. Verify file exists
ls -la .claude/skills/my-skill/SKILL.md

# 2. Check file permissions
chmod 644 .claude/skills/my-skill/SKILL.md

# 3. Verify no syntax errors in frontmatter
head -20 .claude/skills/my-skill/SKILL.md

# 4. Check directory name matches skills.json
jq -r '.skills[] | .["skill-directory"]' .claude/skills/skills.json | grep my-skill
```

### Skills Not Applied by Agent

**Problem**: Agent output doesn't mention skills used

**Possible Causes**:
1. Skills not relevant to task
2. Agent chose not to apply
3. Task too simple to need skills

**Not a System Error**: Agents decide when to apply skills based on task needs.

---

## Migration from v2.x

If upgrading from v2.x without skills:

### 1. Verify Skills Exist
```bash
ls .claude/skills/
# Should show: skills.json and skill directories
```

### 2. Check agents.json Has Skills
```bash
jq '.agents[0].skills' .claude/agents/agents.json
# Should show array, not null
```

### 3. Regenerate if Needed
```bash
# If skills missing from agents.json:
cmat.sh agents generate-json
```

### 4. Test System
```bash
cmat.sh skills test
```

### 5. Run Test Task
```bash
# Run demo-test to verify skills injection
TASK_ID=$(cmat.sh queue add \
  "Skills test" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Test skills system")

cmat.sh queue start $TASK_ID

# Check logs for skills section
grep -A 10 "SPECIALIZED SKILLS" enhancements/demo-test/logs/*.log
```

---

## Further Reading

- **[SKILL_TEMPLATE.md](SKILL_TEMPLATE.md)** - Template for creating skills
- **[SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md)** - Skills commands reference
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Customizing skills for your project
- **[.claude/agents/*.md](.claude/agents/)** - Agent definitions with skill assignments

---

**Version**: 3.0.0  
**Last Updated**: 2025-10-24