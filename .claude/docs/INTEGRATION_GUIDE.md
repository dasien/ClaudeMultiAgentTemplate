# Integration Guide

Complete guide to external system integration (GitHub, Jira, Confluence) in CMAT.

**Version**: 8.2.0

## Table of Contents

- [Overview](#overview)
- [Quickstart](#quickstart)
  - [GitHub Setup (5 min)](#github-setup-5-min)
  - [Atlassian Setup (10 min)](#atlassian-setup-10-min)
- [Integration Agents](#integration-agents)
- [GitHub Integration](#github-integration)
- [Atlassian Integration](#atlassian-integration)
- [Integration Workflow](#integration-workflow)
- [Configuration Reference](#configuration-reference)
- [Automation Control](#automation-control)
- [Troubleshooting](#troubleshooting)

---

## Overview

The integration system synchronizes CMAT workflows with external project management platforms. It maintains bidirectional traceability between internal work and external systems.

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

## Quickstart

Get GitHub and Jira/Confluence integration up and running in 15 minutes.

### Prerequisites

- Node.js 16 or higher
- GitHub account with admin access to repository
- Jira/Confluence access (for Atlassian integration)

### What You'll Get

After completing this guide:
- GitHub issues created automatically from requirements
- Pull requests created from implementations
- Jira tickets synced with workflow status
- Documentation published to Confluence
- Full traceability across all systems

---

### GitHub Setup (5 min)

#### Step 1: Install MCP Server

```bash
cd .claude/mcp-servers
npm install @modelcontextprotocol/server-github
```

#### Step 2: Create GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "Claude Multi-Agent"
4. Select scopes:
   - `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy token immediately** (you won't see it again)

#### Step 3: Configure Environment

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### Step 4: Configure MCP Server

Create `.claude/mcp-servers/github-config.json`:

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
    "default_owner": "your-github-username",
    "default_repo": "your-repository",
    "default_branch": "main",
    "auto_labels": ["multi-agent", "automated"]
  }
}
```

**Update**:
- Replace `/absolute/path/to/` with your actual path
- Set `default_owner` to your GitHub username
- Set `default_repo` to your repository name

#### Step 5: Test

```bash
# Test authentication
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
# Should show your GitHub user info
```

GitHub integration ready!

---

### Atlassian Setup (10 min)

#### Step 1: Get Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name: "Claude Multi-Agent"
4. Click "Create"
5. **Copy token immediately**

#### Step 2: Configure Environment

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your_token_here"
export JIRA_SITE_URL="https://your-company.atlassian.net"
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### Step 3: Install Atlassian MCP Server

**Option A: Use npm package** (if available):
```bash
cd .claude/mcp-servers
npm install @modelcontextprotocol/server-atlassian
```

**Option B: Build from source**:
```bash
cd .claude/mcp-servers
git clone https://github.com/modelcontextprotocol/servers.git mcp-servers-repo
cd mcp-servers-repo/src/atlassian
npm install
npm run build
cd ../../..
```

#### Step 4: Configure MCP Server

Create `.claude/mcp-servers/atlassian-config.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "node",
      "args": [
        "/absolute/path/to/.claude/mcp-servers/node_modules/@modelcontextprotocol/server-atlassian/dist/index.js"
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

**Update**:
- Replace `/absolute/path/to/` with your actual path
- Set `default_project` to your Jira project key
- Update `status_mapping` to match your Jira workflow states exactly
- Set `default_space` to your Confluence space key
- Set `default_parent_page` to parent page ID

#### Step 5: Find Your Jira Workflow States

```bash
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/rest/api/3/status"

# Update status_mapping to match your workflow exactly
```

#### Step 6: Find Confluence Parent Page ID

1. Go to Confluence space
2. Navigate to parent page where docs should be created
3. Click "..." -> "Page Information"
4. Copy page ID from URL: `/pages/viewinfo.action?pageId=123456789`

#### Step 7: Test

```bash
# Test Jira authentication
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/rest/api/3/myself"
# Should show your Jira user info
```

Atlassian integration ready!

---

### Enable Auto-Integration

```bash
# Add to ~/.bashrc or ~/.zshrc

# Always integrate (recommended for production)
export AUTO_INTEGRATE="always"

# Or prompt for each integration (recommended for testing)
export AUTO_INTEGRATE="prompt"

# Or never auto-integrate (manual only)
export AUTO_INTEGRATE="never"
```

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

**Configuration**: `.claude/mcp-servers/atlassian-config.json`

---

## GitHub Integration

### Integration Workflow

#### After Requirements Analysis (READY_FOR_DEVELOPMENT)

**Actions**:
1. Extract requirements from `analysis_summary.md`
2. Create GitHub issue:
   - Title: Feature name
   - Body: Problem statement, acceptance criteria
   - Labels: `enhancement`, `ready-for-dev`, priority
3. Store issue number in task metadata
4. Post confirmation comment with internal task ID

**Output**:
```
INTEGRATION_COMPLETE

GitHub Issue: #145
https://github.com/owner/repo/issues/145

Labels: enhancement, ready-for-dev, priority:high
Acceptance Criteria: 3 items
```

#### After Architecture (READY_FOR_IMPLEMENTATION)

**Actions**:
1. Find GitHub issue from task metadata
2. Post comment with architecture summary
3. Add label: `architecture-complete`
4. Update milestone (if configured)

#### After Implementation (READY_FOR_TESTING)

**Actions**:
1. Find GitHub issue from task metadata
2. Create pull request:
   - Title: Feature name
   - Body: Implementation summary, test notes
   - "Closes #145" reference
   - Labels: `ready-for-review`
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

#### After Testing (TESTING_COMPLETE)

**Actions**:
1. Find PR from task metadata
2. Post comment with test results
3. Add labels: `tests-passing`, `qa-approved`
4. Request review (if configured)

#### After Documentation (DOCUMENTATION_COMPLETE)

**Actions**:
1. Find issue and PR from task metadata
2. Post final documentation comment
3. Add label: `documented`
4. Close issue (references merged PR)

### GitHub Best Practices

**Issue Creation**:
- Clear, concise titles (50 chars)
- Detailed description with acceptance criteria
- Appropriate labels and priority
- Cross-reference internal task ID

**Pull Request Creation**:
- Descriptive title matching issue
- Summary of changes (bullet list)
- Testing notes and coverage
- "Closes #123" reference

---

## Atlassian Integration

### Jira Integration Workflow

#### After Requirements Analysis (READY_FOR_DEVELOPMENT)

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
```

#### After Architecture (READY_FOR_IMPLEMENTATION)

**Actions**:
1. Find Jira ticket from task metadata
2. Transition status: `To Do` -> `In Progress`
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
Status: To Do -> In Progress

Confluence Page Created:
Title: "User Profile - Architecture Design"
URL: https://company.atlassian.net/wiki/spaces/PROJ/pages/123456
```

#### After Implementation (READY_FOR_TESTING)

**Actions**:
1. Find Jira ticket from task metadata
2. Transition status: `In Progress` -> `In Review`
3. Post comment with implementation summary
4. Link GitHub PR

#### After Testing (TESTING_COMPLETE)

**Actions**:
1. Find Jira ticket from task metadata
2. Transition status: `In Review` -> `Testing` (or `Done`)
3. Post comment with test results
4. Add label: `qa-approved` (if passed)

#### After Documentation (DOCUMENTATION_COMPLETE)

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

### Confluence Best Practices

**Page Creation**:
- Descriptive titles with feature name
- Info macro noting auto-generation
- Clear section headings (h2)
- Links to Jira and GitHub
- Appropriate labels

---

## Integration Workflow

### Automatic Integration

Integration tasks are created automatically when:
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
python -m cmat integration sync <task_id>
```

#### Sync All Unsynced Tasks
```bash
# Find and sync all tasks needing integration
python -m cmat integration sync-all
```

---

## Configuration Reference

### GitHub Label Mapping

Map internal statuses to GitHub labels:

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

### Jira Status Mapping

Map internal statuses to Jira workflow states:

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
python -m cmat queue list failed

# Check task log in enhancements directory
```

**Common issues**:
- Authentication (see above)
- API rate limits
- Invalid project/repo names
- Missing permissions

### GitHub API Rate Limits

**Symptoms**: "403 API rate limit exceeded"

**Solution**:
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Authenticated: 5000 requests/hour
# Unauthenticated: 60 requests/hour

# If exceeded: wait for reset or reduce integration frequency
```

### Jira Workflow Transition Errors

**Symptoms**: "Cannot transition ticket to X"

**Causes**:
1. Target status not in workflow
2. Current status doesn't allow transition
3. Required fields not populated
4. Transition name incorrect

**Fix**:
```bash
# Check your workflow states:
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/rest/api/3/project/$PROJECT_KEY/statuses" | \
  jq '.[] | .name'

# Update status_mapping in atlassian-config.json
# Match status names exactly (case-sensitive)
```

### Missing Cross-References

**Symptoms**: GitHub issues not linked to Jira, or vice versa

**Cause**: Integration tasks ran in wrong order or failed

**Solution**:
```bash
# Update task metadata manually
python -m cmat queue metadata <task_id> github_issue "145"
python -m cmat queue metadata <task_id> jira_ticket "PROJ-456"

# Re-run integration
python -m cmat integration sync <task_id>
```

### Can't Find Confluence Parent Page ID

**Method 1 - From URL**:
- Open Confluence page
- Look at URL: `...pageId=123456789`
- Use that number

**Method 2 - From API**:
```bash
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/wiki/rest/api/space/$SPACE_KEY/content?type=page&title=Your+Page+Title" | \
  jq '.results[0].id'
```

---

## Security Best Practices

- **Never commit tokens** to version control
- **Use environment variables** for all credentials
- **Rotate tokens** regularly (every 90 days)
- **Limit token scopes** to minimum required
- **Use .gitignore** for config files with tokens

---

## Quick Reference

### Start with Integration

```bash
# Always integrate
export AUTO_INTEGRATE="always"

# Start workflow
python -m cmat workflow start new-feature-development my-feature

# Monitor progress
python -m cmat queue status
```

### Manual Integration

```bash
# Disable auto-integration
export AUTO_INTEGRATE="never"

# Run workflow
python -m cmat workflow start ...

# Sync after completion
python -m cmat integration sync-all
```

### Check Integration Status

```bash
# View task metadata
python -m cmat queue list completed

# Find integration tasks
python -m cmat queue list active
```

---

## External Resources

- **MCP Documentation**: https://modelcontextprotocol.io
- **GitHub API**: https://docs.github.com/rest
- **Jira API**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **Confluence API**: https://developer.atlassian.com/cloud/confluence/rest/v1/

---

## See Also

- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** - Complete command reference
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow orchestration
- **[QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md)** - Task queue management