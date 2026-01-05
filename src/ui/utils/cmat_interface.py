"""
CMAT interface for communicating with CMAT services directly.
Version 10.0 - Direct service integration with unified package structure.
"""

import threading
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..models import Task, QueueState

# Import core services directly (same package)
from core.utils import set_project_root
from core.services.queue_service import QueueService
from core.services.agent_service import AgentService
from core.services.skills_service import SkillsService
from core.services.workflow_service import WorkflowService
from core.services.task_service import TaskService
from core.services.learnings_service import LearningsService
from core.services.model_service import ModelService
from core.services.tools_service import ToolsService


class CMATInterface:
    """Direct Python interface to CMAT services."""

    def __init__(self, project_root: str):
        """Initialize the CMAT interface.

        Args:
            project_root: Path to project root directory (contains .claude/)
        """
        self.project_root = Path(project_root)

        # Validate project structure
        claude_dir = self.project_root / ".claude"
        if not claude_dir.exists():
            raise FileNotFoundError(f"No .claude directory found in {self.project_root}")

        # 1. FIRST - Set global project root
        #    This ensures log_operation() and other utils work correctly
        set_project_root(self.project_root)

        # 2. Derive all paths from project root
        data_dir = claude_dir / "data"
        agents_dir = claude_dir / "agents"
        skills_dir = claude_dir / "skills"
        logs_dir = claude_dir / "logs"
        enhancements_dir = self.project_root / "enhancements"

        # Ensure directories exist
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = logs_dir

        # 3. Create services with EXPLICIT paths
        self._queue_file = data_dir / "task_queue.json"
        self.queue = QueueService(
            queue_file=str(self._queue_file)
        )

        self.agents = AgentService(
            agents_dir=str(agents_dir)
        )

        self.skills = SkillsService(
            skills_dir=str(skills_dir)
        )

        self.workflow = WorkflowService(
            templates_file=str(data_dir / "workflow_templates.json"),
            enhancements_dir=str(enhancements_dir)
        )

        self.tasks = TaskService(
            templates_file=str(data_dir / "TASK_PROMPT_DEFAULTS.md"),
            agents_dir=str(agents_dir),
            logs_dir=str(logs_dir),
            enhancements_dir=str(enhancements_dir),
        )

        self.learnings = LearningsService(
            data_dir=str(data_dir)
        )

        self.models = ModelService(
            data_dir=str(data_dir)
        )

        self.tools = ToolsService(
            data_dir=str(data_dir)
        )

        # 4. Wire service dependencies
        self._wire_services()

    def _wire_services(self):
        """Wire service dependencies. Called once during initialization."""
        # TaskService needs 5 services for full functionality
        self.tasks.set_services(
            agent=self.agents,
            skills=self.skills,
            queue=self.queue,
            learnings=self.learnings,
            models=self.models,
        )

        # WorkflowService needs queue, task, and agent for orchestration
        self.workflow.set_services(
            queue=self.queue,
            task=self.tasks,
            agent=self.agents,
        )

        # QueueService needs task service for prompt previewing
        self.queue.set_services(
            task_service=self.tasks,
        )

    @property
    def queue_file(self) -> Path:
        """Get the path to the task queue file."""
        return self._queue_file

    # =========================================================================
    # QUEUE COMMANDS
    # =========================================================================

    def add_task(self, title: str, agent: str, priority: str,
                 task_type: str, source_file: str, description: str,
                 auto_complete: bool = False, auto_chain: bool = False,
                 model: Optional[str] = None) -> str:
        """Add a new task to the queue.

        Args:
            model: Optional Claude model ID to use (e.g., "claude-sonnet-4-20250514").
                   If None, uses the project's default model.
        """
        task = self.queue.add(
            title=title,
            assigned_agent=agent,
            priority=priority,
            task_type=task_type,
            source_file=source_file,
            description=description,
            auto_complete=auto_complete,
            auto_chain=auto_chain,
            model=model,
        )
        return task.id

    def start_task(self, task_id: str):
        """Start a task asynchronously."""
        def execute():
            try:
                self.workflow.run_task(task_id)
            except Exception as e:
                print(f"Error executing task {task_id}: {e}")

        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        return None  # UI doesn't actually use the process handle

    def complete_task(self, task_id: str, result: str = "", auto_chain: bool = False):
        """Complete a task."""
        self.queue.complete(task_id, result=result)
        if auto_chain:
            # Trigger workflow auto-chain if applicable
            task = self.queue.get(task_id)
            if task and task.metadata and task.metadata.workflow_name:
                self.workflow.handle_completion(task)

    def cancel_task(self, task_id: str, reason: str = ""):
        """Cancel a task."""
        self.queue.cancel(task_id, reason=reason)

    def rerun_task(self, task_id: str):
        """Re-run a completed or failed task."""
        self.queue.rerun(task_id)

    def cancel_all_tasks(self, reason: str = ""):
        """Cancel all pending and active tasks."""
        tasks = self.queue.list_tasks()  # Get all tasks
        for task in tasks:
            if task.status.value in ['pending', 'active']:
                self.queue.cancel(task.id, reason=reason)

    def clear_tasks(self, task_ids: List[str]) -> int:
        """Remove specific tasks from the queue by ID.

        Args:
            task_ids: List of task IDs to remove.

        Returns:
            Count of tasks actually removed.
        """
        return self.queue.clear_tasks(task_ids)

    def clear_finished_tasks(self):
        """Clear all completed and failed tasks from history."""
        queue_state = self.get_queue_state()
        task_ids = [t.id for t in queue_state.completed_tasks + queue_state.failed_tasks]
        if task_ids:
            self.clear_tasks(task_ids)

    def clear_cancelled_tasks(self):
        """Clear all cancelled tasks from the queue."""
        queue_state = self.get_queue_state()
        task_ids = [t.id for t in queue_state.cancelled_tasks]
        if task_ids:
            self.clear_tasks(task_ids)

    def reset_queue(self):
        """Reset the entire queue system to empty state."""
        self.queue.init(force=True)

    def fail_task(self, task_id: str, error: str = ""):
        """Fail a task."""
        self.queue.fail(task_id, error=error)

    def update_metadata(self, task_id: str, key: str, value: str):
        """Update task metadata."""
        self.queue.update_metadata(task_id, {key: value})

    def get_queue_state(self) -> QueueState:
        """Get current queue state."""
        all_tasks = self.queue.list_tasks()  # Get all tasks regardless of status

        def convert_task(cmat_task) -> Task:
            """Convert CMAT Task model to UI Task model."""
            start_datetime = None
            end_datetime = None
            runtime_seconds = None

            # CMAT v8.2+ uses datetime objects, not strings
            if cmat_task.started:
                try:
                    if isinstance(cmat_task.started, datetime):
                        start_datetime = int(cmat_task.started.timestamp())
                    else:
                        # Fallback for string format
                        start_dt = datetime.fromisoformat(str(cmat_task.started).replace('Z', '+00:00'))
                        start_datetime = int(start_dt.timestamp())
                except (ValueError, AttributeError, TypeError):
                    pass

            if cmat_task.completed:
                try:
                    if isinstance(cmat_task.completed, datetime):
                        end_datetime = int(cmat_task.completed.timestamp())
                    else:
                        # Fallback for string format
                        end_dt = datetime.fromisoformat(str(cmat_task.completed).replace('Z', '+00:00'))
                        end_datetime = int(end_dt.timestamp())
                except (ValueError, AttributeError, TypeError):
                    pass

            # CMAT v8.2+ uses get_duration_seconds() method
            try:
                runtime_seconds = cmat_task.get_duration_seconds()
            except (AttributeError, TypeError):
                # Fallback to direct attribute if method doesn't exist
                runtime_seconds = getattr(cmat_task, 'runtime_seconds', None)

            # Convert metadata
            metadata_dict = None
            if cmat_task.metadata:
                metadata_dict = cmat_task.metadata.to_dict()

            # Convert datetime objects to ISO strings for UI
            created_str = cmat_task.created.isoformat() if isinstance(cmat_task.created, datetime) else cmat_task.created
            started_str = cmat_task.started.isoformat() if isinstance(cmat_task.started, datetime) else cmat_task.started
            completed_str = cmat_task.completed.isoformat() if isinstance(cmat_task.completed, datetime) else cmat_task.completed

            return Task(
                id=cmat_task.id,
                title=cmat_task.title,
                assigned_agent=cmat_task.assigned_agent,
                priority=cmat_task.priority.value if hasattr(cmat_task.priority, 'value') else cmat_task.priority,
                task_type=cmat_task.task_type,
                description=cmat_task.description,
                source_file=cmat_task.source_file,
                created=created_str,
                status=cmat_task.status.value if hasattr(cmat_task.status, 'value') else cmat_task.status,
                started=started_str,
                completed=completed_str,
                result=cmat_task.result,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                runtime_seconds=runtime_seconds,
                auto_complete=cmat_task.auto_complete,
                auto_chain=cmat_task.auto_chain,
                metadata=metadata_dict
            )

        ui_tasks = [convert_task(t) for t in all_tasks]

        return QueueState(
            pending_tasks=[t for t in ui_tasks if t.status == 'pending'],
            active_workflows=[t for t in ui_tasks if t.status == 'active'],
            completed_tasks=[t for t in ui_tasks if t.status == 'completed'],
            failed_tasks=[t for t in ui_tasks if t.status == 'failed'],
            cancelled_tasks=[t for t in ui_tasks if t.status == 'cancelled'],
            agent_status={}
        )

    # =========================================================================
    # WORKFLOW COMMANDS
    # =========================================================================

    def start_workflow(self, workflow_name: str, enhancement_name: str,
                       model: Optional[str] = None):
        """Start a workflow.

        Args:
            model: Optional Claude model ID override for workflow execution.
                   If None, uses model configured in workflow steps or project default.
        """
        # Create task but don't execute yet (execute=False)
        # UI handles async execution in its own thread
        task_id = self.workflow.start_workflow(
            workflow_name, enhancement_name,
            model=model,
            execute=False
        )

        # Execute first task asynchronously
        def execute():
            try:
                self.workflow.run_task(task_id)
            except Exception as e:
                print(f"Error starting workflow {workflow_name}: {e}")

        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        return task_id

    def get_workflow_templates(self) -> List:
        """Get all workflow templates."""
        from ..models import WorkflowTemplate

        templates = self.workflow.list_all()

        # Convert CMAT workflow models to UI models
        ui_templates = []
        for cmat_template in templates:
            ui_template = WorkflowTemplate.from_dict(
                cmat_template.id,
                {
                    'name': cmat_template.name,
                    'description': cmat_template.description,
                    'steps': [
                        {
                            'agent': step.agent,
                            'input': step.input,
                            'required_output': step.required_output,
                            'model': step.model,
                            'on_status': {
                                status: trans.to_dict()
                                for status, trans in (step.on_status or {}).items()
                            }
                        }
                        for step in cmat_template.steps
                    ]
                }
            )
            ui_templates.append(ui_template)

        return ui_templates

    def get_workflow_template(self, slug: str):
        """Get a specific workflow template by slug."""
        from ..models import WorkflowTemplate

        cmat_template = self.workflow.get(slug)
        if not cmat_template:
            return None

        return WorkflowTemplate.from_dict(
            cmat_template.id,
            {
                'name': cmat_template.name,
                'description': cmat_template.description,
                'steps': [
                    {
                        'agent': step.agent,
                        'input': step.input,
                        'required_output': step.required_output,
                        'model': step.model,
                        'on_status': {
                            status: trans.to_dict()
                            for status, trans in (step.on_status or {}).items()
                        }
                    }
                    for step in cmat_template.steps
                ]
            }
        )

    def get_workflow_step_details(self, workflow_name: str, step_index: int) -> Optional[Dict]:
        """Get details for a specific workflow step."""
        # Ensure step_index is an integer (may come from metadata as string)
        if isinstance(step_index, str):
            step_index = int(step_index)

        template = self.workflow.get(workflow_name)
        if not template or step_index >= len(template.steps):
            return None

        step = template.steps[step_index]
        return {
            'agent': step.agent,
            'input': step.input,
            'required_output': step.required_output,
            'on_status': {
                status: {
                    'next_step': trans.next_step,
                    'auto_chain': trans.auto_chain
                }
                for status, trans in (step.on_status or {}).items()
            }
        }

    def get_step_expected_statuses(self, workflow_name: str, step_index: int) -> List[str]:
        """Get expected status codes for a workflow step."""
        step_details = self.get_workflow_step_details(workflow_name, step_index)
        if not step_details:
            return []
        return list(step_details.get('on_status', {}).keys())

    def get_step_input_path(self, workflow_name: str, step_index: int,
                            enhancement_name: str) -> Optional[str]:
        """Get resolved input path for a workflow step."""
        step_details = self.get_workflow_step_details(workflow_name, step_index)
        if not step_details:
            return None

        input_pattern = step_details['input']
        resolved = input_pattern.replace('{enhancement_name}', enhancement_name)

        if step_index > 0 and '{previous_step}' in resolved:
            prev_step = self.get_workflow_step_details(workflow_name, step_index - 1)
            if prev_step:
                prev_agent = prev_step['agent']
                resolved = resolved.replace('{previous_step}',
                                          f"enhancements/{enhancement_name}/{prev_agent}")

        return resolved

    def get_step_output_path(self, workflow_name: str, step_index: int,
                             enhancement_name: str, agent: str) -> Optional[str]:
        """Get expected output path for a workflow step."""
        step_details = self.get_workflow_step_details(workflow_name, step_index)
        if not step_details:
            return None

        required_output = step_details['required_output']
        return f"enhancements/{enhancement_name}/{agent}/required_output/{required_output}"

    def validate_step_output(self, workflow_name: str, step_index: int,
                             agent: str, enhancement_dir: str) -> Tuple[bool, str]:
        """Validate agent outputs for a workflow step."""
        step_details = self.get_workflow_step_details(workflow_name, step_index)
        if not step_details:
            return False, "Workflow step not found"

        required_output = step_details['required_output']
        output_path = Path(enhancement_dir) / agent / "required_output" / required_output

        if output_path.exists():
            return True, f"Output file found: {output_path}"
        else:
            return False, f"Required output not found: {output_path}"

    def add_workflow_step(self, workflow_name: str, agent: str,
                          input_pattern: str, output_filename: str,
                          position: Optional[int] = None):
        """Add a step to a workflow template."""
        step_data = {
            'agent': agent,
            'input': input_pattern,
            'required_output': output_filename,
            'description': '',
            'on_status': {}
        }
        self.workflow.add_step(workflow_name, step_data, position)

    def edit_workflow_step(self, workflow_name: str, step_number: int,
                           input_pattern: Optional[str] = None,
                           output_filename: Optional[str] = None):
        """Edit an existing workflow step."""
        step_index = step_number - 1
        template = self.workflow.get(workflow_name)
        if not template:
            raise ValueError(f"Workflow {workflow_name} not found")
        if step_index >= len(template.steps):
            raise ValueError(f"Step {step_number} not found")

        # Get current step and update fields
        step = template.steps[step_index]
        if input_pattern:
            step.input = input_pattern
        if output_filename:
            step.required_output = output_filename

        self.workflow.update(template)

    def remove_workflow_step(self, workflow_name: str, step_number: int):
        """Remove a step from workflow template."""
        step_index = step_number - 1
        self.workflow.remove_step(workflow_name, step_index)

    def add_workflow_transition(self, workflow_name: str, step_number: int,
                                status: str, next_step: str, auto_chain: bool = True):
        """Add status transition to workflow step."""
        transition = {
            'next_step': next_step,
            'auto_chain': auto_chain
        }
        self.workflow.add_transition(workflow_name, step_number, status, transition)

    def remove_workflow_transition(self, workflow_name: str, step_number: int, status: str):
        """Remove status transition from workflow step."""
        self.workflow.remove_transition(workflow_name, step_number, status)

    def list_workflow_transitions(self, workflow_name: str, step_number: int) -> List[Dict]:
        """List transitions for a workflow step."""
        step_details = self.get_workflow_step_details(workflow_name, step_number)
        if not step_details:
            return []

        transitions = []
        for status, trans in step_details.get('on_status', {}).items():
            transitions.append({
                'status': status,
                'next_step': trans['next_step'],
                'auto_chain': trans['auto_chain']
            })

        return transitions

    def validate_workflow(self, workflow_name: str) -> Tuple[bool, List[str]]:
        """Validate a workflow template."""
        template = self.workflow.get(workflow_name)
        if not template:
            return False, [f"Workflow {workflow_name} not found"]

        messages = []
        is_valid = True

        # Check each step
        for i, step in enumerate(template.steps):
            # Check agent exists
            agent = self.agents.get(step.agent)
            if not agent:
                messages.append(f"Step {i+1}: Agent '{step.agent}' not found")
                is_valid = False

            # Check required fields
            if not step.input:
                messages.append(f"Step {i+1}: Missing input pattern")
                is_valid = False
            if not step.required_output:
                messages.append(f"Step {i+1}: Missing required output")
                is_valid = False

            # Check transitions reference valid steps
            if step.on_status:
                for status, trans in step.on_status.items():
                    if trans.next_step and trans.next_step != 'null':
                        # Check if next_step agent exists
                        next_agent = self.agents.get(trans.next_step)
                        if not next_agent:
                            messages.append(
                                f"Step {i+1}: Transition '{status}' references "
                                f"unknown agent '{trans.next_step}'"
                            )
                            is_valid = False

        if is_valid:
            messages.append("Workflow validation passed")

        return is_valid, messages

    def save_workflow_template(self, slug: str, template_data: dict) -> None:
        """Save/update a workflow template."""
        from core.models import WorkflowTemplate
        template = WorkflowTemplate.from_dict(slug, template_data)
        self.workflow.update(template)

    def create_workflow_template(self, slug: str, template_data: dict) -> None:
        """Create a new workflow template."""
        from core.models import WorkflowTemplate
        template = WorkflowTemplate.from_dict(slug, template_data)
        self.workflow.add(template)

    def delete_workflow_template(self, slug: str) -> None:
        """Delete a workflow template."""
        self.workflow.delete(slug)

    # =========================================================================
    # AGENT COMMANDS - CRUD
    # =========================================================================

    def create_agent(self, agent_data: dict) -> None:
        """Create a new agent and its markdown file."""
        from core.models import Agent

        # Extract instructions before creating Agent (not part of Agent model)
        instructions = agent_data.pop('instructions', None)

        # Create Agent object
        agent = Agent(
            name=agent_data['name'],
            agent_file=agent_data['agent-file'],
            role=agent_data['role'],
            description=agent_data.get('description', ''),
            tools=agent_data.get('tools', []),
            skills=agent_data.get('skills', []),
            validations=agent_data.get('validations', {}),
        )

        # Add to agents.json
        self.agents.add(agent)

        # Write markdown file with frontmatter and instructions
        if instructions:
            self._write_agent_markdown(agent, instructions)

    def update_agent(self, agent_file: str, agent_data: dict) -> None:
        """Update an existing agent and its markdown file."""
        from core.models import Agent

        # Extract instructions before creating Agent (not part of Agent model)
        instructions = agent_data.pop('instructions', None)

        # Create Agent object
        agent = Agent(
            name=agent_data['name'],
            agent_file=agent_data['agent-file'],
            role=agent_data['role'],
            description=agent_data.get('description', ''),
            tools=agent_data.get('tools', []),
            skills=agent_data.get('skills', []),
            validations=agent_data.get('validations', {}),
        )

        # Update agents.json
        self.agents.update(agent)

        # Write markdown file with frontmatter and instructions
        if instructions:
            self._write_agent_markdown(agent, instructions)

    def _write_agent_markdown(self, agent, instructions: str) -> None:
        """Write agent markdown file with frontmatter and instructions."""
        # Build frontmatter
        frontmatter_lines = [
            '---',
            f'name: {agent.name}',
            f'role: {agent.role}',
            f'description: {agent.description}',
        ]

        if agent.tools:
            frontmatter_lines.append('tools:')
            for tool in agent.tools:
                frontmatter_lines.append(f'  - {tool}')

        if agent.skills:
            frontmatter_lines.append('skills:')
            for skill in agent.skills:
                frontmatter_lines.append(f'  - {skill}')

        frontmatter_lines.append('---')
        frontmatter_lines.append('')

        # Combine frontmatter with instructions
        content = '\n'.join(frontmatter_lines) + instructions

        # Write to file
        md_path = self.project_root / ".claude" / "agents" / f"{agent.agent_file}.md"
        md_path.write_text(content)

    def delete_agent(self, agent_file: str) -> None:
        """Delete an agent."""
        self.agents.delete(agent_file)

    def get_agent(self, agent_file: str) -> Optional[Dict]:
        """Get a specific agent by file name.

        Returns dict with agent data including 'instructions' from markdown file.
        Instructions are the content after the YAML frontmatter.
        """
        agent = self.agents.get(agent_file)
        if not agent:
            return None

        # Load full markdown content
        full_content = self.agents.get_agent_prompt(agent_file)

        # Strip frontmatter to get just the instructions
        instructions = None
        if full_content:
            instructions = self._strip_frontmatter(full_content)

        return {
            'name': agent.name,
            'agent-file': agent.agent_file,
            'role': agent.role,
            'description': agent.description or '',
            'tools': agent.tools,
            'skills': agent.skills,
            'instructions': instructions
        }

    def _strip_frontmatter(self, content: str) -> str:
        """Strip YAML frontmatter from markdown content."""
        import re
        # Match and remove frontmatter block
        match = re.match(r'^---\s*\n.*?\n---\s*\n?', content, re.DOTALL)
        if match:
            return content[match.end():].lstrip()
        return content

    # =========================================================================
    # SKILLS COMMANDS
    # =========================================================================

    def get_skills_list(self) -> Optional[Dict]:
        """Get all available skills."""
        skills = self.skills.list_all()

        # Convert to dict format expected by UI
        return {
            "skills": [
                {
                    "name": skill.name,
                    "directory": skill.skill_directory,
                    "category": skill.category,
                    "description": skill.description or ""
                }
                for skill in skills
            ]
        }

    def get_agent_skills(self, agent: str) -> List[str]:
        """Get skills assigned to an agent."""
        agent_obj = self.agents.get(agent)
        if not agent_obj:
            return []
        return agent_obj.skills

    def load_skill_content(self, skill_directory: str) -> Optional[str]:
        """Load skill content from directory."""
        skill = self.skills.get(skill_directory)
        if not skill:
            return None

        skill_path = self.project_root / ".claude/skills" / skill_directory / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text()
        return None

    def get_skills_prompt(self, agent: str) -> Optional[str]:
        """Build complete skills section for agent prompt."""
        # Get agent's skills (returns list of skill directories)
        agent_skills = self.get_agent_skills(agent)
        if not agent_skills:
            return None
        return self.skills.build_skills_prompt(agent_skills)

    def get_skill_categories(self) -> List[str]:
        """Get all unique skill categories."""
        return self.skills.list_categories()

    def get_skill(self, skill_directory: str) -> Optional[Dict]:
        """Get a specific skill by directory name."""
        skill = self.skills.get(skill_directory)
        if not skill:
            return None

        # Load content from SKILL.md
        content = self.skills.get_skill_content(skill_directory)

        return {
            'name': skill.name,
            'directory': skill.skill_directory,
            'category': skill.category,
            'description': skill.description or '',
            'required_tools': skill.required_tools,
            'content': content
        }

    def create_skill(self, skill_data: dict) -> None:
        """Create a new skill with its SKILL.md file."""
        from core.models import Skill

        # Extract content before creating Skill object
        content = skill_data.pop('content', '')

        # Create Skill object
        skill = Skill(
            name=skill_data['name'],
            skill_directory=skill_data['directory'],
            category=skill_data['category'],
            description=skill_data.get('description', ''),
            required_tools=skill_data.get('required_tools', []),
        )

        # Add to skills.json
        self.skills.add(skill)

        # Write SKILL.md file
        if content:
            self.skills.write_skill_content(skill.skill_directory, content)

    def update_skill(self, skill_directory: str, skill_data: dict) -> None:
        """Update an existing skill and its SKILL.md file."""
        from core.models import Skill

        # Extract content before creating Skill object
        content = skill_data.pop('content', '')

        # Create updated Skill object
        skill = Skill(
            name=skill_data['name'],
            skill_directory=skill_data['directory'],
            category=skill_data['category'],
            description=skill_data.get('description', ''),
            required_tools=skill_data.get('required_tools', []),
        )

        # Update skills.json
        self.skills.update(skill)

        # Write SKILL.md file
        if content:
            self.skills.write_skill_content(skill.skill_directory, content)

    def delete_skill(self, skill_directory: str) -> None:
        """Delete a skill from skills.json and remove its directory."""
        # Remove from skills.json
        self.skills.delete(skill_directory)

        # Delete the skill directory and files
        self.skills.delete_skill_files(skill_directory)

    def remove_skill_from_agents(self, skill_directory: str) -> List[str]:
        """
        Remove a skill from all agents that have it.

        Returns list of agent names that were updated.
        """
        affected_agents = []

        # Get all agents
        agents = self.agents.list_all()

        for agent in agents:
            if skill_directory in agent.skills:
                # Remove skill from agent's list
                agent.skills.remove(skill_directory)
                # Update the agent
                self.agents.update(agent)
                affected_agents.append(agent.name)

        return affected_agents

    # =========================================================================
    # INTEGRATION COMMANDS (Placeholder - not in CMAT v8 yet)
    # =========================================================================

    def add_integration_task(self, workflow_status: str, source_file: str,
                             previous_agent: str, parent_task_id: str = "") -> str:
        """Add integration task (not yet implemented in CMAT v8)."""
        # TODO: Implement when integration service is added to CMAT Python
        return ""

    def sync_task_external(self, task_id: str):
        """Sync task to external systems (not yet implemented)."""
        pass

    def sync_all_external(self):
        """Sync all unsynced tasks (not yet implemented)."""
        pass

    # =========================================================================
    # AGENT COMMANDS
    # =========================================================================

    def run_agent_direct(
            self,
            agent_name: str,
            input_file: Path,
            output_dir: Path,
            task_description: str = "UI-invoked task",
            task_type: str = "analysis"
    ) -> Path:
        """Run an agent directly (synchronous)."""
        result = self.tasks.execute_direct(
            agent_name=agent_name,
            input_file=str(input_file),
            output_dir=str(output_dir),
            task_description=task_description,
            task_type=task_type
        )

        if not result.success:
            raise RuntimeError(f"Agent execution failed: {result.error}")

        return Path(output_dir)

    def run_agent_async(
            self,
            agent_name: str,
            input_file: Path,
            output_dir: Path,
            task_description: str = "UI-invoked task",
            task_type: str = "analysis",
            on_success=None,
            on_error=None
    ):
        """Run an agent asynchronously."""
        def run_in_thread():
            try:
                result = self.tasks.execute_direct(
                    agent_name=agent_name,
                    input_file=str(input_file),
                    output_dir=str(output_dir),
                    task_description=task_description,
                    task_type=task_type
                )

                if result.success and on_success:
                    import tkinter as tk
                    root = tk._default_root
                    if root:
                        root.after(0, lambda: on_success(Path(output_dir)))
                    else:
                        on_success(Path(output_dir))
                elif not result.success and on_error:
                    import tkinter as tk
                    root = tk._default_root
                    if root:
                        root.after(0, lambda: on_error(Exception(result.error)))
                    else:
                        on_error(Exception(result.error))

            except Exception as ex:
                if on_error:
                    import tkinter as tk
                    root = tk._default_root
                    if root:
                        root.after(0, lambda: on_error(ex))
                    else:
                        on_error(ex)

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    def get_agents_data(self) -> Optional[Dict]:
        """Get agents data."""
        agents = self.agents.list_all()

        return {
            'agents': [
                {
                    'name': agent.name,
                    'agent-file': agent.agent_file,
                    'role': agent.role,
                    'description': agent.description or '',
                    'tools': agent.tools,
                    'skills': agent.skills
                }
                for agent in agents
            ]
        }

    def regenerate_agents_json(self):
        """Regenerate agents.json from markdown files."""
        # Services read fresh from disk on each call (no caching)
        pass

    def get_agent_list(self) -> Dict[str, str]:
        """Get dictionary of available agents."""
        agents = self.agents.list_all()
        return {agent.agent_file: agent.name for agent in agents}

    def get_agent_role(self, agent: str) -> Optional[str]:
        """Get role for specific agent."""
        agent_obj = self.agents.get(agent)
        if not agent_obj:
            return None
        return agent_obj.role

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_version(self) -> str:
        """Get CMAT version."""
        from core import __version__
        return __version__

    def get_task_types(self) -> Dict[str, str]:
        """Get available task types."""
        return {
            "analysis": "Analysis",
            "technical_analysis": "Technical Analysis",
            "implementation": "Implementation",
            "testing": "Testing",
            "documentation": "Documentation",
            "integration": "Integration"
        }

    def get_priorities(self) -> List[str]:
        """Get available priorities."""
        return ["critical", "high", "normal", "low"]

    def get_tools_data(self) -> Optional[Dict]:
        """Get tools configuration."""
        tools = self.tools.list_all()
        return {
            'tools': [
                {
                    'name': tool.name,
                    'description': tool.description or '',
                    'category': getattr(tool, 'category', ''),
                }
                for tool in tools
            ]
        }

    def get_task_log(self, task_id: str, source_file: str) -> Optional[str]:
        """Get log content for a task."""
        enhancement_name = self._extract_enhancement_name(source_file)
        if not enhancement_name:
            return None

        log_dir = self.project_root / "enhancements" / enhancement_name / "logs"
        if not log_dir.exists():
            return None

        log_files = list(log_dir.glob(f"*{task_id}*.log"))
        if not log_files:
            return None

        log_file = max(log_files, key=lambda p: p.stat().st_mtime)
        with open(log_file, 'r') as f:
            return f.read()

    def task_log_exists(self, task_id: str, source_file: str) -> bool:
        """Check if log exists for a task."""
        return self.get_task_log(task_id, source_file) is not None

    def get_operations_log(self, max_lines: int = 1000) -> str:
        """Get operations log content."""
        log_file = self.logs_dir / "queue_operations.log"
        if not log_file.exists():
            return "No operations log found."

        with open(log_file, 'r') as f:
            lines = f.readlines()
        return ''.join(lines[-max_lines:])

    def extract_skills_used(self, log_content: str) -> List[str]:
        """Extract skills that were applied from task log."""
        import re

        skills_used = []
        agent_output = log_content

        if "END OF PROMPT" in log_content:
            agent_output = log_content.split("END OF PROMPT", 1)[1]

        # Try new format: SKILLS_USED: skill1, skill2
        if "SKILLS_USED:" in agent_output:
            match = re.search(r'SKILLS_USED:\s*([^\n]+)', agent_output)
            if match:
                skills_line = match.group(1).strip()
                skills_used = [s.strip() for s in skills_line.split(',') if s.strip()]
                return skills_used

        # Fall back to old format: ## Skills Applied
        if "Skills Applied" not in log_content:
            return skills_used

        lines = log_content.split('\n')
        in_skills = False

        for line in lines:
            if "## Skills Applied" in line or "Skills Applied:" in line:
                in_skills = True
                continue
            elif in_skills:
                if line.startswith('- '):
                    match = re.search(r'\*\*([^*]+)\*\*', line)
                    if match:
                        skills_used.append(match.group(1))
                elif not line.strip() or line.startswith('#'):
                    break

        return skills_used

    def _extract_enhancement_name(self, source_file: str) -> Optional[str]:
        """Extract enhancement name from source file path."""
        import re
        match = re.match(r'^enhancements/([^/]+)/', source_file)
        return match.group(1) if match else None

    # =========================================================================
    # CLAUDE.md MANAGEMENT
    # =========================================================================

    def check_claude_md_status(self) -> Dict:
        """
        Check if CLAUDE.md exists in project.

        Returns:
            {
                "exists": bool,
                "path": str | None,
                "size": int,
                "modified": datetime | None
            }
        """
        claude_md = self.project_root / "CLAUDE.md"

        if claude_md.exists():
            stat = claude_md.stat()
            return {
                "exists": True,
                "path": str(claude_md),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime)
            }
        else:
            return {
                "exists": False,
                "path": None,
                "size": 0,
                "modified": None
            }

    def open_claude_md_in_editor(self) -> Tuple[bool, str]:
        """
        Open CLAUDE.md in system default editor.

        Returns:
            (success: bool, message: str)

        Platform-specific implementation:
        - macOS: open command
        - Windows: os.startfile()
        - Linux: xdg-open
        """
        import subprocess
        import platform
        import os

        claude_md = self.project_root / "CLAUDE.md"

        if not claude_md.exists():
            return (False, "CLAUDE.md not found in project")

        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                subprocess.Popen(["open", str(claude_md)])
            elif system == "Windows":
                os.startfile(str(claude_md))
            else:  # Linux/Unix
                subprocess.Popen(["xdg-open", str(claude_md)])

            return (True, "Opened in system editor")

        except FileNotFoundError:
            return (False, f"Editor command not found for {system}")
        except Exception as e:
            return (False, f"Failed to open editor: {e}")

    def copy_file_to_claude_md(
        self,
        source_path: str,
        overwrite_existing: bool = False
    ) -> Tuple[bool, str]:
        """
        Copy a markdown file to project root as CLAUDE.md.

        Args:
            source_path: Path to source .md file
            overwrite_existing: If True, overwrite without confirmation

        Returns:
            (success: bool, message: str)

        Validations:
        - Source file exists and is readable
        - Source file is .md extension
        - Target directory is writable
        - Warns if source > 50KB
        """
        import shutil

        source = Path(source_path)
        target = self.project_root / "CLAUDE.md"

        # Validation
        if not source.exists():
            return (False, f"Source file not found: {source}")

        if source.suffix.lower() != ".md":
            return (False, "Source file must be a .md file")

        # Check if overwrite needed
        if target.exists() and not overwrite_existing:
            return (False, "CLAUDE.md already exists. User confirmation needed.")

        # Size warning (return warning, let caller handle dialog)
        if source.stat().st_size > 50 * 1024:
            return (False, f"File is large ({source.stat().st_size // 1024}KB). CLAUDE.md should be concise (< 50KB).")

        # Copy operation
        try:
            shutil.copy2(source, target)
            return (True, f"Copied to {target}")
        except PermissionError as e:
            return (False, f"Permission denied: {e}")
        except Exception as e:
            return (False, f"Copy failed: {e}")
