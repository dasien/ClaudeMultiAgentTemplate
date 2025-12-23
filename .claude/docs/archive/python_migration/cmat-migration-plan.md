# CMAT Core Migration: Bash to Python

## Working Status

**Branch**: `refactor/bash-to-python`

**Current Phase**: Phase 2 complete, Phase 3 mostly complete

**Last Updated**: Session 1

### Progress Checklist

**Phase 1: Foundation (Models)** ✅
- [x] Package scaffolding (`cmat/__init__.py`, `cmat/models/__init__.py`)
- [x] Task model (`task.py`, `task_metadata.py`)
- [x] Agent model (`agent.py`)
- [x] Skill model (`skill.py`)
- [x] Workflow models (`step_transition.py`, `workflow_step.py`, `workflow_template.py`)
- [x] Tool model (`tool.py`)
- [x] ClaudeModel model (`claude_model.py`)
- [x] Enhancement model (`enhancement.py`)
- [ ] Unit tests for models

**Phase 2: Claude Integration** ✅
- [x] ClaudeClient subprocess wrapper (`claude/client.py`)
- [x] ClaudeClientConfig (`claude/config.py`)
- [x] ClaudeResponse (`claude/response.py`)
- [ ] Integration tests

**Phase 3: Services** ✅
- [x] Queue service (`queue_service.py`)
- [x] Agent service with execution (`agent_service.py`)
- [x] Skills service (`skills_service.py`)
- [x] Workflow service (`workflow_service.py`)
- [x] Utils module (`utils.py`)
- [ ] Integration service (GitHub, Atlassian, Bitwarden) - deferred
- [ ] Service tests

**Phase 4: CMAT Entry Point + UI Integration**
- [x] CMAT class composing services (`cmat.py`)
- [ ] Update ClaudeMultiAgentUI utility class
- [ ] End-to-end testing

**Phase 5: Cleanup + Optional CLI**
- [ ] Archive bash scripts
- [ ] Documentation update
- [ ] Python CLI (if needed)

### Decisions Log

1. **Package location**: `.claude/cmat/` to maintain existing deployment model
2. **One class per file**: Preferred organization pattern
3. **Validations as dict**: Flexible key-value rather than typed class
4. **on_status as dict**: `dict[str, StepTransition]` for O(1) lookup by status name
5. **Status renamed to StepTransition**: More descriptive name
6. **Enhancement model**: Created for future use, even though UI currently handles creation
7. **Config vs state files**: Config stays in current locations, only `task_queue.json` is high-churn state
8. **Agent execution in AgentService**: Full execution orchestration (template loading, skills injection, prompt building, status extraction) lives in AgentService, not a separate execution service
9. **Service dependency injection**: AgentService uses `set_services()` to receive SkillsService, WorkflowService, QueueService references to avoid circular imports

### Session Notes

**Session 1**: Created all models, services, and claude integration. Files to create:

**cmat/__init__.py**
**cmat/cmat.py** - Main CMAT entry point
**cmat/utils.py** - Shared utilities

**cmat/models/__init__.py**
**cmat/models/task.py**
**cmat/models/task_metadata.py**
**cmat/models/agent.py**
**cmat/models/skill.py**
**cmat/models/step_transition.py**
**cmat/models/workflow_step.py**
**cmat/models/workflow_template.py**
**cmat/models/tool.py**
**cmat/models/claude_model.py**
**cmat/models/enhancement.py**

**cmat/services/__init__.py**
**cmat/services/queue_service.py**
**cmat/services/agent_service.py** - includes ExecutionResult, invoke(), invoke_direct()
**cmat/services/skills_service.py**
**cmat/services/workflow_service.py**

**cmat/claude/__init__.py**
**cmat/claude/client.py**
**cmat/claude/config.py**
**cmat/claude/response.py**

---

## Executive Summary

This document outlines a phased migration of the CMAT core from bash scripts to Python classes. The goal is to eliminate string-parsing fragility, enable clean RAG integration, and better serve the ClaudeMultiAgentUI as the primary interface while maintaining the CLI for development/testing.

---

## Current State Assessment

### What Exists Today

- **Orchestration layer**: Bash scripts handling workflow execution, agent coordination, and process lifecycle
- **State management**: File-based storage with text parsing for enhancements, tasks, and workflow state
- **Claude Code integration**: Shell subprocess calls with stdout/stderr capture and parsing
- **Workflow templates**: YAML/JSON configuration files defining agent sequences and orchestration logic
- **Skills system**: Built-in capabilities loaded and referenced by agents
- **UI facade**: Python utility class in ClaudeMultiAgentUI that shells out to CMAT bash scripts

