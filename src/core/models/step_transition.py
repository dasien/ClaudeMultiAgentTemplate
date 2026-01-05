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

    Transitions can be:
    - Completion transitions: auto_chain=True, next_step set - workflow continues
    - Halt transitions: auto_chain=False or next_step=None - workflow stops for intervention

    The auto_start flag controls whether the next task starts immediately:
    - auto_start=True (default): Next task starts automatically after creation
    - auto_start=False: Next task is created but left pending for manual review
    """
    name: str
    next_step: Optional[str]
    auto_chain: bool = True
    auto_start: bool = True  # Whether to auto-start the created task
    description: Optional[str] = None  # Optional description shown to agent

    @property
    def is_halt_status(self) -> bool:
        """Returns True if this transition halts the workflow."""
        return not self.auto_chain or self.next_step is None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "next_step": self.next_step,
            "auto_chain": self.auto_chain,
            "auto_start": self.auto_start,
        }
        if self.description:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "StepTransition":
        """Create StepTransition from dictionary (e.g., loaded from JSON)."""
        return cls(
            name=name,
            next_step=data.get("next_step"),
            auto_chain=data.get("auto_chain", True),
            auto_start=data.get("auto_start", True),  # Default True for backward compatibility
            description=data.get("description"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({self.name: self.to_dict()}, indent=2)