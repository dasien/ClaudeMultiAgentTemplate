"""
Unit tests for CMAT services.

These tests don't require Claude CLI - they test service logic in isolation.
"""

import json
import pytest
from pathlib import Path

from cmat.models import Task, TaskStatus, TaskPriority, Agent, Learning, ClaudeModel, ModelPricing
from cmat.services import (
    QueueService,
    AgentService,
    SkillsService,
    LearningsService,
    RetrievalContext,
    ModelService,
    ToolsService,
)
from cmat.models import Tool


class TestQueueService:
    """Tests for QueueService."""

    def test_init_creates_queue_file(self, cmat_test_env):
        """Test that init creates queue file if missing."""
        queue_file = cmat_test_env / ".claude/data/task_queue.json"
        queue_file.unlink()  # Remove existing file

        service = QueueService(str(queue_file))
        assert queue_file.exists()

    def test_add_task(self, cmat_test_env):
        """Test adding a task to the queue."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test Task",
            assigned_agent="test-agent",
            priority="high",
            task_type="analysis",
            source_file="test.md",
            description="A test task",
        )

        assert task.id.startswith("task_")
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING

    def test_add_task_with_model(self, cmat_test_env):
        """Test adding a task with model parameter."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test Task with Model",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="A test task",
            model="claude-sonnet-4-20250514",
        )

        assert task.id.startswith("task_")
        assert task.metadata.requested_model == "claude-sonnet-4-20250514"

        # Test that metadata dict takes precedence
        task2 = service.add(
            title="Test Task with Both",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="A test task",
            metadata={"requested_model": "claude-opus-4-20250514"},
            model="claude-sonnet-4-20250514",  # Should be ignored
        )
        assert task2.metadata.requested_model == "claude-opus-4-20250514"

    def test_get_task(self, cmat_test_env):
        """Test retrieving a task by ID."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test Task",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test",
        )

        retrieved = service.get(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id
        assert retrieved.title == "Test Task"

    def test_get_nonexistent_task(self, cmat_test_env):
        """Test getting a task that doesn't exist."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        assert service.get("nonexistent_id") is None

    def test_start_task(self, cmat_test_env):
        """Test starting a task moves it to active."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test",
        )

        started = service.start(task.id)
        assert started is not None
        assert started.status == TaskStatus.ACTIVE

        # Verify it's in active list
        active = service.list_active()
        assert any(t.id == task.id for t in active)

        # Verify it's not in pending
        pending = service.list_pending()
        assert not any(t.id == task.id for t in pending)

    def test_complete_task(self, cmat_test_env):
        """Test completing a task."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test",
        )

        service.start(task.id)
        completed = service.complete(task.id, "READY_FOR_IMPLEMENTATION")

        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED
        assert completed.result == "READY_FOR_IMPLEMENTATION"

        # Verify it's in completed list
        completed_list = service.list_completed()
        assert any(t.id == task.id for t in completed_list)

    def test_fail_task(self, cmat_test_env):
        """Test failing a task."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test",
        )

        service.start(task.id)
        failed = service.fail(task.id, "Something went wrong")

        assert failed is not None
        assert failed.status == TaskStatus.FAILED
        assert failed.result == "Something went wrong"  # fail() stores in result

    def test_cancel_pending_task(self, cmat_test_env):
        """Test cancelling a pending task."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test",
        )

        result = service.cancel(task.id, "No longer needed")
        assert result is not None  # cancel() returns the task
        assert result.status == TaskStatus.CANCELLED

    def test_rerun_task(self, cmat_test_env):
        """Test rerunning a completed task."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        task = service.add(
            title="Test",
            assigned_agent="test-agent",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test",
        )

        service.start(task.id)
        service.complete(task.id, "DONE")

        # Rerun the task
        rerun = service.rerun(task.id)
        assert rerun is not None
        assert rerun.status == TaskStatus.PENDING
        assert rerun.result is None  # Reset

    def test_status(self, cmat_test_env):
        """Test queue status summary."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        # Add some tasks
        t1 = service.add("Task 1", "agent", "normal", "analysis", "t.md", "Test")
        t2 = service.add("Task 2", "agent", "normal", "analysis", "t.md", "Test")
        t3 = service.add("Task 3", "agent", "normal", "analysis", "t.md", "Test")

        service.start(t2.id)
        service.start(t3.id)
        service.complete(t3.id, "DONE")

        status = service.status()
        assert status["pending"] == 1
        assert status["active"] == 1
        assert status["completed"] == 1
        assert status["failed"] == 0
        assert status["total"] == 3

    def test_init_queue(self, cmat_test_env):
        """Test resetting queue to clean state."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))

        service.add("Task 1", "agent", "normal", "analysis", "t.md", "Test")
        service.add("Task 2", "agent", "normal", "analysis", "t.md", "Test")

        # Reset queue
        result = service.init(force=True)
        assert result is True

        status = service.status()
        assert status["total"] == 0

    def test_start_nonexistent_task(self, cmat_test_env):
        """Test starting a task that doesn't exist."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        result = service.start("nonexistent_task_id")
        assert result is None

    def test_complete_nonexistent_task(self, cmat_test_env):
        """Test completing a task that doesn't exist."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        result = service.complete("nonexistent_task_id", "DONE")
        assert result is None

    def test_rerun_pending_task_fails(self, cmat_test_env):
        """Test that rerun() doesn't work on pending tasks."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task = service.add("Test", "architect", "normal", "analysis", "t.md", "Test")
        result = service.rerun(task.id)
        assert result is None  # Can only rerun completed/failed

    def test_clear_tasks_single(self, cmat_test_env):
        """Test clearing a single task by ID."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task1 = service.add("Test 1", "architect", "normal", "analysis", "t.md", "Test")
        task2 = service.add("Test 2", "architect", "normal", "analysis", "t.md", "Test")

        count = service.clear_tasks([task1.id])

        assert count == 1
        assert service.get(task1.id) is None
        assert service.get(task2.id) is not None

    def test_clear_tasks_multiple(self, cmat_test_env):
        """Test clearing multiple tasks by ID."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task1 = service.add("Test 1", "architect", "normal", "analysis", "t.md", "Test")
        task2 = service.add("Test 2", "architect", "normal", "analysis", "t.md", "Test")
        task3 = service.add("Test 3", "architect", "normal", "analysis", "t.md", "Test")

        count = service.clear_tasks([task1.id, task3.id])

        assert count == 2
        assert service.get(task1.id) is None
        assert service.get(task2.id) is not None
        assert service.get(task3.id) is None

    def test_clear_tasks_empty_list(self, cmat_test_env):
        """Test clearing with empty list does nothing."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task = service.add("Test", "architect", "normal", "analysis", "t.md", "Test")

        count = service.clear_tasks([])

        assert count == 0
        assert service.get(task.id) is not None

    def test_clear_tasks_nonexistent(self, cmat_test_env):
        """Test clearing nonexistent task IDs."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task = service.add("Test", "architect", "normal", "analysis", "t.md", "Test")

        count = service.clear_tasks(["nonexistent_id"])

        assert count == 0
        assert service.get(task.id) is not None

    def test_list_by_agent(self, cmat_test_env):
        """Test listing tasks by agent."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        service.add("Arch Task", "architect", "normal", "analysis", "t.md", "Test")
        service.add("Impl Task", "implementer", "normal", "implementation", "t.md", "Test")

        arch_tasks = service.list_by_agent("architect")
        impl_tasks = service.list_by_agent("implementer")

        assert len(arch_tasks) == 1
        assert len(impl_tasks) == 1
        assert arch_tasks[0].title == "Arch Task"

    def test_agent_status_updates(self, cmat_test_env):
        """Test that agent status is updated during task lifecycle."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task = service.add("Test", "architect", "normal", "analysis", "t.md", "Test")

        service.start(task.id)
        status = service.get_agent_status("architect")

        assert status is not None
        assert status["status"] == "active"
        assert status["current_task"] == task.id

        service.complete(task.id, "DONE")
        status = service.get_agent_status("architect")

        assert status["status"] == "idle"
        assert status["current_task"] is None

    def test_update_single_metadata(self, cmat_test_env):
        """Test updating a single metadata field."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task = service.add("Test", "architect", "normal", "analysis", "t.md", "Test")

        updated = service.update_single_metadata(task.id, "process_pid", "12345")

        assert updated is not None
        retrieved = service.get(task.id)
        assert retrieved.metadata.process_pid == "12345"

    def test_cancel_all(self, cmat_test_env):
        """Test cancelling all tasks."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task1 = service.add("Test 1", "architect", "normal", "analysis", "t.md", "Test")
        task2 = service.add("Test 2", "implementer", "normal", "implementation", "t.md", "Test")
        service.start(task2.id)

        count = service.cancel_all("Bulk cancel")

        assert count == 2
        assert len(service.list_pending()) == 0
        assert len(service.list_active()) == 0
        assert len(service.list_cancelled()) == 2

    def test_cancel_active_task(self, cmat_test_env):
        """Test cancelling an active task."""
        service = QueueService(str(cmat_test_env / ".claude/data/task_queue.json"))
        task = service.add("Test", "architect", "normal", "analysis", "t.md", "Test")
        service.start(task.id)

        cancelled = service.cancel(task.id, "User cancelled")

        assert cancelled is not None
        assert cancelled.status == TaskStatus.CANCELLED
        assert len(service.list_active()) == 0
        assert len(service.list_cancelled()) == 1


