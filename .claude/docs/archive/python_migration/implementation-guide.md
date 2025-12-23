# CMAT Python Implementation Guide v2

## Architecture Overview

This guide reflects a **cleaner separation of concerns** than the original bash scripts, while maintaining full functional parity.

```
┌─────────────────────────────────────────────────────────────────┐
│                    WorkflowService (Orchestrator)                │
│  - Owns the execution flow                                       │
│  - Starts workflows, chains steps                                │
│  - Validates outputs between steps                               │
│  - Template CRUD                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TaskService (Execution Engine)                │
│  - Executes a single task                                        │
│  - Builds prompts (template + skills + variables)                │
│  - Invokes Claude with PID tracking                              │
│  - Extracts status from output                                   │
│  - Handles logging                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  AgentService    │ │  SkillsService   │ │  ClaudeClient    │
│  (Actor Config)  │ │  (Capabilities)  │ │  (Subprocess)    │
│  - Agent CRUD    │ │  - Skills CRUD   │ │  - Run prompt    │
│  - Load prompt   │ │  - Load content  │ │  - PID tracking  │
│  - Validations   │ │  - Build section │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    QueueService (State Management)               │
│  - Task CRUD (add, get, list)                                    │
│  - State transitions (pending → active → completed)              │
│  - Agent status tracking                                         │
│  - NO execution logic                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Single Responsibility | Does NOT Do |
|---------|----------------------|-------------|
| **QueueService** | Task state management | Execution, prompt building |
| **AgentService** | Agent configuration registry | Task execution |
| **SkillsService** | Skills configuration registry | Task execution |
| **TaskService** | Execute single task | Workflow decisions, state persistence |
| **WorkflowService** | Orchestrate multi-step workflows | Direct Claude calls |
| **ClaudeClient** | Subprocess wrapper | Prompt building, state |

---

## Auto-Chain Decision Logic

Auto-chaining is controlled at **two levels**:

### Level 1: Task Flag (`task.auto_chain`)

When a task is created as part of a workflow, it gets `auto_chain=True`. This flag means:
> "After this task completes, consult the workflow to determine what happens next."

Individual tasks (not part of a workflow) have `auto_chain=False` and simply complete without checking for next steps.

### Level 2: Workflow Transition (`step.on_status[status]`)

The workflow step definition maps output statuses to transitions:

```json
{
  "agent": "implementer",
  "on_status": {
    "READY_FOR_TESTING": {
      "next_step": "tester",
      "auto_chain": true       // Auto-proceed to tester
    },
    "BLOCKED": {
      "next_step": null,       // Workflow stops
      "auto_chain": false
    },
    "NEEDS_CLARIFICATION": {
      "next_step": "requirements-analyst",
      "auto_chain": false      // Requires manual intervention
    }
  }
}
```

### Decision Flow

```
Task completes with status
         │
         ▼
┌─────────────────────────┐
│ task.auto_chain = True? │──No──▶ STOP (individual task)
└─────────────────────────┘
         │ Yes
         ▼
┌─────────────────────────┐
│ Status has transition?  │──No──▶ STOP (undefined status)
└─────────────────────────┘
         │ Yes
         ▼
┌─────────────────────────┐
│ transition.next_step    │──null─▶ STOP (workflow complete)
│ defined?                │
└─────────────────────────┘
         │ Has value
         ▼
┌─────────────────────────┐
│ transition.auto_chain   │──False─▶ STOP (manual intervention)
│ = true?                 │
└─────────────────────────┘
         │ True
         ▼
    CREATE NEXT TASK
    AND RUN IT

```

This means:
- `READY_FOR_TESTING` → Creates tester task, runs it automatically
- `BLOCKED` → Stops, no next task (workflow halted)
- `NEEDS_CLARIFICATION` → Stops, but next step IS defined (manual restart possible)
- `RANDOM_STATUS` → Stops (no transition defined for this status)

---

## Part 1: Fix Existing Code

### 1.1 Fix `task.py` Enums and Import

**File:** `cmat/models/task.py`

```python
# Fix import (line ~7)
# BEFORE:
from .utils import get_datetime_utc
# AFTER:
from cmat.utils import get_datetime_utc

# Fix TaskStatus enum
class TaskStatus(Enum):
    """Valid states for a task."""
    PENDING = "pending"
    ACTIVE = "active"          # Was IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

# Fix TaskPriority enum
class TaskPriority(Enum):
    """Priority levels for task execution."""
    LOW = "low"
    NORMAL = "normal"          # Was MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

---

### 1.2 Fix `QueueService` State Management

**File:** `cmat/services/queue_service.py`

The current implementation doesn't properly handle `active_workflows`. Here are the fixes:

**Fix `get()` to search all queues:**

```python
def get(self, task_id: str) -> Optional[Task]:
    """Get a task by ID from any queue."""
    queue = self._read_queue()
    
    # Search ALL queues including active_workflows
    for queue_name in ["pending_tasks", "active_workflows", "completed_tasks", "failed_tasks"]:
        for task_data in queue.get(queue_name, []):
            if task_data["id"] == task_id:
                return Task.from_dict(task_data)
    
    return None
```

