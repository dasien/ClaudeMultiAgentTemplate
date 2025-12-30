"""
CMAT Claude Code integration.

Provides a subprocess wrapper for invoking the Claude Code CLI
with proper configuration, output capture, and error handling.
"""

from .client import ClaudeClient
from .config import ClaudeClientConfig, OutputFormat
from .response import ClaudeResponse

__all__ = [
    "ClaudeClient",
    "ClaudeClientConfig",
    "ClaudeResponse",
    "OutputFormat",
]