class TestAgentService:
    """Tests for AgentService."""

    def test_list_empty(self, cmat_test_env):
        """Test listing agents when none exist."""
        service = AgentService(str(cmat_test_env / ".claude/agents"))
        agents = service.list_all()
        assert agents == []

    def test_add_and_get_agent(self, cmat_test_env):
        """Test adding and retrieving an agent."""
        service = AgentService(str(cmat_test_env / ".claude/agents"))

        agent = Agent(
            name="Test Agent",
            agent_file="test-agent",
            role="testing",
            description="A test agent",
            tools=["Read", "Write"],
            skills=["testing"],
        )

        service.add(agent)
        retrieved = service.get("test-agent")

        assert retrieved is not None
        assert retrieved.name == "Test Agent"
        assert retrieved.role == "testing"

    def test_get_by_name(self, cmat_test_env):
        """Test getting agent by display name."""
        service = AgentService(str(cmat_test_env / ".claude/agents"))

        agent = Agent(
            name="My Agent",
            agent_file="my-agent",
            role="testing",
            description="Test",
        )
        service.add(agent)

        found = service.get_by_name("My Agent")
        assert found is not None
        assert found.agent_file == "my-agent"

    def test_get_by_role(self, cmat_test_env):
        """Test getting agents by role."""
        service = AgentService(str(cmat_test_env / ".claude/agents"))

        service.add(Agent(name="A1", agent_file="a1", role="testing", description="Test"))
        service.add(Agent(name="A2", agent_file="a2", role="testing", description="Test"))
        service.add(Agent(name="A3", agent_file="a3", role="design", description="Test"))

        testing_agents = service.get_by_role("testing")
        assert len(testing_agents) == 2

    def test_generate_agents_json(self, cmat_test_env, sample_agent_md):
        """Test generating agents.json from markdown files."""
        service = AgentService(str(cmat_test_env / ".claude/agents"))

        result = service.generate_agents_json()

        assert result["generated"] == 1
        assert result["errors"] == []

        # Verify agent was loaded
        agent = service.get("test-agent")
        assert agent is not None
        assert agent.name == "Test Agent"
        assert agent.role == "testing"
        assert "Read" in agent.tools

    def test_generate_skips_templates(self, cmat_test_env):
        """Test that generate_agents_json skips template files."""
        service = AgentService(str(cmat_test_env / ".claude/agents"))

        # Create a template file
        template = cmat_test_env / ".claude/agents/AGENT_TEMPLATE.md"
        template.write_text("""---
name: "Template"
role: "template"
description: "A template"
---
Template content
""")

        result = service.generate_agents_json(skip_templates=True)
        assert result["generated"] == 0


