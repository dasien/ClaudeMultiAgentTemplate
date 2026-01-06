"""
WorkflowStep model for CMAT workflow definitions.

Represents a single step in a workflow, defining which agent executes,
what input it receives, what output is required, and status transitions.
"""

from dataclasses import dataclass, field
import json
from typing import Optional

from .step_transition import StepTransition


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.

    Each step specifies the agent to execute, input/output paths,
    and status transitions that determine workflow progression.
    """
    agent: str
    input: str
    required_output: str
    on_status: dict[str, StepTransition] = field(default_factory=dict)
    model: Optional[str] = None  # Claude model to use (e.g., "claude-sonnet-4-20250514")

    def get_transition(self, status_name: str) -> StepTransition | None:
        """Get a transition by status name."""
        return self.on_status.get(status_name)

    def get_next_step_for_status(self, status: str) -> Optional[str]:
        """
        Get next step agent for a given status.

        Args:
            status: Status code (e.g., 'READY_FOR_DEVELOPMENT')

        Returns:
            Next agent name or None if workflow ends
        """
        transition = self.on_status.get(status)
        if not transition:
            return None
        return transition.next_step

    def should_auto_chain(self, status: str) -> bool:
        """
        Check if status should trigger auto-chain.

        Args:
            status: Status code

        Returns:
            True if should auto-chain, False otherwise
        """
        transition = self.on_status.get(status)
        if not transition:
            return False
        return transition.auto_chain

    def get_expected_statuses(self) -> list[str]:
        """
        Get list of expected status codes for this step.

        Returns:
            List of status codes
        """
        return list(self.on_status.keys())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "agent": self.agent,
            "input": self.input,
            "required_output": self.required_output,
            "on_status": {name: transition.to_dict() for name, transition in self.on_status.items()},
        }
        if self.model:
            result["model"] = self.model
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowStep":
        """Create WorkflowStep from dictionary (e.g., loaded from JSON)."""
        on_status = {}
        for name, transition_data in data.get("on_status", {}).items():
            on_status[name] = StepTransition.from_dict(name, transition_data)

        return cls(
            agent=data["agent"],
            input=data["input"],
            required_output=data["required_output"],
            on_status=on_status,
            model=data.get("model"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowStep":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))