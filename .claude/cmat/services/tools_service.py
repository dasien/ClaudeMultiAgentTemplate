"""
ToolsService for managing Claude Code tool definitions.

This service handles CRUD operations for tool definitions in tools.json,
which represent the Claude Code tools available to agents.
"""

import json
from pathlib import Path
from typing import Optional

from cmat.models.tool import Tool
from cmat.utils import find_project_root


class ToolsService:
    """
    Service for managing Claude Code tool definitions.

    Provides CRUD operations for tools.json, which defines the tools
    that can be assigned to agents in their configuration.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize ToolsService.

        Args:
            data_dir: Path to data directory containing tools.json.
                     If None, uses default location via find_project_root().
        """
        if data_dir is None:
            project_root = find_project_root()
            if project_root:
                self._data_dir = project_root / ".claude/data"
            else:
                self._data_dir = Path(".claude/data")
        else:
            self._data_dir = Path(data_dir)

        self._tools_file = self._data_dir / "tools.json"

    def _ensure_file_exists(self) -> None:
        """Ensure tools.json exists with default content."""
        if not self._tools_file.exists():
            self._data_dir.mkdir(parents=True, exist_ok=True)
            default_data = {
                "claude_code_tools": [
                    {
                        "name": "Read",
                        "display_name": "Read Files",
                        "description": "Read file contents from filesystem",
                    },
                    {
                        "name": "Write",
                        "display_name": "Write Files",
                        "description": "Create or overwrite files",
                    },
                    {
                        "name": "Edit",
                        "display_name": "Edit Files",
                        "description": "Make targeted edits to existing files",
                    },
                    {
                        "name": "Glob",
                        "display_name": "Pattern Match Files",
                        "description": "Find files matching patterns (e.g., '**/*.js')",
                    },
                    {
                        "name": "Grep",
                        "display_name": "Search File Contents",
                        "description": "Search for text patterns within files",
                    },
                    {
                        "name": "Bash",
                        "display_name": "Execute Shell Commands",
                        "description": "Execute shell commands and scripts",
                    },
                    {
                        "name": "WebSearch",
                        "display_name": "Web Search",
                        "description": "Search the web for current information",
                    },
                    {
                        "name": "WebFetch",
                        "display_name": "Fetch Web Page",
                        "description": "Retrieve full content from URLs",
                    },
                ]
            }
            with open(self._tools_file, "w") as f:
                json.dump(default_data, f, indent=2)

    def _load(self) -> dict:
        """Load tools.json."""
        self._ensure_file_exists()

        with open(self._tools_file) as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        """Save data to tools.json."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._tools_file, "w") as f:
            json.dump(data, f, indent=2)

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def list_all(self) -> list[Tool]:
        """
        List all available tools.

        Returns:
            List of Tool objects
        """
        data = self._load()
        tools = []
        for tool_data in data.get("claude_code_tools", []):
            tools.append(Tool.from_dict(tool_data))
        return tools

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by its name.

        Args:
            name: The tool name (e.g., "Read", "Write", "Bash")

        Returns:
            Tool if found, None otherwise
        """
        data = self._load()
        for tool_data in data.get("claude_code_tools", []):
            if tool_data.get("name") == name:
                return Tool.from_dict(tool_data)
        return None

    def add(self, tool: Tool) -> str:
        """
        Add a new tool.

        Args:
            tool: Tool to add

        Returns:
            The tool name

        Raises:
            ValueError: If tool with same name already exists
        """
        data = self._load()

        # Check for existing tool with same name
        for existing in data.get("claude_code_tools", []):
            if existing.get("name") == tool.name:
                raise ValueError(f"Tool already exists: {tool.name}")

        if "claude_code_tools" not in data:
            data["claude_code_tools"] = []

        data["claude_code_tools"].append(tool.to_dict())
        self._save(data)

        return tool.name

    def update(self, tool: Tool) -> bool:
        """
        Update an existing tool.

        Args:
            tool: Tool with updated data

        Returns:
            True if updated, False if tool not found
        """
        data = self._load()
        tools_list = data.get("claude_code_tools", [])

        for i, existing in enumerate(tools_list):
            if existing.get("name") == tool.name:
                tools_list[i] = tool.to_dict()
                self._save(data)
                return True

        return False

    def delete(self, name: str) -> bool:
        """
        Delete a tool.

        Args:
            name: Name of tool to delete

        Returns:
            True if deleted, False if not found
        """
        data = self._load()
        tools_list = data.get("claude_code_tools", [])

        for i, existing in enumerate(tools_list):
            if existing.get("name") == name:
                tools_list.pop(i)
                self._save(data)
                return True

        return False

    # =========================================================================
    # Query Operations
    # =========================================================================

    def get_tools_for_agent(self, tool_names: list[str]) -> list[Tool]:
        """
        Get tools assigned to an agent by their names.

        Args:
            tool_names: List of tool names from agent configuration

        Returns:
            List of Tool objects for valid tool names
        """
        tools = []
        for name in tool_names:
            tool = self.get(name)
            if tool:
                tools.append(tool)
        return tools

    def get_all_tool_names(self) -> list[str]:
        """
        Get list of all tool names.

        Returns:
            List of tool name strings
        """
        return [tool.name for tool in self.list_all()]