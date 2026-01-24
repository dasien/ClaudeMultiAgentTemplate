"""
Tests for LearningsRepository.

Tests the vector storage, semantic search, and deduplication functionality.
"""

import tempfile
from pathlib import Path

import pytest

from core.models.learning import Learning
from core.repositories import LearningsRepository


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def repository(temp_dir):
    """Create repository with temporary storage."""
    repo = LearningsRepository(data_dir=str(temp_dir))
    yield repo


class TestLearningsRepository:
    """Tests for LearningsRepository."""

    def test_initialization(self, temp_dir):
        """Test store initialization."""
        store = LearningsRepository(data_dir=str(temp_dir))
        assert store is not None
        assert store.count() == 0

    def test_add_and_retrieve(self, repository):
        """Test adding and retrieving learnings."""
        learning = Learning.from_user_input("Use dataclasses for DTOs", ["python"])

        learning_id = repository.add(learning)
        assert learning_id == learning.id

        results = repository.retrieve("dataclasses", limit=5)
        assert len(results) == 1
        assert results[0].id == learning.id
        assert results[0].summary == learning.summary

    def test_semantic_matching(self, repository):
        """Test semantic search works beyond keyword matching."""
        # Add learning with "DTO" terminology
        learning = Learning.from_user_input(
            "Use dataclasses for DTOs to avoid boilerplate", ["python", "architecture"]
        )
        repository.add(learning)

        # Query with different terminology
        results = repository.retrieve("data transfer objects", limit=5)
        assert len(results) > 0
        assert learning.id in [result.id for result in results]

    def test_deduplication(self, repository):
        """Test automatic deduplication of highly similar learnings."""
        # Use nearly identical text for high similarity (>0.9)
        learning1 = Learning.from_user_input(
            "Use dataclasses for data transfer objects", ["python"]
        )
        learning2 = Learning.from_user_input(
            "Use dataclasses for data transfer objects in Python", ["python"]
        )

        id1 = repository.add(learning1)
        assert id1 is not None

        id2 = repository.add(learning2)
        assert id2 is None  # Duplicate rejected

        assert repository.count() == 1

    def test_find_similar(self, repository):
        """Test finding similar learnings with scores."""
        learning1 = Learning.from_user_input("Use pytest for testing", ["testing"])
        learning2 = Learning.from_user_input("Use pytest fixtures for setup", ["testing"])
        learning3 = Learning.from_user_input("Use black formatter for code style", ["formatting"])

        repository.add(learning1)
        repository.add(learning2)
        repository.add(learning3)

        similar = repository.find_similar(learning1, threshold=0.7, limit=5)

        # Should find learning2 (similar) but not learning3 (unrelated)
        assert len(similar) >= 1
        assert any(learn.id == learning2.id for learn, _ in similar)

        # Verify scores are in valid range
        for _, score in similar:
            assert 0.7 <= score <= 1.0

    def test_delete(self, repository):
        """Test deleting learnings."""
        learning = Learning.from_user_input("Test learning", ["test"])
        repository.add(learning)
        assert repository.count() == 1

        result = repository.delete(learning.id)
        assert result is True
        assert repository.count() == 0

        # Delete non-existent
        result = repository.delete("nonexistent")
        assert result is False

    def test_empty_store(self, repository):
        """Test operations on empty store."""
        assert repository.count() == 0
        assert repository.retrieve("query") == []
        assert repository.delete("nonexistent") is False

    def test_unrelated_query(self, repository):
        """Test query with no semantic matches."""
        learning = Learning.from_user_input("Python testing best practices", ["testing"])
        repository.add(learning)

        # Unrelated query should return results but with low similarity
        results = repository.retrieve("database optimization", limit=5)
        # ChromaDB always returns results, even with low similarity
        # We don't filter by threshold in retrieve()
        assert isinstance(results, list)

    def test_persistence(self, temp_dir):
        """Test that data persists across store instances."""
        # First store
        store1 = LearningsRepository(data_dir=str(temp_dir))
        learning = Learning.from_user_input("Test persistence", ["test"])
        store1.add(learning)

        # Second store (same directory)
        store2 = LearningsRepository(data_dir=str(temp_dir))
        assert store2.count() == 1

        results = store2.retrieve("persistence", limit=5)
        assert len(results) == 1
        assert results[0].id == learning.id

    def test_multiple_learnings(self, repository):
        """Test storing and retrieving multiple learnings."""
        learnings = [
            Learning.from_user_input("Use dataclasses for DTOs", ["python"]),
            Learning.from_user_input("Use pytest for unit testing", ["testing"]),
            Learning.from_user_input("Use black for code formatting", ["formatting"]),
            Learning.from_user_input("Use mypy for type checking", ["typing"]),
        ]

        for learning in learnings:
            repository.add(learning)

        assert repository.count() == 4

        # Query should return relevant results
        results = repository.retrieve("testing", limit=5)
        assert len(results) > 0

    def test_learning_content_preservation(self, repository):
        """Test that learning content is preserved correctly."""
        original = Learning.from_user_input(
            "Use dataclasses for DTOs. They reduce boilerplate and improve readability.",
            ["python", "architecture"],
        )

        repository.add(original)
        results = repository.retrieve("dataclasses", limit=1)

        assert len(results) == 1
        retrieved = results[0]

        # Verify all fields preserved
        assert retrieved.id == original.id
        assert retrieved.summary == original.summary
        assert retrieved.tags == original.tags
        assert retrieved.source_type == original.source_type

    def test_empty_tags(self, repository):
        """Test handling of learnings with no tags."""
        learning = Learning(
            id=Learning.generate_id(),
            summary="Test learning without tags",
            content="This learning has no tags.",
            tags=[],
            applies_to=["general"],
            source_type="user_feedback",
        )

        learning_id = repository.add(learning)
        assert learning_id is not None

        results = repository.retrieve("test learning", limit=1)
        assert len(results) == 1
        assert results[0].tags == []

    def test_high_similarity_threshold(self, repository):
        """Test find_similar with high threshold."""
        learning1 = Learning.from_user_input("Use pytest", ["testing"])
        learning2 = Learning.from_user_input("Use unittest", ["testing"])

        repository.add(learning1)
        repository.add(learning2)

        # High threshold should find fewer results
        similar = repository.find_similar(learning1, threshold=0.95, limit=5)

        # Should not find learning2 (not similar enough)
        assert all(learn.id != learning2.id for learn, _ in similar)

    def test_lazy_model_loading(self, temp_dir):
        """Test that model loads lazily."""
        store = LearningsRepository(data_dir=str(temp_dir))

        # Model should not be loaded yet
        assert store._model is None

        # Adding a learning should trigger model load
        learning = Learning.from_user_input("Test", ["test"])
        store.add(learning)

        # Model should now be loaded
        assert store._model is not None

    def test_count_accuracy(self, repository):
        """Test that count() returns accurate results."""
        assert repository.count() == 0

        # Add learnings one by one with sufficiently different content
        topics = ["Use pytest", "Use black formatter", "Use type hints", "Use docstrings", "Use logging"]
        for i, topic in enumerate(topics):
            learning = Learning.from_user_input(topic, ["test"])
            repository.add(learning)
            assert repository.count() == i + 1

        # Delete learnings one by one
        results = repository.retrieve("Use", limit=10)
        for i, learning in enumerate(results):
            repository.delete(learning.id)
            assert repository.count() == len(results) - i - 1

    def test_retrieve_limit(self, repository):
        """Test that retrieve respects limit parameter."""
        # Add 10 learnings
        for i in range(10):
            learning = Learning.from_user_input(f"Python learning {i}", ["python"])
            repository.add(learning)

        # Request only 3 results
        results = repository.retrieve("Python", limit=3)
        assert len(results) == 3

    def test_special_characters_in_content(self, repository):
        """Test handling of special characters in learning content."""
        learning = Learning.from_user_input(
            'Use f-strings: f"Hello {name}!" for string formatting', ["python"]
        )

        learning_id = repository.add(learning)
        assert learning_id is not None

        results = repository.retrieve("string formatting", limit=1)
        assert len(results) == 1
        assert "{name}" in results[0].content

    def test_near_duplicate_detection(self, repository):
        """Test that near-duplicate learnings are detected."""
        # Use same content and tags to ensure >0.9 similarity
        learning1 = Learning.from_user_input(
            "Use dataclasses for cleaner Python code", ["python"]
        )
        learning2 = Learning.from_user_input(
            "Use dataclasses for cleaner code in Python", ["python"]
        )

        id1 = repository.add(learning1)
        assert id1 is not None

        # Check if they're similar enough
        similar = repository.find_similar(learning2, threshold=0.85, limit=1)

        # They should be similar (>0.85) even if not identical
        assert len(similar) > 0
        assert similar[0][1] > 0.85