class TestSkillsService:
    """Tests for SkillsService."""

    def test_list_empty(self, cmat_test_env):
        """Test listing skills when none exist."""
        service = SkillsService(str(cmat_test_env / ".claude/skills"))
        skills = service.list_all()
        assert skills == []

    def test_build_skills_prompt_empty(self, cmat_test_env):
        """Test building prompt with no skills."""
        service = SkillsService(str(cmat_test_env / ".claude/skills"))
        prompt = service.build_skills_prompt([])
        assert prompt == ""

    def test_build_skills_prompt(self, cmat_test_env):
        """Test building skills prompt with on-demand skill invocation."""
        service = SkillsService(str(cmat_test_env / ".claude/skills"))

        # Create skill directory with SKILL.md (expected structure)
        skill_dir = cmat_test_env / ".claude/skills/test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n\nThis is a test skill.")

        # Create skills.json with correct key names
        skills_data = {
            "skills": [{
                "name": "test-skill",
                "description": "A test skill",
                "skill-directory": "test-skill",
                "category": "testing",
            }]
        }
        with open(cmat_test_env / ".claude/skills/skills.json", "w") as f:
            json.dump(skills_data, f)

        prompt = service.build_skills_prompt(["test-skill"])

        # Check for header and skill reference (not full content - uses Skill tool)
        assert "SPECIALIZED SKILLS" in prompt
        assert "test-skill" in prompt
        assert "A test skill" in prompt  # Description is included
        assert "Skill tool" in prompt  # Instructions for on-demand invocation
        # Full skill content should NOT be in prompt (loaded on-demand via Skill tool)
        assert "This is a test skill" not in prompt


