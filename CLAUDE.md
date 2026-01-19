# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Multi-Agent Template (CMAT) is a Python-based workflow automation system that orchestrates specialized AI agents for software development. It provides a tkinter GUI for task management and multi-agent collaboration.

## Commands

### Setup
```bash
./setup_dev.sh                          # Full dev environment setup
source .venv/bin/activate               # Activate virtual environment
pip install -e ".[dev]"                 # Install with dev dependencies
```

### Running
```bash
cmat                                    # Launch GUI (after pip install)
python -m ui.main                       # Direct launch
```

### Testing
```bash
pytest                                  # Run all tests
pytest tests/test_services.py           # Run specific test file
pytest tests/test_services.py::test_name  # Run specific test
pytest --cov=src/core --cov=src/ui      # With coverage
```

### Code Quality
```bash
black src tests                         # Format code
ruff check src tests                    # Lint
mypy src                                # Type check
```

## Architecture

### Core Components
- **src/core/** - Core orchestration engine
  - `cmat.py` - Main CMAT orchestrator class
  - `services/` - Service layer (queue, agent, workflow, skills, task, learnings, model, tools)
  - `models/` - Data models (Task, Agent, WorkflowTemplate, Skill, Learning)
- **src/ui/** - Tkinter GUI
  - `main.py` - MainView class, entry point
  - `dialogs/` - Dialog windows
  - `components/` - Reusable UI components

### Data Flow
```
Workflow Template → Steps (agent + transitions) → Tasks → Agent Execution
```

### Key Services
- `QueueService` - Task state management
- `WorkflowService` - Workflow orchestration, auto-chaining
- `AgentService` - Agent registry and CRUD
- `SkillsService` - Skills loading and injection
- `LearningsService` - RAG-based memory system

### Agent Configuration
Agents are defined in `.claude/agents/{slug}.md` with YAML frontmatter:
- `name`, `role`, `description`, `tools`, `skills`

### Workflow Status Codes
Completion: `READY_FOR_DEVELOPMENT`, `READY_FOR_IMPLEMENTATION`, `READY_FOR_TESTING`, `TESTING_COMPLETE`, `DOCUMENTATION_COMPLETE`
Halt: `BLOCKED`, `NEEDS_CLARIFICATION`, `TESTS_FAILED`, `BUILD_FAILED`

## Version Tracking

**Version must be updated in 2 places:**
1. `pyproject.toml` - `version = "X.Y.Z"` (source of truth)
2. `README.md` - `**Version**: X.Y.Z` (documentation)

Code reads version from `pyproject.toml` via `importlib.metadata`. After changing the version, run `pip install -e .` to update the installed package metadata.

## Code Style

- Python 3.10+
- Black formatter (100 char line length)
- Ruff linter
- MyPy for type checking
- Files: `snake_case.py`, Classes: `PascalCase`, Functions: `snake_case`
- Agent/skill slugs: `lowercase-with-hyphens`
