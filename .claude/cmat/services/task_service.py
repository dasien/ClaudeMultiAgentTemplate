"""
Task execution service for CMAT.

Handles prompt building, Claude invocation, and status extraction.
This is the execution engine that bridges queue management and Claude.
"""

import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from cmat.models.task import Task
from cmat.models.agent import Agent
from cmat.utils import get_timestamp, log_operation, log_error


@dataclass
class ExecutionResult:
    """Result of a task execution."""
    success: bool
    status: Optional[str]
    exit_code: int
    output_dir: str
    log_file: str
    duration_seconds: int
    pid: Optional[int] = None


class TaskService:
    """
    Task execution service.

    Builds prompts from templates, invokes Claude, and extracts status.
    """

    # Regex pattern for YAML frontmatter completion block
    # Matches: ---\nagent: ...\ntask_id: ...\nstatus: <STATUS>\n---
    COMPLETION_BLOCK_PATTERN = re.compile(
        r"^---\s*\n"
        r"agent:\s*\S+\s*\n"
        r"task_id:\s*\S+\s*\n"
        r"status:\s*(.+?)\s*\n"
        r"---\s*$",
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
        templates_file: str = ".claude/docs/TASK_PROMPT_DEFAULTS.md",
        agents_dir: str = ".claude/agents",
        logs_dir: str = ".claude/logs",
        enhancements_dir: str = "enhancements",
    ):
        self.templates_file = Path(templates_file)
        self.agents_dir = Path(agents_dir)
        self.logs_dir = Path(logs_dir)
        self.enhancements_dir = Path(enhancements_dir)

        self._templates: Optional[dict[str, str]] = None

        # Services injected later to avoid circular imports
        self._agent_service = None
        self._skills_service = None
        self._queue_service = None
        self._learnings_service = None

    def set_services(self, agent=None, skills=None, queue=None, learnings=None) -> None:
        """Inject service dependencies."""
        if agent:
            self._agent_service = agent
        if skills:
            self._skills_service = skills
        if queue:
            self._queue_service = queue
        if learnings:
            self._learnings_service = learnings

    def _load_templates(self) -> dict[str, str]:
        """Load prompt templates from TASK_PROMPT_DEFAULTS.md."""
        if self._templates is not None:
            return self._templates

        if not self.templates_file.exists():
            log_error(f"Templates file not found: {self.templates_file}")
            return {}

        content = self.templates_file.read_text()
        templates = {}

        # Parse each template section
        template_types = [
            "ANALYSIS_TEMPLATE",
            "TECHNICAL_ANALYSIS_TEMPLATE",
            "IMPLEMENTATION_TEMPLATE",
            "TESTING_TEMPLATE",
            "DOCUMENTATION_TEMPLATE",
            "INTEGRATION_TEMPLATE",
        ]

        for template_type in template_types:
            # Find template section
            pattern = rf"^# {template_type}$"
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                start = match.end()
                # Find the end marker
                end_match = re.search(r"^===END_TEMPLATE===$", content[start:], re.MULTILINE)
                if end_match:
                    template_content = content[start:start + end_match.start()].strip()
                    # Map to task type
                    task_type = template_type.replace("_TEMPLATE", "").lower()
                    templates[task_type] = template_content

        self._templates = templates
        return templates

    def get_template(self, task_type: str) -> Optional[str]:
        """Get a prompt template by task type."""
        templates = self._load_templates()
        return templates.get(task_type)

    def _build_input_instruction(self, source_file: Optional[str]) -> str:
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
        task_type: str,
        task_id: str,
        task_description: str,
        source_file: Optional[str] = None,
        enhancement_name: str = "unknown",
        enhancement_dir: str = "enhancements/unknown",
        required_output_filename: str = "output.md",
        expected_statuses: str = "(No workflow-defined statuses)",
    ) -> Optional[str]:
        """
        Build a complete prompt from template and parameters.

        Returns None if template not found.
        """
        template = self.get_template(task_type)
        if not template:
            log_error(f"No template found for task type: {task_type}")
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
            "${task_type}": task_type,
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
            from cmat.services.learnings_service import RetrievalContext
            context = RetrievalContext(
                agent_name=agent_name,
                task_type=task_type,
                task_description=task_description,
                source_file=source_file,
            )
            learnings = self._learnings_service.retrieve(context, limit=5)
            if learnings:
                learnings_section = self._learnings_service.build_learnings_prompt(learnings)
                prompt = f"{prompt}\n\n{learnings_section}"

        return prompt

    def extract_status(self, output: str) -> Optional[str]:
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
        workflow_name: Optional[str] = None,
        workflow_step: Optional[int] = None,
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

        # Create log file
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"{agent.agent_file}_{task.id}_{timestamp}.log"

        # Build prompt
        prompt = self.build_prompt(
            agent_name=agent.agent_file,
            task_type=task.task_type,
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

        # Execute Claude
        result = self._execute_claude(
            prompt=prompt,
            log_file=log_file,
            task_id=task.id,
            agent_name=agent.agent_file,
            enhancement_name=enhancement_name,
        )

        # Extract learnings from successful output
        if result["exit_code"] == 0 and result.get("output") and self._learnings_service:
            self._extract_and_store_learnings(
                output=result["output"],
                agent_name=agent.agent_file,
                task_type=task.task_type,
                task_description=task.description,
                task_id=task.id,
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
        input_file: Optional[str],
        output_dir: str,
        task_description: str = "UI-invoked task",
        task_type: str = "analysis",
    ) -> ExecutionResult:
        """
        Execute an agent directly without task queue integration.

        Designed for UI-driven operations like enhancement creation.
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

        # Build prompt
        prompt = self.build_prompt(
            agent_name=agent_name,
            task_type=task_type,
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

    def _execute_claude(
        self,
        prompt: str,
        log_file: Path,
        task_id: str,
        agent_name: str,
        enhancement_name: str,
    ) -> dict:
        """
        Execute Claude CLI with the given prompt.

        Returns dict with exit_code, status, duration, and optionally pid.
        """
        start_time = time.time()
        start_timestamp = get_timestamp()

        # Write execution header to log
        with open(log_file, "w") as f:
            f.write("=== Starting Agent Execution ===\n")
            f.write(f"Start Time: {start_timestamp}\n")
            f.write(f"Agent: {agent_name}\n")
            f.write(f"Task ID: {task_id}\n")
            f.write(f"Enhancement: {enhancement_name}\n")
            f.write("\n")
            f.write("=" * 70 + "\n")
            f.write("PROMPT SENT TO AGENT\n")
            f.write("=" * 70 + "\n\n")
            f.write(prompt)
            f.write("\n\n")
            f.write("=" * 70 + "\n")
            f.write("END OF PROMPT\n")
            f.write("=" * 70 + "\n\n")

        # Set environment variables for cost tracking hooks
        env = os.environ.copy()
        env["CMAT_CURRENT_TASK_ID"] = task_id
        env["CMAT_CURRENT_LOG_FILE"] = str(log_file)
        env["CMAT_AGENT"] = agent_name
        env["CMAT_ENHANCEMENT"] = enhancement_name

        # Execute Claude with bypass permissions
        try:
            process = subprocess.Popen(
                ["claude", "--permission-mode", "bypassPermissions", prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
            )

            pid = process.pid

            # Store PID if queue service available
            if self._queue_service:
                self._queue_service.update_single_metadata(task_id, "process_pid", str(pid))

            # Wait for completion and capture output
            output, _ = process.communicate()
            exit_code = process.returncode

        except FileNotFoundError:
            output = "Error: claude CLI not found"
            exit_code = 127
            pid = None
        except Exception as e:
            output = f"Error executing claude: {e}"
            exit_code = 1
            pid = None

        end_time = time.time()
        duration = int(end_time - start_time)

        # Write output and completion to log
        with open(log_file, "a") as f:
            f.write("=" * 70 + "\n")
            f.write("AGENT OUTPUT\n")
            f.write("=" * 70 + "\n\n")
            f.write(output or "(no output)")
            f.write("\n\n")
            f.write("=== Agent Execution Complete ===\n")
            f.write(f"End Time: {get_timestamp()}\n")
            f.write(f"Duration: {duration}s\n")
            f.write(f"Exit Code: {exit_code}\n")

        # Extract status from output
        status = self.extract_status(output or "")

        if status:
            with open(log_file, "a") as f:
                f.write(f"Exit Status: {status}\n")

        log_operation("TASK_EXECUTED", f"Task: {task_id}, Agent: {agent_name}, Status: {status}")

        return {
            "exit_code": exit_code,
            "status": status,
            "duration": duration,
            "pid": pid,
            "output": output,
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

    def _extract_and_store_learnings(
        self,
        output: str,
        agent_name: str,
        task_type: str,
        task_description: str,
        task_id: str,
    ) -> None:
        """
        Extract learnings from agent output and store them.

        Called automatically after successful task execution.
        """
        if not self._learnings_service:
            return

        try:
            learnings = self._learnings_service.extract_from_output(
                agent_output=output,
                agent_name=agent_name,
                task_type=task_type,
                task_description=task_description,
                task_id=task_id,
            )

            # Store each extracted learning
            for learning in learnings:
                self._learnings_service.store(learning)

            if learnings:
                log_operation(
                    "LEARNINGS_STORED",
                    f"Stored {len(learnings)} learnings from task {task_id}"
                )
        except Exception as e:
            # Don't fail task if learning extraction fails
            log_error(f"Failed to extract learnings from task {task_id}: {e}")