class TestLearningsService:
    """Tests for LearningsService (without Claude calls)."""

    def test_init_creates_directory(self, cmat_test_env):
        """Test that init creates data directory and learnings.json file."""
        import shutil
        data_path = cmat_test_env / ".claude/data"
        shutil.rmtree(data_path)  # Remove existing

        service = LearningsService(str(data_path))
        assert data_path.exists()
        assert (data_path / "learnings.json").exists()

    def test_store_and_get(self, cmat_test_env):
        """Test storing and retrieving a learning."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))

        learning = Learning.from_user_input(
            "Always use pytest fixtures",
            tags=["testing"],
        )

        learning_id = service.store(learning)
        assert learning_id == learning.id

        retrieved = service.get(learning.id)
        assert retrieved is not None
        assert retrieved.summary == learning.summary

    def test_delete(self, cmat_test_env):
        """Test deleting a learning."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))

        learning = Learning.from_user_input("Test learning")
        service.store(learning)

        result = service.delete(learning.id)
        assert result is True

        assert service.get(learning.id) is None

    def test_delete_nonexistent(self, cmat_test_env):
        """Test deleting non-existent learning."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))
        result = service.delete("nonexistent_id")
        assert result is False

    def test_list_all(self, cmat_test_env):
        """Test listing all learnings."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))

        l1 = Learning.from_user_input("Learning 1", tags=["python"])
        l2 = Learning.from_user_input("Learning 2", tags=["testing"])

        service.store(l1)
        service.store(l2)

        learnings = service.list_all()
        assert len(learnings) == 2

    def test_list_by_tags(self, cmat_test_env):
        """Test filtering learnings by tags."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))

        l1 = Learning.from_user_input("Python tip", tags=["python"])
        l2 = Learning.from_user_input("Testing tip", tags=["testing"])
        l3 = Learning.from_user_input("Python testing", tags=["python", "testing"])

        service.store(l1)
        service.store(l2)
        service.store(l3)

        python_learnings = service.list_by_tags(["python"])
        assert len(python_learnings) == 2  # l1 and l3

        testing_learnings = service.list_by_tags(["testing"])
        assert len(testing_learnings) == 2  # l2 and l3

    def test_count(self, cmat_test_env):
        """Test counting learnings."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))

        assert service.count() == 0

        service.store(Learning.from_user_input("Test 1"))
        service.store(Learning.from_user_input("Test 2"))

        assert service.count() == 2

    def test_build_learnings_prompt_empty(self, cmat_test_env):
        """Test building prompt with no learnings."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))
        prompt = service.build_learnings_prompt([])
        assert prompt == ""

    def test_build_learnings_prompt(self, cmat_test_env):
        """Test building learnings prompt."""
        service = LearningsService(str(cmat_test_env / ".claude/data"))

        learnings = [
            Learning(
                id="test1",
                summary="Use dataclasses",
                content="Prefer dataclasses for DTOs",
                tags=["python"],
                confidence=0.8,
            ),
            Learning(
                id="test2",
                summary="Write tests first",
                content="TDD approach",
                tags=["testing"],
                confidence=0.9,
            ),
        ]

        prompt = service.build_learnings_prompt(learnings)

        assert "RELEVANT LEARNINGS" in prompt
        assert "Use dataclasses" in prompt
        assert "Write tests first" in prompt
        assert "80%" in prompt
        assert "90%" in prompt

class TestModelService:
    """Tests for ModelService."""

    def test_init_creates_models_file(self, cmat_test_env):
        """Test that init creates models.json if missing."""
        data_dir = cmat_test_env / ".claude/data"
        models_file = data_dir / "models.json"
        if models_file.exists():
            models_file.unlink()

        service = ModelService(str(data_dir))
        # Trigger file creation by loading
        service.list_all()
        assert models_file.exists()

    def test_list_all(self, cmat_test_env):
        """Test listing all models."""
        service = ModelService(str(cmat_test_env / ".claude/data"))
        models = service.list_all()

        # Should have default models from the fixture
        assert len(models) >= 1
        assert all(isinstance(m, ClaudeModel) for m in models)

    def test_get_model(self, cmat_test_env):
        """Test getting a model by ID."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        # Get existing model
        model = service.get("claude-sonnet-4.5")
        assert model is not None
        assert model.name == "Claude Sonnet 4.5"

    def test_get_nonexistent_model(self, cmat_test_env):
        """Test getting a model that doesn't exist."""
        service = ModelService(str(cmat_test_env / ".claude/data"))
        assert service.get("nonexistent-model") is None

    def test_get_by_pattern(self, cmat_test_env):
        """Test finding model by pattern matching."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        # Should match claude-sonnet-4.5 pattern
        model = service.get_by_pattern("claude-sonnet-4-5-20250929")
        assert model is not None
        assert "sonnet" in model.id.lower()

    def test_get_default(self, cmat_test_env):
        """Test getting default model."""
        service = ModelService(str(cmat_test_env / ".claude/data"))
        default = service.get_default()

        assert default is not None
        assert isinstance(default, ClaudeModel)

    def test_add_model(self, cmat_test_env):
        """Test adding a new model."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        new_model = ClaudeModel(
            id="test-model",
            name="Test Model",
            description="A test model",
            pattern="*test-model*",
            max_tokens=100000,
            pricing=ModelPricing(
                input=1.0,
                output=2.0,
                cache_write=1.5,
                cache_read=0.1,
            ),
        )

        model_id = service.add(new_model)
        assert model_id == "test-model"

        # Verify it was added
        retrieved = service.get("test-model")
        assert retrieved is not None
        assert retrieved.name == "Test Model"

    def test_add_duplicate_model(self, cmat_test_env):
        """Test that adding duplicate model raises error."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        # Try to add model with existing ID
        duplicate = ClaudeModel(
            id="claude-sonnet-4.5",
            name="Duplicate",
            description="Duplicate model",
            pattern="*",
            max_tokens=100000,
            pricing=ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.1),
        )

        with pytest.raises(ValueError, match="already exists"):
            service.add(duplicate)

    def test_update_model(self, cmat_test_env):
        """Test updating an existing model."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        # Get existing model
        model = service.get("claude-sonnet-4.5")
        assert model is not None

        # Modify and update
        model.description = "Updated description"
        result = service.update(model)
        assert result is True

        # Verify update
        updated = service.get("claude-sonnet-4.5")
        assert updated.description == "Updated description"

    def test_update_nonexistent_model(self, cmat_test_env):
        """Test updating a model that doesn't exist."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        fake_model = ClaudeModel(
            id="nonexistent",
            name="Fake",
            description="Fake model",
            pattern="*",
            max_tokens=100000,
            pricing=ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.1),
        )

        result = service.update(fake_model)
        assert result is False

    def test_delete_model(self, cmat_test_env):
        """Test deleting a model."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        # Add a model to delete
        new_model = ClaudeModel(
            id="to-delete",
            name="To Delete",
            description="Will be deleted",
            pattern="*delete*",
            max_tokens=100000,
            pricing=ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.1),
        )
        service.add(new_model)

        # Delete it
        result = service.delete("to-delete")
        assert result is True

        # Verify deletion
        assert service.get("to-delete") is None

    def test_delete_nonexistent_model(self, cmat_test_env):
        """Test deleting a model that doesn't exist."""
        service = ModelService(str(cmat_test_env / ".claude/data"))
        result = service.delete("nonexistent")
        assert result is False

    def test_set_default(self, cmat_test_env):
        """Test setting default model."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        # Add a new model
        new_model = ClaudeModel(
            id="new-default",
            name="New Default",
            description="New default model",
            pattern="*new*",
            max_tokens=100000,
            pricing=ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.1),
        )
        service.add(new_model)

        # Set as default
        result = service.set_default("new-default")
        assert result is True

        # Verify
        default = service.get_default()
        assert default.id == "new-default"

    def test_set_default_nonexistent(self, cmat_test_env):
        """Test setting nonexistent model as default."""
        service = ModelService(str(cmat_test_env / ".claude/data"))
        result = service.set_default("nonexistent")
        assert result is False

    def test_extract_from_transcript(self, cmat_test_env, tmp_path):
        """Test extracting usage from transcript JSONL."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        # Create a mock transcript file
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(
            '{"type":"assistant","message":{"usage":{"input_tokens":100,"output_tokens":50,"cache_creation_input_tokens":10,"cache_read_input_tokens":5},"model":"claude-sonnet-4-5-20250929"}}\n'
            '{"type":"assistant","message":{"usage":{"input_tokens":200,"output_tokens":100,"cache_creation_input_tokens":20,"cache_read_input_tokens":10}}}\n'
            '{"type":"user","message":{"content":"test"}}\n'
        )

        usage = service.extract_from_transcript(str(transcript))

        assert usage["input_tokens"] == 300
        assert usage["output_tokens"] == 150
        assert usage["cache_creation_tokens"] == 30
        assert usage["cache_read_tokens"] == 15
        assert usage["model"] == "claude-sonnet-4-5-20250929"

    def test_extract_from_nonexistent_transcript(self, cmat_test_env):
        """Test extracting from nonexistent transcript."""
        service = ModelService(str(cmat_test_env / ".claude/data"))
        usage = service.extract_from_transcript("/nonexistent/path.jsonl")

        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0
        assert usage["model"] is None

    def test_calculate_cost(self, cmat_test_env):
        """Test cost calculation."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        usage = {
            "input_tokens": 1000000,  # 1M tokens
            "output_tokens": 500000,  # 500K tokens
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "model": "claude-sonnet-4-5-20250929",
        }

        cost = service.calculate_cost(usage)

        # Sonnet 4.5 pricing: $3/M input, $15/M output
        # Expected: 1M * $3 + 0.5M * $15 = $3 + $7.5 = $10.5
        assert cost == pytest.approx(10.5, rel=0.01)

    def test_calculate_cost_with_cache(self, cmat_test_env):
        """Test cost calculation including cache tokens."""
        service = ModelService(str(cmat_test_env / ".claude/data"))

        usage = {
            "input_tokens": 100000,
            "output_tokens": 50000,
            "cache_creation_tokens": 200000,
            "cache_read_tokens": 300000,
            "model": "claude-sonnet-4-5-20250929",
        }

        cost = service.calculate_cost(usage)

        # Sonnet 4.5 pricing per million:
        # Input: $3.00, Output: $15.00, Cache Write: $3.75, Cache Read: $0.30
        # Expected:
        #   100K input * $3.00/M = $0.30
        #   50K output * $15.00/M = $0.75
        #   200K cache_write * $3.75/M = $0.75
        #   300K cache_read * $0.30/M = $0.09
        #   Total = $1.89
        assert cost == pytest.approx(1.89, rel=0.01)


class TestToolsService:
    """Tests for ToolsService."""

    def test_init_creates_tools_file(self, cmat_test_env):
        """Test that init creates tools.json if missing."""
        data_dir = cmat_test_env / ".claude/data"
        tools_file = data_dir / "tools.json"
        if tools_file.exists():
            tools_file.unlink()

        service = ToolsService(str(data_dir))
        # Trigger file creation by loading
        service.list_all()
        assert tools_file.exists()

    def test_list_all(self, cmat_test_env):
        """Test listing all tools."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))
        tools = service.list_all()

        # Should have default tools from the fixture (Read, Write, Bash)
        assert len(tools) == 3
        assert all(isinstance(t, Tool) for t in tools)
        tool_names = [t.name for t in tools]
        assert "Read" in tool_names
        assert "Write" in tool_names
        assert "Bash" in tool_names

    def test_get_tool(self, cmat_test_env):
        """Test getting a tool by name."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        tool = service.get("Read")
        assert tool is not None
        assert tool.name == "Read"
        assert tool.display_name == "Read Files"

    def test_get_nonexistent_tool(self, cmat_test_env):
        """Test getting a tool that doesn't exist."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))
        assert service.get("NonExistentTool") is None

    def test_add_tool(self, cmat_test_env):
        """Test adding a new tool."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        new_tool = Tool(
            name="Edit",
            display_name="Edit Files",
            description="Make targeted edits to existing files",
        )

        tool_name = service.add(new_tool)
        assert tool_name == "Edit"

        # Verify it was added
        retrieved = service.get("Edit")
        assert retrieved is not None
        assert retrieved.display_name == "Edit Files"

    def test_add_duplicate_tool(self, cmat_test_env):
        """Test that adding duplicate tool raises error."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        # Try to add tool with existing name
        duplicate = Tool(
            name="Read",
            display_name="Duplicate Read",
            description="Duplicate tool",
        )

        with pytest.raises(ValueError, match="already exists"):
            service.add(duplicate)

    def test_update_tool(self, cmat_test_env):
        """Test updating an existing tool."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        # Get existing tool
        tool = service.get("Read")
        assert tool is not None

        # Modify and update
        tool.description = "Updated description"
        result = service.update(tool)
        assert result is True

        # Verify update
        updated = service.get("Read")
        assert updated.description == "Updated description"

    def test_update_nonexistent_tool(self, cmat_test_env):
        """Test updating a tool that doesn't exist."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        fake_tool = Tool(
            name="FakeTool",
            display_name="Fake Tool",
            description="Doesn't exist",
        )

        result = service.update(fake_tool)
        assert result is False

    def test_delete_tool(self, cmat_test_env):
        """Test deleting a tool."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        # Add a tool to delete
        new_tool = Tool(
            name="ToDelete",
            display_name="To Delete",
            description="Will be deleted",
        )
        service.add(new_tool)

        # Delete it
        result = service.delete("ToDelete")
        assert result is True

        # Verify deletion
        assert service.get("ToDelete") is None

    def test_delete_nonexistent_tool(self, cmat_test_env):
        """Test deleting a tool that doesn't exist."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))
        result = service.delete("NonExistent")
        assert result is False

    def test_get_tools_for_agent(self, cmat_test_env):
        """Test getting tools assigned to an agent."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        # Get tools by names (like an agent's tools list)
        tools = service.get_tools_for_agent(["Read", "Write"])
        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "Read" in tool_names
        assert "Write" in tool_names

    def test_get_tools_for_agent_with_invalid(self, cmat_test_env):
        """Test getting tools with some invalid names."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        # Include one invalid tool name
        tools = service.get_tools_for_agent(["Read", "InvalidTool", "Write"])
        assert len(tools) == 2  # Only valid tools returned

    def test_get_all_tool_names(self, cmat_test_env):
        """Test getting all tool names."""
        service = ToolsService(str(cmat_test_env / ".claude/data"))

        names = service.get_all_tool_names()
        assert len(names) == 3
        assert "Read" in names
        assert "Write" in names
        assert "Bash" in names