**Add `list_active()` method:**

```python
def list_active(self) -> list[Task]:
    """List all active (in-progress) tasks."""
    queue = self._read_queue()
    return [Task.from_dict(t) for t in queue.get("active_workflows", [])]
```

**Rewrite `start()` - state only, no execution:**

```python
def start(self, task_id: str) -> Optional[Task]:
    """
    Move task from pending to active.
    
    NOTE: This only updates state. Execution is handled by TaskService.
    """
    queue = self._read_queue()
    
    # Find in pending
    task_index = None
    task_data = None
    for i, t in enumerate(queue.get("pending_tasks", [])):
        if t["id"] == task_id:
            task_index = i
            task_data = t
            break
    
    if task_data is None:
        return None
    
    task = Task.from_dict(task_data)
    
    # Update state
    task.status = TaskStatus.ACTIVE
    task.started = get_datetime_utc()
    
    # Move from pending to active
    queue["pending_tasks"].pop(task_index)
    queue["active_workflows"].append(task.to_dict())
    self._write_queue(queue)
    
    # Update agent status
    self.update_agent_status(task.assigned_agent, "active", task_id)
    
    log_operation("TASK_STARTED", f"Task: {task_id}, Agent: {task.assigned_agent}")
    
    return task
```

**Fix `complete()` to search active_workflows:**

```python
def complete(self, task_id: str, result: str) -> Optional[Task]:
    """
    Mark an active task as completed.
    
    Moves task from active_workflows to completed_tasks.
    """
    queue = self._read_queue()
    
    # Find in active_workflows (NOT pending_tasks)
    task_index = None
    task_data = None
    for i, t in enumerate(queue.get("active_workflows", [])):
        if t["id"] == task_id:
            task_index = i
            task_data = t
            break
    
    if task_data is None:
        return None
    
    task = Task.from_dict(task_data)
    task.status = TaskStatus.COMPLETED
    task.completed = get_datetime_utc()
    task.result = result
    
    # Move from active to completed
    queue["active_workflows"].pop(task_index)
    queue["completed_tasks"].append(task.to_dict())
    self._write_queue(queue)
    
    # Update agent status
    self.update_agent_status(task.assigned_agent, "idle", None)
    
    log_operation("TASK_COMPLETED", f"Task: {task_id}, Result: {result}")
    
    return task
```

**Fix `fail()` similarly:**

```python
def fail(self, task_id: str, reason: str) -> Optional[Task]:
    """
    Mark an active task as failed.
    
    Moves task from active_workflows to failed_tasks.
    """
    queue = self._read_queue()
    
    # Find in active_workflows
    task_index = None
    task_data = None
    for i, t in enumerate(queue.get("active_workflows", [])):
        if t["id"] == task_id:
            task_index = i
            task_data = t
            break
    
    if task_data is None:
        return None
    
    task = Task.from_dict(task_data)
    task.status = TaskStatus.FAILED
    task.completed = get_datetime_utc()
    task.result = reason
    
    # Move from active to failed
    queue["active_workflows"].pop(task_index)
    queue["failed_tasks"].append(task.to_dict())
    self._write_queue(queue)
    
    # Update agent status
    self.update_agent_status(task.assigned_agent, "idle", None)
    
    log_operation("TASK_FAILED", f"Task: {task_id}, Reason: {reason}")
    
    return task
```

**Fix `cancel()` to handle both pending and active:**

```python
def cancel(self, task_id: str, reason: Optional[str] = None) -> Optional[Task]:
    """
    Cancel a pending or active task.
    
    For active tasks, also attempts to kill the process if PID is stored.
    """
    queue = self._read_queue()
    
    # Try pending first
    for i, t in enumerate(queue.get("pending_tasks", [])):
        if t["id"] == task_id:
            task = Task.from_dict(t)
            task.cancel(reason)
            queue["pending_tasks"].pop(i)
            queue["failed_tasks"].append(task.to_dict())
            self._write_queue(queue)
            log_operation("TASK_CANCELLED", f"Task: {task_id} (pending), Reason: {reason}")
            return task
    
    # Try active
    for i, t in enumerate(queue.get("active_workflows", [])):
        if t["id"] == task_id:
            task = Task.from_dict(t)
            
            # Try to kill process if PID stored
            if task.metadata.process_pid:
                try:
                    import os
                    import signal
                    os.kill(int(task.metadata.process_pid), signal.SIGTERM)
                except (ProcessLookupError, ValueError, OSError):
                    pass  # Process already gone
            
            task.cancel(reason)
            queue["active_workflows"].pop(i)
            queue["failed_tasks"].append(task.to_dict())
            self._write_queue(queue)
            
            self.update_agent_status(task.assigned_agent, "idle", None)
            log_operation("TASK_CANCELLED", f"Task: {task_id} (active), Reason: {reason}")
            return task
    
    return None
```

