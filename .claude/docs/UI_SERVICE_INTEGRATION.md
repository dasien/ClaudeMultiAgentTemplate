# UI Service Integration Guide

**Version**: 9.0.0

Guide for migrating the UI from CLI-based CMAT commands to direct service integration.

---

## Current Architecture

```
UI Dialog → CMATInterface → CLI commands ("cmat queue status") → __main__.py → CMAT class → Services
```

**Problems:**
- Unnecessary string parsing/serialization
- CLI overhead for every operation
- Error handling through exit codes instead of exceptions

---

## Target Architecture

```
UI Dialog → CMATInterface → Services directly
```

**Benefits:**
- Direct method calls with proper return types
- Exception-based error handling
- No CLI parsing overhead
- Full access to service capabilities

---

## Key Architectural Decisions

### Services Stay "Ignorant"

Services should NOT know:
- Where files are located (paths injected via constructor)
- What other services exist (dependencies injected via `set_services()`)

This keeps services testable and decoupled.

### CMATInterface Becomes the Composition Root

CMATInterface should:
1. Accept an explicit project path (NOT derive from cwd)
2. Set the global project root for utility functions
3. Create all services with explicit paths
4. Wire service dependencies
5. Expose services or wrapper methods to UI dialogs

---

## Critical: Project Root vs Working Directory

The UI's working directory is NOT the connected project. This is the most important concern.

**CLI behavior (works):**
```python
# CLI runs from within the project
cmat = CMAT()  # Uses find_project_root() from cwd - OK
```

**UI behavior (broken without explicit path):**
```python
# UI runs from its own directory, NOT the project
cmat = CMAT()  # find_project_root() searches from wrong cwd - BROKEN
```

**Solution:**
```python
# UI must pass explicit project path
cmat = CMAT(base_path="/path/to/connected/project")  # Correct
```

---

## Global Project Root Dependency

Several utility functions use `find_project_root()` as a fallback when no explicit path is provided.

### Functions Using Global Fallback

| Function | Falls back when missing |
|----------|------------------------|
| `log_operation()` | `logs_dir` |
| `log_error()` | delegates to `log_operation()` |
| `log_info()` | delegates to `log_operation()` |

### Services Using Global Fallback

All services fall back to `find_project_root()` if path not provided in constructor:

| Service | Parameter |
|---------|-----------|
| QueueService | `queue_file` |
| AgentService | `agents_dir` |
| SkillsService | `skills_dir` |
| LearningsService | `data_dir` |
| ModelService | `data_dir` |
| ToolsService | `data_dir` |

### The Risk

Services call `log_operation()` internally WITHOUT passing `logs_dir`. If `set_project_root()` isn't called first, logs go to wrong location.

---

## CMATInterface Implementation

### Required Initialization Order

```python
from pathlib import Path
from cmat.utils import set_project_root
from cmat.services import (
    QueueService, AgentService, SkillsService,
    WorkflowService, TaskService, LearningsService,
    ModelService, ToolsService
)

class CMATInterface:
    def __init__(self, project_path: str):
        """
        Initialize CMAT services for a specific project.

        Args:
            project_path: Absolute path to the connected project.
                         This is NOT the UI's working directory.
        """
        self._project_path = Path(project_path)

        # 1. FIRST - Set global project root
        #    This ensures log_operation() and other utils work correctly
        #    even when called without explicit paths
        set_project_root(self._project_path)

        # 2. Derive all paths from project root
        claude_dir = self._project_path / ".claude"
        data_dir = claude_dir / "data"
        agents_dir = claude_dir / "agents"
        skills_dir = claude_dir / "skills"
        logs_dir = claude_dir / "logs"
        docs_dir = claude_dir / "docs"
        enhancements_dir = self._project_path / "enhancements"

        # 3. Create services with EXPLICIT paths (belt + suspenders)
        self.queue = QueueService(
            queue_file=str(data_dir / "task_queue.json")
        )

        self.agents = AgentService(
            agents_dir=str(agents_dir)
        )

        self.skills = SkillsService(
            skills_dir=str(skills_dir)
        )

        self.workflow = WorkflowService(
            templates_file=str(data_dir / "workflow_templates.json"),
            enhancements_dir=str(enhancements_dir)
        )

        self.tasks = TaskService(
            templates_file=str(docs_dir / "TASK_PROMPT_DEFAULTS.md"),
            agents_dir=str(agents_dir),
            logs_dir=str(logs_dir),
            enhancements_dir=str(enhancements_dir),
        )

        self.learnings = LearningsService(
            data_dir=str(data_dir)
        )

        self.models = ModelService(
            data_dir=str(data_dir)
        )

        self.tools = ToolsService(
            data_dir=str(data_dir)
        )

        # 4. Wire service dependencies
        self.tasks.set_services(
            agent=self.agents,
            skills=self.skills,
            queue=self.queue,
            learnings=self.learnings,
            models=self.models,
        )

        self.workflow.set_services(
            queue=self.queue,
            task=self.tasks,
            agent=self.agents,
        )

        self.queue.set_services(
            task_service=self.tasks,
        )
```

### Why Both set_project_root AND Explicit Paths?

1. **Explicit paths** ensure services use correct directories
2. **set_project_root()** ensures internal `log_operation()` calls work

Even if you pass explicit paths to services, they call `log_operation()` internally without `logs_dir`. The global fallback catches these.