### Pain Points Driving Migration

1. **Fragile string parsing**: grep/awk/sed chains break when output formats shift
2. **Poor error propagation**: Bash error handling is awkward and inconsistent
3. **Complex state management**: Enhancement/task relationships and cost aggregation are difficult in bash
4. **Testing difficulty**: Unit testing bash is painful compared to Python
5. **RAG incompatibility**: Vector stores and embedding pipelines are Python-native
6. **Wasted abstraction**: CLI layer maintained but rarely used in production

---

## Target Architecture

### Core Python Package Structure

```
cmat/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── enhancement.py      # Enhancement domain model
│   ├── task.py             # Task domain model  
│   ├── agent.py            # Agent configuration and execution
│   ├── workflow.py         # Workflow orchestration engine
│   └── state.py            # State persistence layer
├── claude/
│   ├── __init__.py
│   ├── client.py           # Claude Code subprocess wrapper
│   ├── session.py          # Session management and hooks
│   └── parser.py           # Response parsing utilities
├── integrations/
│   ├── __init__.py
│   ├── github.py           # GitHub coordinator
│   ├── atlassian.py        # Jira/Confluence coordinator
│   └── bitwarden.py        # Bitwarden integration
├── rag/                    # Future: RAG subsystem
│   ├── __init__.py
│   ├── embeddings.py
│   ├── store.py
│   └── retrieval.py
├── api/
│   ├── __init__.py
│   └── facade.py           # Public interface for UI consumption
└── cli/
    ├── __init__.py
    └── main.py             # Click/Typer CLI (thin wrapper)
```

### Key Design Principles

1. **Domain-driven models**: Enhancements, tasks, agents, and workflows as first-class objects with typed fields and methods
2. **Clean separation**: Core logic independent of interface (CLI or UI)
3. **Facade pattern**: Single entry point (`api/facade.py`) that the UI imports
4. **Pluggable persistence**: State layer abstracted so file-based storage can later become database-backed
5. **Subprocess isolation**: All Claude Code interaction through a dedicated client class

---

## Migration Phases

### Phase 1: Foundation (Week 1-2)

**Objective**: Establish Python package structure and migrate domain models.

**Deliverables**:

1. **Package scaffolding**: Create directory structure, setup.py/pyproject.toml, dev dependencies
2. **Enhancement model** (`models/enhancement.py`):
   - `Enhancement` class with fields: id, title, description, status, source, tasks, metadata, cost_summary
   - Status enum: PENDING, IN_PROGRESS, BLOCKED, COMPLETED, FAILED
   - Methods: `add_task()`, `update_status()`, `calculate_cost()`, `to_dict()`, `from_dict()`
3. **Task model** (`models/task.py`):
   - `Task` class with fields: id, enhancement_id, agent_type, status, input_context, output, cost, timestamps
   - Status transitions with validation
   - Methods: `start()`, `complete()`, `fail()`, `to_dict()`, `from_dict()`
4. **State persistence** (`models/state.py`):
   - Abstract base class defining storage interface
   - File-based implementation matching current storage patterns
   - Methods: `save_enhancement()`, `load_enhancement()`, `list_enhancements()`, `save_task()`, etc.

**Validation**: Unit tests for all models. Ability to create, persist, and reload enhancements/tasks.

---

### Phase 2: Claude Integration (Week 2-3)

**Objective**: Replace bash subprocess handling with robust Python wrapper.

**Deliverables**:

1. **Claude client** (`claude/client.py`):
   - `ClaudeClient` class wrapping subprocess execution
   - Methods: `execute(prompt, context, allowed_tools)` returning structured response
   - Proper handling of stdout, stderr, exit codes
   - Timeout management and graceful termination
2. **Session management** (`claude/session.py`):
   - `Session` class tracking conversation state
   - SessionEnd hook data capture and parsing
   - Cost extraction from session metadata
3. **Response parser** (`claude/parser.py`):
   - Structured extraction of Claude responses
   - JSON parsing with fallback handling
   - Tool use result extraction

**Validation**: Integration tests executing real Claude Code calls. Verify cost capture accuracy against current bash implementation.

---

### Phase 3: Agent and Workflow Engine (Week 3-4)

**Objective**: Migrate agent execution and workflow orchestration to Python.

**Deliverables**:

1. **Agent model** (`models/agent.py`):
   - `Agent` class with fields: name, type, system_prompt, allowed_tools, skills
   - `AgentRegistry` for loading agent configurations from YAML
   - Method: `execute(task, context)` using ClaudeClient
2. **Workflow engine** (`models/workflow.py`):
   - `Workflow` class representing a template instantiation
   - `WorkflowEngine` orchestrating agent sequences
   - Support for parallel and sequential execution patterns
   - Event hooks for progress reporting