**Add `update_single_metadata()` for key/value updates:**

```python
def update_single_metadata(self, task_id: str, key: str, value: str) -> Optional[Task]:
    """
    Update a single metadata field on a task.
    
    This matches the bash: cmat queue metadata <task_id> <key> <value>
    """
    queue = self._read_queue()
    
    for queue_name in ["pending_tasks", "active_workflows", "completed_tasks", "failed_tasks"]:
        for i, task_data in enumerate(queue.get(queue_name, [])):
            if task_data["id"] == task_id:
                # Update the metadata field
                if "metadata" not in task_data:
                    task_data["metadata"] = {}
                task_data["metadata"][key] = value
                queue[queue_name][i] = task_data
                self._write_queue(queue)
                
                log_operation("METADATA_UPDATE", f"Task: {task_id}, {key}={value}")
                return Task.from_dict(task_data)
    
    return None
```

**Add `rerun()` method:**

```python
def rerun(self, task_id: str) -> Optional[Task]:
    """
    Re-queue a completed or failed task for re-execution.
    
    Moves task back to pending with reset state.
    """
    queue = self._read_queue()
    
    # Find in completed or failed
    source_queue = None
    task_index = None
    task_data = None
    
    for qname in ["completed_tasks", "failed_tasks"]:
        for i, t in enumerate(queue.get(qname, [])):
            if t["id"] == task_id:
                source_queue = qname
                task_index = i
                task_data = t
                break
        if task_data:
            break
    
    if task_data is None:
        return None
    
    task = Task.from_dict(task_data)
    
    # Reset state
    task.status = TaskStatus.PENDING
    task.started = None
    task.completed = None
    task.result = None
    
    # Move to pending
    queue[source_queue].pop(task_index)
    queue["pending_tasks"].append(task.to_dict())
    self._write_queue(queue)
    
    log_operation("TASK_RERUN", f"Task: {task_id}, From: {source_queue}")
    
    return task
```

**Add `cancel_all()` method:**

```python
def cancel_all(self, reason: str = "bulk cancellation") -> int:
    """
    Cancel all pending and active tasks.
    
    Returns count of cancelled tasks.
    """
    count = 0
    
    # Get all task IDs first to avoid mutation during iteration
    queue = self._read_queue()
    pending_ids = [t["id"] for t in queue.get("pending_tasks", [])]
    active_ids = [t["id"] for t in queue.get("active_workflows", [])]
    
    for task_id in pending_ids + active_ids:
        if self.cancel(task_id, reason):
            count += 1
    
    return count
```

---

## Part 2: Create TaskService (NEW)

**File:** `cmat/services/task_service.py`

