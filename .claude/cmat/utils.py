"""
Utility functions for CMAT.

Provides shared utilities for timestamps, logging, path resolution,
directory management, and dependency checking.
"""

import logging
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Configure module logger
logger = logging.getLogger("cmat")


def get_timestamp() -> str:
    """Generate ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_datetime_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the project root by locating the .claude directory.

    Walks up the directory tree from start_path (or cwd) looking for .claude/.

    Returns:
        Path to project root, or None if not found.
    """
    current = start_path or Path.cwd()

    while current != current.parent:
        if (current / ".claude").is_dir():
            return current
        current = current.parent

    # Check root as well
    if (current / ".claude").is_dir():
        return current

    return None


def ensure_directories(base_path: Optional[Path] = None) -> None:
    """
    Ensure all required CMAT directories exist.

    Creates the directory structure if it doesn't exist.
    """
    base = base_path or Path.cwd()

    directories = [
        base / ".claude/queues",
        base / ".claude/logs",
        base / ".claude/status",
        base / ".claude/agents",
        base / ".claude/skills",
        base / ".claude/models",
        base / "enhancements",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def log_operation(operation: str, details: str, logs_dir: Optional[Path] = None) -> None:
    """
    Log an operation to the queue operations log file.

    Args:
        operation: Operation name (e.g., "TASK_ADDED", "ERROR")
        details: Details about the operation
        logs_dir: Path to logs directory (defaults to .claude/logs)
    """
    logs_path = logs_dir or Path(".claude/logs")
    logs_path.mkdir(parents=True, exist_ok=True)

    log_file = logs_path / "queue_operations.log"
    timestamp = get_timestamp()

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {operation}: {details}\n")

    logger.debug(f"{operation}: {details}")


def log_error(message: str, logs_dir: Optional[Path] = None) -> None:
    """Log an error message."""
    logger.error(message)
    log_operation("ERROR", message, logs_dir)


def log_info(message: str, logs_dir: Optional[Path] = None) -> None:
    """Log an info message."""
    logger.info(message)
    log_operation("INFO", message, logs_dir)


def check_dependencies() -> dict:
    """
    Check for required and optional dependencies.

    Returns:
        Dictionary with dependency status:
        {
            "satisfied": bool,
            "dependencies": {
                "name": {"found": bool, "version": str|None, "required": bool}
            }
        }
    """
    deps = {}
    all_satisfied = True

    # Check jq
    jq_version = _get_command_version("jq", ["--version"], r"[\d.]+")
    deps["jq"] = {"found": jq_version is not None, "version": jq_version, "required": True}
    if not jq_version:
        all_satisfied = False

    # Check claude
    claude_version = _get_command_version("claude", ["--version"], r"[\d.]+")
    deps["claude"] = {"found": claude_version is not None, "version": claude_version, "required": True}
    if not claude_version:
        all_satisfied = False

    # Check git (optional)
    git_version = _get_command_version("git", ["--version"], r"[\d.]+")
    deps["git"] = {"found": git_version is not None, "version": git_version, "required": False}

    # Check python
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    deps["python"] = {"found": True, "version": python_version, "required": True}

    return {
        "satisfied": all_satisfied,
        "dependencies": deps
    }


def _get_command_version(command: str, args: list, pattern: str) -> Optional[str]:
    """Get version string from a command, or None if not found."""
    if not shutil.which(command):
        return None

    try:
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout + result.stderr
        match = re.search(pattern, output)
        return match.group(0) if match else "unknown"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return "unknown"


def extract_enhancement_name(source_file: str, task_id: Optional[str] = None) -> str:
    """
    Extract enhancement name from a source file path.

    Parses paths like "enhancements/my-feature/my-feature.md" to extract "my-feature".

    Args:
        source_file: Path to source file
        task_id: Fallback task ID if extraction fails

    Returns:
        Enhancement name, task_id as fallback, or "unknown"
    """
    if source_file:
        # Match enhancements/{name}/... pattern
        match = re.match(r"^enhancements/([^/]+)/", source_file)
        if match:
            return match.group(1)

    if task_id:
        return task_id

    return "unknown"


def extract_enhancement_title(source_file: str) -> str:
    """
    Extract enhancement title from a source file's content.

    Looks for "Title:", "Enhancement:", or "Bug Fix:" fields in the file.

    Args:
        source_file: Path to source file

    Returns:
        Enhancement title or "Not part of an Enhancement"
    """
    path = Path(source_file)

    if not path.exists():
        return "Not part of an Enhancement"

    try:
        content = path.read_text()
    except (IOError, OSError):
        return "Not part of an Enhancement"

    # Patterns to match (with or without markdown header)
    patterns = [
        r"^#*\s*Title:\s*(.+)$",
        r"^#*\s*Enhancement:\s*(.+)$",
        r"^#*\s*Bug Fix:\s*(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1).strip()

    return "Not part of an Enhancement"


def needs_integration(status: str) -> bool:
    """
    Check if a status indicates integration actions are needed.

    Args:
        status: Task completion status

    Returns:
        True if integration sync should be triggered
    """
    integration_statuses = [
        "READY_FOR_DEVELOPMENT",
        "READY_FOR_IMPLEMENTATION",
        "READY_FOR_TESTING",
        "TESTING_COMPLETE",
        "DOCUMENTATION_COMPLETE",
    ]

    return any(s in status for s in integration_statuses)


def configure_logging(
        level: int = logging.INFO,
        log_file: Optional[Path] = None
) -> None:
    """
    Configure CMAT logging.

    Args:
        level: Logging level (default INFO)
        log_file: Optional file to write logs to
    """
    handlers = [logging.StreamHandler()]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers
    )