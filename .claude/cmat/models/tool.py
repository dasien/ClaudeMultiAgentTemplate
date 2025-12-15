"""
Tool model for CMAT agent capabilities.

Represents the Claude Code tools that can be assigned to agents.
"""

from dataclasses import dataclass
import json


@dataclass
class Tool:
    """
    Represents a Claude Code tool that agents can use.

    Tools are defined in .claude/data/tools.json and represent
    the capabilities available to agents during task execution.
    """
    name: str
    display_name: str
    description: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tool":
        """Create Tool from dictionary (e.g., loaded from JSON)."""
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Tool":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))