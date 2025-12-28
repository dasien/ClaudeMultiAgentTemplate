# CMAT Demo Guide

This guide walks you through running a demo enhancement using the CMAT multi-agent workflow system.

**Version**: 9.0.0

## Overview

The `demo/` directory contains a simple calculator CLI application. The `enhancements/add-power-function/` directory contains an enhancement specification that adds a new `power` command to the calculator.

This demo shows how CMAT agents work together to implement a feature:

1. **Requirements Analyst** - Analyzes the enhancement spec
2. **Architect** - Designs the implementation approach
3. **Implementer** - Writes the code
4. **Tester** - Creates and runs tests
5. **Documenter** - Updates documentation

## Prerequisites

1. CMAT installed and working:
   ```bash
   cd .claude
   python -m cmat version
   # Should show: CMAT version 8.6.1
   ```

2. Demo calculator working:
   ```bash
   python demo/calculator.py add 2 3
   # Should show: 5.0
   ```

## The Demo Enhancement

The enhancement spec is at `enhancements/add-power-function/add-power-function.md`.

**Goal**: Add a `power` command to the calculator that computes exponentiation.

**Before** (current state):
```bash
python demo/calculator.py power 2 3
# Error: invalid choice: 'power'
```

**After** (expected result):
```bash
python demo/calculator.py power 2 3
# 8.0
```

## Running the Demo

### Step 1: View Available Workflows

```bash
cd .claude
python -m cmat workflow list
```

You should see `new-feature-development` among the available workflows.

### Step 2: View Workflow Details

```bash
python -m cmat workflow show new-feature-development
```

This shows the workflow steps: requirements-analyst → architect → implementer → tester → documenter.

### Step 3: Start the Workflow

```bash
python -m cmat workflow start new-feature-development add-power-function
```

This creates the first task (requirements-analyst) and marks it as **active**.

**Output:**
```
Workflow started: new-feature-development
Enhancement: add-power-function
Task: task_1234567890_12345
Agent: requirements-analyst
Status: active
```

### Step 4: Check Queue Status

```bash
python -m cmat queue status
```

You should see 1 active task.

```bash
python -m cmat queue list active
```

Shows details of the active task, including the task ID and assigned agent.

### Step 5: Work on the Task

With the task active, invoke the agent in Claude Code to do the work. The agent will:
- Read the enhancement spec
- Perform its analysis/implementation
- Create output in `required_output/` directory
- Report completion status via YAML block

### Step 6: Complete the Task

After the agent finishes, complete the task with the status from the agent's output:

```bash
python -m cmat queue complete <task_id> READY_FOR_DEVELOPMENT
```

If auto-chain is enabled (default), this automatically creates and starts the next task (architect).

### Step 7: Continue Through Workflow

Check what's active and continue:

```bash
# Check active task
python -m cmat queue list active

# [Agent does work...]

# Complete with the appropriate status
python -m cmat queue complete <task_id> <STATUS>
```

The workflow progresses through:
- `READY_FOR_DEVELOPMENT` → starts architect task
- `READY_FOR_IMPLEMENTATION` → starts implementer task
- `READY_FOR_TESTING` → starts tester task
- `TESTING_COMPLETE` → starts documenter task
- `DOCUMENTATION_COMPLETE` → workflow complete

### Step 8: Monitor Progress

```bash
# Check queue status
python -m cmat queue status

# List completed tasks
python -m cmat queue list completed

# List all tasks
python -m cmat queue list all
```

## Understanding the Workflow

### Workflow Steps

Each step in the workflow:
1. Takes input from the previous step's output
2. Produces required output in `required_output/` directory
3. Reports a completion status via YAML block

### Status Transitions

```
requirements-analyst
    READY_FOR_DEVELOPMENT → architect (auto)
    BLOCKED → (stop)

architect
    READY_FOR_IMPLEMENTATION → implementer (auto)
    BLOCKED → (stop)

implementer
    READY_FOR_TESTING → tester (auto)
    BUILD_FAILED → (stop)

tester
    TESTING_COMPLETE → documenter (auto)
    TESTS_FAILED → (stop)

documenter
    DOCUMENTATION_COMPLETE → (workflow complete)
```