```python
"""
Task execution service for CMAT.

Handles the execution of individual tasks including prompt building,
Claude invocation, and status extraction.
"""

import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cmat.models.task import Task
from cmat.models.agent import Agent
from cmat.claude.client import ClaudeClient
from cmat.claude.config import ClaudeClientConfig
from cmat.claude.response import ClaudeResponse
from cmat.utils import (
    get_timestamp,
    log_operation,
    log_error,
    extract_enhancement_name,
)


@dataclass
class ExecutionResult:
    """Result of a task execution."""
    success: bool
    status: Optional[str]
    exit_code: int
    output_dir: str
    log_file: str
    duration_seconds: int
    pid: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "status": self.status,
            "exit_code": self.exit_code,
            "output_dir": self.output_dir,
            "log_file": self.log_file,
            "duration_seconds": self.duration_seconds,
            "pid": self.pid,
        }


class TaskService:
    """
    Executes individual tasks.
    
    Responsible for:
    - Building prompts (template + skills + variables)
    - Invoking Claude with PID tracking
    - Extracting status from output
    - Managing execution logs
    """
    
    def __init__(
        self,
        templates_file: str = ".claude/docs/TASK_PROMPT_DEFAULTS.md",
        agents_dir: str = ".claude/agents",
        skills_dir: str = ".claude/skills",
        logs_dir: str = ".claude/logs",
    ):
        self.templates_file = Path(templates_file)
        self.agents_dir = Path(agents_dir)
        self.skills_dir = Path(skills_dir)
        self.logs_dir = Path(logs_dir)
        self._templates_cache: Optional[dict[str, str]] = None
        
        # Service dependencies
        self._agent_service = None
        self._skills_service = None
        self._queue_service = None
        self._claude_client = None
    
    def set_services(self, agent=None, skills=None, queue=None, claude=None):
        """Inject service dependencies."""
        self._agent_service = agent
        self._skills_service = skills
        self._queue_service = queue
        self._claude_client = claude or ClaudeClient()
    
    # =========================================================================
    # TEMPLATE LOADING
    # =========================================================================
    
    def _load_templates(self) -> dict[str, str]:
        """Load all templates from TASK_PROMPT_DEFAULTS.md."""
        if self._templates_cache is not None:
            return self._templates_cache
        
        if not self.templates_file.exists():
            return {}
        
        content = self.templates_file.read_text()
        templates = {}
        
        # Parse each template section
        template_types = [
            ("analysis", "ANALYSIS_TEMPLATE"),
            ("technical_analysis", "TECHNICAL_ANALYSIS_TEMPLATE"),
            ("implementation", "IMPLEMENTATION_TEMPLATE"),
            ("testing", "TESTING_TEMPLATE"),
            ("documentation", "DOCUMENTATION_TEMPLATE"),
            ("integration", "INTEGRATION_TEMPLATE"),
        ]
        
        for task_type, template_name in template_types:
            # Extract content between "# TEMPLATE_NAME" and "===END_TEMPLATE==="
            pattern = rf"^# {template_name}$\n(.*?)^===END_TEMPLATE===$"
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                templates[task_type] = match.group(1).strip()
        
        self._templates_cache = templates
        return templates
    
    def get_template(self, task_type: str) -> Optional[str]:
        """Get template for a task type."""
        return self._load_templates().get(task_type)
    
    # =========================================================================
    # PROMPT BUILDING
    # =========================================================================
    
    def build_prompt(
        self,
        agent: Agent,
        task_type: str,
        task_id: str,
        task_description: str,
        source_file: str,
        enhancement_name: str,
        enhancement_dir: str,
        required_output_filename: str = "output.md",
        expected_statuses: str = "(No workflow-defined statuses)",
    ) -> Optional[str]:
        """
        Build complete prompt with template, skills, and variable substitution.
        """
        # Load template
        template = self.get_template(task_type)
        if not template:
            log_error(f"No template found for task type: {task_type}")
            return None
        
        # Build skills section
        skills_section = ""
        if self._skills_service and agent.skills:
            skills_section = self._skills_service.build_skills_prompt(agent.skills)
        
        # Append skills to template
        if skills_section:
            template = template + "\n" + skills_section
        
        # Build input instruction
        input_instruction = self._build_input_instruction(source_file)
        
        # Get agent config path
        agent_config = str(self.agents_dir / f"{agent.agent_file}.md")
        
        # Substitute variables
        variables = {
            "agent": agent.agent_file,
            "agent_config": agent_config,
            "source_file": source_file or "",
            "task_description": task_description,
            "task_id": task_id,
            "task_type": task_type,
            "enhancement_name": enhancement_name,
            "enhancement_dir": enhancement_dir,
            "input_instruction": input_instruction,
            "required_output_filename": required_output_filename,
            "expected_statuses": expected_statuses,
        }
        
        prompt = template
        for key, value in variables.items():
            prompt = prompt.replace(f"${{{key}}}", str(value))
        
        return prompt
    
    def _build_input_instruction(self, source_file: str) -> str:
        """Build the input instruction based on source file type."""
        if not source_file or source_file == "null":
            return "Work from the task description provided."
        
        path = Path(source_file)
        if path.is_file():
            return f"Read and process this file: {source_file}"
        elif path.is_dir():
            return f"Read and process all files in this directory: {source_file}"
        else:
            return f"Input: {source_file}"
    
    # =========================================================================
    # EXECUTION
    # =========================================================================
    
    def execute(
        self,
        task: Task,
        agent: Agent,
        workflow_name: Optional[str] = None,
        workflow_step: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Execute a task.
        
        This is the core execution method used by both workflow-integrated
        and direct invocations.
        """
        start_time = time.time()
        
        # Extract enhancement context
        enhancement_name = extract_enhancement_name(task.source_file, task.id)
        enhancement_dir = f"enhancements/{enhancement_name}"
        
        # Create output directory
        output_dir = Path(enhancement_dir) / agent.agent_file
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file
        log_dir = Path(enhancement_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = get_timestamp().replace(":", "-").replace("T", "_").replace("Z", "")
        log_file = log_dir / f"{agent.agent_file}_{task.id}_{timestamp}.log"
        
        # Get workflow context for prompt
        required_output = "output.md"
        expected_statuses = "(No workflow-defined statuses - output any appropriate status)"
        
        if workflow_name and workflow_step is not None:
            # Would get from workflow service
            pass  # TODO: integrate with workflow service
        
        # Build prompt
        prompt = self.build_prompt(
            agent=agent,
            task_type=task.task_type,
            task_id=task.id,
            task_description=task.description,
            source_file=task.source_file,
            enhancement_name=enhancement_name,
            enhancement_dir=enhancement_dir,
            required_output_filename=required_output,
            expected_statuses=expected_statuses,
        )
        
        if not prompt:
            return ExecutionResult(
                success=False,
                status=None,
                exit_code=-1,
                output_dir=str(output_dir),
                log_file=str(log_file),
                duration_seconds=0,
            )
        
        # Write log header
        self._write_log(log_file, "=== Starting Agent Execution ===")
        self._write_log(log_file, f"Start Time: {get_timestamp()}")
        self._write_log(log_file, f"Agent: {agent.agent_file}")
        self._write_log(log_file, f"Task ID: {task.id}")
        self._write_log(log_file, f"Input: {task.source_file}")
        self._write_log(log_file, f"Output: {output_dir}")
        self._write_log(log_file, f"Log: {log_file}")
        self._write_log(log_file, "")
        self._write_log(log_file, "=" * 69)
        self._write_log(log_file, "PROMPT SENT TO AGENT")
        self._write_log(log_file, "=" * 69)
        self._write_log(log_file, "")
        self._write_log(log_file, prompt)
        self._write_log(log_file, "")
        self._write_log(log_file, "=" * 69)
        self._write_log(log_file, "END OF PROMPT")
        self._write_log(log_file, "=" * 69)
        self._write_log(log_file, "")
        
        # Set environment for cost hook
        env = {
            "CMAT_CURRENT_TASK_ID": task.id,
            "CMAT_CURRENT_LOG_FILE": str(log_file),
            "CMAT_AGENT": agent.agent_file,
            "CMAT_ENHANCEMENT": enhancement_name,
        }
        
        # Execute with PID tracking
        pid, exit_code, output = self._execute_claude(
            prompt=prompt,
            log_file=log_file,
            env=env,
            tools=agent.tools,
        )
        
        # Store PID in metadata if queue service available
        if self._queue_service and pid:
            self._queue_service.update_single_metadata(task.id, "process_pid", str(pid))
        
        duration = int(time.time() - start_time)
        
        # Extract status
        status = self.extract_status(output)
        
        # Write log footer
        self._write_log(log_file, "")
        self._write_log(log_file, "=== Agent Execution Complete ===")
        self._write_log(log_file, f"End Time: {get_timestamp()}")
        self._write_log(log_file, f"Duration: {duration}s")
        self._write_log(log_file, f"Exit Code: {exit_code}")
        self._write_log(log_file, f"Status: {status or 'UNKNOWN'}")
        
        log_operation("TASK_EXECUTED", f"Task: {task.id}, Status: {status}, Duration: {duration}s")
        
        return ExecutionResult(
            success=(exit_code == 0),
            status=status,
            exit_code=exit_code,
            output_dir=str(output_dir),
            log_file=str(log_file),
            duration_seconds=duration,
            pid=pid,
        )
    
    def _execute_claude(
        self,
        prompt: str,
        log_file: Path,
        env: dict,
        tools: list[str],
    ) -> tuple[Optional[int], int, str]:
        """
        Execute Claude with PID tracking.
        
        Returns: (pid, exit_code, output)
        """
        # Merge environment
        full_env = os.environ.copy()
        full_env.update(env)
        
        # Build command
        args = [
            "claude",
            "--print",
            "--permission-mode", "bypassPermissions",
        ]
        if tools:
            args.extend(["--allowedTools", ",".join(tools)])
        args.extend(["--prompt", prompt])
        
        try:
            with open(log_file, 'a') as log_handle:
                process = subprocess.Popen(
                    args,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    env=full_env,
                )
                
                pid = process.pid
                exit_code = process.wait()
            
            # Read output from log for status extraction
            output = log_file.read_text()
            
            return pid, exit_code, output
            
        except FileNotFoundError:
            log_error("Claude CLI not found")
            return None, -1, ""
        except Exception as e:
            log_error(f"Execution error: {e}")
            return None, -1, ""
    
    def _write_log(self, log_file: Path, message: str) -> None:
        """Append message to log file."""
        with open(log_file, 'a') as f:
            f.write(message + "\n")
    
    # =========================================================================
    # STATUS EXTRACTION
    # =========================================================================
    
    def extract_status(self, output: str) -> Optional[str]:
        """
        Extract completion status from agent output.
        
        Looks for patterns like:
        - READY_FOR_TESTING
        - IMPLEMENTATION_COMPLETE
        - BLOCKED: <reason>
        """
        pattern = r"(READY_FOR_[A-Z_]+|[A-Z_]+_COMPLETE|BLOCKED:[^\n]*)"
        matches = re.findall(pattern, output)
        
        if matches:
            return matches[-1].strip()
        return None
    
    # =========================================================================
    # DIRECT INVOCATION (UI Operations)
    # =========================================================================
    
    def execute_direct(
        self,
        agent_name: str,
        input_file: str,
        output_dir: str,
        description: str = "UI-invoked task",
        task_type: str = "analysis",
    ) -> ExecutionResult:
        """
        Execute agent directly without queue integration.
        
        Used for UI operations like enhancement creation.
        """
        # Get agent
        agent = self._agent_service.get(agent_name) if self._agent_service else None
        if not agent:
            return ExecutionResult(
                success=False,
                status=None,
                exit_code=-1,
                output_dir=output_dir,
                log_file="",
                duration_seconds=0,
            )
        
        # Create a temporary task object
        from cmat.models.task import Task, TaskStatus, TaskPriority
        from cmat.utils import get_datetime_utc
        
        task = Task(
            id=f"ui_{agent_name}_{int(time.time())}",
            title=description,
            assigned_agent=agent_name,
            priority=TaskPriority.NORMAL,
            task_type=task_type,
            description=description,
            source_file=input_file,
            created=get_datetime_utc(),
            status=TaskStatus.ACTIVE,
        )
        
        # Execute (no workflow context for direct invocations)
        return self.execute(task, agent)
```

