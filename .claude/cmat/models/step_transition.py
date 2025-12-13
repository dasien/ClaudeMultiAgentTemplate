"""
StepTransition model for CMAT workflow transitions.

Represents a transition that determines what happens after
an agent completes a workflow step with a given status.
"""

from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class StepTransition:
    """
    Represents a transition triggered by an agent's output status.

    When an agent outputs a status matching the name, the workflow
    engine uses this to determine the next step and whether to
    automatically chain to it.
    """
    name: str
    next_step: Optional[str]
    auto_chain: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "next_step": self.next_step,
            "auto_chain": self.auto_chain,
        }

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "StepTransition":
        """Create StepTransition from dictionary (e.g., loaded from JSON)."""
        return cls(
            name=name,
            next_step=data.get("next_step"),
            auto_chain=data.get("auto_chain", True),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({self.name: self.to_dict()}, indent=2)