class TestTaskServiceTemplates:
    """Tests for TaskService template loading and prompt building."""

    @pytest.fixture
    def task_service(self, tmp_path):
        """Create TaskService with test templates."""
        templates_file = tmp_path / "templates.md"
        templates_file.write_text("""# Task Prompt Defaults

# ANALYSIS_TEMPLATE

You are the **${agent}** agent.

## Task: ${task_description}

Enhancement: ${enhancement_name}

${input_instruction}

Output to: ${enhancement_dir}/${agent}/required_output/${required_output_filename}

Task ID: ${task_id}

Expected statuses: ${expected_statuses}

===END_TEMPLATE===

# IMPLEMENTATION_TEMPLATE

You are ${agent} implementing: ${task_description}

===END_TEMPLATE===
""")
        from cmat.services.task_service import TaskService
        return TaskService(
            templates_file=str(templates_file),
            agents_dir=str(tmp_path / "agents"),
            logs_dir=str(tmp_path / "logs"),
        )

    def test_load_templates(self, task_service):
        """Test that templates are loaded correctly."""
        templates = task_service._load_templates()
        assert "analysis" in templates
        assert "implementation" in templates
        assert "${agent}" in templates["analysis"]

    def test_get_template(self, task_service):
        """Test getting a specific template."""
        template = task_service.get_template("analysis")
        assert template is not None
        assert "${agent}" in template

    def test_get_nonexistent_template(self, task_service):
        """Test getting a template that doesn't exist."""
        template = task_service.get_template("nonexistent")
        assert template is None

    def test_build_prompt_substitutions(self, task_service):
        """Test that all variables are substituted in prompt."""
        prompt = task_service.build_prompt(
            agent_name="architect",
            task_type="analysis",
            task_id="task_123",
            task_description="Analyze the feature",
            source_file="requirements.md",
            enhancement_name="new-feature",
            enhancement_dir="enhancements/new-feature",
            required_output_filename="analysis.md",
            expected_statuses="- READY_FOR_DEVELOPMENT",
        )
        assert prompt is not None
        assert "architect" in prompt
        assert "Analyze the feature" in prompt
        assert "new-feature" in prompt
        assert "task_123" in prompt
        assert "READY_FOR_DEVELOPMENT" in prompt
        # Verify no unsubstituted variables remain
        assert "${" not in prompt

    def test_build_prompt_invalid_type(self, task_service):
        """Test building prompt with invalid task type."""
        prompt = task_service.build_prompt(
            agent_name="architect",
            task_type="invalid_type",
            task_id="task_123",
            task_description="Test",
        )
        assert prompt is None