---

## Part 3: Update WorkflowService (Orchestrator)

**File:** `cmat/services/workflow_service.py`

Add these methods to the existing WorkflowService:

```python
def set_services(self, queue=None, task=None, agent=None):
    """Inject service dependencies."""
    self._queue_service = queue
    self._task_service = task
    self._agent_service = agent

def start_workflow(self, workflow_name: str, enhancement_name: str) -> Optional[str]:
    """
    Start a workflow for an enhancement.
    
    Creates and starts the first task in the workflow.
    Returns the task ID.
    """
    # Validate workflow
    template = self.get(workflow_name)
    if not template:
        log_error(f"Workflow not found: {workflow_name}")
        return None
    
    if not template.steps:
        log_error(f"Workflow has no steps: {workflow_name}")
        return None
    
    # Get first step
    first_step = template.steps[0]
    
    # Resolve input path
    input_path = self.resolve_input_path(first_step, enhancement_name)
    
    # Verify input exists
    if not Path(input_path).exists():
        log_error(f"Workflow input not found: {input_path}")
        return None
    
    # Get task type for agent
    task_type = self.get_task_type_for_agent(first_step.agent)
    
    # Create task
    task = self._queue_service.add(
        title=f"Workflow: {workflow_name} - {enhancement_name}",
        assigned_agent=first_step.agent,
        priority="high",
        task_type=task_type,
        source_file=input_path,
        description=f"Workflow: {workflow_name}, Step 0",
        auto_complete=True,
        auto_chain=True,
        metadata={
            "workflow_name": workflow_name,
            "workflow_step": "0",
            "enhancement_title": enhancement_name,
        },
    )
    
    log_operation("WORKFLOW_STARTED", f"Workflow: {workflow_name}, Task: {task.id}")
    
    # Start the task (this triggers execution)
    self.run_task(task.id)
    
    return task.id

def run_task(self, task_id: str) -> Optional[str]:
    """
    Run a pending task through to completion.
    
    Orchestrates: start -> execute -> complete/fail -> auto_chain (if applicable)
    
    Returns: Next task ID if auto-chained, None otherwise
    """
    # Move to active
    task = self._queue_service.start(task_id)
    if not task:
        return None
    
    # Get agent
    agent = self._agent_service.get(task.assigned_agent)
    if not agent:
        self._queue_service.fail(task_id, f"Agent not found: {task.assigned_agent}")
        return None
    
    # Execute
    result = self._task_service.execute(
        task=task,
        agent=agent,
        workflow_name=task.metadata.workflow_name,
        workflow_step=int(task.metadata.workflow_step) if task.metadata.workflow_step else None,
    )
    
    # Complete or fail based on result
    if result.success and result.status:
        self._queue_service.complete(task_id, result.status)
        
        # Auto-chain if:
        # 1. Task has auto_chain=True (meaning it's part of a workflow)
        # 2. We got a status from the agent
        # The auto_chain() method itself will check if the status
        # has a valid transition defined in the workflow
        if task.auto_chain and result.status:
            return self.auto_chain(task_id, result.status)
    else:
        self._queue_service.fail(task_id, result.status or "Execution failed")
        
        # Even on failure, check if workflow defines a transition for this status
        # (e.g., BLOCKED might have a defined handler)
        if task.auto_chain and result.status:
            return self.auto_chain(task_id, result.status)
    
    return None

def auto_chain(self, task_id: str, status: str) -> Optional[str]:
    """
    Chain to next workflow step based on completion status.
    
    Returns the new task ID if chained, None otherwise.
    """
    # Get completed task
    task = self._queue_service.get(task_id)
    if not task:
        return None
    
    # Check workflow context
    workflow_name = task.metadata.workflow_name
    workflow_step = task.metadata.workflow_step
    
    if not workflow_name or workflow_step is None:
        log_info("Task not part of workflow - cannot auto-chain")
        return None
    
    step_index = int(workflow_step)
    
    # Get enhancement context
    enhancement_name = extract_enhancement_name(task.source_file, task_id)
    enhancement_dir = Path("enhancements") / enhancement_name
    
    # Load workflow
    template = self.get(workflow_name)
    if not template:
        log_error(f"Workflow not found: {workflow_name}")
        return None
    
    current_step = template.get_step(step_index)
    if not current_step:
        log_error(f"Step {step_index} not found")
        return None
    
    # Validate outputs
    if not self.validate_agent_outputs(
        task.assigned_agent,
        str(enhancement_dir),
        current_step.required_output,
    ):
        log_error("Output validation failed - cannot auto-chain")
        return None
    
    # Check transition
    transition = current_step.get_transition(status)
    if not transition:
        log_info(f"No transition for status: {status}")
        return None
    
    if not transition.next_step:
        log_info("Workflow complete - no next step")
        return None
    
    if not transition.auto_chain:
        log_info("Auto-chain disabled for this transition")
        return None
    
    # Get next step
    next_step_index = step_index + 1
    next_step = template.get_step(next_step_index)
    if not next_step:
        log_error(f"Next step not found at index {next_step_index}")
        return None
    
    # Resolve input
    next_input = self.resolve_input_path(
        next_step,
        enhancement_name,
        previous_agent=task.assigned_agent,
    )
    
    if not Path(next_input).exists():
        log_error(f"Next step input not found: {next_input}")
        return None
    
    # Get task type
    task_type = self.get_task_type_for_agent(next_step.agent)
    
    # Create next task
    new_task = self._queue_service.add(
        title=f"Process {enhancement_name} with {next_step.agent}",
        assigned_agent=next_step.agent,
        priority="high",
        task_type=task_type,
        source_file=next_input,
        description=f"Workflow: {workflow_name}, Step {next_step_index}",
        auto_complete=True,
        auto_chain=True,
        metadata={
            "workflow_name": workflow_name,
            "workflow_step": str(next_step_index),
            "enhancement_title": task.metadata.enhancement_title,
        },
    )
    
    log_operation("AUTO_CHAIN", f"From {task_id} to {new_task.id}")
    
    # Run next task
    self.run_task(new_task.id)
    
    return new_task.id

def validate_agent_outputs(
    self,
    agent_name: str,
    enhancement_dir: str,
    required_output_filename: str,
) -> bool:
    """
    Validate that an agent has produced required outputs.
    """
    # Get agent for validation settings
    agent = self._agent_service.get(agent_name) if self._agent_service else None
    metadata_required = True
    if agent:
        metadata_required = agent.get_validation("metadata_required", True)
    
    # Check directory structure
    required_dir = Path(enhancement_dir) / agent_name / "required_output"
    required_file = required_dir / required_output_filename
    
    if not required_dir.is_dir():
        log_error(f"Required output directory missing: {required_dir}")
        return False
    
    if not required_file.is_file():
        log_error(f"Required output file missing: {required_file}")
        return False
    
    # Validate metadata if required
    if metadata_required:
        content = required_file.read_text()
        
        if "---" not in content:
            log_error(f"Missing metadata header in: {required_file}")
            return False
        
        required_fields = ["enhancement:", "agent:", "task_id:", "timestamp:", "status:"]
        for field in required_fields:
            if field not in content:
                log_error(f"Missing metadata field '{field}' in: {required_file}")
                return False
    
    return True

def get_task_type_for_agent(self, agent_name: str) -> str:
    """Get the appropriate task type for an agent based on its role."""
    agent = self._agent_service.get(agent_name) if self._agent_service else None
    if not agent:
        return "analysis"
    
    role_to_type = {
        "analysis": "analysis",
        "technical_design": "technical_analysis",
        "implementation": "implementation",
        "testing": "testing",
        "documentation": "documentation",
        "integration": "integration",
    }
    
    return role_to_type.get(agent.role, "analysis")
```