---

## Service Method Reference

### QueueService

```python
# Task CRUD
queue.add(title, assigned_agent, priority, task_type, source_file, description, metadata?, model?)
queue.get(task_id) -> Optional[Task]
queue.list_tasks(status?) -> list[Task]
queue.list_pending() -> list[Task]
queue.list_active() -> list[Task]
queue.list_completed() -> list[Task]
queue.list_failed() -> list[Task]
queue.list_cancelled() -> list[Task]

# Task lifecycle
queue.start(task_id) -> Optional[Task]
queue.complete(task_id, result) -> Optional[Task]
queue.fail(task_id, reason) -> Optional[Task]
queue.cancel(task_id, reason?) -> Optional[Task]
queue.rerun(task_id) -> Optional[Task]
queue.cancel_all(reason) -> int

# Metadata
queue.update_metadata(task_id, metadata_dict) -> Optional[Task]
queue.update_single_metadata(task_id, key, value) -> Optional[Task]

# Status
queue.status() -> dict
queue.init(force=True) -> bool  # Reset queue

# Filtering
queue.list_by_agent(agent_name) -> list[Task]
queue.list_by_enhancement(enhancement_name) -> list[Task]

# Batch operations
queue.clear_tasks(task_ids) -> int
queue.clear_completed() -> int
queue.clear_failed() -> int

# Logs
queue.get_operations_log_path() -> Path
```

### AgentService

```python
agents.list_all() -> list[Agent]
agents.get(agent_file) -> Optional[Agent]
agents.get_by_name(name) -> Optional[Agent]
agents.get_by_role(role) -> list[Agent]
agents.add(agent) -> Agent
agents.update(agent) -> Optional[Agent]
agents.delete(agent_file) -> bool
agents.generate_agents_json(skip_templates?) -> dict
agents.get_agent_prompt(agent_file) -> Optional[str]
```

### WorkflowService

```python
# Template CRUD
workflow.list_all() -> list[WorkflowTemplate]
workflow.get(workflow_id) -> Optional[WorkflowTemplate]
workflow.add(template) -> WorkflowTemplate
workflow.update(template) -> Optional[WorkflowTemplate]
workflow.delete(workflow_id) -> bool

# Step management
workflow.add_step(workflow_id, step, index?) -> Optional[WorkflowTemplate]
workflow.remove_step(workflow_id, step_index) -> Optional[WorkflowTemplate]

# Transition management
workflow.add_transition(workflow_id, step_index, status, transition) -> Optional[WorkflowTemplate]
workflow.remove_transition(workflow_id, step_index, status) -> Optional[WorkflowTemplate]

# Orchestration
workflow.start_workflow(workflow_name, enhancement_name, description?, auto_chain?, execute?, model?) -> Optional[str]
workflow.run_task(task_id) -> Optional[str]
workflow.auto_chain(task_id, status) -> Optional[str]

# Validation
workflow.validate_template(template) -> list[str]  # Returns errors
```

### ToolsService

```python
tools.list_all() -> list[Tool]
tools.get(name) -> Optional[Tool]
tools.add(tool) -> str
tools.update(tool) -> bool
tools.delete(name) -> bool
tools.get_tools_for_agent(tool_names) -> list[Tool]
tools.get_all_tool_names() -> list[str]
```

### ModelService

```python
models.list_all() -> list[ClaudeModel]
models.get(model_id) -> Optional[ClaudeModel]
models.get_default() -> ClaudeModel
models.set_default(model_id) -> bool
models.add(model) -> str
models.update(model) -> bool
models.delete(model_id) -> bool
```

### SkillsService

```python
skills.list_all() -> list[Skill]
skills.get(skill_directory) -> Optional[Skill]
skills.get_by_name(name) -> Optional[Skill]
skills.get_by_category(category) -> list[Skill]
skills.add(skill) -> Skill
skills.update(skill) -> Optional[Skill]
skills.delete(skill_directory) -> bool
```

### LearningsService

```python
learnings.list_all() -> list[Learning]
learnings.get(learning_id) -> Optional[Learning]
learnings.store(learning) -> str
learnings.delete(learning_id) -> bool
learnings.list_by_tags(tags) -> list[Learning]
learnings.count() -> int
```

### TaskService

```python
# Direct execution (for UI-driven operations)
tasks.execute_direct(agent_name, input_file?, output_dir, task_description, task_type) -> ExecutionResult
```

---

## Migration Strategy

### Phase 1: Parallel Implementation

1. Keep existing CLI-based methods in CMATInterface
2. Add new service-based methods alongside
3. Gradually migrate dialogs to use new methods

### Phase 2: Direct Service Access

Once stable, dialogs can access services directly:

```python
# Instead of wrapper methods
status = self.cmat_interface.get_queue_status()

# Direct service access
status = self.cmat_interface.queue.status()
```

### Phase 3: Remove CLI Code

Once all dialogs migrated, remove:
- CLI command building code
- String parsing/serialization
- CLI-specific error handling

---

## Error Handling

Services raise exceptions instead of returning exit codes:

```python
try:
    task = self.queue.add(...)
except ValueError as e:
    # Handle validation error
except FileNotFoundError as e:
    # Handle missing file
except Exception as e:
    # Handle unexpected error
```

---

## See Also

- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** - CLI command reference (for comparison)
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow system documentation
- **[QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md)** - Task queue documentation