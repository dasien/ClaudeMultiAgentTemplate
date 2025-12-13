"""Tests for Task model."""

import pytest
from datetime import datetime

from cmat.models.task import Task, TaskStatus, TaskPriority
from cmat.models.task_metadata import TaskMetadata


class TestTaskStatus:
    """Tests for TaskStatus enum values."""

    def test_status_values(self):
        """Verify enum values match expected strings."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.ACTIVE.value == "active"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_status_from_string(self):
        """Verify enums can be created from string values."""
        assert TaskStatus("pending") == TaskStatus.PENDING
        assert TaskStatus("active") == TaskStatus.ACTIVE
        assert TaskStatus("completed") == TaskStatus.COMPLETED


class TestTaskPriority:
    """Tests for TaskPriority enum values."""

    def test_priority_values(self):
        """Verify enum values match expected strings."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.NORMAL.value == "normal"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"

    def test_priority_from_string(self):
        """Verify enums can be created from string values."""
        assert TaskPriority("normal") == TaskPriority.NORMAL
        assert TaskPriority("high") == TaskPriority.HIGH


class TestTask:
    """Tests for Task model."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return Task(
            id="task_123",
            title="Test Task",
            assigned_agent="architect",
            priority=TaskPriority.NORMAL,
            task_type="analysis",
            description="A test task",
            source_file="test.md",
            created=datetime(2025, 1, 1, 12, 0, 0),
        )

    def test_task_creation(self, sample_task):
        """Test basic task creation."""
        assert sample_task.id == "task_123"
        assert sample_task.title == "Test Task"
        assert sample_task.assigned_agent == "architect"
        assert sample_task.priority == TaskPriority.NORMAL
        assert sample_task.status == TaskStatus.PENDING
        assert sample_task.started is None
        assert sample_task.completed is None

    def test_task_start(self, sample_task):
        """Test starting a task transitions to ACTIVE."""
        sample_task.start()

        assert sample_task.status == TaskStatus.ACTIVE
        assert sample_task.started is not None

    def test_task_start_only_from_pending(self, sample_task):
        """Test that start() only works from PENDING status."""
        sample_task.start()

        with pytest.raises(ValueError, match="Cannot start task"):
            sample_task.start()

    def test_task_complete(self, sample_task):
        """Test completing a task."""
        sample_task.start()
        sample_task.complete("READY_FOR_DEVELOPMENT")

        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.result == "READY_FOR_DEVELOPMENT"
        assert sample_task.completed is not None

    def test_task_complete_only_from_active(self, sample_task):
        """Test that complete() only works from ACTIVE status."""
        with pytest.raises(ValueError, match="Cannot complete task"):
            sample_task.complete("DONE")

    def test_task_fail(self, sample_task):
        """Test failing a task."""
        sample_task.start()
        sample_task.fail("BLOCKED: missing requirements")

        assert sample_task.status == TaskStatus.FAILED
        assert sample_task.result == "BLOCKED: missing requirements"
        assert sample_task.completed is not None

    def test_task_cancel(self, sample_task):
        """Test cancelling a task."""
        sample_task.cancel("User requested cancellation")

        assert sample_task.status == TaskStatus.CANCELLED
        assert sample_task.result == "User requested cancellation"

    def test_task_cancel_completed_fails(self, sample_task):
        """Test that completed tasks cannot be cancelled."""
        sample_task.start()
        sample_task.complete("DONE")

        with pytest.raises(ValueError, match="Cannot cancel a completed task"):
            sample_task.cancel("Too late")

    def test_task_to_dict(self, sample_task):
        """Test serialization to dict."""
        data = sample_task.to_dict()

        assert data["id"] == "task_123"
        assert data["status"] == "pending"
        assert data["priority"] == "normal"
        assert data["assigned_agent"] == "architect"

    def test_task_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "id": "task_456",
            "title": "From Dict",
            "assigned_agent": "implementer",
            "priority": "high",
            "task_type": "implementation",
            "description": "Test",
            "source_file": "test.md",
            "created": "2025-01-01T12:00:00Z",
            "status": "active",
            "started": "2025-01-01T12:05:00Z",
            "completed": None,
            "result": None,
            "auto_complete": True,
            "auto_chain": True,
            "metadata": {},
        }

        task = Task.from_dict(data)

        assert task.id == "task_456"
        assert task.status == TaskStatus.ACTIVE
        assert task.priority == TaskPriority.HIGH
        assert task.auto_complete is True
        assert task.auto_chain is True

    def test_task_roundtrip(self, sample_task):
        """Test that to_dict/from_dict preserves data."""
        sample_task.start()
        sample_task.complete("DONE")

        data = sample_task.to_dict()
        restored = Task.from_dict(data)

        assert restored.id == sample_task.id
        assert restored.status == sample_task.status
        assert restored.result == sample_task.result

    def test_get_duration_seconds(self, sample_task):
        """Test duration calculation."""
        # No duration when not started
        assert sample_task.get_duration_seconds() is None

        sample_task.start()
        # No duration when not completed
        assert sample_task.get_duration_seconds() is None

        sample_task.complete("DONE")
        # Has duration when completed
        duration = sample_task.get_duration_seconds()
        assert duration is not None
        assert duration >= 0
