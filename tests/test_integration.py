"""
Integration tests for CMAT that require Claude CLI.

These tests are marked with @pytest.mark.requires_claude and will be skipped
if the Claude CLI is not available (unless --run-claude is passed).

Run these tests with:
    pytest -m requires_claude --run-claude
"""

import pytest
from core.models import Learning
from core.services import LearningsService, RetrievalContext


@pytest.mark.requires_claude
class TestLearningsServiceWithClaude:
    """Integration tests for LearningsService that require Claude."""

    def test_extract_from_output(self, cmat_test_env):
        """Test extracting learnings from agent output using Claude."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        # Sample agent output that might contain learnable patterns
        agent_output = """
        I've analyzed the codebase and implemented the following changes:

        1. Created a new UserService class using the repository pattern
        2. Used dataclasses for DTOs instead of Pydantic since validation wasn't needed
        3. Added comprehensive error handling with custom exceptions
        4. All database queries use parameterized queries to prevent SQL injection

        Key decisions:
        - Chose SQLite for simplicity during development
        - Used dependency injection for testability
        - Applied the single responsibility principle throughout

        Status: READY_FOR_REVIEW
        """

        learnings = service.extract_from_output(
            agent_output=agent_output,
            agent_name="implementer",
            task_type="implementation",
            task_description="Implement user management feature",
            task_id="task_test_123",
        )

        # Claude should extract 0-3 learnings
        assert isinstance(learnings, list)
        assert len(learnings) <= 3

        # If learnings were extracted, verify structure
        for learning in learnings:
            assert isinstance(learning, Learning)
            assert learning.id.startswith("learn_")
            assert learning.summary  # Non-empty summary
            assert learning.source_type == "agent_output"
            assert learning.source_task_id == "task_test_123"

    def test_retrieve_learnings(self, cmat_test_env):
        """Test retrieving relevant learnings using Claude."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        # Add some learnings
        learnings_to_add = [
            Learning.from_user_input(
                "Always use dataclasses for simple DTOs without validation",
                tags=["python", "data-models"],
            ),
            Learning.from_user_input(
                "Use pytest fixtures for database test setup",
                tags=["testing", "database"],
            ),
            Learning.from_user_input(
                "Apply repository pattern for data access layer",
                tags=["architecture", "patterns"],
            ),
            Learning.from_user_input(
                "Use parameterized queries to prevent SQL injection",
                tags=["security", "database"],
            ),
        ]

        for learning in learnings_to_add:
            service.store(learning)

        # Test retrieval for a database-related task
        context = RetrievalContext(
            agent_name="implementer",
            task_type="implementation",
            task_description="Implement database access layer for user management",
        )

        retrieved = service.retrieve(context, limit=2)

        # Should retrieve some relevant learnings
        assert isinstance(retrieved, list)
        assert len(retrieved) <= 2

        # The database/architecture learnings should be more relevant
        # (though we can't guarantee exact results from Claude)
        if retrieved:
            assert all(isinstance(l, Learning) for l in retrieved)

    def test_extract_empty_output(self, cmat_test_env):
        """Test extraction from minimal output returns empty list."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        learnings = service.extract_from_output(
            agent_output="Done.",
            agent_name="test",
            task_type="test",
            task_description="Test task",
        )

        # Should return empty list for trivial output
        assert isinstance(learnings, list)


@pytest.mark.requires_claude
@pytest.mark.slow
class TestFullWorkflowWithClaude:
    """End-to-end workflow tests requiring Claude."""

    def test_learning_lifecycle(self, cmat_test_env):
        """Test complete learning lifecycle: add, retrieve, use in prompt."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        # 1. Add a manual learning
        learning = Learning.from_user_input(
            "This project uses Black for code formatting with line-length=88",
            tags=["python", "formatting", "tools"],
        )
        service.store(learning)

        # 2. Simulate agent output that could generate learnings
        agent_output = """
        I've reviewed the code and made formatting changes:
        - Applied Black formatter with line-length=88
        - Sorted imports using isort
        - The project uses type hints throughout

        Observation: The codebase consistently uses f-strings over .format()

        Status: READY_FOR_REVIEW
        """

        # 3. Extract learnings from output
        extracted = service.extract_from_output(
            agent_output=agent_output,
            agent_name="code-reviewer",
            task_type="review",
            task_description="Review code formatting",
            task_id="task_format_review",
        )

        # Store any extracted learnings
        for l in extracted:
            service.store(l)

        # 4. Retrieve for a new formatting task
        context = RetrievalContext(
            agent_name="implementer",
            task_type="implementation",
            task_description="Write new Python module following project conventions",
        )

        relevant = service.retrieve(context, limit=3)

        # 5. Build prompt with learnings
        prompt = service.build_learnings_prompt(relevant)

        # Should have some learnings in prompt
        if relevant:
            assert "RELEVANT LEARNINGS" in prompt
            # The formatting learning should likely be included
            # (can't guarantee exact behavior from Claude)

        # 6. Verify total count
        assert service.count() >= 1  # At least the manual one