"""
Learning model for CMAT RAG system.

Learnings represent persistent knowledge extracted from agent outputs,
user feedback, or code patterns that can be retrieved to inform future tasks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json

from core.utils import get_timestamp, get_datetime_utc


@dataclass
class Learning:
    """
    Represents a piece of persistent knowledge in the RAG system.

    Learnings are extracted from various sources and retrieved during
    task execution to provide relevant context to agents.
    """
    id: str                                  # "learn_" + timestamp
    summary: str                             # 1-2 sentence description
    content: str                             # Full learning content
    tags: list[str] = field(default_factory=list)  # Categories: architecture, testing, python, etc.
    applies_to: list[str] = field(default_factory=list)  # Contexts: implementation, analysis, review
    source_type: str = "user_feedback"       # "agent_output", "user_feedback", "code_pattern"
    source_task_id: Optional[str] = None     # Task that generated this learning
    confidence: float = 0.5                  # 0.0-1.0, how universal vs project-specific
    created: str = field(default_factory=get_timestamp)  # ISO timestamp

    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique learning ID."""
        import random
        timestamp = int(get_datetime_utc().timestamp())
        random_suffix = random.randint(10000, 99999)
        return f"learn_{timestamp}_{random_suffix}"

    @classmethod
    def from_user_input(cls, content: str, tags: Optional[list[str]] = None) -> "Learning":
        """
        Create a Learning from user-provided content.

        Args:
            content: The learning content provided by the user
            tags: Optional tags for categorization

        Returns:
            A new Learning instance
        """
        # Use first sentence as summary, or first 100 chars
        summary = content.split('.')[0] if '.' in content else content[:100]
        if len(summary) > 100:
            summary = summary[:97] + "..."

        return cls(
            id=cls.generate_id(),
            summary=summary,
            content=content,
            tags=tags or [],
            applies_to=["general"],
            source_type="user_feedback",
            confidence=0.8,  # User-provided learnings are typically high confidence
        )

    @classmethod
    def from_claude_extraction(cls, extraction: dict, source_task_id: Optional[str] = None) -> "Learning":
        """
        Create a Learning from Claude's extraction response.

        Args:
            extraction: Dict with keys: summary, tags, applies_to, confidence, content
            source_task_id: ID of the task that generated this learning

        Returns:
            A new Learning instance
        """
        return cls(
            id=cls.generate_id(),
            summary=extraction.get("summary", ""),
            content=extraction.get("content", extraction.get("summary", "")),
            tags=extraction.get("tags", []),
            applies_to=extraction.get("applies_to", []),
            source_type="agent_output",
            source_task_id=source_task_id,
            confidence=extraction.get("confidence", 0.5),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "summary": self.summary,
            "content": self.content,
            "tags": self.tags,
            "applies_to": self.applies_to,
            "source_type": self.source_type,
            "source_task_id": self.source_task_id,
            "confidence": self.confidence,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Learning":
        """Create Learning from dictionary (e.g., loaded from JSON)."""
        return cls(
            id=data["id"],
            summary=data["summary"],
            content=data["content"],
            tags=data.get("tags", []),
            applies_to=data.get("applies_to", []),
            source_type=data.get("source_type", "user_feedback"),
            source_task_id=data.get("source_task_id"),
            confidence=data.get("confidence", 0.5),
            created=data.get("created", get_timestamp()),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Learning":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def matches_tags(self, query_tags: list[str]) -> bool:
        """Check if this learning matches any of the query tags."""
        if not query_tags:
            return True
        return bool(set(self.tags) & set(query_tags))

    def matches_context(self, context: str) -> bool:
        """Check if this learning applies to a given context."""
        if not self.applies_to:
            return True
        return context.lower() in [c.lower() for c in self.applies_to]

    def formatted_for_prompt(self) -> str:
        """Format this learning for inclusion in a prompt."""
        return f"""**Learning**: {self.summary}
Tags: {', '.join(self.tags) if self.tags else 'general'}
Confidence: {self.confidence:.0%}

{self.content}
"""