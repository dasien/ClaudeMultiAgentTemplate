---
slug: vector-learnings
status: NEW
created: 2026-01-13
author: CMAT Team
priority: medium
---

# Enhancement: Vector-Based Learnings Retrieval

## Overview
**Goal:** Replace the current Claude-powered learnings retrieval with local vector embeddings using ChromaDB and sentence-transformers for faster, offline-capable semantic search.

**User Story:**
As a CMAT user, I want learnings to be retrieved using local semantic search so that retrieval is faster, works offline, and doesn't incur API costs.

## Context & Background
**Current State:**
- Learnings stored in `.claude/data/learnings.json`
- Each learning has: id, summary, content, tags, applies_to, source_type, confidence, created
- Retrieval uses Claude API calls to match learnings to task context
- Works but requires API connectivity and incurs token costs

**Technical Context:**
- Desktop Python/tkinter application
- Must work offline (no cloud dependency for retrieval)
- Typical corpus: 50-500 learnings
- Query latency target: <100ms (currently ~500ms via API)
- Memory budget: <100MB for embeddings infrastructure

**Dependencies:**
- New dependencies: `chromadb>=0.4.0`, `sentence-transformers>=3.0.0`
- sentence-transformers will download `all-MiniLM-L6-v2` model (~22MB) on first use
- Existing: `LearningsService` in `src/core/services/learnings_service.py`

## Requirements

### Functional Requirements
1. Store learning embeddings in a persistent local vector database (ChromaDB)
2. Retrieve semantically similar learnings using vector similarity search
3. Support hybrid retrieval: vector similarity + metadata filtering (tags, applies_to)
4. Migrate existing learnings from JSON to vector store on first run
5. Keep JSON as export/backup format (not a live retrieval path)
6. Provide re-embedding capability when model or learnings change

### Non-Functional Requirements
- **Performance:** Query latency <100ms after model warmup; first query <5s (model download)
- **Memory:** Embedding model ~80MB in RAM; vector index ~10MB for 500 learnings
- **Reliability:** Graceful handling if model download fails; clear error messaging
- **Compatibility:** Existing learnings.json format preserved for data portability

### Must Have (MVP)
- [ ] VectorLearningsStore class using ChromaDB
- [ ] Sentence-transformers integration with `all-MiniLM-L6-v2`
- [ ] Hybrid retrieval (vector + metadata filtering)
- [ ] Automatic migration from existing learnings.json
- [ ] Update LearningsService to use vector store
- [ ] Add/update/delete learnings with automatic re-embedding
- [ ] Confidence threshold setting (exclude low-confidence learnings from retrieval)
- [ ] JSON export/import for backup and portability
- [ ] Loading spinner dialog during first-run model download
- [ ] Unit tests for vector retrieval quality

### Should Have (if time permits)
- [ ] CLI command to rebuild embeddings
- [ ] Re-ranking with confidence scores

### Won't Have (out of scope)
- Cloud vector database options (Pinecone, etc.)
- Multiple embedding model support
- Fallback to Claude retrieval (hard cutover approach)
- Cross-encoder re-ranking (overkill for corpus size)

## Technical Design

### New Files
```
src/core/services/vector_learnings_store.py  # New - ChromaDB wrapper
src/core/services/learnings_service.py       # Update - use vector store
tests/test_vector_learnings.py               # New - retrieval quality tests
```

### Storage Location
```
.claude/data/
├── learnings.json           # Kept as backup/export format
├── embeddings/              # New - ChromaDB persistent storage
│   ├── chroma.sqlite3
│   └── [index files]
└── learnings_index.json     # New - vector store metadata
```

### Key Classes

**VectorLearningsStore:**
```python
class VectorLearningsStore:
    def __init__(self, persist_dir: str):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="learnings",
            metadata={"hnsw:space": "cosine"}
        )
        self._embedding_model = None  # Lazy load

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._embedding_model

    def add_learning(self, learning: Learning) -> None: ...
    def delete_learning(self, learning_id: str) -> None: ...
    def retrieve(self, query: str, limit: int = 5) -> list[Learning]: ...
    def retrieve_hybrid(self, query: str, tags: list = None,
                        applies_to: list = None, limit: int = 5) -> list[Learning]: ...
    def rebuild_all(self, learnings: list[Learning]) -> None: ...
```

**Updated LearningsService:**
```python
class LearningsService:
    def __init__(self, project_root: str):
        self.vector_store = VectorLearningsStore(
            persist_dir=os.path.join(project_root, ".claude/data/embeddings")
        )
        self.json_path = os.path.join(project_root, ".claude/data/learnings.json")
        self._ensure_migrated()

    def retrieve(self, context: RetrievalContext, limit: int = 5) -> list[Learning]:
        return self.vector_store.retrieve_hybrid(
            query=context.task_description,
            tags=context.tags,
            applies_to=[context.task_type] if context.task_type else None,
            limit=limit
        )

    def store(self, learning: Learning) -> str:
        self.vector_store.add_learning(learning)
        self._update_json_backup(learning)
        return learning.id

    def export_to_json(self) -> dict: ...
    def import_from_json(self, data: dict) -> int: ...
```

### Retrieval Algorithm
```
Input: query string, optional tags[], optional applies_to[], confidence_threshold

1. Encode query → 384-dim vector using sentence-transformers
2. Query ChromaDB with:
   - query_embeddings: [query_vector]
   - where: metadata filter for tags/applies_to (if provided)
   - where: confidence >= confidence_threshold
   - n_results: limit * 2 (over-fetch for filtering)
3. Return top `limit` results sorted by similarity score
```

### Learning CRUD Operations

