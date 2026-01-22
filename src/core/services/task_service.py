"""
Task execution service for CMAT.

Handles prompt building, Claude invocation, and status extraction.
This is the execution engine that bridges queue management and Claude.
"""

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.claude.client import ClaudeClient
from core.claude.config import ClaudeClientConfig
from core.models.agent import Agent
from core.models.task import Task
from core.utils import get_timestamp, log_error, log_operation


@dataclass
class ExecutionResult:
    """Result of a task execution."""

    success: bool
    status: str | None
    exit_code: int
    output_dir: str
    log_file: str
    duration_seconds: int
    pid: int | None = None


class TaskService:
    """
    Task execution service.

    Builds prompts from base + role-specific templates, invokes Claude,
    and extracts status from completion blocks.

    Prompt Structure:
        Prompts are loaded from .claude/prompts/ directory:
        - base.md: Common content for all task types
        - {role}.md: Role-specific optional output guidance

        Templates are combined with double newline separator and passed
        through variable substitution before being sent to agents.
    """

    # Regex pattern for YAML frontmatter completion block
    # Matches: ---\nagent: ...\ntask_id: ...\nstatus: <STATUS>\n---
    COMPLETION_BLOCK_PATTERN = re.compile(
        r"^---\s*\n" r"agent:\s*\S+\s*\n" r"task_id:\s*\S+\s*\n" r"status:\s*(.+?)\s*\n" r"---\s*$",
        re.MULTILINE,
    )

    # Legacy regex patterns for backward compatibility
    # Used as fallback if YAML completion block not found
    LEGACY_STATUS_PATTERNS = [
        r"(READY_FOR_[A-Z_]+)",
        r"([A-Z_]+_COMPLETE)",
        r"(BLOCKED:[^\n*]+)",
        r"(NEEDS_CLARIFICATION:[^\n*]+)",
        r"(NEEDS_RESEARCH:[^\n*]+)",
        r"(TESTS_FAILED:[^\n*]+)",
        r"(BUILD_FAILED:[^\n*]+)",
        r"(INTEGRATION_FAILED:[^\n*]+)",
    ]

    def __init__(
        self,
        templates_file: str = ".claude/data/TASK_PROMPT_DEFAULTS.md",  # DEPRECATED
        prompts_dir: str = ".claude/prompts",
        agents_dir: str = ".claude/agents",
        logs_dir: str = ".claude/logs",
        enhancements_dir: str = "enhancements",
        project_root: str | None = None,
    ):
        self.templates_file = Path(templates_file)  # Deprecated, kept for compatibility
        self.prompts_dir = Path(prompts_dir)
        self.agents_dir = Path(agents_dir)
        self.logs_dir = Path(logs_dir)
        self.enhancements_dir = Path(enhancements_dir)

        # Project root for subprocess cwd - derive from logs_dir if not provided
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Derive from logs_dir (remove .claude/logs suffix)
            logs_path = Path(logs_dir).resolve()
            if ".claude" in logs_path.parts:
                idx = logs_path.parts.index(".claude")
                self.project_root = Path(*logs_path.parts[:idx])
            else:
                self.project_root = Path.cwd()

        # Services injected later to avoid circular imports
        self._agent_service = None
        self._skills_service = None
        self._queue_service = None
        self._learnings_service = None
        self._model_service = None

    def set_services(
        self, agent=None, skills=None, queue=None, learnings=None, models=None
    ) -> None:
        """Inject service dependencies."""
        if agent:
            self._agent_service = agent
        if skills:
            self._skills_service = skills
        if models:
            self._model_service = models
        if queue:
            self._queue_service = queue
        if learnings:
            self._learnings_service = learnings

    def _load_prompt_file(self, filename: str) -> str | None:
        """
        Load a prompt file from the prompts directory.

        Args:
            filename: Name of the prompt file (e.g., "base.md", "analysis.md")

        Returns:
            File content as string, or None if file doesn't exist
        """
        file_path = self.prompts_dir / filename

        if not file_path.exists():
            return None

        try:
            return file_path.read_text(encoding="utf-8")
        except OSError as e:
            log_error(f"Failed to read prompt file {file_path}: {e}")
            return None

    def get_template(self, role: str) -> str | None:
        """
        Get a prompt template by role.

        Loads and combines base.md with role-specific prompt file.

        Args:
            role: Role name (e.g., "analysis", "design", "implementation")

        Returns:
            Combined prompt content, or None if base.md not found
        """
        # Load base prompt (required)
        base_content = self._load_prompt_file("base.md")
        if not base_content:
            log_error(f"Base prompt not found: {self.prompts_dir}/base.md")
            return None

        # Load role-specific prompt (optional)
        role_content = self._load_prompt_file(f"{role}.md")
        if not role_content:
            log_operation(
                "PROMPT_LOAD_WARNING", f"Role prompt not found: {role}.md, using base only"
            )
            return base_content

        # Combine with double newline
        return base_content + "\n\n" + role_content

    def _build_input_instruction(self, source_file: str | None) -> str:
        """Build the input instruction based on source file type."""
        if not source_file or source_file == "null":
            return "Work from the task description provided."

        path = Path(source_file)
        if path.is_file():
            return f"Read and process this file: {source_file}"
        elif path.is_dir():
            return f"Read and process all files in this directory: {source_file}"
        else:
            return f"Input: {source_file}"

    def build_prompt(
        self,
        agent_name: str,
        role: str,
        task_id: str,
        task_description: str,
        source_file: str | None = None,
        enhancement_name: str = "unknown",
        enhancement_dir: str = "enhancements/unknown",
        required_output_filename: str = "output.md",
        expected_statuses: str = "(No workflow-defined statuses)",
    ) -> str | None:
        """
        Build a complete prompt from template and parameters.

        Args:
            agent_name: Name of the agent to execute
            role: Agent's role (e.g., "analysis", "implementation") - derived from agent config
            task_id: Unique task identifier
            task_description: Description of the task
            source_file: Optional input file path
            enhancement_name: Name of the enhancement being worked on
            enhancement_dir: Path to enhancement directory
            required_output_filename: Expected output filename
            expected_statuses: Workflow-expected status codes

        Returns None if template not found.
        """
        template = self.get_template(role)
        if not template:
            log_error(f"No template found for role: {role}")
            return None

        # Build agent config path
        agent_config = f"{self.agents_dir}/{agent_name}.md"

        # Build input instruction
        input_instruction = self._build_input_instruction(source_file)

        # Get skills section if service available
        skills_section = ""
        if self._skills_service and self._agent_service:
            agent = self._agent_service.get(agent_name)
            if agent and agent.skills:
                skills_section = self._skills_service.build_skills_prompt(agent.skills)

        # Substitute variables
        prompt = template
        substitutions = {
            "${agent}": agent_name,
            "${agent_config}": agent_config,
            "${source_file}": source_file or "",
            "${task_description}": task_description,
            "${task_id}": task_id,
            "${enhancement_name}": enhancement_name,
            "${enhancement_dir}": enhancement_dir,
            "${input_instruction}": input_instruction,
            "${required_output_filename}": required_output_filename,
            "${expected_statuses}": expected_statuses,
        }

        for var, value in substitutions.items():
            prompt = prompt.replace(var, value)

        # Append skills section if present
        if skills_section:
            prompt = f"{prompt}\n\n{skills_section}"

        # Retrieve and append learnings section if service available
        if self._learnings_service:
            from core.services.learnings_service import RetrievalContext

            context = RetrievalContext(
                agent_name=agent_name,
                role=role,
                task_description=task_description,
                source_file=source_file,
            )
            learnings = self._learnings_service.retrieve(context, limit=5)
            if learnings:
                learnings_section = self._learnings_service.build_learnings_prompt(learnings)
                prompt = f"{prompt}\n\n{learnings_section}"

        return prompt

    def extract_status(self, output: str) -> str | None:
        """
        Extract completion status from agent output.

        Primary method: Parse YAML frontmatter completion block at end of output.
        Expected format:
            ---
            agent: <agent_name>
            task_id: <task_id>
            status: <STATUS>
            ---

        Fallback: Legacy regex patterns for backward compatibility with older
        agent outputs that don't include the completion block.
        """
        if not output:
            return None

        # Check last portion of output (completion block should be at end)
        check_text = output[-5000:] if len(output) > 5000 else output

        # Primary: Try to find YAML completion block
        matches = self.COMPLETION_BLOCK_PATTERN.findall(check_text)
        if matches:
            # Return the last match (most recent completion block)
            return matches[-1].strip()

        # Fallback: Try legacy status patterns for backward compatibility
        for pattern in self.LEGACY_STATUS_PATTERNS:
            matches = re.findall(pattern, check_text)
            if matches:
                # Return the last match (most recent status)
                return matches[-1].strip()

        return None

    def execute(
        self,
        task: Task,
        agent: Agent,
        workflow_name: str | None = None,
        workflow_step: int | None = None,
        expected_statuses: str = "(No workflow-defined statuses)",
        required_output_filename: str = "output.md",
    ) -> ExecutionResult:
        """
        Execute a task with an agent.

        This is the main execution method for workflow tasks.
        """
        # Extract enhancement name from metadata or source
        enhancement_name = self._extract_enhancement_name(task)
        enhancement_dir = f"{self.enhancements_dir}/{enhancement_name}"

        # Create output directory
        output_dir = f"{enhancement_dir}/{agent.agent_file}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Create log file in enhancement's logs directory
        enhancement_logs_dir = Path(enhancement_dir) / "logs"
        enhancement_logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = enhancement_logs_dir / f"{agent.agent_file}_{task.id}_{timestamp}.log"

        # Build prompt using agent's role (not task_type)
        prompt = self.build_prompt(
            agent_name=agent.agent_file,
            role=agent.role,
            task_id=task.id,
            task_description=task.description,
            source_file=task.source_file,
            enhancement_name=enhancement_name,
            enhancement_dir=enhancement_dir,
            required_output_filename=required_output_filename,
            expected_statuses=expected_statuses,
        )

        if not prompt:
            return ExecutionResult(
                success=False,
                status=None,
                exit_code=1,
                output_dir=output_dir,
                log_file=str(log_file),
                duration_seconds=0,
            )

        # Get requested model from task metadata
        model = task.metadata.requested_model

        # Execute Claude
        result = self._execute_claude(
            prompt=prompt,
            log_file=log_file,
            task_id=task.id,
            agent_name=agent.agent_file,
            enhancement_name=enhancement_name,
            model=model,
        )

        # Process retrospective output if this is the retrospective agent
        if result["exit_code"] == 0:
            self._process_retrospective_output(
                agent_name=agent.agent_file,
                enhancement_dir=enhancement_dir,
            )

        return ExecutionResult(
            success=result["exit_code"] == 0,
            status=result["status"],
            exit_code=result["exit_code"],
            output_dir=output_dir,
            log_file=str(log_file),
            duration_seconds=result["duration"],
            pid=result.get("pid"),
        )

    def execute_direct(
        self,
        agent_name: str,
        input_file: str | None,
        output_dir: str,
        task_description: str = "UI-invoked task",
    ) -> ExecutionResult:
        """
        Execute an agent directly without task queue integration.

        Designed for UI-driven operations like enhancement creation.
        Role is derived from the agent's configuration.
        """
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Create log file
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"ui_agent_{agent_name}_{timestamp}.log"

        # Generate task ID for logging
        task_id = f"ui_{agent_name}_{timestamp}"

        # Extract enhancement name from output_dir if possible
        enhancement_name = "ui-operation"
        enhancement_dir = output_dir
        match = re.search(r"enhancements/([^/]+)", output_dir)
        if match:
            enhancement_name = match.group(1)

        # Get agent's role from agent service (default to "analysis" if not found)
        role = "analysis"
        if self._agent_service:
            agent = self._agent_service.get(agent_name)
            if agent:
                role = agent.role

        # Build prompt using agent's role
        prompt = self.build_prompt(
            agent_name=agent_name,
            role=role,
            task_id=task_id,
            task_description=task_description,
            source_file=input_file,
            enhancement_name=enhancement_name,
            enhancement_dir=enhancement_dir,
        )

        if not prompt:
            return ExecutionResult(
                success=False,
                status=None,
                exit_code=1,
                output_dir=output_dir,
                log_file=str(log_file),
                duration_seconds=0,
            )

        # Execute Claude (synchronous, no PID tracking needed)
        result = self._execute_claude(
            prompt=prompt,
            log_file=log_file,
            task_id=task_id,
            agent_name=agent_name,
            enhancement_name=enhancement_name,
        )

        return ExecutionResult(
            success=result["exit_code"] == 0,
            status=result["status"],
            exit_code=result["exit_code"],
            output_dir=output_dir,
            log_file=str(log_file),
            duration_seconds=result["duration"],
        )

    def _resolve_model(self, model: str | None) -> str | None:
        """
        Resolve model name to API ID.

        Args:
            model: Model name or ID (may be None)

        Returns:
            API model ID string, or None if no model configured
        """
        if model and self._model_service:
            # Look up the model to get its api_id
            model_obj = self._model_service.get(model)
            if model_obj:
                return model_obj.api_id
            # If not found by ID, it might already be an API ID - use as-is
            return model
        elif self._model_service:
            # Use CMAT default model if none specified
            default = self._model_service.get_default()
            if default:
                return default.api_id
        return None

    def _build_environment(
        self,
        task_id: str,
        log_file: Path,
        agent_name: str,
        enhancement_name: str,
    ) -> dict[str, str]:
        """
        Build environment variables for Claude execution.

        Args:
            task_id: Task identifier
            log_file: Path to log file
            agent_name: Agent name
            enhancement_name: Enhancement name

        Returns:
            Dictionary of environment variables (not merged with os.environ)
        """
        env = {
            "CMAT_CURRENT_TASK_ID": task_id,
            "CMAT_CURRENT_LOG_FILE": str(log_file),
            "CMAT_AGENT": agent_name,
            "CMAT_ENHANCEMENT": enhancement_name,
        }

        # Set CMAT_ROOT so hooks can find the CMAT package
        # Go from src/core/services/ up to the root containing src/
        cmat_root = Path(__file__).resolve().parent.parent.parent.parent
        if (cmat_root / "src" / "core").exists():
            env["CMAT_ROOT"] = str(cmat_root)

        # Enable hook debugging if CMAT_HOOK_DEBUG is set in parent environment
        if os.environ.get("CMAT_HOOK_DEBUG"):
            env["CMAT_HOOK_DEBUG"] = os.environ["CMAT_HOOK_DEBUG"]

        return env

    def _write_log_header(
        self,
        log_file: Path,
        task_id: str,
        agent_name: str,
        enhancement_name: str,
        model: str | None,
        prompt: str,
    ) -> None:
        """Write execution header to log file."""
        with open(log_file, "w") as f:
            f.write("=== Starting Agent Execution ===\n")
            f.write(f"Start Time: {get_timestamp()}\n")
            f.write(f"Agent: {agent_name}\n")
            f.write(f"Task ID: {task_id}\n")
            f.write(f"Enhancement: {enhancement_name}\n")
            if model:
                f.write(f"Model: {model}\n")
            f.write("\n")
            f.write("=" * 70 + "\n")
            f.write("PROMPT SENT TO AGENT\n")
            f.write("=" * 70 + "\n\n")
            f.write(prompt)
            f.write("\n\n")
            f.write("=" * 70 + "\n")
            f.write("END OF PROMPT\n")
            f.write("=" * 70 + "\n\n")

    def _write_log_output_header(self, log_file: Path) -> None:
        """Write the AGENT OUTPUT section header to log file."""
        with open(log_file, "a") as f:
            f.write("=" * 70 + "\n")
            f.write("AGENT OUTPUT (streaming)\n")
            f.write("=" * 70 + "\n\n")

    def _write_log_footer(
        self,
        log_file: Path,
        output: str,
        exit_code: int,
        duration: int,
        status: str | None,
        output_already_written: bool = False,
    ) -> None:
        """Write execution footer to log file."""
        with open(log_file, "a") as f:
            if not output_already_written:
                f.write("=" * 70 + "\n")
                f.write("AGENT OUTPUT\n")
                f.write("=" * 70 + "\n\n")
                f.write(output or "(no output)")
            f.write("\n\n")
            f.write("=== Agent Execution Complete ===\n")
            f.write(f"End Time: {get_timestamp()}\n")
            f.write(f"Duration: {duration}s\n")
            f.write(f"Exit Code: {exit_code}\n")
            if status:
                f.write(f"Exit Status: {status}\n")

    def _execute_claude(
        self,
        prompt: str,
        log_file: Path,
        task_id: str,
        agent_name: str,
        enhancement_name: str,
        model: str | None = None,
    ) -> dict:
        """
        Execute Claude CLI with the given prompt.

        Output is streamed to the log file in real-time as Claude produces it,
        allowing monitoring of agent progress during execution.

        Args:
            prompt: The prompt to send to Claude
            log_file: Path to write execution log
            task_id: Task identifier for tracking
            agent_name: Name of the agent executing
            enhancement_name: Name of the enhancement being worked on
            model: Optional Claude model to use (e.g., "claude-sonnet-4-20250514")

        Returns dict with exit_code, status, duration, and optionally pid.
        """
        # Resolve model to API ID
        api_model_id = self._resolve_model(model)

        # Write log header
        self._write_log_header(
            log_file, task_id, agent_name, enhancement_name, api_model_id, prompt
        )

        # Write output section header before execution starts
        self._write_log_output_header(log_file)

        # Build environment variables for cost tracking hooks
        env = self._build_environment(task_id, log_file, agent_name, enhancement_name)

        # Build config and execute via ClaudeClient
        # Use stream-json format for real-time output visibility
        from core.claude.config import OutputFormat

        config = ClaudeClientConfig(
            model=api_model_id,
            permission_mode="bypassPermissions",
            working_dir=str(self.project_root),
            environment=env,
            output_format=OutputFormat.STREAM_JSON,
            verbose=True,  # Required for stream-json with --print
        )

        # Create line callback to stream output to log file
        log_file_handle = open(log_file, "a")

        def line_callback(line: str) -> None:
            """Write each line to log file as it arrives."""
            log_file_handle.write(line)
            log_file_handle.flush()

        client = ClaudeClient()
        try:
            response = client.run(prompt, config, line_callback=line_callback)
        finally:
            log_file_handle.close()

        # Store PID if queue service available
        if response.pid and self._queue_service:
            self._queue_service.update_single_metadata(task_id, "process_pid", str(response.pid))

        # Extract status from output
        status = self.extract_status(response.output or "")

        # Write log footer (output already written via streaming)
        self._write_log_footer(
            log_file,
            response.output,
            response.exit_code,
            response.duration_seconds,
            status,
            output_already_written=True,
        )

        log_operation("TASK_EXECUTED", f"Task: {task_id}, Agent: {agent_name}, Status: {status}")

        return {
            "exit_code": response.exit_code,
            "status": status,
            "duration": response.duration_seconds,
            "pid": response.pid,
            "output": response.output,
        }

    def _extract_enhancement_name(self, task: Task) -> str:
        """Extract enhancement name from task metadata or source file."""
        # Check metadata first
        if task.metadata.enhancement_title:
            return task.metadata.enhancement_title

        # Try to extract from source file path
        if task.source_file:
            match = re.search(r"enhancements/([^/]+)", task.source_file)
            if match:
                return match.group(1)

        # Fallback to task ID
        return task.id

    def _process_retrospective_output(
        self,
        agent_name: str,
        enhancement_dir: str,
    ) -> None:
        """
        Process retrospective agent output and store learnings.

        Called automatically after task completion if the agent is "retrospective".
        Constructs the path to learnings_actions.json, processes it via
        LearningsService, and logs the results. All errors are caught to prevent
        learnings processing from breaking task execution.

        Args:
            agent_name: Name of the agent that just completed. Only processes if
                this is "retrospective".
            enhancement_dir: Path to the enhancement directory (e.g.,
                "enhancements/my-feature"). Used to locate retrospective output.

        Returns:
            None. All errors are logged but not raised.

        Integration:
            This method is called from TaskService.execute() after successful
            task completion. It has no effect on task completion status.

        Error Handling:
            - Missing learnings service: Logs error, returns early
            - Missing output file: Logs error, returns early
            - Processing errors: Caught, logged, execution continues
        """
        from pathlib import Path

        # Only process retrospective agent
        if agent_name != "retrospective":
            return

        # Check if learnings service is available
        if not self._learnings_service:
            log_error("LearningsService not available for retrospective processing")
            return

        # Construct path to learnings_actions.json
        actions_file = (
            Path(enhancement_dir) / "retrospective" / "required_output" / "learnings_actions.json"
        )

        if not actions_file.exists():
            log_error(f"Retrospective output file not found: {actions_file}")
            return

        try:
            # Process the actions file
            result = self._learnings_service.process_actions_file(str(actions_file))

            # Log summary
            log_operation(
                "RETROSPECTIVE_PROCESSED",
                f"Enhancement: {Path(enhancement_dir).name}, "
                f"Stored: {result['stored']}, "
                f"Duplicates: {result['duplicates']}, "
                f"Errors: {result['errors']}",
            )

        except Exception as e:
            # Don't let learnings processing failures break the task
            log_error(f"Failed to process retrospective output: {e}")