class TestTaskServiceInputInstruction:
    """Tests for TaskService input instruction building."""

    @pytest.fixture
    def task_service(self, tmp_path):
        """Create TaskService."""
        templates_file = tmp_path / "templates.md"
        templates_file.write_text("""# ANALYSIS_TEMPLATE
${input_instruction}
===END_TEMPLATE===
""")
        from cmat.services.task_service import TaskService
        return TaskService(templates_file=str(templates_file))

    def test_input_instruction_no_file(self, task_service):
        """Test input instruction when no source file."""
        instruction = task_service._build_input_instruction(None)
        assert "task description" in instruction.lower()

    def test_input_instruction_null_string(self, task_service):
        """Test input instruction with 'null' string."""
        instruction = task_service._build_input_instruction("null")
        assert "task description" in instruction.lower()

    def test_input_instruction_file(self, task_service, tmp_path):
        """Test input instruction for a file."""
        test_file = tmp_path / "input.md"
        test_file.write_text("test content")
        instruction = task_service._build_input_instruction(str(test_file))
        assert "Read and process this file" in instruction

    def test_input_instruction_directory(self, task_service, tmp_path):
        """Test input instruction for a directory."""
        test_dir = tmp_path / "inputs"
        test_dir.mkdir()
        instruction = task_service._build_input_instruction(str(test_dir))
        assert "directory" in instruction.lower()


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_creation(self):
        """Test creating an ExecutionResult."""
        from cmat.services.task_service import ExecutionResult
        result = ExecutionResult(
            success=True,
            status="READY_FOR_TESTING",
            exit_code=0,
            output_dir="/path/to/output",
            log_file="/path/to/log",
            duration_seconds=120,
            pid=12345,
        )
        assert result.success is True
        assert result.status == "READY_FOR_TESTING"
        assert result.exit_code == 0
        assert result.pid == 12345

    def test_execution_result_default_pid(self):
        """Test ExecutionResult with default pid."""
        from cmat.services.task_service import ExecutionResult
        result = ExecutionResult(
            success=False,
            status=None,
            exit_code=1,
            output_dir="/path",
            log_file="/log",
            duration_seconds=0,
        )
        assert result.pid is None


