# Workflow Patterns Guide

This guide describes common workflow patterns in the multi-agent system. All patterns are driven by the agent contracts defined in `AGENT_CONTRACTS.json`.

## Standard Workflows

### Complete Feature Development

**Flow**: Requirements → Architecture → Implementation → Testing → Documentation

**Agents**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **architect** → `READY_FOR_IMPLEMENTATION`
3. **implementer** → `READY_FOR_TESTING`
4. **tester** → `TESTING_COMPLETE`
5. **documenter** → `DOCUMENTATION_COMPLETE`

**When to Use**: New features, major enhancements

**Duration**: Typically 6-12 hours total across all phases

---

### Bug Fix Workflow

**Flow**: Requirements → Architecture → Implementation → Testing

**Agents**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **architect** → `READY_FOR_IMPLEMENTATION`
3. **implementer** → `READY_FOR_TESTING`
4. **tester** → `TESTING_COMPLETE`

**When to Use**: Bug fixes requiring analysis and design

**Duration**: Typically 2-4 hours total

**Note**: Documentation phase usually skipped for bug fixes unless API changes

---

### Refactoring Workflow

**Flow**: Architecture → Implementation → Testing → Documentation

**Agents**:
1. **architect** → `READY_FOR_IMPLEMENTATION`
2. **implementer** → `READY_FOR_TESTING`
3. **tester** → `TESTING_COMPLETE`
4. **documenter** → `DOCUMENTATION_COMPLETE`

**When to Use**: Code refactoring, technical debt reduction

**Duration**: 4-8 hours total

**Note**: Requirements analysis skipped since functionality doesn't change

---

### Documentation Update Workflow

**Flow**: Requirements → Documentation → Testing

**Agents**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **documenter** → `DOCUMENTATION_COMPLETE`
3. **tester** → `TESTING_COMPLETE` (validates examples)

**When to Use**: Documentation improvements, guide updates

**Duration**: 2-4 hours total

---

## Workflow States and Transitions

Each status code triggers a specific next agent:

| Current Status | Next Agent | Notes |
|----------------|------------|-------|
| `READY_FOR_DEVELOPMENT` | architect | Requirements complete, ready for design |
| `READY_FOR_IMPLEMENTATION` | implementer | Architecture complete, ready to code |
| `READY_FOR_TESTING` | tester | Implementation complete, needs validation |
| `READY_FOR_INTEGRATION` | tester | Implementation complete, needs integration testing |
| `TESTING_COMPLETE` | documenter | Tests passed, ready for docs (optional) |
| `DOCUMENTATION_COMPLETE` | none | Workflow complete |
| `BLOCKED: <reason>` | none | Manual intervention required |

See `WORKFLOW_STATES.json` for the complete state machine definition.

---

## Branching Workflows

### Parallel Development

**When to Use**: Independent components can be developed simultaneously

**Example**: Frontend and backend implementation

**Flow**:
1. **requirements-analyst** → `READY_FOR_DEVELOPMENT`
2. **architect** → `READY_FOR_IMPLEMENTATION`
3. **Parallel**:
   - **implementer-frontend** → `READY_FOR_INTEGRATION`
   - **implementer-backend** → `READY_FOR_INTEGRATION`
4. **tester** → `TESTING_COMPLETE` (integration testing)
5. **documenter** → `DOCUMENTATION_COMPLETE`

**Note**: Requires custom workflow configuration in `WORKFLOW_STATES.json`

---

## Handling Special Cases

### When Agent Gets Blocked

If an agent outputs `BLOCKED: <reason>`:
1. Workflow halts automatically
2. Task marked as blocked in queue
3. Manual review and resolution required
4. After resolution, restart from blocked agent

### When Validation Fails

If output validation fails:
1. Agent completion detected
2. Contract validation runs
3. Validation fails (missing outputs)
4. Task marked as failed
5. Manual correction required

### When Tests Fail

If tester outputs `BLOCKED: Tests failed`:
1. Workflow halts
2. Review test failures
3. Fix implementation
4. Restart implementer agent
5. Rerun tester

---

## Integration with External Systems

### Integration Tasks

After each phase completion, optionally create integration tasks:

**Triggers**:
- `READY_FOR_DEVELOPMENT` → Create GitHub issue, Jira ticket
- `READY_FOR_IMPLEMENTATION` → Update status to "In Progress"
- `READY_FOR_TESTING` → Create pull request
- `TESTING_COMPLETE` → Update PR with test results
- `DOCUMENTATION_COMPLETE` → Close issue, merge PR

**Control**: Set `AUTO_INTEGRATE` environment variable:
- `always` - Automatic integration task creation
- `prompt` - Ask before creating (default)
- `never` - Manual integration only

---

## Best Practices

### Starting a Workflow

1. Create enhancement specification in `enhancements/<name>/<name>.md`
2. Add requirements-analyst task to queue
3. Let the workflow chain automatically (or manually approve each step)
4. Monitor queue status regularly

### Choosing a Workflow

- **Full workflow** for new features or when design is unclear
- **Skip requirements** if specifications are crystal clear
- **Skip documentation** for internal refactoring
- **Hotfix only** for critical production issues

### Workflow Efficiency

- Enable `auto_chain: true` on tasks to eliminate manual approval
- Use `AUTO_INTEGRATE: always` for fully automated external sync
- Review validation failures immediately to avoid blocking
- Keep enhancement specifications clear to minimize back-and-forth

---

## Customizing Workflows

To add custom workflows:

1. **Define in WORKFLOW_STATES.json** if needed (branching workflows)
2. **Update agent contracts** if new status codes required
3. **Document in this guide** for team reference
4. **Test thoroughly** before using in production

---

## Troubleshooting Workflows

### Workflow Stuck

**Symptoms**: No next agent suggested, workflow stopped

**Solutions**:
- Check task status in queue: `.claude/queues/queue_manager.sh status`
- Look for blocked tasks
- Review last agent's output for errors
- Check if validation failed

### Wrong Next Agent

**Symptoms**: System suggests incorrect next agent

**Solutions**:
- Verify agent contract has correct `next_agents` for the status
- Check `WORKFLOW_STATES.json` for valid transitions
- Cancel automatic suggestion and create task manually

### Validation Always Failing

**Symptoms**: Every agent completion fails validation

**Solutions**:
- Check agent contracts match actual output structure
- Verify `root_document` filename is correct
- Ensure `output_directory` matches agent name
- Review agent prompt templates for correctness

---

This guide should be updated as new workflows are discovered or system capabilities expand.