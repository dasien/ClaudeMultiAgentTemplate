"""
Unit tests for CMAT models.

These tests don't require Claude CLI.
"""

import pytest
from cmat.models import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskMetadata,
    Agent,
    Learning,
)
from cmat.models.workflow_step import WorkflowStep
from cmat.models.step_transition import StepTransition


class TestWorkflowStep:
    """Tests for WorkflowStep dataclass."""

    def test_workflow_step_with_model(self):
        """Test WorkflowStep with model field."""
        step = WorkflowStep(
            agent="architect",
            input="enhancements/{enhancement_name}/spec.md",
            required_output="design.md",
            model="claude-opus-4-20250514",
        )
        assert step.agent == "architect"
        assert step.model == "claude-opus-4-20250514"

    def test_workflow_step_without_model(self):
        """Test WorkflowStep without model field (defaults to None)."""
        step = WorkflowStep(
            agent="implementer",
            input="input.md",
            required_output="output.md",
        )
        assert step.model is None

    def test_workflow_step_to_dict_with_model(self):
        """Test serialization includes model field."""
        step = WorkflowStep(
            agent="architect",
            input="input.md",
            required_output="output.md",
            model="claude-sonnet-4-20250514",
        )
        d = step.to_dict()
        assert d["model"] == "claude-sonnet-4-20250514"

    def test_workflow_step_to_dict_without_model(self):
        """Test serialization omits model when None."""
        step = WorkflowStep(
            agent="architect",
            input="input.md",
            required_output="output.md",
        )
        d = step.to_dict()
        assert "model" not in d

    def test_workflow_step_from_dict_with_model(self):
        """Test deserialization includes model field."""
        data = {
            "agent": "architect",
            "input": "input.md",
            "required_output": "output.md",
            "model": "claude-opus-4-20250514",
            "on_status": {},
        }
        step = WorkflowStep.from_dict(data)
        assert step.model == "claude-opus-4-20250514"

    def test_workflow_step_from_dict_without_model(self):
        """Test deserialization when model not present."""
        data = {
            "agent": "implementer",
            "input": "input.md",
            "required_output": "output.md",
            "on_status": {},
        }
        step = WorkflowStep.from_dict(data)
        assert step.model is None


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        """Verify status enum values match expected strings."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.ACTIVE.value == "active"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_status_from_string(self):
        """Test creating status from string value."""
        assert TaskStatus("pending") == TaskStatus.PENDING
        assert TaskStatus("active") == TaskStatus.ACTIVE


class TestTaskPriority:
    """Tests for TaskPriority enum."""

    def test_priority_values(self):
        """Verify priority enum values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.NORMAL.value == "normal"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"


class TestTaskMetadata:
    """Tests for TaskMetadata dataclass."""

    def test_default_values(self):
        """Test that defaults are set correctly."""
        metadata = TaskMetadata()
        assert metadata.github_issue is None
        assert metadata.workflow_name is None
        assert metadata.learnings_retrieved == []
        assert metadata.learnings_created == []

    def test_to_dict(self):
        """Test serialization to dict."""
        metadata = TaskMetadata(
            github_issue="https://github.com/org/repo/issues/1",
            workflow_name="test-workflow",
            learnings_retrieved=["learn_1", "learn_2"],
        )
        d = metadata.to_dict()
        assert d["github_issue"] == "https://github.com/org/repo/issues/1"
        assert d["workflow_name"] == "test-workflow"
        assert d["learnings_retrieved"] == ["learn_1", "learn_2"]
        assert d["learnings_created"] == []

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "github_issue": "https://github.com/org/repo/issues/1",
            "workflow_name": "test-workflow",
            "learnings_retrieved": ["learn_1"],
            "learnings_created": ["learn_2"],
        }
        metadata = TaskMetadata.from_dict(data)
        assert metadata.github_issue == "https://github.com/org/repo/issues/1"
        assert metadata.workflow_name == "test-workflow"
        assert metadata.learnings_retrieved == ["learn_1"]
        assert metadata.learnings_created == ["learn_2"]

    def test_from_dict_missing_learnings(self):
        """Test that missing learnings fields default to empty lists."""
        data = {"github_issue": "test"}
        metadata = TaskMetadata.from_dict(data)
        assert metadata.learnings_retrieved == []
        assert metadata.learnings_created == []

    def test_requested_model(self):
        """Test requested_model field for model selection."""
        metadata = TaskMetadata(requested_model="claude-sonnet-4-20250514")
        assert metadata.requested_model == "claude-sonnet-4-20250514"
        d = metadata.to_dict()
        assert d["requested_model"] == "claude-sonnet-4-20250514"

        # Test from_dict
        metadata2 = TaskMetadata.from_dict({"requested_model": "claude-opus-4-20250514"})
        assert metadata2.requested_model == "claude-opus-4-20250514"


