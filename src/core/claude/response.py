"""
Claude Code response model.

Represents the response from a Claude Code CLI invocation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClaudeResponse:
    """Response from a Claude Code invocation."""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    session_id: Optional[str] = None
    cost_usd: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "session_id": self.session_id,
            "cost_usd": self.cost_usd,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClaudeResponse":
        """Create ClaudeResponse from dictionary."""
        return cls(
            success=data["success"],
            output=data["output"],
            error=data.get("error"),
            exit_code=data.get("exit_code", 0),
            session_id=data.get("session_id"),
            cost_usd=data.get("cost_usd"),
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
        )