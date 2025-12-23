"""Tests for QueueService."""

import pytest

from cmat.services.queue_service import QueueService
from cmat.models.task import TaskStatus


class TestQueueService:
    """Tests for QueueService state management."""

    @pytest.fixture
    def queue_service(self, tmp_path):
        """Create a QueueService with temporary directory."""
        queue_file = tmp_path / "queues" / "task_queue.json"
        return QueueService(queue_file=str(queue_file))

    def test_add_task(self, queue_service):
        """Test adding a task to the queue."""
        task = queue_service.add(
            title="Test Task",
            assigned_agent="architect",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test description",
        )

        assert task.id.startswith("task_")
        assert task.status == TaskStatus.PENDING
        assert task.assigned_agent == "architect"

    def test_get_task_from_pending(self, queue_service):
        """Test getting a task from pending queue."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )

        retrieved = queue_service.get(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id

    def test_get_task_from_active(self, queue_service):
        """Test getting a task from active queue."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        queue_service.start(task.id)

        retrieved = queue_service.get(task.id)
        assert retrieved is not None
        assert retrieved.status == TaskStatus.ACTIVE

    def test_start_moves_to_active(self, queue_service):
        """Test that start() moves task from pending to active_workflows."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )

        started = queue_service.start(task.id)

        assert started is not None
        assert started.status == TaskStatus.ACTIVE
        assert started.started is not None

        # Verify it's in active, not pending
        pending = queue_service.list_pending()
        active = queue_service.list_active()

        assert len(pending) == 0
        assert len(active) == 1
        assert active[0].id == task.id

    def test_complete_moves_from_active(self, queue_service):
        """Test that complete() moves task from active to completed."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        queue_service.start(task.id)

        completed = queue_service.complete(task.id, "READY_FOR_DEVELOPMENT")

        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED
        assert completed.result == "READY_FOR_DEVELOPMENT"

        # Verify it moved
        active = queue_service.list_active()
        completed_list = queue_service.list_completed()

        assert len(active) == 0
        assert len(completed_list) == 1

    def test_complete_from_pending_fails(self, queue_service):
        """Test that complete() fails if task is still pending."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )

        # complete() looks in active_workflows, not pending
        result = queue_service.complete(task.id, "DONE")
        assert result is None

    def test_fail_moves_from_active(self, queue_service):
        """Test that fail() moves task from active to failed."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        queue_service.start(task.id)

        failed = queue_service.fail(task.id, "BLOCKED: missing deps")

        assert failed is not None
        assert failed.status == TaskStatus.FAILED
        assert failed.result == "BLOCKED: missing deps"

        active = queue_service.list_active()
        failed_list = queue_service.list_failed()

        assert len(active) == 0
        assert len(failed_list) == 1

    def test_cancel_pending_task(self, queue_service):
        """Test cancelling a pending task."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )

        cancelled = queue_service.cancel(task.id, "User cancelled")

        assert cancelled is not None
        assert cancelled.status == TaskStatus.CANCELLED

        pending = queue_service.list_pending()
        failed = queue_service.list_failed()

        assert len(pending) == 0
        assert len(failed) == 1

    def test_cancel_active_task(self, queue_service):
        """Test cancelling an active task."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        queue_service.start(task.id)

        cancelled = queue_service.cancel(task.id, "User cancelled")

        assert cancelled is not None
        assert cancelled.status == TaskStatus.CANCELLED

        active = queue_service.list_active()
        failed = queue_service.list_failed()

        assert len(active) == 0
        assert len(failed) == 1

    def test_rerun_completed_task(self, queue_service):
        """Test re-running a completed task."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        queue_service.start(task.id)
        queue_service.complete(task.id, "DONE")

        rerun = queue_service.rerun(task.id)

        assert rerun is not None
        assert rerun.status == TaskStatus.PENDING
        assert rerun.started is None
        assert rerun.completed is None
        assert rerun.result is None

        pending = queue_service.list_pending()
        completed = queue_service.list_completed()

        assert len(pending) == 1
        assert len(completed) == 0

    def test_rerun_failed_task(self, queue_service):
        """Test re-running a failed task."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        queue_service.start(task.id)
        queue_service.fail(task.id, "Error")

        rerun = queue_service.rerun(task.id)

        assert rerun is not None
        assert rerun.status == TaskStatus.PENDING

    def test_cancel_all(self, queue_service):
        """Test cancelling all tasks."""
        # Add multiple tasks
        task1 = queue_service.add(
            title="Test 1", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        task2 = queue_service.add(
            title="Test 2", assigned_agent="implementer",
            priority="normal", task_type="implementation",
            source_file="test.md", description="Test",
        )
        queue_service.start(task2.id)

        count = queue_service.cancel_all("Bulk cancel")

        assert count == 2

        pending = queue_service.list_pending()
        active = queue_service.list_active()
        failed = queue_service.list_failed()

        assert len(pending) == 0
        assert len(active) == 0
        assert len(failed) == 2

    def test_update_single_metadata(self, queue_service):
        """Test updating a single metadata field."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )

        updated = queue_service.update_single_metadata(task.id, "process_pid", "12345")

        assert updated is not None

        # Verify it persisted
        retrieved = queue_service.get(task.id)
        assert retrieved.metadata.process_pid == "12345"

    def test_list_by_agent(self, queue_service):
        """Test listing tasks by agent."""
        queue_service.add(
            title="Arch Task", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )
        queue_service.add(
            title="Impl Task", assigned_agent="implementer",
            priority="normal", task_type="implementation",
            source_file="test.md", description="Test",
        )

        arch_tasks = queue_service.list_by_agent("architect")
        impl_tasks = queue_service.list_by_agent("implementer")

        assert len(arch_tasks) == 1
        assert len(impl_tasks) == 1
        assert arch_tasks[0].title == "Arch Task"

    def test_agent_status_updates(self, queue_service):
        """Test that agent status is updated during task lifecycle."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )

        queue_service.start(task.id)
        status = queue_service.get_agent_status("architect")

        assert status is not None
        assert status["status"] == "active"
        assert status["current_task"] == task.id

        queue_service.complete(task.id, "DONE")
        status = queue_service.get_agent_status("architect")

        assert status["status"] == "idle"
        assert status["current_task"] is None


class TestQueueServiceEdgeCases:
    """Edge case tests for QueueService."""

    @pytest.fixture
    def queue_service(self, tmp_path):
        """Create a QueueService with temporary directory."""
        queue_file = tmp_path / "queues" / "task_queue.json"
        return QueueService(queue_file=str(queue_file))

    def test_get_nonexistent_task(self, queue_service):
        """Test getting a task that doesn't exist."""
        result = queue_service.get("nonexistent_task_id")
        assert result is None

    def test_start_nonexistent_task(self, queue_service):
        """Test starting a task that doesn't exist."""
        result = queue_service.start("nonexistent_task_id")
        assert result is None

    def test_complete_nonexistent_task(self, queue_service):
        """Test completing a task that doesn't exist."""
        result = queue_service.complete("nonexistent_task_id", "DONE")
        assert result is None

    def test_rerun_pending_task_fails(self, queue_service):
        """Test that rerun() doesn't work on pending tasks."""
        task = queue_service.add(
            title="Test", assigned_agent="architect",
            priority="normal", task_type="analysis",
            source_file="test.md", description="Test",
        )

        result = queue_service.rerun(task.id)
        assert result is None  # Can only rerun completed/failed
