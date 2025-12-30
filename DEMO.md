# CMAT Demo Guide

This guide walks you through running a demo enhancement using the CMAT multi-agent workflow system.

**Version**: 10.0.0

## Overview

The `demo/` directory contains a simple calculator CLI application. This demo shows how to:

1. Initialize CMAT in a project
2. Create an enhancement
3. Run a multi-agent workflow to implement a new feature

The workflow uses these agents in sequence:
1. **Requirements Analyst** - Analyzes the enhancement spec
2. **Architect** - Designs the implementation approach
3. **Implementer** - Writes the code
4. **Tester** - Creates and runs tests
5. **Documenter** - Updates documentation

## Prerequisites

1. CMAT installed:
   ```bash
   pip install -e .
   ```

2. Demo calculator working:
   ```bash
   python demo/calculator.py add 2 3
   # Should show: 5.0
   ```

## The Demo Enhancement

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

### Step 1: Launch CMAT UI

```bash
cmat
```

This opens the graphical UI for managing CMAT projects.

### Step 2: Initialize the Demo Project

In the UI:
1. Click **File > Initialize Project** (or use the keyboard shortcut)
2. Navigate to and select the `demo/` directory
3. Click **Open/Select**

CMAT will copy the templates to `demo/.claude/` and create `demo/enhancements/`.

### Step 3: Connect to the Demo Project

In the UI:
1. Click **File > Connect to Project**
2. Select the `demo/` directory
3. The UI should show "Connected" status

### Step 4: Create the Enhancement

In the UI:
1. Click **File > New Enhancement**
2. Fill in the details:
   - **Name**: `add-power-function`
   - **Title**: Add Power Function to Calculator
   - **Description**: Add a `power` command that computes exponentiation. `python demo/calculator.py power 2 3` should return `8.0`.
3. Click **Create**

This creates `demo/enhancements/add-power-function/add-power-function.md`.

### Step 5: Start the Workflow

In the UI:
1. Click **Workflows > Launch Workflow**
2. Select **new-feature-development** workflow
3. Select **add-power-function** enhancement
4. Click **Start**

The first task (requirements-analyst) is created and marked as active.

### Step 6: Monitor Progress

The UI shows:
- **Active Tasks**: Currently running agent
- **Completed Tasks**: Finished steps
- **Queue Status**: Overall progress

Each agent will:
- Read input from the previous step
- Perform its analysis/implementation
- Create output in `required_output/` directory
- Report completion status

### Step 7: Workflow Progression

The workflow progresses automatically through:
1. `READY_FOR_DEVELOPMENT` → starts architect task
2. `READY_FOR_IMPLEMENTATION` → starts implementer task
3. `READY_FOR_TESTING` → starts tester task
4. `TESTING_COMPLETE` → starts documenter task
5. `DOCUMENTATION_COMPLETE` → workflow complete

### Step 8: Verify Results

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
demo/enhancements/add-power-function/
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

## Task Management in the UI

### View Task Details
- Click on any task to see its details
- View assigned agent, status, timestamps
- Access task logs and outputs

### Manual Task Control
- **Complete**: Mark task with a result status
- **Fail**: Mark task as failed with reason
- **Cancel**: Cancel a pending/active task
- **Rerun**: Re-queue a completed/failed task

### Queue Management
- **Clear Completed**: Remove finished tasks
- **Cancel All**: Cancel all pending/active tasks
- **Reset Queue**: Start fresh

## Try Your Own Enhancement

Create your own enhancement to extend the calculator:

### Enhancement Ideas

- **Square root**: `sqrt 16` → `4.0`
- **Absolute value**: `abs -5` → `5.0`
- **Factorial**: `factorial 5` → `120`
- **Percentage**: `percent 50 200` → `100.0` (50% of 200)
- **Modulo**: `modulo 10 3` → `1.0`

### Steps

1. In the UI: **File > New Enhancement**
2. Name it (e.g., `add-square-root`)
3. Write a clear description with examples
4. Start the **new-feature-development** workflow
5. Monitor progress and verify results

## Tracking Costs

After running agents, view costs in the UI:
1. Select a completed task
2. View the **Cost** section in task details
3. Or use **View > Enhancement Costs** to see totals

## Next Steps

- Read [README.md](README.md) for system overview
- Read [docs/WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md) for workflow patterns
- Read [docs/SKILLS_GUIDE.md](docs/SKILLS_GUIDE.md) for domain expertise
- Read [docs/CUSTOMIZATION_GUIDE.md](docs/CUSTOMIZATION_GUIDE.md) to adapt CMAT to your project