class TestTaskServiceStatusExtraction:
    """Tests for TaskService.extract_status() method."""

    def test_extract_yaml_completion_block(self):
        """Test extracting status from YAML completion block."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        output = """
Some agent output here...

Done with implementation.

---
agent: implementer
task_id: task_1234567890_12345
status: READY_FOR_TESTING
---
"""
        status = service.extract_status(output)
        assert status == "READY_FOR_TESTING"

    def test_extract_yaml_completion_block_with_halt_status(self):
        """Test extracting halt status from YAML completion block."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        output = """
I encountered an issue...

---
agent: implementer
task_id: task_1234567890_12345
status: BLOCKED: Missing database schema
---
"""
        status = service.extract_status(output)
        assert status == "BLOCKED: Missing database schema"

    def test_extract_multiple_completion_blocks_returns_last(self):
        """Test that the last completion block is returned."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        output = """
First attempt...

---
agent: implementer
task_id: task_123
status: BLOCKED: Initial issue
---

After fixing the issue...

---
agent: implementer
task_id: task_123
status: READY_FOR_TESTING
---
"""
        status = service.extract_status(output)
        assert status == "READY_FOR_TESTING"

    def test_legacy_fallback_ready_for_pattern(self):
        """Test fallback to legacy READY_FOR_* pattern."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        # Old format without YAML block
        output = """
Implementation complete.

**Status: READY_FOR_TESTING**
"""
        status = service.extract_status(output)
        assert status == "READY_FOR_TESTING"

    def test_legacy_fallback_complete_pattern(self):
        """Test fallback to legacy *_COMPLETE pattern."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        output = """
