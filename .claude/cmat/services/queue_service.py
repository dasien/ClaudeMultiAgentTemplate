"""
Queue service for CMAT task management.

Handles task queue operations including adding, listing, updating,
and managing task lifecycle.

NOTE: This service handles state management only. Execution logic
lives in TaskService.
"""

import json
import os
import signal
from pathlib import Path
from typing import Optional
import random

from cmat.models.task import Task, TaskStatus, TaskPriority
from cmat.models.task_metadata import TaskMetadata
from cmat.utils import get_timestamp, get_datetime_utc, log_operation, log_error


class QueueService:
    """
    Manages the task queue for CMAT workflows.

    Provides operations for adding tasks, updating status, listing tasks,
    and managing task lifecycle.
    """

    def __init__(self, queue_file: str = ".claude/queues/task_queue.json"):
        self.queue_file = Path(queue_file)
        self._task_service = None  # Injected via set_services()
        self._ensure_queue_exists()

    def _ensure_queue_exists(self) -> None:
        """Ensure the queue file exists with valid structure."""
        if not self.queue_file.exists():
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_queue(self._empty_queue())

    def _empty_queue(self) -> dict:
        """Return an empty queue structure."""
        return {
            "queue_metadata": {
                "created": get_timestamp(),
                "version": "2.0.0",
                "description": "Task queue for multi-agent development system"
            },
            "active_workflows": [],
            "pending_tasks": [],
            "completed_tasks": [],
            "failed_tasks": [],
            "agent_status": {}
        }

    def _read_queue(self) -> dict:
        """Read the queue file."""
        with open(self.queue_file, 'r') as f:
            return json.load(f)

    def _write_queue(self, data: dict) -> None:
        """Write the queue file."""
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        timestamp = int(get_datetime_utc().timestamp())
        random_suffix = random.randint(10000, 99999)
        return f"task_{timestamp}_{random_suffix}"

    def add(
            self,
            title: str,
            assigned_agent: str,
            priority: str,
            task_type: str,
            source_file: str,
            description: str,
            metadata: Optional[dict] = None,
            auto_complete: bool = False,
            auto_chain: bool = False,
    ) -> Task:
        """
        Add a new task to the queue.

        Returns the created Task.
        """
        task = Task(
            id=self._generate_task_id(),
            title=title,
            assigned_agent=assigned_agent,
            priority=TaskPriority(priority),
            task_type=task_type,
            source_file=source_file,
            description=description,
            created=get_datetime_utc(),
            status=TaskStatus.PENDING,
            auto_complete=auto_complete,
            auto_chain=auto_chain,
            metadata=TaskMetadata.from_dict(metadata or {}),
        )

        queue = self._read_queue()
        queue["pending_tasks"].append(task.to_dict())
        self._write_queue(queue)

        log_operation("TASK_ADDED", f"Task: {task.id}, Agent: {assigned_agent}, Title: {title}")

        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID from any queue."""
        queue = self._read_queue()

        # Search ALL queues including active_workflows
        for queue_name in ["pending_tasks", "active_workflows", "completed_tasks", "failed_tasks"]:
            for task_data in queue.get(queue_name, []):
                if task_data["id"] == task_id:
                    return Task.from_dict(task_data)

        return None

    def list_pending(self) -> list[Task]:
        """List all pending tasks."""
        queue = self._read_queue()
        return [Task.from_dict(t) for t in queue.get("pending_tasks", [])]

    def list_completed(self) -> list[Task]:
        """List all completed tasks."""
        queue = self._read_queue()
        return [Task.from_dict(t) for t in queue.get("completed_tasks", [])]

    def list_failed(self) -> list[Task]:
        """List all failed tasks."""
        queue = self._read_queue()
        return [Task.from_dict(t) for t in queue.get("failed_tasks", [])]

    def list_active(self) -> list[Task]:
        """List all active (in-progress) tasks."""
        queue = self._read_queue()
        return [Task.from_dict(t) for t in queue.get("active_workflows", [])]

    def list_by_agent(self, agent_name: str) -> list[Task]:
        """List all tasks assigned to a specific agent."""
        all_tasks = self.list_pending() + self.list_active() + self.list_completed() + self.list_failed()
        return [t for t in all_tasks if t.assigned_agent == agent_name]

    def list_by_enhancement(self, enhancement_name: str) -> list[Task]:
        """List all tasks for a specific enhancement."""
        all_tasks = self.list_pending() + self.list_active() + self.list_completed() + self.list_failed()
        return [t for t in all_tasks if t.metadata.enhancement_title == enhancement_name]

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

    def update_metadata(self, task_id: str, metadata_updates: dict) -> Optional[Task]:
        """
        Update metadata fields on a task.

        Searches all queues for the task.
        """
        queue = self._read_queue()

        for queue_name in ["pending_tasks", "active_workflows", "completed_tasks", "failed_tasks"]:
            for i, task_data in enumerate(queue.get(queue_name, [])):
                if task_data["id"] == task_id:
                    task = Task.from_dict(task_data)
                    for key, value in metadata_updates.items():
                        if hasattr(task.metadata, key):
                            setattr(task.metadata, key, value)

                    queue[queue_name][i] = task.to_dict()
                    self._write_queue(queue)
                    return task

        return None

    def get_agent_status(self, agent_name: str) -> Optional[dict]:
        """Get the current status of an agent."""
        queue = self._read_queue()
        return queue.get("agent_status", {}).get(agent_name)

    def update_agent_status(
            self,
            agent_name: str,
            status: str,
            current_task: Optional[str] = None
    ) -> None:
        """Update an agent's status."""
        queue = self._read_queue()

        if "agent_status" not in queue:
            queue["agent_status"] = {}

        queue["agent_status"][agent_name] = {
            "status": status,
            "last_activity": get_timestamp(),
            "current_task": current_task
        }

        self._write_queue(queue)

        log_operation("AGENT_STATUS_UPDATE", f"Agent: {agent_name}, Status: {status}, Task: {current_task}")

    def clear_completed(self) -> int:
        """Clear all completed tasks. Returns count of cleared tasks."""
        queue = self._read_queue()
        count = len(queue.get("completed_tasks", []))
        queue["completed_tasks"] = []
        self._write_queue(queue)
        return count

    def clear_failed(self) -> int:
        """Clear all failed tasks. Returns count of cleared tasks."""
        queue = self._read_queue()
        count = len(queue.get("failed_tasks", []))
        queue["failed_tasks"] = []
        self._write_queue(queue)
        return count

    def status(self) -> dict:
        """
        Get queue status summary.

        Returns dict with counts and agent status:
        {
            "pending": count,
            "active": count,
            "completed": count,
            "failed": count,
            "total": count,
            "agent_status": {agent_name: {status, current_task, last_activity}}
        }
        """
        queue = self._read_queue()

        return {
            "pending": len(queue.get("pending_tasks", [])),
            "active": len(queue.get("active_workflows", [])),
            "completed": len(queue.get("completed_tasks", [])),
            "failed": len(queue.get("failed_tasks", [])),
            "total": (
                len(queue.get("pending_tasks", [])) +
                len(queue.get("active_workflows", [])) +
                len(queue.get("completed_tasks", [])) +
                len(queue.get("failed_tasks", []))
            ),
            "agent_status": queue.get("agent_status", {}),
        }

    def init(self, force: bool = False) -> bool:
        """
        Initialize/reset the queue to a clean state.

        Args:
            force: If True, reset even if active tasks exist

        Returns:
            True if queue was reset, False if refused (active tasks without force)
        """
        queue = self._read_queue()

        # Safety check: don't reset if active tasks exist
        if not force and queue.get("active_workflows"):
            return False

        self._write_queue(self._empty_queue())
        log_operation("QUEUE_INIT", "Queue reset to clean state")
        return True

    def show_task_cost(self, task_id: str) -> Optional[float]:
        """
        Get the cost in USD for a specific task.

        Returns the cost as a float, or None if task not found or no cost recorded.
        """
        task = self.get(task_id)
        if not task:
            return None

        return task.get_cost_usd()

    def show_enhancement_cost(self, enhancement_name: str) -> float:
        """
        Calculate total cost for all tasks in an enhancement.

        Returns sum of costs in USD (0.0 if no costs recorded).
        """
        tasks = self.list_by_enhancement(enhancement_name)
        total = 0.0

        for task in tasks:
            cost = task.get_cost_usd()
            if cost:
                total += cost

        return total

    def preview_prompt(self, task_id: str) -> Optional[str]:
        """
        Preview the prompt that would be sent for a task.

        NOTE: Requires TaskService to be injected via set_services().
        Returns the prompt string, or None if task not found or service unavailable.
        """
        task = self.get(task_id)
        if not task:
            return None

        if not self._task_service:
            log_error("Cannot preview prompt: TaskService not configured")
            return None

        # Get agent from agent service if available
        agent_name = task.assigned_agent

        # Build prompt using task service
        return self._task_service.build_prompt(
            agent_name=agent_name,
            task_type=task.task_type,
            task_id=task.id,
            task_description=task.description,
            source_file=task.source_file,
            enhancement_name=task.metadata.enhancement_title or "unknown",
            enhancement_dir=f"enhancements/{task.metadata.enhancement_title or 'unknown'}",
        )

    def set_services(self, task_service=None) -> None:
        """Inject service dependencies."""
        if task_service:
            self._task_service = task_service