**Add Learning (user creates via UI):**
```python
def store(self, learning: Learning) -> str:
    # 1. Generate embedding for new learning
    embedding = self.embedding_model.encode(f"{learning.summary} {learning.content}")

    # 2. Store in vector DB with metadata
    self.vector_store.add_learning(learning, embedding)

    # 3. Update JSON backup
    self._update_json_backup(learning)

    return learning.id
```

**Update Learning (user edits via UI):**
```python
def update(self, learning: Learning) -> None:
    # 1. Re-generate embedding (content may have changed)
    embedding = self.embedding_model.encode(f"{learning.summary} {learning.content}")

    # 2. Upsert in vector DB (ChromaDB handles update)
    self.vector_store.upsert_learning(learning, embedding)

    # 3. Update JSON backup
    self._update_json_backup(learning)
```

**Delete Learning:**
```python
def delete(self, learning_id: str) -> bool:
    # 1. Remove from vector DB
    self.vector_store.delete_learning(learning_id)

    # 2. Remove from JSON backup
    self._remove_from_json_backup(learning_id)

    return True
```

### Confidence Threshold Setting

Store in `.claude/settings.json`:
```json
{
  "learnings": {
    "confidence_threshold": 0.5
  }
}
```

Applied during retrieval - learnings with `confidence < threshold` are excluded from results.

## Open Questions
> These need answers before implementation

1. ~~**Similarity threshold:**~~ **RESOLVED:** Yes, implement confidence threshold setting. User can configure minimum confidence level (0.0-1.0) below which learnings are excluded from retrieval results.
2. ~~**First-run UX:**~~ **RESOLVED:** Use existing loading spinner popup dialog to show "Initializing AI search..." during model download.
3. **Migration trigger:** Auto-migrate on first retrieval, or explicit migration step in UI? (TBD)

## Constraints & Limitations
**Technical Constraints:**
- Embedding model downloads from Hugging Face Hub (requires one-time internet)
- ChromaDB uses SQLite internally (single-writer limitation)
- Model file cached in `~/.cache/torch/sentence_transformers/`

**Business/Timeline Constraints:**
- Should not break existing learnings data
- JSON export must remain human-readable

## Success Criteria
**Definition of Done:**
- [ ] Vector retrieval returns semantically relevant results
- [ ] Query latency <100ms after warmup
- [ ] Existing learnings migrated without data loss
- [ ] Works fully offline after initial model download
- [ ] All existing LearningsService tests pass
- [ ] New vector retrieval quality tests pass

**Acceptance Tests:**
1. Given a learning about "error handling patterns", when querying "exception management", then the learning is returned (semantic match)
2. Given 100 learnings, when querying with tags filter, then only matching-tag learnings are returned
3. Given no internet after model cached, when querying, then retrieval works offline
4. Given existing learnings.json, when service initializes, then all learnings are migrated to vector store

## Security & Safety Considerations
- Embedding model is from Hugging Face (trusted source: sentence-transformers)
- No user data sent to external services (all local)
- ChromaDB data stored in project directory (follows existing security model)
- JSON backup ensures data recovery if vector store corrupts

## UI/UX Considerations
- First-run: Show "Initializing AI search..." with progress (if feasible)
- Learnings Browser: No changes needed (retrieval is internal)
- Settings: Consider adding "Rebuild Embeddings" button for troubleshooting
- Error case: If model download fails, show clear error with retry option

## Testing Strategy
**Unit Tests:**
- VectorLearningsStore: add, delete, retrieve, rebuild operations
- Embedding consistency: same text → same vector
- Hybrid filtering: tag and applies_to filters work correctly

**Integration Tests:**
- Migration from JSON to vector store
- LearningsService API compatibility (existing tests should pass)
- Full retrieval flow with real embeddings

**Quality Tests:**
```python
def test_semantic_similarity():
    """Related concepts should match even without keyword overlap"""
    store.add_learning(Learning(summary="Use dataclasses for DTOs", ...))

    results = store.retrieve("data transfer objects")
    assert len(results) > 0  # Should find it semantically

def test_unrelated_queries():
    """Unrelated queries should have low similarity scores"""
    store.add_learning(Learning(summary="Python testing patterns", ...))

    results = store.retrieve("Docker configuration", limit=5)
    # Either no results or low similarity scores
```

**Manual Test Scenarios:**
1. Fresh install: Verify model downloads and learnings migrate
2. Offline: Disable network after setup, verify retrieval works
3. Large corpus: Add 500 learnings, verify query time <100ms

## References & Research
- [sentence-transformers documentation](https://www.sbert.net/)
- [ChromaDB documentation](https://docs.trychroma.com/)
- [all-MiniLM-L6-v2 model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- CMAT Learnings System: `docs/LEARNINGS_GUIDE.md`

## Notes for Architect Subagent
> Key architectural considerations

- Lazy-load embedding model to avoid startup delay
- Use ChromaDB's persistent client (not in-memory) for durability
- Keep JSON as backup format but remove it as retrieval path
- Consider batch embedding for migration (more efficient than one-by-one)
- Evaluate whether to store full learning content in ChromaDB or just metadata

## Notes for Implementer Subagent
> Implementation guidance

- Start with VectorLearningsStore as standalone class
- Use `@property` for lazy model loading
- Batch encode during migration: `model.encode(texts, batch_size=32)`
- ChromaDB `upsert` handles both add and update
- Keep learning ID format unchanged for compatibility
- Update `pyproject.toml` with new dependencies

## Notes for Testing Subagent
> Testing and validation guidance

- Focus on retrieval quality tests (semantic matching)
- Test with real embeddings, not mocks (quality matters)
- Verify migration preserves all learning fields
- Test hybrid filtering edge cases (empty tags, multiple applies_to)
- Performance test: 500 learnings, measure P95 query latency
- Test offline scenario after model is cached