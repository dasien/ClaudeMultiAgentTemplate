"""
Claude Code client for CMAT.

Provides a subprocess wrapper for invoking Claude Code CLI
with proper argument handling, output capture, and error management.
"""

import os
import select
import subprocess
import time
from pathlib import Path
from typing import Optional, Callable

from .config import ClaudeClientConfig, OutputFormat
from .response import ClaudeResponse
from ..utils import log_operation, log_error


class ClaudeClient:
    """
    Client for invoking Claude Code CLI.

    Wraps the `claude` command-line tool with proper argument handling,
    subprocess management, and output parsing.

    Usage:
        client = ClaudeClient()

        # Simple prompt
        response = client.run("Explain this code", config=ClaudeClientConfig(
            allowed_tools=["Read", "Glob"]
        ))

        # With system prompt from file
        response = client.run_with_agent_prompt(
            prompt="Analyze requirements",
            agent_prompt_file=".claude/agents/architect.md"
        )
    """

    def __init__(self, claude_path: str = "claude"):
        """
        Initialize the Claude client.

        Args:
            claude_path: Path to claude CLI executable (default: "claude" in PATH)
        """
        self.claude_path = claude_path

    def _build_args(self, prompt: str, config: ClaudeClientConfig) -> list[str]:
        """Build command-line arguments for claude CLI."""
        args = [self.claude_path]

        # Add print flag for non-interactive mode
        if config.print_mode:
            args.append("--print")

        # Model selection
        if config.model:
            args.extend(["--model", config.model])

        # Max turns
        if config.max_turns:
            args.extend(["--max-turns", str(config.max_turns)])

        # System prompts
        if config.system_prompt:
            args.extend(["--system-prompt", config.system_prompt])

        if config.append_system_prompt:
            args.extend(["--append-system-prompt", config.append_system_prompt])

        # Tool permissions
        if config.allowed_tools:
            args.extend(["--allowedTools", ",".join(config.allowed_tools)])

        if config.disallowed_tools:
            args.extend(["--disallowedTools", ",".join(config.disallowed_tools)])

        # MCP configuration
        if config.mcp_config:
            args.extend(["--mcp-config", config.mcp_config])

        # Permission mode
        if config.permission_mode:
            args.extend(["--permission-mode", config.permission_mode])

        # Output format
        if config.output_format != OutputFormat.TEXT:
            args.extend(["--output-format", config.output_format.value])

        # Verbose mode (required for stream-json with --print)
        if config.verbose:
            args.append("--verbose")

        # Session management
        if config.resume_session:
            args.extend(["--resume", config.resume_session])
        elif config.continue_session:
            args.append("--continue")

        # Add the prompt as positional argument
        if prompt:
            args.append(prompt)

        return args

    def run(
            self,
            prompt: str,
            config: Optional[ClaudeClientConfig] = None,
            line_callback: Optional[Callable[[str], None]] = None,
    ) -> ClaudeResponse:
        """
        Run a prompt through Claude Code with streaming output.

        Args:
            prompt: The prompt to send to Claude
            config: Configuration options (uses defaults if not provided)
            line_callback: Optional callback invoked for each line of output (for live monitoring)

        Returns:
            ClaudeResponse with output and metadata
        """
        config = config or ClaudeClientConfig()
        args = self._build_args(prompt, config)

        log_operation("CLAUDE_INVOKE", f"Prompt length: {len(prompt)}, Tools: {config.allowed_tools}")

        # Merge environment variables
        env = {**os.environ, **config.environment} if config.environment else None

        start_time = time.time()
        pid = None
        process = None

        try:
            # If input_text is provided, use communicate() for stdin handling
            # This is used for special commands like /init
            if config.input_text:
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    env=env,
                    text=True,
                    cwd=config.working_dir,
                )
                pid = process.pid

                output, _ = process.communicate(
                    input=config.input_text,
                    timeout=config.timeout,
                )
                exit_code = process.returncode
                duration = int(time.time() - start_time)

                if exit_code == 0:
                    return ClaudeResponse(
                        success=True,
                        output=output,
                        exit_code=exit_code,
                        pid=pid,
                        duration_seconds=duration,
                    )
                else:
                    log_error(f"Claude exited with code {exit_code}")
                    return ClaudeResponse(
                        success=False,
                        output=output,
                        exit_code=exit_code,
                        pid=pid,
                        duration_seconds=duration,
                    )

            # Standard execution: stream output line-by-line
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                env=env,
                text=True,
                cwd=config.working_dir,
                bufsize=1,  # Line buffered
            )
            pid = process.pid

            # Read output line-by-line with idle timeout
            output_lines = []
            last_output_time = time.time()
            idle_timeout = config.timeout  # Use configured timeout as idle timeout

            while True:
                # Check if process has ended
                if process.poll() is not None:
                    # Process ended, read any remaining output
                    for line in process.stdout:
                        output_lines.append(line)
                        if line_callback:
                            line_callback(line)
                    break

                # Use select to check if there's data to read (with 1 second timeout)
                ready, _, _ = select.select([process.stdout], [], [], 1.0)

                if ready:
                    line = process.stdout.readline()
                    if line:
                        output_lines.append(line)
                        last_output_time = time.time()
                        if line_callback:
                            line_callback(line)

                # Check for idle timeout
                if time.time() - last_output_time > idle_timeout:
                    log_error(f"Claude idle timeout after {idle_timeout}s of no output")
                    process.kill()
                    duration = int(time.time() - start_time)
                    return ClaudeResponse(
                        success=False,
                        output="".join(output_lines),
                        error=f"Idle timeout after {idle_timeout} seconds of no output",
                        exit_code=-1,
                        pid=pid,
                        duration_seconds=duration,
                    )

            exit_code = process.returncode
            duration = int(time.time() - start_time)
            output = "".join(output_lines)

            if exit_code == 0:
                return ClaudeResponse(
                    success=True,
                    output=output,
                    exit_code=exit_code,
                    pid=pid,
                    duration_seconds=duration,
                )
            else:
                log_error(f"Claude exited with code {exit_code}")
                return ClaudeResponse(
                    success=False,
                    output=output,
                    exit_code=exit_code,
                    pid=pid,
                    duration_seconds=duration,
                )

        except subprocess.TimeoutExpired:
            duration = int(time.time() - start_time)
            log_error(f"Claude timed out after {config.timeout}s")
            if process:
                process.kill()
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Timeout after {config.timeout} seconds",
                exit_code=-1,
                pid=pid,
                duration_seconds=duration,
            )
        except FileNotFoundError:
            duration = int(time.time() - start_time)
            log_error(f"Claude CLI not found at: {self.claude_path}")
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Claude CLI not found: {self.claude_path}",
                exit_code=-1,
                pid=pid,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = int(time.time() - start_time)
            log_error(f"Error invoking Claude: {str(e)}")
            if process:
                try:
                    process.kill()
                except Exception:
                    pass
            return ClaudeResponse(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                pid=pid,
                duration_seconds=duration,
            )

    def run_with_agent_prompt(
            self,
            prompt: str,
            agent_prompt_file: str,
            config: Optional[ClaudeClientConfig] = None,
    ) -> ClaudeResponse:
        """
        Run a prompt with an agent's system prompt loaded from file.

        Args:
            prompt: The task prompt to send
            agent_prompt_file: Path to agent's markdown file containing system prompt
            config: Additional configuration options

        Returns:
            ClaudeResponse with output and metadata
        """
        config = config or ClaudeClientConfig()

        # Load agent prompt from file
        agent_path = Path(agent_prompt_file)
        if not agent_path.exists():
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Agent prompt file not found: {agent_prompt_file}",
                exit_code=-1,
            )

        agent_prompt = agent_path.read_text()

        # Combine with any existing system prompt
        if config.system_prompt:
            config.system_prompt = f"{agent_prompt}\n\n{config.system_prompt}"
        else:
            config.system_prompt = agent_prompt

        return self.run(prompt, config)

    def run_with_skills(
            self,
            prompt: str,
            skills_content: str,
            config: Optional[ClaudeClientConfig] = None,
    ) -> ClaudeResponse:
        """
        Run a prompt with skills injected into the system prompt.

        Args:
            prompt: The task prompt to send
            skills_content: Combined skills content to inject
            config: Additional configuration options

        Returns:
            ClaudeResponse with output and metadata
        """
        config = config or ClaudeClientConfig()

        skills_section = f"## Available Skills\n\n{skills_content}"

        if config.append_system_prompt:
            config.append_system_prompt = f"{config.append_system_prompt}\n\n{skills_section}"
        else:
            config.append_system_prompt = skills_section

        return self.run(prompt, config)

    def check_available(self) -> bool:
        """Check if the Claude CLI is available."""
        try:
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def get_version(self) -> Optional[str]:
        """Get the Claude CLI version string."""
        try:
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None