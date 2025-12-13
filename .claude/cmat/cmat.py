"""
CMAT - Claude Multi-Agent Template

Main entry point class that composes all services and provides
a unified interface for CMAT operations.
"""

from pathlib import Path
from typing import Optional

from cmat.services.queue_service import QueueService
from cmat.services.agent_service import AgentService
from cmat.services.skills_service import SkillsService
from cmat.services.workflow_service import WorkflowService
from cmat.services.task_service import TaskService
from cmat.utils import find_project_root, ensure_directories


class CMAT:
    """
    Main entry point for CMAT operations.

    Composes all services and provides a unified interface for
    managing tasks, agents, skills, and workflows.

    Usage:
        cmat = CMAT()

        # Queue operations
        task = cmat.queue.add("Task title", "architect", "high", ...)
        cmat.queue.complete(task.id, "READY_FOR_IMPLEMENTATION")

        # Agent operations
        agents = cmat.agents.list_all()
        architect = cmat.agents.get("architect")

        # Skills operations
        skills = cmat.skills.list_all()
        skill_content = cmat.skills.get_skill_content("api-design")

        # Workflow operations
        templates = cmat.workflow.list_all()
        next_step = cmat.workflow.get_next_step("new-feature-development", 0, "READY_FOR_DEVELOPMENT")

        # Task execution
        result = cmat.tasks.execute_direct("architect", "input.md", "output/", "Analyze this")

        # Full workflow orchestration
        task_id = cmat.workflow.start_workflow("new-feature-development", "my-feature")
        cmat.workflow.run_task(task_id)
    """

    def __init__(
            self,
            base_path: Optional[str] = None,
            queue_file: Optional[str] = None,
            agents_dir: Optional[str] = None,
            skills_dir: Optional[str] = None,
            templates_file: Optional[str] = None,
            enhancements_dir: Optional[str] = None,
            auto_find_root: bool = True,
    ):
        """
        Initialize CMAT with optional custom paths.

        Args:
            base_path: Base directory for all CMAT files (defaults to project root or cwd)
            queue_file: Path to task queue JSON file
            agents_dir: Path to agents directory
            skills_dir: Path to skills directory
            templates_file: Path to workflow templates JSON file
            enhancements_dir: Path to enhancements directory
            auto_find_root: If True and base_path not provided, search for project root
        """
        # Determine base path
        if base_path:
            base = Path(base_path)
        elif auto_find_root:
            found_root = find_project_root()
            base = found_root if found_root else Path.cwd()
        else:
            base = Path.cwd()

        self._base_path = base

        # Store paths for later use
        _agents_dir = agents_dir or str(base / ".claude/agents")
        _skills_dir = skills_dir or str(base / ".claude/skills")
        _enhancements_dir = enhancements_dir or str(base / "enhancements")

        # Initialize services with paths
        self.queue = QueueService(
            queue_file=queue_file or str(base / ".claude/queues/task_queue.json")
        )

        self.agents = AgentService(
            agents_dir=_agents_dir
        )

        self.skills = SkillsService(
            skills_dir=_skills_dir
        )

        self.workflow = WorkflowService(
            templates_file=templates_file or str(base / ".claude/queues/workflow_templates.json"),
            enhancements_dir=_enhancements_dir
        )

        self.tasks = TaskService(
            templates_file=str(base / ".claude/docs/TASK_PROMPT_DEFAULTS.md"),
            agents_dir=_agents_dir,
            logs_dir=str(base / ".claude/logs"),
            enhancements_dir=_enhancements_dir,
        )

        # Wire up service dependencies
        self.tasks.set_services(
            agent=self.agents,
            skills=self.skills,
            queue=self.queue,
        )

        self.workflow.set_services(
            queue=self.queue,
            task=self.tasks,
            agent=self.agents,
        )

    @property
    def base_path(self) -> Path:
        """Get the base path for CMAT files."""
        return self._base_path

    def ensure_directories(self) -> None:
        """Ensure all required CMAT directories exist."""
        ensure_directories(self._base_path)

    def invalidate_caches(self) -> None:
        """Invalidate all service caches to force reload from disk."""
        self.agents.invalidate_cache()
        self.skills.invalidate_cache()
        self.workflow.invalidate_cache()

    @property
    def version(self) -> str:
        """Get the CMAT version."""
        from cmat import __version__
        return __version__