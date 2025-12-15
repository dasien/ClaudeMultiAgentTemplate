"""
Unit tests for CMAT services.

These tests don't require Claude CLI - they test service logic in isolation.
"""

import json
import pytest
from pathlib import Path

from cmat.models import Task, TaskStatus, TaskPriority, Agent, Learning
from cmat.services import (
    QueueService,
    AgentService,
    SkillsService,
    LearningsService,
    RetrievalContext,
)


class TestQueueService:
    """Tests for QueueService."""

    def test_init_creates_queue_file(self, cmat_test_env):
        """Test that init creates queue file if missing."""
        queue_file = cmat_test_env / ".claude/queues/task_queue.json"
        queue_file.unlink()  # Remove existing file

        service = QueueService(str(queue_file))
        assert queue_file.exists()

    def test_add_task(self, cmat_test_env):
        """Test adding a task to the queue."""
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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

    def test_get_task(self, cmat_test_env):
        """Test retrieving a task by ID."""
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))
        assert service.get("nonexistent_id") is None

    def test_start_task(self, cmat_test_env):
        """Test starting a task moves it to active."""
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

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
        service = QueueService(str(cmat_test_env / ".claude/queues/task_queue.json"))

        service.add("Task 1", "agent", "normal", "analysis", "t.md", "Test")
        service.add("Task 2", "agent", "normal", "analysis", "t.md", "Test")

        # Reset queue
        result = service.init(force=True)
        assert result is True

        status = service.status()
        assert status["total"] == 0


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
        """Test building skills prompt."""
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

        service.invalidate_cache()
        prompt = service.build_skills_prompt(["test-skill"])

        assert "SPECIALIZED SKILLS" in prompt
        assert "Test Skill" in prompt


class TestLearningsService:
    """Tests for LearningsService (without Claude calls)."""

    def test_init_creates_directory(self, cmat_test_env):
        """Test that init creates learnings directory."""
        learnings_path = cmat_test_env / ".claude/learnings"
        learnings_path.rmdir()  # Remove existing

        service = LearningsService(str(learnings_path))
        assert learnings_path.exists()

    def test_store_and_get(self, cmat_test_env):
        """Test storing and retrieving a learning."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

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
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        learning = Learning.from_user_input("Test learning")
        service.store(learning)

        result = service.delete(learning.id)
        assert result is True

        assert service.get(learning.id) is None

    def test_delete_nonexistent(self, cmat_test_env):
        """Test deleting non-existent learning."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))
        result = service.delete("nonexistent_id")
        assert result is False

    def test_list_all(self, cmat_test_env):
        """Test listing all learnings."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        l1 = Learning.from_user_input("Learning 1", tags=["python"])
        l2 = Learning.from_user_input("Learning 2", tags=["testing"])

        service.store(l1)
        service.store(l2)

        learnings = service.list_all()
        assert len(learnings) == 2

    def test_list_by_tags(self, cmat_test_env):
        """Test filtering learnings by tags."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

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
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        assert service.count() == 0

        service.store(Learning.from_user_input("Test 1"))
        service.store(Learning.from_user_input("Test 2"))

        assert service.count() == 2

    def test_build_learnings_prompt_empty(self, cmat_test_env):
        """Test building prompt with no learnings."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))
        prompt = service.build_learnings_prompt([])
        assert prompt == ""

    def test_build_learnings_prompt(self, cmat_test_env):
        """Test building learnings prompt."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

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

    def test_cache_invalidation(self, cmat_test_env):
        """Test that cache invalidation works."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        learning = Learning.from_user_input("Test")
        service.store(learning)

        # Manually modify the file
        learnings_file = cmat_test_env / ".claude/learnings/learnings.json"
        with open(learnings_file) as f:
            data = json.load(f)
        data["learnings"].append({
            "id": "manual_add",
            "summary": "Manually added",
            "content": "Content",
            "tags": [],
            "applies_to": [],
            "source_type": "user_feedback",
            "source_task_id": None,
            "confidence": 0.5,
            "created": "2025-01-01T00:00:00Z",
        })
        with open(learnings_file, "w") as f:
            json.dump(data, f)

        # Without invalidation, cache returns old count
        assert service.count() == 1

        # After invalidation, returns new count
        service.invalidate_cache()
        assert service.count() == 2