3. **Workflow template loader**:
   - Parse existing YAML workflow templates
   - Validate agent references and dependencies
   - Instantiate workflows with enhancement context

**Validation**: Execute existing workflow templates through Python engine. Compare outputs with bash implementation.

---

### Phase 4: CMAT Entry Point and UI Integration (Week 4-5)

**Objective**: Create the main CMAT class and update ClaudeMultiAgentUI integration.

**Deliverables**:

1. **CMAT entry point class** (`cmat.py`):
   - `CMAT` class composing all services
   - Services exposed as attributes: `queue`, `workflow`, `agents`, `skills`, `integrations`
   - Initialization handles configuration loading and dependency wiring
2. **UI integration update**:
   - Modify ClaudeMultiAgentUI utility class to import and instantiate `CMAT`
   - Replace shell-out logic with direct service method calls
   - Update any response parsing to use structured returns
3. **Backward compatibility layer** (optional):
   - Thin bash script that calls `python -m cmat` for any remaining CLI usage
   - Allows gradual deprecation of bash interface

**Validation**: Full end-to-end testing through UI. Verify all existing UI functionality works unchanged.

---

### Phase 5: Cleanup and Optional CLI (Week 5-6)

**Objective**: Remove deprecated bash scripts and optionally provide Python CLI.

**Deliverables**:

1. **Bash deprecation**:
   - Archive old bash scripts to `legacy/` directory
   - Update documentation
   - Remove from primary execution paths
2. **Python CLI** (optional, `cli.py`):
   - Click or Typer-based CLI wrapping `CMAT` class
   - Commands: `cmat queue add`, `cmat workflow run`, `cmat status`, etc.
   - Only if CLI access is actually needed for development/debugging
3. **Documentation update**:
   - Installation instructions (Python environment setup)
   - API reference for CMAT class and services
   - Migration notes for any external consumers

**Validation**: Documentation review. CLI feature parity if implemented.

---

## Integration Coordinator Migration

The integration coordinators (GitHub, Atlassian, Bitwarden) can migrate in parallel with phases 2-3 or as a follow-on effort.

**Approach**:

- Wrap existing MCP tool interactions in Python classes
- `GitHubCoordinator`: issue fetching, PR creation, status updates
- `AtlassianCoordinator`: Jira ticket sync, Confluence publishing
- `BitwardenCoordinator`: secrets retrieval for workflows

These become injectable dependencies for workflows that need external system access.

---

## RAG Integration Preparation

The migration specifically enables RAG by:

1. **Python ecosystem access**: Direct use of LangChain, LlamaIndex, ChromaDB, pgvector
2. **Clean integration points**: 
   - `Enhancement.get_relevant_context()` can query RAG
   - `Agent.execute()` can inject retrieved knowledge into prompts
3. **Structured data**: Domain models provide clean chunking boundaries for indexing
4. **State layer abstraction**: Same persistence interface can back both operational state and vector store metadata

**Recommended RAG implementation sequence** (post-migration):

1. Choose vector store (ChromaDB for simplicity, pgvector for PostgreSQL alignment)
2. Implement embedding pipeline for codebase and documentation
3. Add retrieval methods to facade
4. Integrate retrieval into agent context injection

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Regression in workflow execution | Parallel testing: run both bash and Python on same inputs, compare outputs |
| UI integration breakage | Maintain facade interface contract; integration tests before switchover |
| Performance degradation | Profile Python implementation; subprocess overhead should be similar |
| State file format changes | Version state files; write migration script if schema changes |
| Extended timeline | Phases are independent; can pause after any phase with working system |

---

## Success Criteria

1. **Functional parity**: All existing workflows execute correctly through Python core
2. **UI unchanged**: ClaudeMultiAgentUI works without user-visible changes
3. **Test coverage**: Core domain models have >80% unit test coverage
4. **Error handling**: Failures produce clear, actionable error messages (not bash trace dumps)
5. **RAG-ready**: Architecture supports adding RAG module without restructuring
6. **Maintainability**: New developers can understand and modify system without bash expertise

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Foundation | 1-2 weeks | None |
| Phase 2: Claude Integration | 1 week | Phase 1 |
| Phase 3: Workflow Engine | 1-2 weeks | Phases 1, 2 |
| Phase 4: UI Integration | 1 week | Phases 1-3 |
| Phase 5: CLI and Cleanup | 1 week | Phases 1-4 |

**Total**: 5-7 weeks for core migration, with RAG implementation following.

Phases can overlap where dependencies allow. Phase 1 and initial Phase 2 work can proceed in parallel.
