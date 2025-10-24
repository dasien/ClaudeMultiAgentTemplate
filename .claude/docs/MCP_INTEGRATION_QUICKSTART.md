# MCP Integration Quickstart

Get GitHub and Jira/Confluence integration up and running in 15 minutes.

## What You'll Get

After completing this guide:
- ✅ GitHub issues created automatically from requirements
- ✅ Pull requests created from implementations
- ✅ Jira tickets synced with workflow status
- ✅ Documentation published to Confluence
- ✅ Full traceability across all systems

## Prerequisites

- Node.js 16 or higher
- GitHub account with admin access to repository
- Jira/Confluence access (for Atlassian integration)
- Claude Multi-Agent Template v3.0 installed

## GitHub Integration (5 minutes)

### Step 1: Install MCP Server

```bash
cd .claude/mcp-servers
npm install @modelcontextprotocol/server-github
```

### Step 2: Create GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "Claude Multi-Agent"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy token immediately** (you won't see it again)

### Step 3: Configure Environment

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### Step 4: Configure MCP Server

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

### Step 5: Test

```bash
# Test authentication
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Should show your GitHub user info

# Test with dry run
echo "test" > test.md
TASK_ID=$(cmat.sh queue add \
  "Test GitHub integration" \
  "github-integration-coordinator" \
  "normal" \
  "integration" \
  "test.md" \
  "Testing GitHub setup")

cmat.sh queue start $TASK_ID
```

✅ **GitHub integration ready!**

---

## Atlassian Integration (10 minutes)

### Step 1: Get Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name: "Claude Multi-Agent"
4. Click "Create"
5. **Copy token immediately**

### Step 2: Configure Environment

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

### Step 3: Install Atlassian MCP Server

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

### Step 4: Configure MCP Server

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
- Set `default_project` to your Jira project key (e.g., "MYPROJ")
- Update `status_mapping` to match your Jira workflow states exactly
- Set `default_space` to your Confluence space key
- Set `default_parent_page` to parent page ID (or remove if not needed)

### Step 5: Find Your Jira Workflow States

```bash
# List your Jira project's workflow
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/rest/api/3/status"

# Find your project's statuses and update status_mapping accordingly
```

**Common Jira Workflows**:

**Simple Workflow**:
- "To Do" → "In Progress" → "Done"

**Standard Workflow**:
- "To Do" → "In Progress" → "In Review" → "Testing" → "Done"

**Custom Workflow**:
- Check your Jira project settings

### Step 6: Find Confluence Parent Page ID

1. Go to Confluence space
2. Navigate to parent page where docs should be created
3. Click "..." → "Page Information"
4. Copy page ID from URL: `/pages/viewinfo.action?pageId=123456789`
5. Update `default_parent_page` in config

### Step 7: Test

```bash
# Test Jira authentication
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/rest/api/3/myself"

# Should show your Jira user info

# Test with dry run
TASK_ID=$(cmat.sh queue add \
  "Test Jira integration" \
  "atlassian-integration-coordinator" \
  "normal" \
  "integration" \
  "test.md" \
  "Testing Jira setup")

cmat.sh queue start $TASK_ID
```

✅ **Atlassian integration ready!**

---

## Enable Auto-Integration

### Set Integration Mode

```bash
# Add to ~/.bashrc or ~/.zshrc

# Always integrate (recommended for production)
export AUTO_INTEGRATE="always"

# Or prompt for each integration (recommended for testing)
export AUTO_INTEGRATE="prompt"

# Or never auto-integrate (manual only)
export AUTO_INTEGRATE="never"
```

Reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

---

## Test Complete Workflow

Now test the full workflow with integration:

```bash
# Enable integration
export AUTO_INTEGRATE="always"

# Create fully automated task
TASK_ID=$(cmat.sh queue add \
  "Test integration workflow" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/demo-test/demo-test.md" \
  "Complete workflow with integration" \
  true \
  true)

# Start and let it run
cmat.sh queue start $TASK_ID

# Monitor progress
watch -n 5 'cmat.sh queue status'
```

**What should happen**:
1. Requirements analyst runs → `READY_FOR_DEVELOPMENT`
2. **GitHub**: Issue #XXX created
3. **Jira**: Ticket PROJ-XXX created (status: To Do)
4. Architect runs → `READY_FOR_IMPLEMENTATION`
5. **Jira**: Ticket updated (status: In Progress)
6. **Confluence**: Architecture page published
7. Implementer runs → `READY_FOR_TESTING`
8. **Jira**: Ticket updated (status: In Review)
9. **GitHub**: PR #YYY created, linked to issue
10. Tester runs → `TESTING_COMPLETE`
11. **Jira**: Ticket updated (status: Testing or Done)
12. **GitHub**: PR updated with test results
13. Documenter runs → `DOCUMENTATION_COMPLETE`
14. **Confluence**: User documentation published
15. **Jira**: Ticket marked Done
16. **GitHub**: Issue closed, PR merged

