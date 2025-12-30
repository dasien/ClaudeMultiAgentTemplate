"""
Workflow service for CMAT workflow orchestration.

Handles loading workflow templates, managing workflow execution,
and coordinating agent steps.
"""

import json
import re
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from core.models.workflow_template import WorkflowTemplate
from core.models.workflow_step import WorkflowStep
from core.models.enhancement import Enhancement
from core.utils import log_operation, log_error

if TYPE_CHECKING:
    from core.services.queue_service import QueueService
    from core.services.task_service import TaskService
    from core.services.agent_service import AgentService


class WorkflowService:
    """
    Manages workflow templates and orchestration for CMAT.

    Provides operations for loading templates, resolving input/output paths,
    and managing workflow execution state.
    """

    def __init__(
            self,
            templates_file: str = ".claude/data/workflow_templates.json",
            enhancements_dir: str = "enhancements"
    ):
        self.templates_file = Path(templates_file)
        self.enhancements_dir = Path(enhancements_dir)

        # Services injected via set_services()
        self._queue_service: Optional["QueueService"] = None
        self._task_service: Optional["TaskService"] = None
        self._agent_service: Optional["AgentService"] = None

    def _load_templates(self) -> dict[str, WorkflowTemplate]:
        """Load all workflow templates."""
        if not self.templates_file.exists():
            return {}

        with open(self.templates_file, 'r') as f:
            data = json.load(f)

        templates = {}
        for workflow_id, workflow_data in data.get("workflows", {}).items():
            template = WorkflowTemplate.from_dict(workflow_id, workflow_data)
            templates[workflow_id] = template

        return templates

    def _save_templates(self, templates: dict[str, WorkflowTemplate]) -> None:
        """Save all workflow templates."""
        data = {
            "version": "2.0.0",
            "description": "Workflow templates with input/output specifications and status transitions",
            "workflows": {wf_id: wf.to_dict() for wf_id, wf in templates.items()}
        }

        self.templates_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.templates_file, 'w') as f:
            json.dump(data, f, indent=2)

    def list_all(self) -> list[WorkflowTemplate]:
        """List all available workflow templates."""
        return list(self._load_templates().values())

    def get(self, workflow_id: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by ID."""
        return self._load_templates().get(workflow_id)

    def add(self, template: WorkflowTemplate) -> WorkflowTemplate:
        """Add a new workflow template."""
        templates = self._load_templates()
        templates[template.id] = template
        self._save_templates(templates)
        return template

    def update(self, template: WorkflowTemplate) -> Optional[WorkflowTemplate]:
        """Update an existing workflow template."""
        templates = self._load_templates()
        if template.id not in templates:
            return None

        templates[template.id] = template
        self._save_templates(templates)
        return template

    def delete(self, workflow_id: str) -> bool:
        """Delete a workflow template."""
        templates = self._load_templates()
        if workflow_id not in templates:
            return False

        del templates[workflow_id]
        self._save_templates(templates)
        return True

    def add_step(self, workflow_id: str, step: WorkflowStep, index: Optional[int] = None) -> Optional[WorkflowTemplate]:
        """
        Add a step to a workflow template.

        Args:
            workflow_id: ID of the workflow to modify
            step: The WorkflowStep to add
            index: Optional position to insert at (appends if not specified)

        Returns:
            Updated WorkflowTemplate or None if workflow not found.
        """
        templates = self._load_templates()
        if workflow_id not in templates:
            return None

        template = templates[workflow_id]
        if index is not None and 0 <= index <= len(template.steps):
            template.steps.insert(index, step)
        else:
            template.steps.append(step)

        self._save_templates(templates)
        return template

    def remove_step(self, workflow_id: str, step_index: int) -> Optional[WorkflowTemplate]:
        """
        Remove a step from a workflow template.

        Args:
            workflow_id: ID of the workflow to modify
            step_index: Index of the step to remove

        Returns:
            Updated WorkflowTemplate or None if workflow/step not found.
        """
        templates = self._load_templates()
        if workflow_id not in templates:
            return None

        template = templates[workflow_id]
        if step_index < 0 or step_index >= len(template.steps):
            return None

        template.steps.pop(step_index)
        self._save_templates(templates)
        return template

    def add_transition(
        self,
        workflow_id: str,
        step_index: int,
        status: str,
        transition: "StatusTransition",
    ) -> Optional[WorkflowTemplate]:
        """
        Add or update a status transition for a workflow step.

        Args:
            workflow_id: ID of the workflow to modify
            step_index: Index of the step to modify
            status: Status name (e.g., "READY_FOR_DEVELOPMENT")
            transition: StatusTransition object defining the transition

        Returns:
            Updated WorkflowTemplate or None if workflow/step not found.
        """
        from core.models.status_transition import StatusTransition

        templates = self._load_templates()
        if workflow_id not in templates:
            return None

        template = templates[workflow_id]
        step = template.get_step(step_index)
        if not step:
            return None

        step.on_status[status] = transition
        self._save_templates(templates)
        return template

    def remove_transition(
        self,
        workflow_id: str,
        step_index: int,
        status: str,
    ) -> Optional[WorkflowTemplate]:
        """
        Remove a status transition from a workflow step.

        Args:
            workflow_id: ID of the workflow to modify
            step_index: Index of the step to modify
            status: Status name to remove

        Returns:
            Updated WorkflowTemplate or None if workflow/step/status not found.
        """
        templates = self._load_templates()
        if workflow_id not in templates:
            return None

        template = templates[workflow_id]
        step = template.get_step(step_index)
        if not step or status not in step.on_status:
            return None

        del step.on_status[status]
        self._save_templates(templates)
        return template

    def resolve_input_path(
            self,
            step: WorkflowStep,
            enhancement_name: str,
            previous_agent: Optional[str] = None
    ) -> str:
        """
        Resolve the input path for a workflow step.

        Handles template variables like {enhancement_name} and {previous_step}.
        """
        input_path = step.input

        # Replace enhancement name
        input_path = input_path.replace("{enhancement_name}", enhancement_name)

        # Replace previous step reference
        if "{previous_step}" in input_path and previous_agent:
            input_path = input_path.replace(
                "{previous_step}",
                f"enhancements/{enhancement_name}/{previous_agent}"
            )

        return input_path

    def resolve_output_path(
            self,
            step: WorkflowStep,
            enhancement_name: str
    ) -> str:
        """
        Resolve the output directory for a workflow step.

        Returns the path where the agent should write its required output.
        """
        return f"enhancements/{enhancement_name}/{step.agent}/required_output/{step.required_output}"

    def get_step_at_index(
            self,
            workflow_id: str,
            step_index: int
    ) -> Optional[WorkflowStep]:
        """Get a specific step from a workflow by index."""
        template = self.get(workflow_id)
        if not template:
            return None
        return template.get_step(step_index)

    def format_statuses_for_prompt(self, step: WorkflowStep) -> str:
        """
        Format the step's status transitions for inclusion in agent prompts.

        Separates statuses into completion (workflow continues) and halt
        (requires intervention) groups based on auto_chain and next_step.

        Args:
            step: The WorkflowStep to format statuses for

        Returns:
            Formatted string with completion and halt status sections
        """
        completion_statuses = []
        halt_statuses = []

        for status_name, transition in step.on_status.items():
            if transition.is_halt_status:
                # Halt status - include description if available
                if transition.description:
                    halt_statuses.append(f"- `{status_name}` - {transition.description}")
                else:
                    # Default descriptions for common halt patterns
                    halt_statuses.append(f"- `{status_name}`")
            else:
                # Completion status
                completion_statuses.append(f"- `{status_name}`")

        sections = []

        if completion_statuses:
            sections.append(
                "**Completion Statuses (workflow continues automatically):**\n"
                + "\n".join(completion_statuses)
            )

        if halt_statuses:
            sections.append(
                "**Halt Statuses (stops workflow, requires human intervention):**\n"
                + "\n".join(halt_statuses)
            )

        if not sections:
            return "(No workflow-defined statuses)"

        result = "\n\n".join(sections)
        result += "\n\nChoose a completion status if your work is successful. Choose a halt status if you encountered an issue that prevents progression."

        return result

    def get_next_step(
            self,
            workflow_id: str,
            current_step_index: int,
            status: str
    ) -> Optional[tuple[int, WorkflowStep]]:
        """
        Get the next step based on current step's status transition.

        Returns tuple of (step_index, WorkflowStep) or None if no next step.
        """
        template = self.get(workflow_id)
        if not template:
            return None

        current_step = template.get_step(current_step_index)
        if not current_step:
            return None

        transition = current_step.get_transition(status)
        if not transition or not transition.next_step:
            return None

        # Find the step with the matching agent
        for i, step in enumerate(template.steps):
            if step.agent == transition.next_step:
                return (i, step)

        return None

    def should_auto_chain(
            self,
            workflow_id: str,
            step_index: int,
            status: str
    ) -> bool:
        """Check if the workflow should automatically chain to the next step."""
        template = self.get(workflow_id)
        if not template:
            return False

        step = template.get_step(step_index)
        if not step:
            return False

        transition = step.get_transition(status)
        if not transition:
            return False

        return transition.auto_chain

    def validate_template(self, template: WorkflowTemplate) -> list[str]:
        """
        Validate a workflow template.

        Returns a list of validation errors (empty if valid).
        """
        errors = []

        if not template.id:
            errors.append("Workflow ID is required")

        if not template.name:
            errors.append("Workflow name is required")

        if not template.steps:
            errors.append("Workflow must have at least one step")

        # Validate each step
        agent_names = set()
        for i, step in enumerate(template.steps):
            if not step.agent:
                errors.append(f"Step {i}: agent is required")
            else:
                agent_names.add(step.agent)

            if not step.input:
                errors.append(f"Step {i}: input is required")

            if not step.required_output:
                errors.append(f"Step {i}: required_output is required")

            # Validate transitions reference valid agents
            for status_name, transition in step.on_status.items():
                if transition.next_step and transition.next_step not in agent_names:
                    # Check if it's a forward reference
                    found = False
                    for future_step in template.steps[i + 1:]:
                        if future_step.agent == transition.next_step:
                            found = True
                            break
                    if not found:
                        errors.append(
                            f"Step {i}: transition '{status_name}' references "
                            f"unknown agent '{transition.next_step}'"
                        )

        return errors

    def get_enhancement(self, enhancement_name: str) -> Enhancement:
        """Get an Enhancement object for the given name."""
        return Enhancement.from_name(enhancement_name, str(self.enhancements_dir))

    def list_enhancements(self) -> list[Enhancement]:
        """List all enhancements in the enhancements directory."""
        if not self.enhancements_dir.exists():
            return []

        enhancements = []
        for path in self.enhancements_dir.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                enhancement = Enhancement.from_path(path)
                if enhancement.exists:
                    enhancements.append(enhancement)

        return enhancements

    # =========================================================================
    # Orchestration Methods
    # =========================================================================

    def set_services(
        self,
        queue: Optional["QueueService"] = None,
        task: Optional["TaskService"] = None,
        agent: Optional["AgentService"] = None,
    ) -> None:
        """Inject service dependencies for orchestration."""
        self._queue_service = queue
        self._task_service = task
        self._agent_service = agent

    def get_task_type_for_agent(self, agent_name: str) -> str:
        """
        Map agent role to task type.

        Returns appropriate task type based on agent's role.
        """
        if not self._agent_service:
            return "analysis"  # default

        agent = self._agent_service.get(agent_name)
        if not agent:
            return "analysis"

        # Map roles to task types
        role_map = {
            "analyst": "analysis",
            "requirements-analyst": "analysis",
            "product-analyst": "analysis",
            "architect": "technical_analysis",
            "implementer": "implementation",
            "tester": "testing",
            "documenter": "documentation",
            "integration": "integration",
        }

        return role_map.get(agent.role.lower(), "analysis")

    def validate_agent_outputs(
        self,
        agent_name: str,
        enhancement_dir: str,
        required_output: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that agent produced required output with metadata.

        Returns (is_valid, error_message).
        """
        output_path = Path(enhancement_dir) / agent_name / "required_output" / required_output

        if not output_path.exists():
            return False, f"Required output not found: {output_path}"

        # Check for metadata header
        content = output_path.read_text()
        if not content.startswith("---"):
            return False, f"Output missing metadata header: {output_path}"

        # Extract and validate metadata
        metadata_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not metadata_match:
            return False, f"Invalid metadata format: {output_path}"

        metadata_text = metadata_match.group(1)
        required_fields = ["enhancement", "agent", "task_id", "timestamp", "status"]

        for field in required_fields:
            if f"{field}:" not in metadata_text:
                return False, f"Missing metadata field '{field}' in: {output_path}"

        return True, None

    def start_workflow(
        self,
        workflow_name: str,
        enhancement_name: str,
        description: str = "",
        auto_chain: bool = True,
        execute: bool = True,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Start a workflow by creating the first task and executing it.

        Args:
            workflow_name: Name of the workflow template
            enhancement_name: Name of the enhancement to process
            description: Optional task description
            auto_chain: Whether to auto-chain to next steps
            execute: Whether to execute the task (True) or just create it (False)
            model: Optional model override for first step (e.g., "claude-sonnet-4-20250514")

        Returns the task ID or None if workflow not found.
        """
        if not self._queue_service or not self._agent_service:
            log_error("Cannot start workflow: services not configured")
            return None

        template = self.get(workflow_name)
        if not template:
            log_error(f"Workflow not found: {workflow_name}")
            return None

        if not template.steps:
            log_error(f"Workflow has no steps: {workflow_name}")
            return None

        first_step = template.steps[0]
        agent = self._agent_service.get(first_step.agent)
        if not agent:
            log_error(f"Agent not found: {first_step.agent}")
            return None

        # Resolve input path
        input_path = self.resolve_input_path(first_step, enhancement_name)

        # Determine task type from agent role
        task_type = self.get_task_type_for_agent(first_step.agent)

        # Use CLI override if provided, otherwise step's configured model
        effective_model = model or first_step.model

        # Create task (in pending state)
        task = self._queue_service.add(
            title=f"{workflow_name}: {first_step.agent}",
            assigned_agent=first_step.agent,
            priority="normal",
            task_type=task_type,
            source_file=input_path,
            description=description or f"Execute {first_step.agent} for {enhancement_name}",
            metadata={
                "workflow_name": workflow_name,
                "workflow_step": 0,
                "enhancement_title": enhancement_name,
                "requested_model": effective_model,
            },
            auto_complete=True,
            auto_chain=auto_chain,
        )

        log_operation(
            "WORKFLOW_STARTED",
            f"Workflow: {workflow_name}, Enhancement: {enhancement_name}, Task: {task.id}"
        )

        # Execute the task if requested (run_task handles start + execute)
        if execute:
            self.run_task(task.id)

        return task.id

    def auto_chain(self, task_id: str, status: str) -> Optional[str]:
        """
        Chain to next workflow step based on task completion status.

        Auto-chain logic:
        1. Check if task.auto_chain is True
        2. Look up transition for status
        3. If transition.next_step is null -> workflow complete
        4. If transition.auto_chain is False -> stop (manual intervention)
        5. Otherwise create next task and return its ID

        Returns next task ID, or None if no chaining.
        """
        if not self._queue_service or not self._agent_service:
            return None

        task = self._queue_service.get(task_id)
        if not task:
            return None

        # Check if auto_chain enabled on task
        if not task.auto_chain:
            log_operation("AUTO_CHAIN_SKIP", f"Task {task_id}: auto_chain disabled")
            return None

        # Get workflow context from metadata
        workflow_name = task.metadata.workflow_name
        step_index = task.metadata.workflow_step
        enhancement_name = task.metadata.enhancement_title

        if not workflow_name or step_index is None:
            return None

        # Check if workflow should auto-chain for this status
        if not self.should_auto_chain(workflow_name, int(step_index), status):
            log_operation(
                "AUTO_CHAIN_STOP",
                f"Task {task_id}: transition for '{status}' has auto_chain=false"
            )
            return None

        # Get next step
        next_step_info = self.get_next_step(workflow_name, int(step_index), status)
        if not next_step_info:
            log_operation(
                "WORKFLOW_COMPLETE",
                f"Workflow {workflow_name} completed at step {step_index} with status {status}"
            )
            return None

        next_step_index, next_step = next_step_info

        # Get previous agent for input resolution
        template = self.get(workflow_name)
        current_step = template.get_step(int(step_index))
        previous_agent = current_step.agent if current_step else None

        # Resolve input path for next step
        input_path = self.resolve_input_path(next_step, enhancement_name, previous_agent)

        # Determine task type
        task_type = self.get_task_type_for_agent(next_step.agent)

        # Create next task (in pending state)
        next_task = self._queue_service.add(
            title=f"{workflow_name}: {next_step.agent}",
            assigned_agent=next_step.agent,
            priority="normal",
            task_type=task_type,
            source_file=input_path,
            description=f"Execute {next_step.agent} for {enhancement_name}",
            metadata={
                "workflow_name": workflow_name,
                "workflow_step": next_step_index,
                "enhancement_title": enhancement_name,
                "requested_model": next_step.model,
            },
            auto_complete=True,
            auto_chain=task.auto_chain,  # Inherit from previous task
        )

        log_operation(
            "AUTO_CHAIN",
            f"Chained from {task_id} to {next_task.id} ({next_step.agent})"
        )

        # Execute the chained task (run_task handles start + execute)
        self.run_task(next_task.id)

        return next_task.id

    def run_task(self, task_id: str) -> Optional[str]:
        """
        Run a task through its full lifecycle.

        Orchestrates: start -> execute -> complete/fail -> auto_chain

        Returns the completion status, or None if task not found.
        """
        if not self._queue_service or not self._task_service or not self._agent_service:
            log_error("Cannot run task: services not configured")
            return None

        # Get task
        task = self._queue_service.get(task_id)
        if not task:
            log_error(f"Task not found: {task_id}")
            return None

        # Get agent
        agent = self._agent_service.get(task.assigned_agent)
        if not agent:
            log_error(f"Agent not found: {task.assigned_agent}")
            return None

        # Start task
        started_task = self._queue_service.start(task_id)
        if not started_task:
            log_error(f"Failed to start task: {task_id}")
            return None

        # Get workflow context for expected statuses
        workflow_name = task.metadata.workflow_name
        step_index = task.metadata.workflow_step
        expected_statuses = "(No workflow-defined statuses)"
        required_output = "output.md"

        if workflow_name and step_index is not None:
            step = self.get_step_at_index(workflow_name, int(step_index))
            if step:
                # Build expected statuses string with completion/halt grouping
                expected_statuses = self.format_statuses_for_prompt(step)
                required_output = step.required_output or required_output

        # Execute task
        result = self._task_service.execute(
            task=started_task,
            agent=agent,
            workflow_name=workflow_name,
            workflow_step=int(step_index) if step_index is not None else None,
            expected_statuses=expected_statuses,
            required_output_filename=required_output,
        )

        # Store log file path in task metadata
        if result.log_file:
            self._queue_service.update_metadata(task_id, {"log_file_path": result.log_file})

        # Complete or fail based on result
        if result.success and result.status:
            self._queue_service.complete(task_id, result.status)

            # Auto-chain if configured
            if task.auto_chain:
                self.auto_chain(task_id, result.status)
        else:
            reason = result.status or f"Execution failed with exit code {result.exit_code}"
            self._queue_service.fail(task_id, reason)

        return result.status