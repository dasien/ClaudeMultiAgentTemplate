"""
Task model for CMAT workflow execution.

Tasks represent individual units of work assigned to agents within a workflow.
They track execution state, timing, costs, and integration metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json

from .task_metadata import TaskMetadata
from core.utils import get_datetime_utc


class TaskStatus(Enum):
    """Valid states for a task."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Priority levels for task execution."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """
    Represents a unit of work assigned to an agent.

    Tasks are created by the queue service, executed by agents via workflows,
    and track their full lifecycle including timing and cost information.
    """
    id: str
    title: str
    assigned_agent: str
    priority: TaskPriority
    task_type: str
    description: str
    source_file: str
    created: datetime
    status: TaskStatus = TaskStatus.PENDING
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    result: Optional[str] = None
    auto_complete: bool = False
    auto_chain: bool = False
    metadata: TaskMetadata = field(default_factory=TaskMetadata)

    def start(self) -> None:
        """Mark task as started."""
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {self.status.value} status")
        self.status = TaskStatus.ACTIVE
        self.started = get_datetime_utc()

    def complete(self, result: str) -> None:
        """Mark task as completed with a result."""
        if self.status != TaskStatus.ACTIVE:
            raise ValueError(f"Cannot complete task in {self.status.value} status")
        self.status = TaskStatus.COMPLETED
        self.completed = get_datetime_utc()
        self.result = result

    def fail(self, reason: str) -> None:
        """Mark task as failed with a reason."""
        self.status = TaskStatus.FAILED
        self.completed = get_datetime_utc()
        self.result = reason

    def block(self, reason: str) -> None:
        """Mark task as blocked with a reason."""
        self.status = TaskStatus.BLOCKED
        self.result = reason

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the task."""
        if self.status == TaskStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed task")
        self.status = TaskStatus.CANCELLED
        self.completed = get_datetime_utc()
        self.result = reason

    def get_duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds, if started and completed."""
        if self.started and self.completed:
            return (self.completed - self.started).total_seconds()
        return None

    def get_cost_usd(self) -> Optional[float]:
        """Get cost as float, if available."""
        if self.metadata.cost_usd:
            try:
                return float(self.metadata.cost_usd)
            except ValueError:
                return None
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "assigned_agent": self.assigned_agent,
            "priority": self.priority.value,
            "task_type": self.task_type,
            "description": self.description,
            "source_file": self.source_file,
            "created": self.created.isoformat() + "Z",
            "status": self.status.value,
            "started": self.started.isoformat() + "Z" if self.started else None,
            "completed": self.completed.isoformat() + "Z" if self.completed else None,
            "result": self.result,
            "auto_complete": self.auto_complete,
            "auto_chain": self.auto_chain,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary (e.g., loaded from JSON)."""
        return cls(
            id=data["id"],
            title=data["title"],
            assigned_agent=data["assigned_agent"],
            priority=TaskPriority(data["priority"]),
            task_type=data["task_type"],
            description=data["description"],
            source_file=data["source_file"],
            created=datetime.fromisoformat(data["created"].rstrip("Z")),
            status=TaskStatus(data["status"]),
            started=datetime.fromisoformat(data["started"].rstrip("Z")) if data.get("started") else None,
            completed=datetime.fromisoformat(data["completed"].rstrip("Z")) if data.get("completed") else None,
            result=data.get("result"),
            auto_complete=data.get("auto_complete", False),
            auto_chain=data.get("auto_chain", False),
            metadata=TaskMetadata.from_dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Task":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))