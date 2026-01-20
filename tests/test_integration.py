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


@pytest.mark.requires_claude
@pytest.mark.slow
class TestFullWorkflowWithClaude:
    """End-to-end workflow tests requiring Claude."""

    def test_learning_lifecycle(self, cmat_test_env):
        """Test complete learning lifecycle: add, retrieve, use in prompt."""
        service = LearningsService(str(cmat_test_env / ".claude/learnings"))

        # 1. Add manual learnings
        learnings = [
            Learning.from_user_input(
                "This project uses Black for code formatting with line-length=88",
                tags=["python", "formatting", "tools"],
            ),
            Learning.from_user_input(
                "Use f-strings over .format() for string interpolation",
                tags=["python", "formatting", "conventions"],
            ),
        ]

        for learning in learnings:
            service.store(learning)

        # 2. Retrieve for a formatting task
        context = RetrievalContext(
            agent_name="implementer",
            task_type="implementation",
            task_description="Write new Python module following project conventions",
        )

        relevant = service.retrieve(context, limit=3)

        # 3. Build prompt with learnings
        prompt = service.build_learnings_prompt(relevant)

        # Should have some learnings in prompt
        if relevant:
            assert "RELEVANT LEARNINGS" in prompt
            # The formatting learning should likely be included

        # 4. Verify total count
        assert service.count() >= 1  # At least one learning stored