"""
Learnings service for CMAT RAG system.

Provides persistent memory for agents through learning extraction,
storage, and retrieval using Claude for semantic understanding.

Uses the "Full Claude" approach:
- Claude extracts structured learnings from agent outputs
- Claude retrieves relevant learnings based on task context
- No vector embeddings or external dependencies required
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from cmat.models.learning import Learning
from cmat.utils import get_timestamp, log_operation, log_error, find_project_root

if TYPE_CHECKING:
    from cmat.models.task import Task


@dataclass
class RetrievalContext:
    """Context for learning retrieval."""
    agent_name: str
    task_type: str
    task_description: str
    source_file: Optional[str] = None
    tags: Optional[list[str]] = None


class LearningsService:
    """
    Manages the RAG/learnings system for CMAT.

    Uses Claude for both extraction (from agent outputs) and retrieval
    (selecting relevant learnings for task context).

    Storage: Simple JSON file at .claude/data/learnings.json
    """

    # Extraction prompt template
    EXTRACTION_PROMPT = """Analyze this agent output and extract any learnings that would help future tasks.

Look for:
- Coding patterns and conventions used
- Architectural decisions made
- Gotchas or pitfalls discovered
- Best practices applied
- Project-specific preferences
- Testing approaches
- Error handling strategies

Agent: {agent_name}
Task Type: {task_type}
Task Description: {task_description}

=== AGENT OUTPUT START ===
{agent_output}
=== AGENT OUTPUT END ===

Extract 0-3 learnings. For each learning, provide:
- summary: 1-2 sentence description of the learning
- content: Detailed explanation (2-4 sentences)
- tags: Categories like "python", "architecture", "testing", "error-handling", etc.
- applies_to: Contexts where this applies like "implementation", "analysis", "review"
- confidence: 0.0-1.0 (how universal vs project-specific)

Return ONLY a JSON array of learnings. If no valuable learnings, return empty array [].
Example format:
[
  {{
    "summary": "Use dataclasses for simple DTOs",
    "content": "When creating data transfer objects that don't need validation, prefer dataclasses over Pydantic for simplicity and performance.",
    "tags": ["python", "architecture", "data-models"],
    "applies_to": ["implementation"],
    "confidence": 0.7
  }}
]

JSON response:"""

    # Retrieval prompt template
    RETRIEVAL_PROMPT = """Given this task context, select the most relevant learnings from the list below.

Task Context:
- Agent: {agent_name}
- Task Type: {task_type}
- Description: {task_description}
- Source File: {source_file}

Available Learnings:
{learnings_list}

Select the learnings that would be most helpful for this specific task.
Consider:
- Relevance to the task type and description
- Matching tags and applies_to contexts
- Higher confidence learnings are more reliable

Return ONLY a JSON array of learning IDs, ordered by relevance (most relevant first).
Maximum {limit} learnings.
If no learnings are relevant, return empty array [].

Example: ["learn_123_456", "learn_789_012"]

