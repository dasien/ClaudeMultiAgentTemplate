"""
WorkflowStep model for CMAT workflow definitions.

Represents a single step in a workflow, defining which agent executes,
what input it receives, what output is required, and status transitions.
"""

from dataclasses import dataclass, field
import json

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

    def get_transition(self, status_name: str) -> StepTransition | None:
        """Get a transition by status name."""
        return self.on_status.get(status_name)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "agent": self.agent,
            "input": self.input,
            "required_output": self.required_output,
            "on_status": {name: transition.to_dict() for name, transition in self.on_status.items()},
        }

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
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowStep":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))