---

## Verify Integration

### Check GitHub

```bash
# List recent issues
curl -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/your-username/your-repo/issues?state=open&labels=multi-agent" | \
  jq '.[] | {number, title, labels: [.labels[].name]}'

# Should show issue(s) created by integration
```

### Check Jira

1. Go to your Jira project
2. Look for tickets with label "multi-agent"
3. Verify status matches workflow progression
4. Check for links to GitHub

### Check Confluence

1. Go to your Confluence space
2. Navigate to parent page
3. Look for auto-generated child pages
4. Verify architecture and documentation pages

### Check Task Metadata

```bash
# View completed task with integration metadata
cmat.sh queue list completed | jq '.[-1] | {
  id,
  title,
  github_issue: .metadata.github_issue,
  github_pr: .metadata.github_pr,
  jira_ticket: .metadata.jira_ticket,
  confluence_page: .metadata.confluence_page
}'

# Should show populated metadata
```

---

## Troubleshooting

### GitHub: "401 Unauthorized"

**Fix**: Check token
```bash
echo $GITHUB_TOKEN
# Should show: ghp_...

# If empty, set it:
export GITHUB_TOKEN="ghp_your_token_here"
source ~/.bashrc
```

### Jira: "401 Unauthorized"

**Fix**: Check credentials
```bash
echo $JIRA_EMAIL
echo $JIRA_API_TOKEN
echo $JIRA_SITE_URL

# Test manually:
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$JIRA_SITE_URL/rest/api/3/myself"
```

### Jira: "Cannot transition issue"

**Fix**: Update status_mapping
```bash
# Get your workflow states:
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_SITE_URL/rest/api/3/project/$PROJECT_KEY/statuses" | \
  jq '.[] | .name'

# Update .claude/mcp-servers/atlassian-config.json
# Match status names exactly (case-sensitive)
```

### Integration tasks not being created

**Fix**: Check AUTO_INTEGRATE
```bash
echo $AUTO_INTEGRATE
# Should be: always, prompt, or never

# Set if missing:
export AUTO_INTEGRATE="prompt"
```

### Can't find Confluence parent page ID

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

## Configuration Templates

### Minimal GitHub Config

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["./node_modules/@modelcontextprotocol/server-github/dist/index.js"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  },
  "settings": {
    "default_owner": "username",
    "default_repo": "repo"
  }
}
```

### Minimal Atlassian Config

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "node",
      "args": ["./node_modules/@modelcontextprotocol/server-atlassian/dist/index.js"],
      "env": {
        "JIRA_EMAIL": "${JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}",
        "JIRA_SITE_URL": "${JIRA_SITE_URL}"
      }
    }
  },
  "jira": {
    "default_project": "PROJ",
    "status_mapping": {
      "READY_FOR_DEVELOPMENT": "To Do",
      "DOCUMENTATION_COMPLETE": "Done"
    }
  }
}
```

---

## Next Steps

### Production Setup

1. **Test thoroughly** with demo enhancements
2. **Adjust status mappings** to match your workflows
3. **Configure labels** for your team's taxonomy
4. **Set up automation** (`AUTO_INTEGRATE=always`)
5. **Document** team-specific procedures

### Advanced Configuration

See these guides for more:
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Complete integration documentation
- **[github-integration-coordinator.md](../agents/github-integration-coordinator.md)** - GitHub agent details
- **[atlassian-integration-coordinator.md](../agents/atlassian-integration-coordinator.md)** - Jira/Confluence details

### Security

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

# Create automated task
TASK_ID=$(cmat.sh queue add \
  "Feature name" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/feature/feature.md" \
  "Description" \
  true \
  true)

# Start
cmat.sh queue start $TASK_ID

# Monitor
cmat.sh queue status
```

### Manual Integration

```bash
# Disable auto-integration
export AUTO_INTEGRATE="never"

# Run workflow
cmat.sh queue add ... && cmat.sh queue start ...

# Sync after completion
cmat.sh integration sync-all
```

### Check Integration Status

```bash
# View metadata
cmat.sh queue list completed | jq '.[-1].metadata'

# Find integration tasks
cmat.sh queue list all | jq '.active[] | select(.assigned_agent | contains("integration"))'
```

---

## Support

**Common Issues**: See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Troubleshooting section

**MCP Documentation**: https://modelcontextprotocol.io

**GitHub API**: https://docs.github.com/rest

**Jira API**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

**Confluence API**: https://developer.atlassian.com/cloud/confluence/rest/v1/

---

**Setup Time**: ~15 minutes  
**Difficulty**: Beginner  
**Version**: 3.0.0  
**Last Updated**: 2025-10-24