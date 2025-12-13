"""
Claude Code client configuration.

Configuration options for invoking Claude Code CLI.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OutputFormat(Enum):
    """Output format options for Claude Code."""
    TEXT = "text"
    JSON = "json"
    STREAM_JSON = "stream-json"


@dataclass
class ClaudeClientConfig:
    """Configuration for Claude Code client."""
    model: Optional[str] = None
    max_turns: Optional[int] = None
    system_prompt: Optional[str] = None
    append_system_prompt: Optional[str] = None
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    mcp_config: Optional[str] = None
    permission_mode: Optional[str] = None  # default, acceptEdits, bypassPermissions
    output_format: OutputFormat = OutputFormat.TEXT
    timeout: int = 600  # 10 minutes default
    working_dir: Optional[str] = None
    resume_session: Optional[str] = None
    continue_session: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "max_turns": self.max_turns,
            "system_prompt": self.system_prompt,
            "append_system_prompt": self.append_system_prompt,
            "allowed_tools": self.allowed_tools,
            "disallowed_tools": self.disallowed_tools,
            "mcp_config": self.mcp_config,
            "permission_mode": self.permission_mode,
            "output_format": self.output_format.value,
            "timeout": self.timeout,
            "working_dir": self.working_dir,
            "resume_session": self.resume_session,
            "continue_session": self.continue_session,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClaudeClientConfig":
        """Create ClaudeClientConfig from dictionary."""
        output_format = data.get("output_format", "text")
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        return cls(
            model=data.get("model"),
            max_turns=data.get("max_turns"),
            system_prompt=data.get("system_prompt"),
            append_system_prompt=data.get("append_system_prompt"),
            allowed_tools=data.get("allowed_tools", []),
            disallowed_tools=data.get("disallowed_tools", []),
            mcp_config=data.get("mcp_config"),
            permission_mode=data.get("permission_mode"),
            output_format=output_format,
            timeout=data.get("timeout", 600),
            working_dir=data.get("working_dir"),
            resume_session=data.get("resume_session"),
            continue_session=data.get("continue_session", False),
        )