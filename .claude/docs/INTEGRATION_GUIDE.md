# Integration Guide

Complete guide to external system integration in Claude Multi-Agent Template v3.0.

## Table of Contents

- [Overview](#overview)
- [Integration Agents](#integration-agents)
- [GitHub Integration](#github-integration)
- [Atlassian Integration](#atlassian-integration)
- [Integration Workflow](#integration-workflow)
- [Configuration](#configuration)
- [Automation Control](#automation-control)
- [Troubleshooting](#troubleshooting)

---

## Overview

The integration system synchronizes the internal multi-agent workflow with external project management and collaboration platforms. It maintains bidirectional traceability between internal work and external systems.

### Supported Integrations

**GitHub** (via github-mcp):
- Create and update issues
- Create and manage pull requests
- Apply labels and milestones
- Add comments and track status
- Link commits and branches

**Atlassian** (via atlassian-mcp):
- Create and update Jira tickets
- Transition ticket workflow states
- Publish documentation to Confluence
- Maintain cross-references
- Track sprint assignments

### Integration Benefits

- **Visibility**: Work tracked in team's existing tools
- **Traceability**: Links between all systems (internal, GitHub, Jira)
- **Automation**: Reduces manual status updates
- **Consistency**: Single source of truth
- **Collaboration**: Team sees progress in familiar tools

---

## Integration Agents

The system includes two specialized integration coordinator agents:

### github-integration-coordinator

**Role**: Synchronize with GitHub

**Responsibilities**:
- Create GitHub issues from requirements
- Create pull requests from implementations
- Update issue status based on workflow state
- Post comments with progress updates
- Apply labels for workflow stages
- Link issues to PRs

**Contract**: `.claude/AGENT_CONTRACTS.json → agents.github-integration-coordinator`

**Configuration**: `.claude/mcp-servers/github-config.json`

### atlassian-integration-coordinator

**Role**: Synchronize with Jira and Confluence

**Responsibilities**:
- Create Jira tickets from requirements
- Update ticket status through workflow
- Publish architecture docs to Confluence
- Publish user documentation to Confluence
- Maintain cross-references
- Track sprint assignments

**Contract**: `.claude/AGENT_CONTRACTS.json → agents.atlassian-integration-coordinator`

**Configuration**: `.claude/mcp-servers/atlassian-config.json`

---

## GitHub Integration

### Setup

#### 1. Install GitHub MCP Server

```bash
cd .claude/mcp-servers
npm install @modelcontextprotocol/server-github
```

#### 2. Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name: "Claude Multi-Agent Integration"
4. Scopes:
   - ✅ `repo` - Full control of private repositories
   - ✅ `write:discussion` - Write discussions
   - ✅ `project` - Full control of projects
5. Generate token and save securely

#### 3. Configure Environment

Add to your shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### 4. Configure MCP Server

Create or edit `.claude/mcp-servers/github-config.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": [
        "/absolute/path/to/.claude/mcp-servers/node_modules/@modelcontextprotocol/server-github/dist/index.js"
      ],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  },
  "settings": {
    "default_owner": "your-username",
    "default_repo": "your-repository",
    "default_branch": "main",
    "auto_labels": ["multi-agent", "automated"],
    "label_mapping": {
      "READY_FOR_DEVELOPMENT": ["ready-for-dev", "requirements-complete"],
      "READY_FOR_IMPLEMENTATION": ["architecture-complete", "ready-to-code"],
      "READY_FOR_TESTING": ["implementation-complete", "needs-testing"],
      "TESTING_COMPLETE": ["tests-passing", "ready-to-merge"],
      "DOCUMENTATION_COMPLETE": ["documented", "ready-to-close"]
    }
  }
}
```

#### 5. Test Configuration

```bash
# Test GitHub authentication
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Should return your GitHub user info

# Test with agent (dry run)
echo "test" > test.md
TASK_ID=$(cmat.sh queue add \
  "Test GitHub" \
  "github-integration-coordinator" \
  "normal" \
  "integration" \
  "test.md" \
  "Test GitHub integration")

cmat.sh queue start $TASK_ID
```

### GitHub Integration Workflow

#### After Requirements Analysis → READY_FOR_DEVELOPMENT

**Actions**:
1. Extract requirements from `analysis_summary.md`
2. Create GitHub issue:
   - Title: Feature name
   - Body: Problem statement, acceptance criteria
   - Labels: `enhancement`, `ready-for-dev`, priority
   - Assignee: (if configured)
3. Store issue number in task metadata
4. Post confirmation comment with internal task ID

**Output**:
```
INTEGRATION_COMPLETE

GitHub Issue: #145
https://github.com/owner/repo/issues/145

Labels: enhancement, ready-for-dev, priority:high
Acceptance Criteria: 3 items
Cross-reference: Internal task task_1234567890_12345
```

#### After Architecture Design → READY_FOR_IMPLEMENTATION

**Actions**:
1. Find GitHub issue from task metadata
2. Post comment with architecture summary
3. Add label: `architecture-complete`
4. Update milestone (if configured)

**Output**:
```
INTEGRATION_COMPLETE

Updated GitHub Issue: #145
Architecture design comment posted
Label added: architecture-complete
```

#### After Implementation → READY_FOR_TESTING

**Actions**:
1. Find GitHub issue from task metadata
2. Create pull request:
   - Title: Feature name
   - Body: Implementation summary, test notes
   - "Closes #145" reference
   - Labels: `ready-for-review`
   - Link to Jira ticket
3. Store PR number in task metadata
4. Update issue with PR link

**Output**:
```
INTEGRATION_COMPLETE

GitHub Pull Request: #156
https://github.com/owner/repo/pull/156

Linked to Issue: #145
Status: Open, awaiting review
```

#### After Testing → TESTING_COMPLETE

**Actions**:
1. Find PR from task metadata
2. Post comment with test results
3. Add labels: `tests-passing`, `qa-approved`
4. Request review (if configured)

**Output**:
```
INTEGRATION_COMPLETE

Updated Pull Request: #156
Test results: All tests passed (95% coverage)
Labels: tests-passing, qa-approved
Status: Ready to merge
```

#### After Documentation → DOCUMENTATION_COMPLETE

**Actions**:
1. Find issue and PR from task metadata
2. Post final documentation comment
3. Add label: `documented`
4. Close issue (references merged PR)

**Output**:
```
INTEGRATION_COMPLETE

Closed GitHub Issue: #145
Merged Pull Request: #156
Documentation published
Feature complete
```

### GitHub Best Practices

**Issue Creation**:
- ✅ Clear, concise titles (50 chars)
- ✅ Detailed description with acceptance criteria
- ✅ Appropriate labels and priority
- ✅ Cross-reference internal task ID
- ❌ Avoid generic titles ("Update", "Fix bug")
- ❌ Avoid missing acceptance criteria

**Pull Request Creation**:
- ✅ Descriptive title matching issue
- ✅ Summary of changes (bullet list)
- ✅ Testing notes and coverage
- ✅ "Closes #123" reference
- ❌ Avoid missing issue reference
- ❌ Avoid untested PRs

---

## Atlassian Integration

### Setup

#### 1. Install Atlassian MCP Server

```bash
cd .claude/mcp-servers
# Follow atlassian-mcp installation instructions
# (See MCP_INTEGRATION_QUICKSTART.md for details)
```

#### 2. Create Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name: "Claude Multi-Agent Integration"
4. Copy token and save securely

#### 3. Configure Environment

Add to your shell profile:

```bash
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your_token_here"
export JIRA_SITE_URL="https://your-company.atlassian.net"
```

Reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### 4. Configure MCP Server

Create or edit `.claude/mcp-servers/atlassian-config.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "node",
      "args": [
        "/absolute/path/to/.claude/mcp-servers/atlassian-mcp/dist/index.js"
      ],
      "env": {
        "JIRA_EMAIL": "${JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}",
        "JIRA_SITE_URL": "${JIRA_SITE_URL}"
      }
    }
  },
  "jira": {
    "default_project": "PROJ",
    "default_issue_type": "Story",
    "status_mapping": {
      "READY_FOR_DEVELOPMENT": "To Do",
      "READY_FOR_IMPLEMENTATION": "In Progress",
      "READY_FOR_TESTING": "In Review",
      "TESTING_COMPLETE": "Testing",
      "DOCUMENTATION_COMPLETE": "Done"
    }
  },
  "confluence": {
    "default_space": "PROJ",
    "default_parent_page": "123456789",
    "page_labels": ["multi-agent", "automated"]
  }
}
```

#### 5. Test Configuration

```bash
# Test Jira authentication
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/rest/api/3/myself"

# Should return your Jira user info

# Test with agent (dry run)
TASK_ID=$(cmat.sh queue add \
  "Test Jira" \
  "atlassian-integration-coordinator" \
  "normal" \
  "integration" \
  "test.md" \
  "Test Jira integration")

cmat.sh queue start $TASK_ID
```

### Jira Integration Workflow

#### After Requirements Analysis → READY_FOR_DEVELOPMENT

**Actions**:
1. Extract requirements from `analysis_summary.md`
2. Create Jira ticket (Story):
   - Summary: Feature name
   - Description: Jira-formatted with acceptance criteria
   - Issue Type: Story or Task
   - Priority: Mapped from internal priority
   - Labels: `multi-agent`, `automated`
   - Link to GitHub issue
3. Store ticket key in task metadata
4. Assign to sprint (if configured)

**Output**:
```
INTEGRATION_COMPLETE

Jira Ticket: PROJ-456
https://company.atlassian.net/browse/PROJ-456

Type: Story
Priority: High
Status: To Do
Labels: multi-agent, automated, enhancement
```

#### After Architecture Design → READY_FOR_IMPLEMENTATION

**Actions**:
1. Find Jira ticket from task metadata
2. Transition status: `To Do` → `In Progress`
3. Post comment with architecture approach
4. Publish architecture to Confluence:
   - Create page in project space
   - Title: "{Feature} - Architecture Design"
   - Content: Implementation plan
   - Labels: `architecture`, `design`
   - Link to Jira ticket
5. Update Jira with Confluence link

**Output**:
```
INTEGRATION_COMPLETE

Updated Jira Ticket: PROJ-456
Status: To Do → In Progress

Confluence Page Created:
Title: "User Profile - Architecture Design"
URL: https://company.atlassian.net/wiki/spaces/PROJ/pages/123456

Cross-referenced in Jira
```

#### After Implementation → READY_FOR_TESTING

**Actions**:
1. Find Jira ticket from task metadata
2. Transition status: `In Progress` → `In Review`
3. Post comment with implementation summary
4. Link GitHub PR

**Output**:
```
INTEGRATION_COMPLETE

Updated Jira Ticket: PROJ-456
Status: In Progress → In Review
GitHub PR linked: #156
```

#### After Testing → TESTING_COMPLETE

**Actions**:
1. Find Jira ticket from task metadata
2. Transition status: `In Review` → `Testing` (or `Done`)
3. Post comment with test results
4. Add label: `qa-approved` (if passed)

**Output**:
```
INTEGRATION_COMPLETE

Updated Jira Ticket: PROJ-456
Status: Testing → Done
Test results: All passed (95% coverage)
Label: qa-approved
```

#### After Documentation → DOCUMENTATION_COMPLETE

**Actions**:
1. Find Jira ticket from task metadata
2. Publish user documentation to Confluence:
   - Create page in user docs space
   - Title: "{Feature} - User Guide"
   - Content: User documentation
   - Labels: `user-documentation`
   - Link to Jira
3. Update Jira with documentation link
4. Add label: `documented`
5. Transition to `Done` (if not already)

**Output**:
```
INTEGRATION_COMPLETE

Jira Ticket: PROJ-456
Status: Done

Confluence Pages:
- Architecture: .../architecture
- User Guide: .../userguide

Feature complete in all systems
```

### Confluence Best Practices

**Page Creation**:
- ✅ Descriptive titles with feature name
- ✅ Info macro noting auto-generation
- ✅ Clear section headings (h2)
- ✅ Links to Jira and GitHub
- ✅ Appropriate labels
- ❌ Avoid generic titles ("Documentation")
- ❌ Avoid walls of unformatted text

---

## Integration Workflow

### Automatic Integration

Integration tasks are created automatically by the `on-subagent-stop.sh` hook when:
1. Task completes with specific status
2. Status requires external sync
3. AUTO_INTEGRATE is not set to "never"

**Trigger Statuses**:
- `READY_FOR_DEVELOPMENT` - Create issue/ticket
- `READY_FOR_IMPLEMENTATION` - Update status
- `READY_FOR_TESTING` - Create PR
- `TESTING_COMPLETE` - Post results
- `DOCUMENTATION_COMPLETE` - Close issue, publish docs

### Manual Integration

#### Sync Single Task
```bash
# Sync specific completed task
cmat.sh integration sync task_1234567890_12345
```

#### Sync All Unsynced Tasks
```bash
# Find and sync all tasks needing integration
cmat.sh integration sync-all

# Output:
# 🔍 Scanning for tasks requiring integration...
# 🔗 Creating integration for task_123 (READY_FOR_DEVELOPMENT)
# 🔗 Creating integration for task_456 (TESTING_COMPLETE)
# ✅ Created 2 integration tasks
```

#### Create Integration Task Manually
```bash
# Create integration task for specific status
cmat.sh integration add \
  "READY_FOR_DEVELOPMENT" \
  "enhancements/feature/requirements-analyst/analysis_summary.md" \
  "requirements-analyst" \
  "task_1234567890_12345"
```

### Integration Task Execution

Integration tasks execute like normal tasks:

```bash
# Check pending integrations
cmat.sh queue list pending | jq '.[] | select(.assigned_agent | contains("integration"))'

# Start integration task
cmat.sh queue start task_integration_12345

# Monitor
cmat.sh queue status
```

---

## Configuration

### Status Mapping

Map internal workflow statuses to external system states:

**GitHub** (`.claude/mcp-servers/github-config.json`):
```json
{
  "label_mapping": {
    "READY_FOR_DEVELOPMENT": ["ready-for-dev", "requirements-complete"],
    "READY_FOR_IMPLEMENTATION": ["architecture-complete"],
    "READY_FOR_TESTING": ["needs-testing"],
    "TESTING_COMPLETE": ["tests-passing", "qa-approved"],
    "DOCUMENTATION_COMPLETE": ["documented"]
  }
}
```

**Jira** (`.claude/mcp-servers/atlassian-config.json`):
```json
{
  "status_mapping": {
    "READY_FOR_DEVELOPMENT": "To Do",
    "READY_FOR_IMPLEMENTATION": "In Progress",
    "READY_FOR_TESTING": "In Review",
    "TESTING_COMPLETE": "Testing",
    "DOCUMENTATION_COMPLETE": "Done"
  }
}
```

**Important**: Jira status names must match your Jira workflow exactly (case-sensitive).

### Project Configuration

Set default project/repository for each integration:

**GitHub**:
```json
{
  "settings": {
    "default_owner": "your-github-username",
    "default_repo": "your-repository-name",
    "default_branch": "main"
  }
}
```

**Jira**:
```json
{
  "jira": {
    "default_project": "PROJ",
    "default_issue_type": "Story"
  }
}
```

**Confluence**:
```json
{
  "confluence": {
    "default_space": "PROJ",
    "default_parent_page": "123456789"
  }
}
```

---

## Automation Control

### AUTO_INTEGRATE Environment Variable

Control automatic integration task creation:

```bash
# Always create integration tasks automatically
export AUTO_INTEGRATE="always"

# Never create integration tasks (manual only)
export AUTO_INTEGRATE="never"

# Prompt user for each integration (default)
export AUTO_INTEGRATE="prompt"
```

**Examples**:

**Always Integrate**:
```bash
export AUTO_INTEGRATE="always"
TASK_ID=$(cmat.sh queue add ... true true)
cmat.sh queue start $TASK_ID
# Integration tasks created automatically
# No prompts
```

**Never Integrate**:
```bash
export AUTO_INTEGRATE="never"
TASK_ID=$(cmat.sh queue add ... true true)
cmat.sh queue start $TASK_ID
# No integration tasks created
# Sync manually later with: cmat.sh integration sync-all
```

**Prompt Mode** (default):
```bash
# AUTO_INTEGRATE not set or set to "prompt"
TASK_ID=$(cmat.sh queue add ... true true)
cmat.sh queue start $TASK_ID
# When status needs integration:
# "Create integration task? [Y/n]: "
```

### Per-Session Control

```bash
# Disable for testing
export AUTO_INTEGRATE="never"
./run_tests.sh

# Re-enable for production
export AUTO_INTEGRATE="always"
./deploy.sh
```

---

## Troubleshooting

### Authentication Failures

**Symptoms**: "401 Unauthorized" or "403 Forbidden"

**GitHub**:
```bash
# Verify token is set
echo $GITHUB_TOKEN
# Should show: ghp_...

# Test authentication
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# If fails:
# 1. Check token hasn't expired
# 2. Regenerate token with correct scopes
# 3. Update GITHUB_TOKEN environment variable
```

**Jira**:
```bash
# Verify credentials
echo $JIRA_EMAIL
echo $JIRA_API_TOKEN
echo $JIRA_SITE_URL

# Test authentication
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$JIRA_SITE_URL/rest/api/3/myself"

# If fails:
# 1. Check token hasn't been revoked
# 2. Verify email matches Atlassian account
# 3. Confirm site URL is correct
```

### Integration Tasks Failing

**Symptoms**: Integration tasks in failed_tasks

**Debug**:
```bash
# Find failed integration
cmat.sh queue list failed | jq '.[] | select(.assigned_agent | contains("integration"))'

# Check log
LOG=$(cmat.sh queue list failed | jq -r '.[-1].id' | xargs -I {} find enhancements -name "*{}_*.log")
tail -100 "$LOG"

# Common issues:
# - Authentication (see above)
# - API rate limits
# - Invalid project/repo names
# - Missing permissions
```

### GitHub API Rate Limits

**Symptoms**: "403 API rate limit exceeded"

**Solution**:
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Authenticated: 5000 requests/hour
# Unauthenticated: 60 requests/hour

# If exceeded:
# 1. Wait for reset (shown in response)
# 2. Use authentication (if not already)
# 3. Reduce integration frequency
# 4. Batch operations
```

### Jira Workflow Transition Errors

**Symptoms**: "Cannot transition ticket to X"

**Causes**:
1. Target status not in workflow
2. Current status doesn't allow transition
3. Required fields not populated
4. Transition name incorrect

**Debug**:
```bash
# Check ticket's current status
# Check Jira workflow configuration
# Verify status_mapping in atlassian-config.json
# Ensure transition names match exactly

# Fix status_mapping:
vim .claude/mcp-servers/atlassian-config.json
# Update status names to match Jira workflow
```

### Missing Cross-References

**Symptoms**: GitHub issues not linked to Jira, or vice versa

**Cause**: Integration tasks ran in wrong order or failed

**Solution**:
```bash
# Manually update metadata
TASK_ID="task_123"
cmat.sh queue metadata $TASK_ID github_issue "145"
cmat.sh queue metadata $TASK_ID jira_ticket "PROJ-456"

# Re-run integration
cmat.sh integration sync $TASK_ID
```

### Duplicate Issues/Tickets

**Symptoms**: Multiple issues created for same enhancement

**Cause**: Integration ran multiple times or task recreated

**Prevention**:
```bash
# Check if integration already exists
cmat.sh queue list all | jq '.completed[] | 
  select(.metadata.github_issue != null) | 
  select(.source_file == "enhancements/feature/...")' 

# If exists, don't create new integration task
```

**Cleanup**:
- Close duplicate GitHub issues manually
- Link primary issue in ticket description
- Update task metadata to reference correct issue/ticket

---

## Further Reading

- **[MCP_INTEGRATION_QUICKSTART.md](../mcp-servers/MCP_INTEGRATION_QUICKSTART.md)** - Quick setup guide
- **[github-integration-coordinator.md](../agents/github-integration-coordinator.md)** - GitHub agent details
- **[atlassian-integration-coordinator.md](../agents/atlassian-integration-coordinator.md)** - Atlassian agent details
- **[QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md)** - Task queue operations
- **[SCRIPTS_REFERENCE.md](../SCRIPTS_REFERENCE.md)** - Integration commands

---

**Version**: 3.0.0  
**Last Updated**: 2025-10-24