---

## Part 4: Update SkillsService

**File:** `cmat/services/skills_service.py`

Add this method:

```python
def build_skills_prompt(self, skill_names: list[str]) -> str:
    """
    Build complete skills section for agent prompt.
    
    Matches the bash formatting with header and footer.
    """
    if not skill_names:
        return ""
    
    sections = []
    sections.append("""
################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

You have access to the following specialized skills that enhance your capabilities.
Use these skills when they are relevant to your task:

""")
    
    skill_count = 0
    for name in skill_names:
        content = self.get_skill_content(name)
        if content:
            skill_count += 1
            sections.append("---\n\n")
            sections.append(content)
            sections.append("\n\n")
    
    if skill_count > 0:
        sections.append("""---

**Using Skills**: Apply the above skills as appropriate to accomplish your objectives.
Reference specific skills in your work when they guide your approach or decisions.

################################################################################
""")
    
    return "".join(sections)
```

---

## Part 5: Update CMAT Entry Point

**File:** `cmat/cmat.py`

The existing file needs these additions:

```python
"""
CMAT - Claude Multi-Agent Template

Main entry point class that composes all services and provides
a unified interface for CMAT operations.
"""

from pathlib import Path
from typing import Optional

from cmat.services.queue_service import QueueService
from cmat.services.agent_service import AgentService
from cmat.services.skills_service import SkillsService
from cmat.services.workflow_service import WorkflowService
from cmat.services.task_service import TaskService  # NEW
from cmat.claude.client import ClaudeClient  # NEW
from cmat.utils import find_project_root, ensure_directories


class CMAT:
    """
    Main entry point for CMAT operations.

    Composes all services and provides a unified interface for
    managing tasks, agents, skills, and workflows.

    Usage:
        cmat = CMAT()

        # Start a workflow (creates and runs tasks automatically)
        cmat.workflow.start_workflow("feature-development", "my-feature")

        # Or run individual tasks
        task = cmat.queue.add("Task title", "architect", "high", ...)
        cmat.workflow.run_task(task.id)

        # Direct execution (no queue, no workflow)
        result = cmat.tasks.execute_direct("architect", "input.md", "output/")
    """

    def __init__(
            self,
            base_path: Optional[str] = None,
            queue_file: Optional[str] = None,
            agents_dir: Optional[str] = None,
            skills_dir: Optional[str] = None,
            templates_file: Optional[str] = None,
            enhancements_dir: Optional[str] = None,
            auto_find_root: bool = True,
    ):
        # Determine base path
        if base_path:
            base = Path(base_path)
        elif auto_find_root:
            found_root = find_project_root()
            base = found_root if found_root else Path.cwd()
        else:
            base = Path.cwd()

        self._base_path = base
        claude_base = base / ".claude"

        # Initialize Claude client
        self.claude = ClaudeClient()

        # Initialize services with paths
        self.queue = QueueService(
            queue_file=queue_file or str(claude_base / "queues/task_queue.json")
        )

        self.agents = AgentService(
            agents_dir=agents_dir or str(claude_base / "agents")
        )

        self.skills = SkillsService(
            skills_dir=skills_dir or str(claude_base / "skills")
        )

        # NEW: Task execution service
        self.tasks = TaskService(
            templates_file=str(claude_base / "docs/TASK_PROMPT_DEFAULTS.md"),
            agents_dir=agents_dir or str(claude_base / "agents"),
            skills_dir=skills_dir or str(claude_base / "skills"),
            logs_dir=str(claude_base / "logs"),
        )

        self.workflow = WorkflowService(
            templates_file=templates_file or str(claude_base / "queues/workflow_templates.json"),
            enhancements_dir=enhancements_dir or str(base / "enhancements")
        )

        # NEW: Wire up service dependencies
        self.tasks.set_services(
            agent=self.agents,
            skills=self.skills,
            queue=self.queue,
            claude=self.claude,
        )

        self.workflow.set_services(
            queue=self.queue,
            task=self.tasks,
            agent=self.agents,
        )

    @property
    def base_path(self) -> Path:
        """Get the base path for CMAT files."""
        return self._base_path

    def ensure_directories(self) -> None:
        """Ensure all required CMAT directories exist."""
        ensure_directories(self._base_path)

    def invalidate_caches(self) -> None:
        """Invalidate all service caches to force reload from disk."""
        self.agents.invalidate_cache()
        self.skills.invalidate_cache()
        self.workflow.invalidate_cache()

    @property
    def version(self) -> str:
        """Get the CMAT version."""
        from cmat import __version__
        return __version__
```