class TestTask:
    """Tests for Task dataclass."""

    def test_create_task(self, sample_task_data):
        """Test creating a task from dict."""
        task = Task.from_dict(sample_task_data)
        assert task.id == "task_1234567890_12345"
        assert task.title == "Test Task"
        assert task.assigned_agent == "test-agent"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING

    def test_task_start(self, sample_task_data):
        """Test starting a task changes status to ACTIVE."""
        task = Task.from_dict(sample_task_data)
        assert task.status == TaskStatus.PENDING
        task.start()
        assert task.status == TaskStatus.ACTIVE
        assert task.started is not None

    def test_task_complete(self, sample_task_data):
        """Test completing a task."""
        task = Task.from_dict(sample_task_data)
        task.start()
        task.complete("READY_FOR_IMPLEMENTATION")
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "READY_FOR_IMPLEMENTATION"
        assert task.completed is not None

    def test_task_fail(self, sample_task_data):
        """Test failing a task."""
        task = Task.from_dict(sample_task_data)
        task.start()
        task.fail("Error occurred")
        assert task.status == TaskStatus.FAILED
        assert task.result == "Error occurred"  # fail() stores reason in result

    def test_task_to_dict_roundtrip(self, sample_task_data):
        """Test that to_dict/from_dict roundtrip preserves data."""
        task = Task.from_dict(sample_task_data)
        task.start()
        task.complete("DONE")

        task_dict = task.to_dict()
        restored = Task.from_dict(task_dict)

        assert restored.id == task.id
        assert restored.title == task.title
        assert restored.status == task.status
        assert restored.result == task.result


class TestAgent:
    """Tests for Agent dataclass."""

    def test_create_agent(self):
        """Test creating an agent."""
        agent = Agent(
            name="Architect",
            agent_file="architect",
            role="technical_design",
            description="Designs systems",
            tools=["Read", "Write"],
            skills=["api-design"],
        )
        assert agent.name == "Architect"
        assert agent.agent_file == "architect"
        assert "Read" in agent.tools
        assert "api-design" in agent.skills

    def test_has_skill(self):
        """Test has_skill method."""
        agent = Agent(
            name="Test",
            agent_file="test",
            role="test",
            description="Test",
            skills=["api-design", "testing"],
        )
        assert agent.has_skill("api-design")
        assert agent.has_skill("testing")
        assert not agent.has_skill("unknown")

    def test_has_tool(self):
        """Test has_tool method."""
        agent = Agent(
            name="Test",
            agent_file="test",
            role="test",
            description="Test",
            tools=["Read", "Write", "Bash"],
        )
        assert agent.has_tool("Read")
        assert agent.has_tool("Bash")
        assert not agent.has_tool("Delete")

    def test_to_dict_roundtrip(self):
        """Test serialization roundtrip."""
        agent = Agent(
            name="Test Agent",
            agent_file="test-agent",
            role="testing",
            description="A test agent",
            tools=["Read"],
            skills=["testing"],
        )
        d = agent.to_dict()
        restored = Agent.from_dict(d)
        assert restored.name == agent.name
        assert restored.agent_file == agent.agent_file
        assert restored.tools == agent.tools
        assert restored.skills == agent.skills


class TestLearning:
    """Tests for Learning dataclass."""

    def test_create_learning(self, sample_learning_data):
        """Test creating a learning from dict."""
        learning = Learning.from_dict(sample_learning_data)
        assert learning.id == "learn_1234567890_12345"
        assert learning.summary == "Test learning summary"
        assert "testing" in learning.tags
        assert learning.confidence == 0.8

    def test_from_user_input(self):
        """Test creating learning from user input."""
        learning = Learning.from_user_input(
            "Always use dataclasses for DTOs",
            tags=["python", "architecture"],
        )
        assert learning.id.startswith("learn_")
        assert "dataclasses" in learning.summary
        assert learning.source_type == "user_feedback"
        assert learning.confidence == 0.8
        assert "python" in learning.tags

    def test_from_user_input_long_content(self):
        """Test that long content is truncated in summary."""
        long_content = "A" * 200
        learning = Learning.from_user_input(long_content)
        assert len(learning.summary) <= 103  # 100 + "..."
        assert learning.content == long_content

    def test_generate_id(self):
        """Test ID generation."""
        id1 = Learning.generate_id()
        id2 = Learning.generate_id()
        assert id1.startswith("learn_")
        assert id2.startswith("learn_")
        # IDs should be unique (different random suffix)
        assert id1 != id2

    def test_matches_tags(self):
        """Test tag matching."""
        learning = Learning(
            id="test",
            summary="Test",
            content="Test",
            tags=["python", "testing"],
        )
        assert learning.matches_tags(["python"])
        assert learning.matches_tags(["testing"])
        assert learning.matches_tags(["python", "java"])  # OR match
        assert not learning.matches_tags(["java", "rust"])
        assert learning.matches_tags([])  # Empty matches all

    def test_matches_context(self):
        """Test context matching."""
        learning = Learning(
            id="test",
            summary="Test",
            content="Test",
            applies_to=["implementation", "review"],
        )
        assert learning.matches_context("implementation")
        assert learning.matches_context("IMPLEMENTATION")  # Case insensitive
        assert learning.matches_context("review")
        assert not learning.matches_context("analysis")

    def test_formatted_for_prompt(self):
        """Test prompt formatting."""
        learning = Learning(
            id="test",
            summary="Use dataclasses",
            content="Prefer dataclasses for simple DTOs.",
            tags=["python"],
            confidence=0.7,
        )
        formatted = learning.formatted_for_prompt()
        assert "Use dataclasses" in formatted
        assert "python" in formatted
        assert "70%" in formatted
        assert "Prefer dataclasses" in formatted

    def test_to_dict_roundtrip(self, sample_learning_data):
        """Test serialization roundtrip."""
        learning = Learning.from_dict(sample_learning_data)
        d = learning.to_dict()
        restored = Learning.from_dict(d)
        assert restored.id == learning.id
        assert restored.summary == learning.summary
        assert restored.tags == learning.tags
        assert restored.confidence == learning.confidence

    def test_json_serialization(self, sample_learning_data):
        """Test JSON serialization."""
        learning = Learning.from_dict(sample_learning_data)
        json_str = learning.to_json()
        restored = Learning.from_json(json_str)
        assert restored.id == learning.id
        assert restored.summary == learning.summary