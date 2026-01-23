"""
Agent event models for parsing Claude CLI stream-json output.

Provides structured representations of streaming events from Claude Code,
enabling real-time monitoring and human-readable log generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EventType(Enum):
    """Types of events from Claude CLI stream-json output."""

    INIT = "init"  # Session initialization
    ASSISTANT_TEXT = "assistant_text"  # Assistant reasoning/thinking
    TOOL_USE = "tool_use"  # Tool invocation
    TOOL_RESULT = "tool_result"  # Tool result returned
    RESULT = "result"  # Final completion result
    ERROR = "error"  # Error event
    UNKNOWN = "unknown"  # Unrecognized event type


@dataclass
class AgentEvent:
    """
    Represents a parsed event from Claude CLI stream-json output.

    Each JSON line from stream-json output is parsed into an AgentEvent
    for structured handling in the UI and log formatting.
    """

    event_type: EventType
    timestamp: str
    raw_data: dict = field(default_factory=dict, repr=False)

    # For INIT events
    model: Optional[str] = None
    session_id: Optional[str] = None
    tools: list[str] = field(default_factory=list)

    # For ASSISTANT_TEXT events
    text: Optional[str] = None

    # For TOOL_USE events
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_use_id: Optional[str] = None

    # For TOOL_RESULT events
    tool_result_content: Optional[str] = None
    tool_result_id: Optional[str] = None
    tool_duration_ms: Optional[int] = None

    # For RESULT events
    is_error: bool = False
    duration_ms: Optional[int] = None
    num_turns: Optional[int] = None
    total_cost_usd: Optional[float] = None
    result_text: Optional[str] = None

    # Token usage (from RESULT or assistant messages)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_read_tokens: Optional[int] = None
    cache_write_tokens: Optional[int] = None

    @classmethod
    def from_json(cls, data: dict) -> "AgentEvent":
        """
        Parse a stream-json line into an AgentEvent.

        Args:
            data: Parsed JSON dict from a stream-json line

        Returns:
            AgentEvent representing the parsed data
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_type_str = data.get("type", "")
        subtype = data.get("subtype", "")

        # System init event
        if event_type_str == "system" and subtype == "init":
            return cls(
                event_type=EventType.INIT,
                timestamp=timestamp,
                raw_data=data,
                model=data.get("model"),
                session_id=data.get("session_id"),
                tools=data.get("tools", []),
            )

        # Final result event
        if event_type_str == "result":
            # Note: The result event's "usage" field contains only the final turn's tokens.
            # To get cumulative totals, we sum from "modelUsage" which has per-model breakdowns.
            model_usage = data.get("modelUsage", {})
            total_input = 0
            total_output = 0
            total_cache_read = 0
            total_cache_creation = 0
            for model_data in model_usage.values():
                total_input += model_data.get("inputTokens", 0)
                total_output += model_data.get("outputTokens", 0)
                total_cache_read += model_data.get("cacheReadInputTokens", 0)
                total_cache_creation += model_data.get("cacheCreationInputTokens", 0)

            return cls(
                event_type=EventType.RESULT,
                timestamp=timestamp,
                raw_data=data,
                is_error=data.get("is_error", False),
                duration_ms=data.get("duration_ms"),
                num_turns=data.get("num_turns"),
                total_cost_usd=data.get("total_cost_usd"),
                result_text=data.get("result"),
                input_tokens=total_input if total_input else None,
                output_tokens=total_output if total_output else None,
                cache_read_tokens=total_cache_read if total_cache_read else None,
                cache_write_tokens=total_cache_creation if total_cache_creation else None,
            )

        # Assistant message (text or tool_use)
        if event_type_str == "assistant":
            message = data.get("message", {})
            content = message.get("content", [])

            # Extract usage if present
            usage = message.get("usage", {})

            for item in content:
                item_type = item.get("type")

                if item_type == "tool_use":
                    return cls(
                        event_type=EventType.TOOL_USE,
                        timestamp=timestamp,
                        raw_data=data,
                        tool_name=item.get("name"),
                        tool_input=item.get("input", {}),
                        tool_use_id=item.get("id"),
                        input_tokens=usage.get("input_tokens"),
                        output_tokens=usage.get("output_tokens"),
                    )

                if item_type == "text":
                    text = item.get("text", "")
                    if text.strip():  # Only create event if there's actual text
                        return cls(
                            event_type=EventType.ASSISTANT_TEXT,
                            timestamp=timestamp,
                            raw_data=data,
                            text=text,
                            input_tokens=usage.get("input_tokens"),
                            output_tokens=usage.get("output_tokens"),
                        )

            # If we get here with content but no recognized items, return unknown
            if content:
                return cls(
                    event_type=EventType.UNKNOWN,
                    timestamp=timestamp,
                    raw_data=data,
                )

        # User message (tool_result)
        if event_type_str == "user":
            message = data.get("message", {})
            content = message.get("content", [])
            tool_result_meta = data.get("tool_use_result")
            # tool_use_result can be dict or other type
            duration_ms = None
            if isinstance(tool_result_meta, dict):
                duration_ms = tool_result_meta.get("durationMs")

            for item in content:
                if item.get("type") == "tool_result":
                    result_content = item.get("content", "")
                    # Handle case where content is a list (multiple results)
                    if isinstance(result_content, list):
                        result_content = "\n".join(str(r) for r in result_content)

                    return cls(
                        event_type=EventType.TOOL_RESULT,
                        timestamp=timestamp,
                        raw_data=data,
                        tool_result_content=result_content,
                        tool_result_id=item.get("tool_use_id"),
                        tool_duration_ms=duration_ms,
                    )

        # Unrecognized event
        return cls(
            event_type=EventType.UNKNOWN,
            timestamp=timestamp,
            raw_data=data,
        )

    def format_human_readable(self, wrap_threshold: int = 500) -> str:
        """
        Format this event as human-readable text for logs.

        Short content stays on one line. Long content (>wrap_threshold) wraps
        to subsequent indented lines.

        Args:
            wrap_threshold: Character count before wrapping to new lines

        Returns:
            Formatted string representation of the event
        """
        lines = []

        if self.event_type == EventType.INIT:
            lines.append(f"[{self.timestamp}] === Session Started === Model: {self.model} | Session: {self.session_id} | Tools: {len(self.tools)}")

        elif self.event_type == EventType.ASSISTANT_TEXT:
            text = self.text or ""
            if len(text) <= wrap_threshold and "\n" not in text:
                lines.append(f"[{self.timestamp}] Assistant: {text}")
            else:
                lines.append(f"[{self.timestamp}] Assistant:")
                for line in text.split("\n"):
                    lines.append(f"    {line}")

        elif self.event_type == EventType.TOOL_USE:
            input_str = self._format_tool_input(self.tool_input) if self.tool_input else ""
            if len(input_str) <= wrap_threshold and "\n" not in input_str:
                lines.append(f"[{self.timestamp}] Tool:{self.tool_name} | {input_str}")
            else:
                lines.append(f"[{self.timestamp}] Tool:{self.tool_name}")
                for line in input_str.split("\n"):
                    lines.append(f"    {line}")

        elif self.event_type == EventType.TOOL_RESULT:
            duration_str = f" ({self.tool_duration_ms}ms)" if self.tool_duration_ms else ""
            result = self.tool_result_content or ""
            if len(result) <= wrap_threshold and "\n" not in result:
                lines.append(f"[{self.timestamp}] Result{duration_str}: {result}")
            else:
                lines.append(f"[{self.timestamp}] Result{duration_str}:")
                for line in result.split("\n"):
                    lines.append(f"    {line}")

        elif self.event_type == EventType.RESULT:
            status = "FAILED" if self.is_error else "COMPLETE"
            parts = [f"[{self.timestamp}] === {status} ==="]
            if self.duration_ms:
                parts.append(f"Duration: {self.duration_ms / 1000:.1f}s")
            if self.num_turns:
                parts.append(f"Turns: {self.num_turns}")
            if self.total_cost_usd:
                parts.append(f"Cost: ${self.total_cost_usd:.4f}")
            if self.input_tokens or self.output_tokens:
                parts.append(f"Tokens: {self.input_tokens or 0} in / {self.output_tokens or 0} out")
            lines.append(" | ".join(parts))

        elif self.event_type == EventType.ERROR:
            lines.append(f"[{self.timestamp}] Error: {self.text or 'Unknown error'}")

        return "\n".join(lines)

    def _format_tool_input(self, input_dict: dict) -> str:
        """Format tool input dict for display."""
        if not input_dict:
            return "{}"

        parts = []
        for key, value in input_dict.items():
            parts.append(f"{key}={value}")

        return ", ".join(parts)