---

## Part 6: File Structure Summary

```
.claude/cmat/
├── __init__.py
├── cmat.py                    # Main entry point (NEW)
├── utils.py                   # Shared utilities (EXISTS - OK)
├── models/
│   ├── __init__.py
│   ├── agent.py               # EXISTS - OK
│   ├── skill.py               # EXISTS - OK
│   ├── task.py                # EXISTS - FIX enums, import
│   ├── task_metadata.py       # EXISTS - OK
│   ├── enhancement.py         # EXISTS - OK
│   ├── tool.py                # EXISTS - OK
│   ├── claude_model.py        # EXISTS - OK
│   ├── step_transition.py     # EXISTS - OK
│   ├── workflow_step.py       # EXISTS - OK
│   └── workflow_template.py   # EXISTS - OK
├── services/
│   ├── __init__.py
│   ├── queue_service.py       # EXISTS - FIX multiple methods
│   ├── agent_service.py       # EXISTS - OK (stays as registry)
│   ├── skills_service.py      # EXISTS - ADD build_skills_prompt
│   ├── workflow_service.py    # EXISTS - ADD orchestration methods
│   └── task_service.py        # NEW - execution engine
└── claude/
    ├── __init__.py
    ├── client.py              # EXISTS - OK
    ├── config.py              # EXISTS - OK
    └── response.py            # EXISTS - OK
```

---

## Implementation Order

### Phase 1: Fix Foundations
1. Fix `task.py` enums and import
2. Fix `queue_service.py` state management methods

### Phase 2: Add TaskService
3. Create `task_service.py` with full execution logic

### Phase 3: Wire Up Orchestration
4. Add orchestration methods to `workflow_service.py`
5. Add `build_skills_prompt()` to `skills_service.py`
6. Create `cmat.py` entry point

### Phase 4: Complete Queue Commands
7. Add `rerun()`, `cancel_all()`, `update_single_metadata()`

### Phase 5: Remaining Features
8. Add remaining workflow template CRUD
9. Add `init()`, `status()`, `preview_prompt()` to queue
10. Add `generate_agents_json()` to agent service
