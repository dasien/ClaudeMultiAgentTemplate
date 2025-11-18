# Enhancement Guide

This guide explains how to create and manage enhancements (features and bug fixes) in your project using the Claude Multi-Agent Template system.

## Getting Started

### 1. Create Enhancements Directory

First, create an `enhancements/` directory in your project root (NOT in `.claude/`):

```bash
# In your project root
mkdir -p enhancements
```

This directory will contain all your enhancement specifications and workflow outputs.

### 2. Choose a Template

The system provides three templates in `.claude/enhancement-templates/`:

- **`enhancement_template_sm.md`** - Small/simple enhancements (quick features, small changes)
- **`enhancement_template_lg.md`** - Large/complex enhancements (major features, architectural changes)
- **`bugfix_template.md`** - Bug fixes and issue resolution

### 3. Create an Enhancement

For each new enhancement or bug fix:

1. **Create enhancement directory:**
   ```bash
   mkdir -p enhancements/my-feature-name
   ```

2. **Copy appropriate template:**
   ```bash
   # For a feature
   cp .claude/enhancement-templates/enhancement_template_sm.md \
      enhancements/my-feature-name/my-feature-name.md

   # For a bug fix
   cp .claude/enhancement-templates/bugfix_template.md \
      enhancements/my-bugfix/my-bugfix.md
   ```

3. **Fill in the template** with your enhancement details

4. **Start the workflow** using the queue system

## Enhancement Directory Structure

After workflow execution, your enhancement directory will contain:

```
enhancements/
└── my-feature-name/
    ├── my-feature-name.md                    # Enhancement specification (you create this)
    ├── requirements-analyst/
    │   └── analysis_summary.md               # Requirements analysis output
    ├── architect/
    │   └── implementation_plan.md            # Architecture design output
    ├── implementer/
    │   ├── test_plan.md                      # Implementation output
    │   └── [code changes in project]
    ├── tester/
    │   └── test_summary.md                   # Testing results output
    ├── documenter/
    │   └── documentation_summary.md          # Documentation output
    └── logs/
        ├── requirements-analyst_task_*_*.log # Agent execution logs
        ├── architect_task_*_*.log
        └── ...
```

Each agent creates its own subdirectory with outputs following the contract specifications.

## Starting a Workflow

Once you've created and filled in your enhancement file, start the workflow:

### Manual Workflow (Review Each Step)

```bash
# Create task for requirements analysis
TASK_ID=$(cmat queue add \
  "User Profile Feature" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/user-profile/user-profile.md" \
  "Analyze requirements for user profile feature")

# Start the task
cmat queue start $TASK_ID

# After completion, review output and manually create next task...
```

### Automated Workflow (Hands-Free)

```bash
# Create fully automated task that chains through entire workflow
TASK_ID=$(cmat queue add \
  "User Profile Feature" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/user-profile/user-profile.md" \
  "Complete automated workflow" \
  true \
  true)

# Start and let it run automatically
cmat queue start $TASK_ID

# Monitor progress
cmat queue status
```

The automated workflow will progress through:
1. **Requirements Analyst** → `READY_FOR_DEVELOPMENT`
2. **Architect** → `READY_FOR_IMPLEMENTATION`
3. **Implementer** → `READY_FOR_TESTING`
4. **Tester** → `TESTING_COMPLETE`
5. **Documenter** → `DOCUMENTATION_COMPLETE`

## Workflow Phases

### 1. Requirements Analysis (requirements-analyst)
- Clarifies and documents requirements
- Identifies technical constraints
- Creates detailed acceptance criteria
- **Output**: `requirements-analyst/analysis_summary.md`
- **Status**: `READY_FOR_DEVELOPMENT`

### 2. Architecture Design (architect)
- Designs technical solution
- Makes technology choices
- Plans implementation approach
- **Output**: `architect/implementation_plan.md`
- **Status**: `READY_FOR_IMPLEMENTATION`

### 3. Implementation (implementer)
- Writes production code
- Follows architectural design
- Creates test plan
- **Output**: Code changes + `implementer/test_plan.md`
- **Status**: `READY_FOR_TESTING`

### 4. Testing (tester)
- Validates functionality
- Writes test suite
- Reports test results
- **Output**: Test code + `tester/test_summary.md`
- **Status**: `TESTING_COMPLETE`

