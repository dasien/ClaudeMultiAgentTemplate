"""
Learnings service for CMAT RAG system.

Provides persistent memory for agents through learning storage and retrieval.

Architecture:
- Retrospective agent extracts learnings from workflow outputs
- Vector store (ChromaDB) is the single source of truth for all operations
- JSON file used only for one-time migration from legacy format
"""

import json
from dataclasses import dataclass
from pathlib import Path

from core.models.learning import Learning
from core.services.base import JSONFileServiceMixin
from core.utils import get_timestamp, log_error, log_operation


@dataclass
class RetrievalContext:
    """Context for learning retrieval."""

    agent_name: str
    task_type: str
    task_description: str
    source_file: str | None = None
    tags: list[str] | None = None


class LearningsService(JSONFileServiceMixin):
    """
    Manages the RAG/learnings system for CMAT.

    Uses vector store (ChromaDB) as the single source of truth for all operations.
    Learning extraction is handled by the Retrospective agent at the end of workflows.

    Storage:
    - Vector store: .claude/data/embeddings/ (single source of truth)
    - JSON file: .claude/data/learnings.json (migration source only, not used after migration)
    """

    COLLECTION_KEY = "learnings"

    def __init__(
        self,
        data_dir: str | None = None,
    ):
        # Initialize JSON storage (only for migration)
        self._init_data_path(data_dir, "learnings.json")
        self._ensure_file_exists()

        # Initialize repository (single source of truth)
        from core.repositories import LearningsRepository

        self._repository = LearningsRepository(data_dir)

        # Run migration if needed (reads JSON once, then vector store is the source)
        self._ensure_migrated()

    def _get_default_data(self) -> dict:
        """Get default learnings data structure (for migration file)."""
        return {
            "version": "2.0.0",
            "last_updated": get_timestamp(),
            "migrated_to_vector": False,
            self.COLLECTION_KEY: [],
        }

    def _ensure_migrated(self) -> None:
        """
        Ensure existing learnings are migrated to vector store.

        Runs once on first initialization after upgrade to v2.0.0.
        Safe to call multiple times (checks flag first).

        Process:
        1. Check migrated_to_vector flag in JSON
        2. If True, skip (already migrated)
        3. If False:
           a. Read all learnings from JSON
           b. Add each to vector store
           c. Set flag to True
           d. Write updated JSON

        Error Handling:
        - Malformed learnings are logged and skipped
        - Vector store failures are logged and skipped
        - Migration continues even if individual learnings fail
        - Flag is only set if migration completes without critical errors
        """
        data = self._read_json()

        # Check if already migrated
        if data.get("migrated_to_vector", False):
            log_operation("MIGRATION_SKIPPED", "Learnings already migrated to vector store")
            return

        # Get learnings from JSON
        learnings_data = data.get(self.COLLECTION_KEY, [])

        if not learnings_data:
            # No learnings to migrate, just set flag
            log_operation("MIGRATION_EMPTY", "No learnings to migrate")
            data["migrated_to_vector"] = True
            data["version"] = "2.0.0"
            # Remove v1.0.0 fields
            if "count" in data:
                del data["count"]
            self._write_json(data)
            return

        # Migrate each learning
        migrated_count = 0
        failed_count = 0

        log_operation(
            "MIGRATION_START", f"Migrating {len(learnings_data)} learnings to vector store"
        )

        for learning_data in learnings_data:
            try:
                learning = Learning.from_dict(learning_data)
                result = self._repository.add(learning)

                if result is not None:
                    migrated_count += 1
                else:
                    # Duplicate detected (similarity > 0.9)
                    log_operation("MIGRATION_DUPLICATE", f"Skipped duplicate: {learning.id}")

            except Exception as e:
                failed_count += 1
                learning_id = learning_data.get("id", "unknown")
                log_error(f"Failed to migrate learning {learning_id}: {e}")
                # Continue with next learning

        # Set migration flag and remove old fields
        data["migrated_to_vector"] = True
        data["version"] = "2.0.0"
        # Remove v1.0.0 fields that are no longer needed
        if "count" in data:
            del data["count"]
        self._write_json(data)

        log_operation(
            "MIGRATION_COMPLETE",
            f"Migrated {migrated_count} learnings, {failed_count} failed, "
            f"{len(learnings_data) - migrated_count - failed_count} duplicates",
        )

    # =========================================================================
    # Storage Operations
    # =========================================================================

    def store(self, learning: Learning) -> str:
        """
        Store a learning in the vector store.

        Returns the learning ID. Returns existing ID if duplicate detected.
        """
        vector_result = self._repository.add(learning)

        if vector_result is None:
            log_operation(
                "LEARNING_DUPLICATE", f"Duplicate learning detected: {learning.summary[:50]}..."
            )
        else:
            log_operation(
                "LEARNING_STORED", f"ID: {learning.id}, Summary: {learning.summary[:50]}..."
            )

        return learning.id

    def get(self, learning_id: str) -> Learning | None:
        """Get a learning by ID from the vector store."""
        return self._repository.get(learning_id)

    def delete(self, learning_id: str) -> bool:
        """
        Delete a learning from the vector store.

        Returns True if deleted, False if not found.
        """
        deleted = self._repository.delete(learning_id)

        if deleted:
            log_operation("LEARNING_DELETED", f"ID: {learning_id}")

        return deleted

    def list_all(self) -> list[Learning]:
        """List all learnings from the vector store."""
        return self._repository.get_all()

    def list_by_tags(self, tags: list[str]) -> list[Learning]:
        """List learnings matching any of the given tags."""
        return self._repository.get_by_tags(tags)

    def list_by_source(self, source_type: str) -> list[Learning]:
        """List learnings from a specific source type."""
        return self._repository.get_by_source(source_type)

    def count(self) -> int:
        """Get the total number of learnings in the vector store."""
        return self._repository.count()

    def export_to_json(self) -> dict:
        """
        Export all learnings to JSON-compatible dictionary.

        Returns:
            Dictionary with version, metadata, and all learnings

        Use Cases:
        - Backup before major changes
        - Sharing learnings between projects
        - Manual inspection and editing
        """
        learnings = self.list_all()

        return {
            "version": "2.0.0",
            "last_updated": get_timestamp(),
            "migrated_to_vector": True,
            "count": len(learnings),  # Include for export (helpful metadata)
            self.COLLECTION_KEY: [learning.to_dict() for learning in learnings],
        }

    def import_from_json(self, data: dict) -> int:
        """
        Import learnings from JSON dictionary.

        Args:
            data: Dictionary with "learnings" key containing learning objects

        Returns:
            Number of learnings successfully imported

        Note: Uses store() for deduplication - duplicates are skipped
        """
        learnings_data = data.get(self.COLLECTION_KEY, [])

        if not learnings_data:
            log_operation("IMPORT_EMPTY", "No learnings in import data")
            return 0

        imported_count = 0
        failed_count = 0

        log_operation("IMPORT_START", f"Importing {len(learnings_data)} learnings")

        for learning_data in learnings_data:
            try:
                learning = Learning.from_dict(learning_data)
                self.store(learning)  # Uses deduplication
                imported_count += 1

            except Exception as e:
                failed_count += 1
                learning_id = learning_data.get("id", "unknown")
                log_error(f"Failed to import learning {learning_id}: {e}")

        log_operation(
            "IMPORT_COMPLETE", f"Imported {imported_count} learnings, {failed_count} failed"
        )

        return imported_count

    def process_actions_file(self, actions_file_path: str) -> dict[str, int]:
        """
        Process retrospective actions file and store learnings.

        Reads a learnings_actions.json file produced by the Retrospective agent,
        parses the learnings array, creates Learning objects, and stores them
        in the vector store. Deduplication is handled automatically.

        Args:
            actions_file_path: Path to learnings_actions.json file produced by
                the Retrospective agent. Expected format:
                {
                    "learnings": [
                        {
                            "summary": "One-sentence description",
                            "content": "Detailed explanation",
                            "tags": ["tag1", "tag2"],
                            "applies_to": ["implementation"]
                        }
                    ]
                }

        Returns:
            Dictionary with keys:
            - stored (int): Number of learnings successfully stored
            - duplicates (int): Number of duplicates skipped (similarity > 0.9)
            - errors (int): Number of learnings that failed to process

        Error Handling:
            All errors are caught and logged. Method always returns a result dict.
            Processing failures for individual learnings don't stop the batch.

        Example:
            >>> result = service.process_actions_file("path/to/actions.json")
            >>> print(f"Stored {result['stored']} learnings")
        """
        from pathlib import Path

        # Initialize counters
        result = {"stored": 0, "duplicates": 0, "errors": 0}

        # Validate file exists
        actions_path = Path(actions_file_path)
        if not actions_path.exists():
            log_error(f"Actions file not found: {actions_file_path}")
            result["errors"] = 1
            return result

        # Read and parse JSON
        try:
            with open(actions_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON in actions file: {e}")
            result["errors"] = 1
            return result
        except Exception as e:
            log_error(f"Failed to read actions file: {e}")
            result["errors"] = 1
            return result

        # Extract learnings array
        learnings_data = data.get("learnings", [])

        if not learnings_data:
            log_operation("RETROSPECTIVE_EMPTY", "No learnings in actions file")
            return result

        log_operation(
            "RETROSPECTIVE_PROCESSING",
            f"Processing {len(learnings_data)} learnings from {actions_file_path}",
        )

        # Process each learning
        for learning_data in learnings_data:
            try:
                # Validate required fields
                if not isinstance(learning_data, dict):
                    result["errors"] += 1
                    continue

                if not learning_data.get("summary") or not learning_data.get("content"):
                    log_error(f"Learning missing required fields: {learning_data}")
                    result["errors"] += 1
                    continue

                # Create Learning object from retrospective extraction
                # Use from_claude_extraction since format is similar
                learning = Learning.from_claude_extraction(
                    extraction=learning_data,
                    source_task_id=None,  # Retrospective learnings are workflow-level
                )

                # Store (handles deduplication internally)
                # Check count before/after to detect duplicates
                before_count = self.count()
                self.store(learning)
                after_count = self.count()

                if after_count > before_count:
                    result["stored"] += 1
                else:
                    result["duplicates"] += 1

            except Exception as e:
                result["errors"] += 1
                log_error(f"Failed to process learning: {e}")
                # Continue with next learning

        log_operation(
            "RETROSPECTIVE_COMPLETE",
            f"Stored {result['stored']}, duplicates {result['duplicates']}, "
            f"errors {result['errors']}",
        )

        return result

    # =========================================================================
    # User Input
    # =========================================================================

    def extract_from_user_input(self, content: str, tags: list[str] | None = None) -> Learning:
        """
        Create a learning from direct user input.

        Args:
            content: The learning content from the user
            tags: Optional tags for categorization

        Returns:
            The created Learning object
        """
        learning = Learning.from_user_input(content, tags)
        log_operation("LEARNING_FROM_USER", f"ID: {learning.id}")
        return learning

    # =========================================================================
    # Retrieval (Vector-powered)
    # =========================================================================

    def retrieve(
        self,
        context: RetrievalContext,
        limit: int = 5,
    ) -> list[Learning]:
        """
        Retrieve relevant learnings using vector search.

        Args:
            context: RetrievalContext with task information
            limit: Maximum number of learnings to return

        Returns:
            List of relevant Learning objects, ordered by similarity

        Performance: <100ms after model warmup, <5s first call
        """
        # Check if vector store is empty
        if self._repository.count() == 0:
            return []

        # Build query string from context
        query_parts = [context.task_description]

        if context.agent_name:
            query_parts.append(f"agent: {context.agent_name}")

        if context.task_type:
            query_parts.append(f"task type: {context.task_type}")

        if context.source_file:
            query_parts.append(f"file: {context.source_file}")

        if context.tags:
            query_parts.append(f"tags: {', '.join(context.tags)}")

        query = " ".join(query_parts)

        # Retrieve from vector store
        learnings = self._repository.retrieve(query, limit=limit)

        log_operation(
            "LEARNINGS_RETRIEVED",
            f"Retrieved {len(learnings)} learnings for {context.agent_name} using vector search",
        )

        return learnings

    # =========================================================================
    # Prompt Building
    # =========================================================================

    def build_learnings_prompt(self, learnings: list[Learning]) -> str:
        """
        Build a formatted learnings section for prompt injection.

        Args:
            learnings: List of Learning objects to include

        Returns:
            Formatted string for inclusion in agent prompts
        """
        if not learnings:
            return ""

        header = """
################################################################################
## RELEVANT LEARNINGS FROM PREVIOUS TASKS
################################################################################

The following learnings from previous tasks may be relevant to your current work.
Consider them as context that could inform your approach.

"""
        footer = """

**Using Learnings**: Apply these learnings where relevant, but use your judgment.
They represent past decisions that may or may not apply to the current context.

################################################################################
"""

        content_parts = []
        for learning in learnings:
            content_parts.append(f"---\n{learning.formatted_for_prompt()}\n---")

        return header + "\n\n".join(content_parts) + footer


# Convenience function for simple retrieval
def get_relevant_learnings(
    agent_name: str,
    task_type: str,
    task_description: str,
    data_dir: str | None = None,
    limit: int = 5,
) -> list[Learning]:
    """
    Convenience function to retrieve relevant learnings.

    Args:
        agent_name: Name of the agent
        task_type: Type of task
        task_description: Description of the task
        data_dir: Path to data directory (defaults to .claude/data/)
        limit: Maximum number of learnings

    Returns:
        List of relevant Learning objects
    """
    service = LearningsService(data_dir)
    context = RetrievalContext(
        agent_name=agent_name,
        task_type=task_type,
        task_description=task_description,
    )
    return service.retrieve(context, limit)
