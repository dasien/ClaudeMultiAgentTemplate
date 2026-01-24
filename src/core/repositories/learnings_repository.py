"""
Vector storage for learning embeddings using ChromaDB.

Provides local, offline semantic search for learnings without
requiring Claude API calls.
"""

import json
import shutil
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from core.models.learning import Learning
from core.utils.common import find_project_root, log_operation, log_error


class LearningsRepository:
    """
    Local vector storage for learning embeddings.

    Provides semantic search, deduplication, and CRUD operations for
    learnings without requiring Claude API calls.

    Features:
    - Lazy-loaded embedding model (no startup penalty)
    - Automatic deduplication (similarity > 0.9)
    - Fast semantic retrieval (<100ms after warmup)
    - Persistent storage in .claude/data/embeddings/
    """

    # Model configuration
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    COLLECTION_NAME = "learnings"
    DEDUP_THRESHOLD = 0.9

    def __init__(self, data_dir: str | None = None):
        """
        Initialize vector store with ChromaDB client.

        Args:
            data_dir: Base data directory (e.g., .claude/data/).
                     Embeddings will be stored in {data_dir}/embeddings/

        Note: Embedding model loads lazily on first use
        """
        if data_dir is None:
            project_root = find_project_root()
            if project_root:
                embeddings_dir = str(project_root / ".claude/data/embeddings")
            else:
                embeddings_dir = ".claude/data/embeddings"
        else:
            # Always append /embeddings to the data directory
            embeddings_dir = str(Path(data_dir) / "embeddings")

        self._persist_dir = embeddings_dir

        # Initialize ChromaDB client with recovery on corruption
        self._client, self._collection = self._init_chromadb_with_recovery()

        # Model will be lazily loaded
        self._model: SentenceTransformer | None = None

    def _init_chromadb_with_recovery(self) -> tuple:
        """
        Initialize ChromaDB with automatic recovery on database corruption.

        If the database is corrupt or readonly (e.g., after incomplete shutdown
        or reinstallation), this will delete and recreate it.

        Returns:
            Tuple of (client, collection)

        Raises:
            RuntimeError: If initialization fails even after recovery attempt
        """
        persist_path = Path(self._persist_dir)

        def _create_client_and_collection():
            """Create ChromaDB client and collection."""
            client = chromadb.PersistentClient(path=self._persist_dir)
            collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            return client, collection

        # First attempt
        try:
            client, collection = _create_client_and_collection()

            # Verify database is writable by attempting a test write/delete
            # count() is a read operation and won't catch "readonly database" errors
            test_id = "__write_test__"
            try:
                # Try to add a test document
                collection.add(
                    ids=[test_id],
                    embeddings=[[0.0] * self.EMBEDDING_DIM],
                    documents=["write test"],
                )
                # Clean up test document
                collection.delete(ids=[test_id])
            except Exception as write_error:
                # Re-raise with the write error - this will be caught below
                raise write_error

            return client, collection

        except Exception as first_error:
            error_str = str(first_error).lower()

            # Check if this is a recoverable database error
            is_db_error = any(
                indicator in error_str
                for indicator in [
                    "readonly",
                    "read-only",
                    "database error",
                    "sqlite",
                    "corrupt",
                    "locked",
                    "wal",
                    "disk i/o",
                    "unable to open",
                ]
            )

            if not is_db_error:
                # Not a database error - can't recover
                raise RuntimeError(
                    f"Failed to initialize vector store: {first_error}\n"
                    f"Try deleting {self._persist_dir} to recreate."
                ) from first_error

            # Attempt recovery by deleting and recreating the database
            log_operation(
                "VECTOR_DB_RECOVERY",
                f"Database error detected, attempting recovery: {first_error}",
            )

            try:
                # Delete the corrupted database directory if it exists
                if persist_path.exists():
                    shutil.rmtree(persist_path)
                    log_operation("VECTOR_DB_RECOVERY", f"Deleted corrupted database at {persist_path}")

                # Also check for and remove any stale lock files in parent directory
                parent_dir = persist_path.parent
                for lock_file in parent_dir.glob("*.lock"):
                    try:
                        lock_file.unlink()
                        log_operation("VECTOR_DB_RECOVERY", f"Removed stale lock file: {lock_file}")
                    except Exception:
                        pass  # Ignore errors removing lock files

                # Ensure parent directory exists
                persist_path.mkdir(parents=True, exist_ok=True)

                # Recreate with fresh database
                client, collection = _create_client_and_collection()

                log_operation("VECTOR_DB_RECOVERY", "Successfully recreated vector database")
                return client, collection

            except Exception as recovery_error:
                log_error(f"Vector database recovery failed: {recovery_error}")
                raise RuntimeError(
                    f"Failed to initialize vector store even after recovery attempt.\n"
                    f"Original error: {first_error}\n"
                    f"Recovery error: {recovery_error}\n"
                    f"Please manually delete {self._persist_dir} and try again."
                ) from recovery_error

    @property
    def embedding_model(self) -> SentenceTransformer:
        """
        Lazy-loaded embedding model.

        Returns:
            SentenceTransformer instance (cached after first load)

        Implementation:
        - Check if self._model exists
        - If not, load all-MiniLM-L6-v2 and cache
        - Handle download errors gracefully
        - First call takes ~2-5s (model download/load)
        - Subsequent calls return cached instance
        """
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.EMBEDDING_MODEL)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load embedding model: {e}\n"
                    "Ensure internet connection available for first-time model download."
                ) from e
        return self._model

    def add(self, learning: Learning) -> str | None:
        """
        Add learning to vector store with automatic deduplication.

        Args:
            learning: Learning object to store

        Returns:
            Learning ID if stored, None if duplicate (similarity > 0.9)

        Implementation:
        1. Check for duplicates using find_similar()
        2. If similarity > 0.9, return None (duplicate)
        3. Generate embedding from learning text
        4. Store in ChromaDB with metadata
        5. Return learning.id
        """
        # Check for duplicates
        similar = self.find_similar(learning, threshold=self.DEDUP_THRESHOLD, limit=1)
        if similar:
            return None  # Duplicate detected

        # Generate embedding
        text = self._learning_to_text(learning)
        embedding = self._embed(text)

        # Store in ChromaDB
        metadata = {
            "summary": learning.summary,
            "tags": json.dumps(learning.tags),
            "applies_to": json.dumps(learning.applies_to),
            "source_type": learning.source_type,
            "source_task_id": learning.source_task_id or "",
            "created": learning.created,
        }

        self._collection.add(  # type: ignore[arg-type,list-item]
            ids=[learning.id], embeddings=[embedding], documents=[text], metadatas=[metadata]
        )

        return learning.id

    def retrieve(self, query: str, limit: int = 5) -> list[Learning]:
        """
        Retrieve semantically similar learnings.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of Learning objects, sorted by similarity (highest first)

        Performance: <100ms after model warmup
        """
        # Handle empty collection
        if self.count() == 0:
            return []

        # Generate query embedding
        query_embedding = self._embed(query)

        # Query ChromaDB
        results = self._collection.query(  # type: ignore[arg-type]
            query_embeddings=[query_embedding],
            n_results=min(limit, self.count()),  # Don't request more than available
        )

        # Reconstruct Learning objects
        learnings = []
        if results["ids"] and results["ids"][0]:  # type: ignore[index]
            for i in range(len(results["ids"][0])):  # type: ignore[index]
                learning_id = results["ids"][0][i]  # type: ignore[index]
                metadata = results["metadatas"][0][i]  # type: ignore[index]
                document = results["documents"][0][i]  # type: ignore[index]

                learning_dict = {
                    "id": learning_id,
                    "summary": str(metadata["summary"]),
                    "content": self._extract_content_from_text(str(document), str(metadata["summary"])),
                    "tags": json.loads(str(metadata["tags"])),
                    "applies_to": json.loads(str(metadata["applies_to"])),
                    "source_type": str(metadata["source_type"]),
                    "source_task_id": (
                        str(metadata["source_task_id"]) if metadata["source_task_id"] else None
                    ),
                    "created": str(metadata["created"]),
                }

                learnings.append(Learning.from_dict(learning_dict))

        return learnings

    def find_similar(
        self, learning: Learning, threshold: float = 0.9, limit: int = 5
    ) -> list[tuple[Learning, float]]:
        """
        Find learnings similar to given learning.

        Args:
            learning: Learning to compare against
            threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of (Learning, similarity_score) tuples above threshold,
            sorted by similarity (highest first)

        Use case: Deduplication during add()
        """
        # Handle empty collection
        if self.count() == 0:
            return []

        # Generate embedding for learning
        text = self._learning_to_text(learning)
        embedding = self._embed(text)

        # Query for similar (request extra to account for self-match)
        n_results = min(limit + 1, self.count())
        results = self._collection.query(query_embeddings=[embedding], n_results=n_results)  # type: ignore[arg-type]

        # Filter by threshold and exclude self
        similar = []
        if results["ids"] and results["ids"][0]:  # type: ignore[index]
            for i in range(len(results["ids"][0])):  # type: ignore[index]
                learning_id = results["ids"][0][i]  # type: ignore[index]
                distance = results["distances"][0][i]  # type: ignore[index]
                similarity = 1 - distance  # Convert distance to similarity

                # Skip self and below threshold
                if learning_id == learning.id or similarity < threshold:
                    continue

                # Reconstruct learning
                metadata = results["metadatas"][0][i]  # type: ignore[index]
                document = results["documents"][0][i]  # type: ignore[index]

                learning_dict = {
                    "id": learning_id,
                    "summary": str(metadata["summary"]),
                    "content": self._extract_content_from_text(str(document), str(metadata["summary"])),
                    "tags": json.loads(str(metadata["tags"])),
                    "applies_to": json.loads(str(metadata["applies_to"])),
                    "source_type": str(metadata["source_type"]),
                    "source_task_id": (
                        str(metadata["source_task_id"]) if metadata["source_task_id"] else None
                    ),
                    "created": str(metadata["created"]),
                }

                similar.append((Learning.from_dict(learning_dict), similarity))

        return similar

    def get(self, learning_id: str) -> Learning | None:
        """
        Get a learning by ID.

        Args:
            learning_id: ID of learning to retrieve

        Returns:
            Learning object if found, None otherwise
        """
        try:
            result = self._collection.get(
                ids=[learning_id],
                include=["documents", "metadatas"],
            )

            if not result["ids"]:  # type: ignore[index]
                return None

            metadata = result["metadatas"][0]  # type: ignore[index]
            document = result["documents"][0]  # type: ignore[index]

            learning_dict = {
                "id": learning_id,
                "summary": str(metadata["summary"]),
                "content": self._extract_content_from_text(str(document), str(metadata["summary"])),
                "tags": json.loads(str(metadata["tags"])),
                "applies_to": json.loads(str(metadata["applies_to"])),
                "source_type": str(metadata["source_type"]),
                "source_task_id": (
                    str(metadata["source_task_id"]) if metadata["source_task_id"] else None
                ),
                "created": str(metadata["created"]),
            }

            return Learning.from_dict(learning_dict)
        except Exception:
            return None

    def get_all(self) -> list[Learning]:
        """
        Get all learnings from the vector store.

        Returns:
            List of all Learning objects
        """
        if self.count() == 0:
            return []

        # ChromaDB get() without IDs returns all documents
        result = self._collection.get(
            include=["documents", "metadatas"],
        )

        learnings = []
        if result["ids"]:  # type: ignore[index]
            for i in range(len(result["ids"])):  # type: ignore[index]
                learning_id = result["ids"][i]  # type: ignore[index]
                metadata = result["metadatas"][i]  # type: ignore[index]
                document = result["documents"][i]  # type: ignore[index]

                learning_dict = {
                    "id": learning_id,
                    "summary": str(metadata["summary"]),
                    "content": self._extract_content_from_text(str(document), str(metadata["summary"])),
                    "tags": json.loads(str(metadata["tags"])),
                    "applies_to": json.loads(str(metadata["applies_to"])),
                    "source_type": str(metadata["source_type"]),
                    "source_task_id": (
                        str(metadata["source_task_id"]) if metadata["source_task_id"] else None
                    ),
                    "created": str(metadata["created"]),
                }

                learnings.append(Learning.from_dict(learning_dict))

        return learnings

    def get_by_tags(self, tags: list[str]) -> list[Learning]:
        """
        Get learnings that match any of the given tags.

        Args:
            tags: List of tags to filter by

        Returns:
            List of Learning objects matching any tag
        """
        # Get all and filter - ChromaDB where clause doesn't support JSON array contains
        all_learnings = self.get_all()
        return [l for l in all_learnings if any(tag in l.tags for tag in tags)]

    def get_by_source(self, source_type: str) -> list[Learning]:
        """
        Get learnings from a specific source type.

        Args:
            source_type: Source type to filter by (e.g., "retrospective", "user")

        Returns:
            List of Learning objects from that source
        """
        if self.count() == 0:
            return []

        # Use ChromaDB where clause for metadata filtering
        result = self._collection.get(
            where={"source_type": source_type},
            include=["documents", "metadatas"],
        )

        learnings = []
        if result["ids"]:  # type: ignore[index]
            for i in range(len(result["ids"])):  # type: ignore[index]
                learning_id = result["ids"][i]  # type: ignore[index]
                metadata = result["metadatas"][i]  # type: ignore[index]
                document = result["documents"][i]  # type: ignore[index]

                learning_dict = {
                    "id": learning_id,
                    "summary": str(metadata["summary"]),
                    "content": self._extract_content_from_text(str(document), str(metadata["summary"])),
                    "tags": json.loads(str(metadata["tags"])),
                    "applies_to": json.loads(str(metadata["applies_to"])),
                    "source_type": str(metadata["source_type"]),
                    "source_task_id": (
                        str(metadata["source_task_id"]) if metadata["source_task_id"] else None
                    ),
                    "created": str(metadata["created"]),
                }

                learnings.append(Learning.from_dict(learning_dict))

        return learnings

    def update(self, learning: Learning) -> bool:
        """
        Update an existing learning in the vector store.

        Args:
            learning: Learning object with updated fields

        Returns:
            True if updated, False if not found
        """
        # Check if exists
        existing = self.get(learning.id)
        if existing is None:
            return False

        # Generate new embedding and update
        text = self._learning_to_text(learning)
        embedding = self._embed(text)

        metadata = {
            "summary": learning.summary,
            "tags": json.dumps(learning.tags),
            "applies_to": json.dumps(learning.applies_to),
            "source_type": learning.source_type,
            "source_task_id": learning.source_task_id or "",
            "created": learning.created,
        }

        self._collection.update(  # type: ignore[arg-type,list-item]
            ids=[learning.id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

        return True

    def delete(self, learning_id: str) -> bool:
        """
        Delete learning from vector store.

        Args:
            learning_id: ID of learning to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            # Check if the learning exists first
            existing = self._collection.get(ids=[learning_id])  # type: ignore[arg-type]
            if not existing["ids"]:  # type: ignore[index]
                return False

            self._collection.delete(ids=[learning_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        """
        Get total number of learnings in store.

        Returns:
            Count of stored learnings
        """
        return self._collection.count()

    def _embed(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            384-dimensional embedding vector

        Uses: self.embedding_model (triggers lazy load)
        """
        model = self.embedding_model  # Triggers lazy load
        embedding = model.encode(text)
        return embedding.tolist()

    def _learning_to_text(self, learning: Learning) -> str:
        """
        Convert learning to text for embedding.

        Args:
            learning: Learning object

        Returns:
            Formatted text combining summary, content, and tags

        Format:
            "{summary}. {content} Tags: {tags}"

        Rationale: Summary and content contain semantic meaning,
                   tags help with categorization
        """
        tags_str = ", ".join(learning.tags) if learning.tags else ""
        if tags_str:
            return f"{learning.summary}. {learning.content} Tags: {tags_str}"
        return f"{learning.summary}. {learning.content}"

    def _extract_content_from_text(self, text: str, summary: str) -> str:
        """
        Extract content from embedded text.

        Args:
            text: Full embedded text
            summary: Learning summary

        Returns:
            Content portion of the text

        The embedded text has format "{summary}. {content} Tags: {tags}"
        This extracts just the content portion.
        """
        # Remove summary from start
        if text.startswith(summary):
            text = text[len(summary) :].lstrip(". ")

        # Remove tags from end if present
        if " Tags: " in text:
            text = text.split(" Tags: ")[0]

        return text.strip()