### 5. Documentation (documenter)
- Updates user documentation
- Documents APIs
- Creates guides
- **Output**: Doc updates + `documenter/documentation_summary.md`
- **Status**: `DOCUMENTATION_COMPLETE`

## Template Selection Guide

### Use `enhancement_template_sm.md` for:
- Simple features or small changes
- Clear, well-defined requirements
- Minimal architectural impact
- Quick turnaround needed

**Examples**:
- Add new command-line flag
- Simple UI enhancement
- Configuration option addition

### Use `enhancement_template_lg.md` for:
- Complex features or major changes
- Unclear requirements needing analysis
- Significant architectural design
- Multiple components affected

**Examples**:
- New subsystem or module
- API redesign
- Integration with external systems
- Performance optimization projects

### Use `bugfix_template.md` for:
- Bug fixes and defects
- Incorrect behavior corrections
- Regression fixes
- Issue resolution

**Examples**:
- Function returning wrong values
- UI rendering issues
- Data corruption bugs
- Performance problems

## Status Markers

Each workflow phase produces a status marker that determines the next agent:

| Status | Meaning | Next Agent |
|--------|---------|------------|
| `READY_FOR_DEVELOPMENT` | Requirements complete | architect |
| `READY_FOR_IMPLEMENTATION` | Architecture complete | implementer |
| `READY_FOR_TESTING` | Implementation complete | tester |
| `TESTING_COMPLETE` | Testing complete | documenter |
| `DOCUMENTATION_COMPLETE` | Workflow complete | none |

These status markers are automatically detected and used for workflow chaining when `auto_chain` is enabled.

## Integration with External Systems

### GitHub Issues

You can create enhancements from GitHub issues:

```bash
# Fetch issue and create enhancement directory
mkdir -p enhancements/gh-issue-145
gh issue view 145 --json body --jq '.body' > enhancements/gh-issue-145/gh-issue-145.md

# Start workflow
TASK_ID=$(cmat queue add \
  "$(gh issue view 145 --json title --jq '.title')" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/gh-issue-145/gh-issue-145.md" \
  "Process GitHub issue #145" \
  true \
  true)

# Link to GitHub issue
cmat queue metadata $TASK_ID github_issue "145"

# Start
cmat queue start $TASK_ID
```

The GitHub integration agent will automatically update the issue throughout the workflow.

### Jira Tickets

Similar to GitHub, you can link enhancements to Jira tickets:

```bash
cmat queue metadata $TASK_ID jira_ticket "PROJ-456"
```

The Atlassian integration agent will sync status and publish documentation to Confluence.

## Best Practices

### Enhancement Specification

- ✅ **Be Specific**: Clearly define what the enhancement should do
- ✅ **Include Examples**: Provide concrete examples of expected behavior
- ✅ **Set Scope**: Clearly define what's in and out of scope
- ✅ **Provide Context**: Explain why this enhancement is needed
- ✅ **Define Success**: Clear acceptance criteria

### Directory Naming

- ✅ Use lowercase with hyphens: `user-profile`, `fix-auth-bug`
- ✅ Keep names concise but descriptive
- ✅ Use prefixes for categories: `feat-`, `fix-`, `refactor-`
- ❌ Avoid spaces, underscores, or special characters

### Template Usage

- ✅ Fill in ALL sections of the template
- ✅ Remove placeholder text after filling in
- ✅ Add agent-specific notes when relevant
- ✅ Include test scenarios and edge cases
- ❌ Don't skip sections - mark as "N/A" if not applicable

### Workflow Management

- ✅ Use automated workflows for well-tested processes
- ✅ Use manual workflows when learning or debugging
- ✅ Monitor queue status during execution
- ✅ Review agent outputs after each phase
- ✅ Archive completed enhancements periodically

## Troubleshooting

### Enhancement Not Found

**Problem**: Agent can't find source file

**Solution**: Verify file path is correct and relative to project root
```bash
ls -la enhancements/my-feature/my-feature.md
```

### Workflow Stuck

**Problem**: Task remains in active state

**Solution**: Check logs for errors
```bash
tail -f enhancements/my-feature/logs/*_task_*.log
```

### Output Directory Issues

**Problem**: Agent outputs not appearing

**Solution**: Verify enhancement directory exists and is writable
```bash
ls -ld enhancements/my-feature/
```

## Further Reading

- **[QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md)** - Complete queue system documentation
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow patterns and orchestration
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - External system integration
- **[SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md)** - Command reference
