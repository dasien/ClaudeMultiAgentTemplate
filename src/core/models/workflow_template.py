"""
WorkflowTemplate model for CMAT workflow definitions.

Represents a complete workflow template that orchestrates a sequence
of agent steps to accomplish a development task.
"""

from dataclasses import dataclass, field
import json

from .workflow_step import WorkflowStep


@dataclass
class WorkflowTemplate:
    """
    Represents a complete workflow template.

    Workflow templates define sequences of agent steps for common
    development tasks like feature development, bug fixes, or refactoring.
    """
    id: str
    name: str
    description: str
    steps: list[WorkflowStep] = field(default_factory=list)

    def get_step(self, index: int) -> WorkflowStep | None:
        """Get a step by index."""
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    def get_step_by_agent(self, agent_name: str) -> WorkflowStep | None:
        """Get the first step assigned to a specific agent."""
        for step in self.steps:
            if step.agent == agent_name:
                return step
        return None

    def get_agent_sequence(self) -> list[str]:
        """Get the ordered list of agents in this workflow."""
        return [step.agent for step in self.steps]

    def get_step_index_by_agent(self, agent: str) -> int | None:
        """
        Get step index for a specific agent.

        Args:
            agent: Agent name

        Returns:
            Step index (0-based) or None if not found
        """
        for i, step in enumerate(self.steps):
            if step.agent == agent:
                return i
        return None

    def get_total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.steps)

    def validate_chain(self) -> list[str]:
        """
        Validate workflow chain continuity.

        Returns:
            List of validation messages (empty if valid)
        """
        issues = []

        if not self.steps:
            issues.append("Workflow has no steps")
            return issues

        for i, step in enumerate(self.steps):
            # Check if step has transitions defined
            if not step.on_status:
                issues.append(f"Step {i} ({step.agent}): No status transitions defined")

            # Check next step references
            for status, transition in step.on_status.items():
                next_step = transition.next_step
                if next_step and next_step != 'null':
                    # Verify next agent exists in workflow
                    if not self.get_step_by_agent(next_step):
                        issues.append(
                            f"Step {i} ({step.agent}): References non-existent agent '{next_step}' "
                            f"in status '{status}'"
                        )

            # Check input/output chain
            if i > 0:
                prev_step = self.steps[i - 1]
                # Check if current input references previous step
                if '{previous_step}' in step.input:
                    # Good - uses previous step output
                    pass
                elif prev_step.agent in step.input:
                    # Good - explicitly references previous agent
                    pass
                else:
                    issues.append(
                        f"Step {i} ({step.agent}): Input doesn't reference previous step output"
                    )

        return issues

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, workflow_id: str, data: dict) -> "WorkflowTemplate":
        """Create WorkflowTemplate from dictionary (e.g., loaded from JSON)."""
        steps = [WorkflowStep.from_dict(step_data) for step_data in data.get("steps", [])]

        return cls(
            id=workflow_id,
            name=data["name"],
            description=data["description"],
            steps=steps,
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({self.id: self.to_dict()}, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowTemplate":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        workflow_id = list(data.keys())[0]
        return cls.from_dict(workflow_id, data[workflow_id])