### Agent Output Structure

Each agent creates output in:

```
enhancements/add-power-function/
├── add-power-function.md              # Original spec
├── requirements-analyst/
│   └── required_output/
│       └── analysis_summary.md        # Requirements analysis
├── architect/
│   └── required_output/
│       └── implementation_plan.md     # Technical design
├── implementer/
│   └── required_output/
│       └── implementation_summary.md  # Code changes
├── tester/
│   └── required_output/
│       └── test_summary.md            # Test results
└── documenter/
    └── required_output/
        └── documentation_summary.md   # Doc updates
```

## Verifying Results

After the workflow completes, verify the implementation:

```bash
# Test the new power command
python demo/calculator.py power 2 3
# Should show: 8.0

python demo/calculator.py power 10 0
# Should show: 1.0

python demo/calculator.py power 2 -1
# Should show: 0.5

# Run the tests
cd demo
python -m pytest test_calculator.py -v
# Should show all tests passing, including new power tests
```

## Queue Management

### View Task Details

```bash
python -m cmat queue list all
```

### Manually Complete a Task

If you need to manually mark a task as complete:

```bash
python -m cmat queue complete <task_id> READY_FOR_TESTING
```

### Re-run a Failed Task

```bash
python -m cmat queue rerun <task_id>
```

### Cancel a Task

```bash
python -m cmat queue cancel <task_id> "No longer needed"
```

## Tracking Costs

After running agents, check the costs:

```bash
cd .claude
python -m cmat costs enhancement add-power-function
```

## Try Your Own Enhancement

Create your own enhancement to extend the calculator:

1. Create enhancement directory:
   ```bash
   mkdir -p enhancements/add-modulo
   ```

2. Create spec file `enhancements/add-modulo/add-modulo.md`:
   ```markdown
   # Add Modulo Function to Calculator

   ## Overview
   Add a `modulo` command that returns the remainder of division.

   ## Acceptance Criteria
   - `python demo/calculator.py modulo 10 3` returns `1.0`
   - Tests added for the new function
   ```

3. Start the workflow:
   ```bash
   cd .claude
   python -m cmat workflow start new-feature-development add-modulo
   ```

### Other Enhancement Ideas

- **Square root**: `sqrt 16` → `4.0`
- **Absolute value**: `abs -5` → `5.0`
- **Factorial**: `factorial 5` → `120`
- **Percentage**: `percent 50 200` → `100.0` (50% of 200)

## CLI Quick Reference

```bash
# Workflow commands
python -m cmat workflow list                    # List workflows
python -m cmat workflow show <name>             # Show workflow details
python -m cmat workflow start <name> <enh>      # Start a workflow (creates first task)
python -m cmat workflow validate <name>         # Validate workflow

# Queue commands
python -m cmat queue status                     # Queue summary
python -m cmat queue list [type]                # List tasks
python -m cmat queue start <task_id>            # Mark task as active
python -m cmat queue complete <id> <result>     # Complete task
python -m cmat queue fail <id> <reason>         # Fail task
python -m cmat queue cancel <id> [reason]       # Cancel task
python -m cmat queue rerun <id>                 # Re-queue task

# Cost tracking
python -m cmat costs show <task_id>             # Task cost
python -m cmat costs enhancement <name>         # Enhancement cost
```

## Next Steps

- Read [README.md](README.md) for system overview and quick start
- Read [.claude/docs/WORKFLOW_GUIDE.md](.claude/docs/WORKFLOW_GUIDE.md) for workflow patterns
- Read [.claude/docs/CLI_REFERENCE.md](.claude/docs/CLI_REFERENCE.md) for complete CLI reference
- Read [.claude/docs/CUSTOMIZATION_GUIDE.md](.claude/docs/CUSTOMIZATION_GUIDE.md) to adapt CMAT to your project