JSON response:"""

    def __init__(
        self,
        data_dir: Optional[str] = None,
    ):
        # Resolve path relative to project root, not cwd
        if data_dir is None:
            project_root = find_project_root()
            if project_root:
                self.learnings_file = project_root / ".claude/data/learnings.json"
            else:
                self.learnings_file = Path(".claude/data/learnings.json")
        else:
            self.learnings_file = Path(data_dir) / "learnings.json"

        self._cache: Optional[dict[str, Learning]] = None
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Ensure the storage directory and file exist."""
        self.learnings_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.learnings_file.exists():
            self._write_learnings({})

    def _read_learnings(self) -> dict[str, Learning]:
        """Read all learnings from storage."""
        if self._cache is not None:
            return self._cache

        if not self.learnings_file.exists():
            return {}

        with open(self.learnings_file, 'r') as f:
            data = json.load(f)

        learnings = {}
        for learning_data in data.get("learnings", []):
            learning = Learning.from_dict(learning_data)
            learnings[learning.id] = learning

        self._cache = learnings
        return learnings

    def _write_learnings(self, learnings: dict[str, Learning]) -> None:
        """Write all learnings to storage."""
        data = {
            "version": "1.0.0",
            "last_updated": get_timestamp(),
            "count": len(learnings),
            "learnings": [l.to_dict() for l in learnings.values()],
        }

        with open(self.learnings_file, 'w') as f:
            json.dump(data, f, indent=2)

        self._cache = learnings

    def invalidate_cache(self) -> None:
        """Invalidate the cache to force reload from disk."""
        self._cache = None

    # =========================================================================
    # Storage Operations
    # =========================================================================

    def store(self, learning: Learning) -> str:
        """
        Store a learning in the database.

        Returns the learning ID.
        """
        learnings = self._read_learnings()
        learnings[learning.id] = learning
        self._write_learnings(learnings)

        log_operation("LEARNING_STORED", f"ID: {learning.id}, Summary: {learning.summary[:50]}...")
        return learning.id

    def get(self, learning_id: str) -> Optional[Learning]:
        """Get a learning by ID."""
        return self._read_learnings().get(learning_id)

    def delete(self, learning_id: str) -> bool:
        """Delete a learning by ID."""
        learnings = self._read_learnings()
        if learning_id not in learnings:
            return False

        del learnings[learning_id]
        self._write_learnings(learnings)

        log_operation("LEARNING_DELETED", f"ID: {learning_id}")
        return True

    def list_all(self) -> list[Learning]:
        """List all learnings."""
        return list(self._read_learnings().values())

    def list_by_tags(self, tags: list[str]) -> list[Learning]:
        """List learnings matching any of the given tags."""
        learnings = self._read_learnings()
        return [l for l in learnings.values() if l.matches_tags(tags)]

    def list_by_source(self, source_type: str) -> list[Learning]:
        """List learnings from a specific source type."""
        learnings = self._read_learnings()
        return [l for l in learnings.values() if l.source_type == source_type]

    def count(self) -> int:
        """Get the total number of learnings."""
        return len(self._read_learnings())

    # =========================================================================
    # Extraction (Claude-powered)
    # =========================================================================

    def extract_from_output(
        self,
        agent_output: str,
        agent_name: str,
        task_type: str,
        task_description: str,
        task_id: Optional[str] = None,
    ) -> list[Learning]:
        """
        Extract learnings from agent output using Claude.

        Args:
            agent_output: The full output from the agent
            agent_name: Name of the agent that produced the output
            task_type: Type of task (analysis, implementation, etc.)
            task_description: Description of the task
            task_id: Optional task ID for source tracking

        Returns:
            List of extracted Learning objects (may be empty)
        """
        # Limit output size to avoid token limits
        max_output = 10000
        if len(agent_output) > max_output:
            agent_output = agent_output[:max_output] + "\n...(truncated)"

        prompt = self.EXTRACTION_PROMPT.format(
            agent_name=agent_name,
            task_type=task_type,
            task_description=task_description,
            agent_output=agent_output,
        )

        # Call Claude for extraction
        response = self._call_claude(prompt)
        if not response:
            return []

        # Parse JSON response
        try:
            extractions = json.loads(response)
            if not isinstance(extractions, list):
                return []

            learnings = []
            for extraction in extractions:
                if isinstance(extraction, dict) and extraction.get("summary"):
                    learning = Learning.from_claude_extraction(extraction, task_id)
                    learnings.append(learning)

            log_operation(
                "LEARNINGS_EXTRACTED",
                f"Extracted {len(learnings)} learnings from {agent_name} output"
            )
            return learnings

        except json.JSONDecodeError:
            log_error(f"Failed to parse extraction response: {response[:200]}")
            return []

    def extract_from_user_input(self, content: str, tags: Optional[list[str]] = None) -> Learning:
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
    # Retrieval (Claude-powered)
    # =========================================================================

    def retrieve(
        self,
        context: RetrievalContext,
        limit: int = 5,
    ) -> list[Learning]:
        """
        Retrieve relevant learnings for a task context using Claude.

        Args:
            context: RetrievalContext with task information
            limit: Maximum number of learnings to return

        Returns:
            List of relevant Learning objects, ordered by relevance
        """
        all_learnings = self.list_all()
        if not all_learnings:
            return []

        # Pre-filter by tags if provided
        if context.tags:
            candidates = [l for l in all_learnings if l.matches_tags(context.tags)]
        else:
            candidates = all_learnings

        # If few candidates, return all without Claude call
        if len(candidates) <= limit:
            return candidates

        # Format learnings for Claude
        learnings_list = "\n".join([
            f"- ID: {l.id}\n  Summary: {l.summary}\n  Tags: {', '.join(l.tags)}\n  Applies to: {', '.join(l.applies_to)}\n  Confidence: {l.confidence:.0%}"
            for l in candidates
        ])

        prompt = self.RETRIEVAL_PROMPT.format(
            agent_name=context.agent_name,
            task_type=context.task_type,
            task_description=context.task_description,
            source_file=context.source_file or "N/A",
            learnings_list=learnings_list,
            limit=limit,
        )

        # Call Claude for selection
        response = self._call_claude(prompt)
        if not response:
            # Fallback: return most recent learnings
            return sorted(candidates, key=lambda l: l.created, reverse=True)[:limit]

        # Parse JSON response
        try:
            selected_ids = json.loads(response)
            if not isinstance(selected_ids, list):
                return candidates[:limit]

            # Return learnings in the order Claude specified
            learnings_map = {l.id: l for l in candidates}
            selected = []
            for learning_id in selected_ids:
                if learning_id in learnings_map:
                    selected.append(learnings_map[learning_id])
                if len(selected) >= limit:
                    break

            log_operation(
                "LEARNINGS_RETRIEVED",
                f"Retrieved {len(selected)} learnings for {context.agent_name}"
            )
            return selected

        except json.JSONDecodeError:
            log_error(f"Failed to parse retrieval response: {response[:200]}")
            return candidates[:limit]

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

    # =========================================================================
    # Claude Integration
    # =========================================================================

    def _call_claude(self, prompt: str) -> Optional[str]:
        """
        Call Claude CLI with a prompt and return the response.

        Uses Claude Haiku for cost efficiency.

        Returns the response text or None if failed.
        """
        try:
            # Use Claude CLI with haiku model for efficiency
            # cwd must be project root so Claude finds the correct .claude directory
            project_root = find_project_root()
            result = subprocess.run(
                [
                    "claude",
                    "--model", "claude-3-haiku-20240307",
                    "--print",  # Output to stdout instead of interactive
                    prompt,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(project_root) if project_root else None,
                stdin=subprocess.DEVNULL,  # Explicitly close stdin to prevent any waiting
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                log_error(f"Claude call failed: {result.stderr}")
                return None

        except FileNotFoundError:
            log_error("Claude CLI not found")
            return None
        except subprocess.TimeoutExpired:
            log_error("Claude call timed out")
            return None
        except Exception as e:
            log_error(f"Claude call error: {e}")
            return None


# Convenience function for simple retrieval
def get_relevant_learnings(
    agent_name: str,
    task_type: str,
    task_description: str,
    data_dir: Optional[str] = None,
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