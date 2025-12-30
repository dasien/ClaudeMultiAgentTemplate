"""
Workflow template data model (v5.0).
Updated to support input/output patterns and status transitions.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class WorkflowStep:
    """Workflow step data model (v5.0)."""
    agent: str
    input: str  # Input file/directory pattern
    required_output: str  # Required output filename
    on_status: Dict[str, Dict[str, any]]  # Status → transition mapping
    description: str

    @staticmethod
    def from_dict(data: dict) -> 'WorkflowStep':
        """Create WorkflowStep from dictionary (v5.0 format only)."""
        return WorkflowStep(
            agent=data.get('agent', ''),
            input=data.get('input', ''),
            required_output=data.get('required_output', ''),
            on_status=data.get('on_status', {}),
            description=data.get('description', '')
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization (v5.0 format)."""
        return {
            'agent': self.agent,
            'input': self.input,
            'required_output': self.required_output,
            'on_status': self.on_status,
            'description': self.description
        }

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

        return transition.get('next_step')

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

        return transition.get('auto_chain', False)

    def get_expected_statuses(self) -> List[str]:
        """
        Get list of expected status codes for this step.

        Returns:
            List of status codes
        """
        return list(self.on_status.keys())


@dataclass
class WorkflowTemplate:
    """Workflow template data model (v5.0)."""
    slug: str  # JSON object key
    name: str  # User-friendly display name
    description: str
    steps: List[WorkflowStep]
    created: Optional[str] = None

    @staticmethod
    def from_dict(slug: str, data: dict) -> 'WorkflowTemplate':
        """Create WorkflowTemplate from dictionary."""
        steps_data = data.get('steps', [])
        steps = [WorkflowStep.from_dict(s) for s in steps_data]

        return WorkflowTemplate(
            slug=slug,
            name=data.get('name', slug),
            description=data.get('description', ''),
            steps=steps,
            created=data.get('created')
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'name': self.name,
            'description': self.description,
            'steps': [s.to_dict() for s in self.steps]
        }
        if self.created:
            result['created'] = self.created
        return result

    def get_step(self, step_index: int) -> Optional[WorkflowStep]:
        """
        Get step by index.

        Args:
            step_index: Step index (0-based)

        Returns:
            WorkflowStep or None if out of range
        """
        if 0 <= step_index < len(self.steps):
            return self.steps[step_index]
        return None

    def get_step_by_agent(self, agent: str) -> Optional[WorkflowStep]:
        """
        Get first step using a specific agent.

        Args:
            agent: Agent name

        Returns:
            WorkflowStep or None if not found
        """
        for step in self.steps:
            if step.agent == agent:
                return step
        return None

    def get_step_index_by_agent(self, agent: str) -> Optional[int]:
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

    def validate_chain(self) -> List[str]:
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
                next_step = transition.get('next_step')
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

    def get_agent_sequence(self) -> List[str]:
        """
        Get ordered list of agents in workflow.

        Returns:
            List of agent names
        """
        return [step.agent for step in self.steps]

    def get_total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.steps)