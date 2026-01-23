"""
Stream formatter for Claude CLI stream-json output.

Converts streaming JSON events into human-readable log output,
with support for real-time callbacks and cost accumulation.
"""

import json
from typing import Callable, Optional

from core.models.agent_event import AgentEvent, EventType


class StreamFormatter:
    """
    Formats Claude CLI stream-json output into human-readable text.

    Maintains state across events to track accumulated costs and
    provide context-aware formatting.

    Usage:
        formatter = StreamFormatter()

        # Format a single JSON line
        text = formatter.format_line('{"type":"system","subtype":"init",...}')

        # Or process with callback
        def on_text(text: str):
            print(text, end="")

        formatter.format_line(json_line, callback=on_text)
    """

    def __init__(self):
        """Initialize the formatter."""
        self.total_cost = 0.0
        self.num_turns = 0
        self.current_model: Optional[str] = None
        self.session_id: Optional[str] = None
        self._last_tool_name: Optional[str] = None

    def format_line(
        self,
        json_line: str,
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Format a single JSON line from stream-json output.

        Args:
            json_line: Raw JSON line from Claude CLI
            callback: Optional callback to receive formatted text

        Returns:
            Human-readable formatted text (empty string if line couldn't be parsed)
        """
        json_line = json_line.strip()
        if not json_line:
            return ""

        try:
            data = json.loads(json_line)
        except json.JSONDecodeError:
            # Non-JSON line, return as-is
            result = f"{json_line}\n"
            if callback:
                callback(result)
            return result

        # Parse into AgentEvent
        event = AgentEvent.from_json(data)

        # Track state for context
        if event.event_type == EventType.INIT:
            self.current_model = event.model
            self.session_id = event.session_id

        if event.event_type == EventType.TOOL_USE:
            self._last_tool_name = event.tool_name

        if event.event_type == EventType.RESULT:
            self.total_cost = event.total_cost_usd or 0.0
            self.num_turns = event.num_turns or 0

        # Skip unknown events
        if event.event_type == EventType.UNKNOWN:
            return ""

        # Format the event
        formatted = event.format_human_readable()

        if callback and formatted:
            callback(formatted)

        return formatted

    def format_all(
        self,
        json_lines: list[str],
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Format multiple JSON lines.

        Args:
            json_lines: List of JSON lines
            callback: Optional callback for each formatted line

        Returns:
            Complete formatted output
        """
        results = []
        for line in json_lines:
            formatted = self.format_line(line, callback)
            if formatted:
                results.append(formatted)
        return "\n".join(results)

    def get_event(self, json_line: str) -> Optional[AgentEvent]:
        """
        Parse a JSON line into an AgentEvent without formatting.

        Args:
            json_line: Raw JSON line

        Returns:
            Parsed AgentEvent or None if parsing fails
        """
        json_line = json_line.strip()
        if not json_line:
            return None

        try:
            data = json.loads(json_line)
            event = AgentEvent.from_json(data)
            if event.event_type == EventType.UNKNOWN:
                return None
            return event
        except json.JSONDecodeError:
            return None


def convert_log_file(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert a stream-json log file to human-readable format.

    Args:
        input_path: Path to JSON log file
        output_path: Optional output path (prints to stdout if not provided)

    Returns:
        Formatted log content
    """
    formatter = StreamFormatter()

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find where JSON starts (skip header)
    json_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("{"):
            json_start = i
            break

    # Keep header (non-JSON lines)
    header = "".join(lines[:json_start])

    # Format JSON lines
    json_lines = lines[json_start:]
    formatted = formatter.format_all(json_lines)

    result = header + formatted

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)

    return result