Documentation finished.

DOCUMENTATION_COMPLETE
"""
        status = service.extract_status(output)
        assert status == "DOCUMENTATION_COMPLETE"

    def test_legacy_fallback_blocked_pattern(self):
        """Test fallback to legacy BLOCKED: pattern."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        output = """
Cannot proceed.

BLOCKED: Missing API credentials
"""
        status = service.extract_status(output)
        assert status == "BLOCKED: Missing API credentials"

    def test_no_status_returns_none(self):
        """Test that no status returns None."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        output = """
Some output without any status indicator.
Just regular text here.
"""
        status = service.extract_status(output)
        assert status is None

    def test_empty_output_returns_none(self):
        """Test that empty output returns None."""
        from cmat.services.task_service import TaskService

        service = TaskService()
        assert service.extract_status("") is None
        assert service.extract_status(None) is None

    def test_yaml_block_takes_priority_over_legacy(self):
        """Test that YAML block is preferred over legacy patterns."""
        from cmat.services.task_service import TaskService

        service = TaskService()

        # Output has both YAML block and legacy pattern
        output = """
Implementation done.

READY_FOR_INTEGRATION

---
agent: implementer
task_id: task_123
status: READY_FOR_TESTING
---
"""
        status = service.extract_status(output)
        # Should return from YAML block, not legacy pattern
        assert status == "READY_FOR_TESTING"