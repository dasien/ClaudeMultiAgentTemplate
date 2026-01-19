"""
ToolsService for managing Claude Code tool definitions.

This service handles CRUD operations for tool definitions in tools.json,
which represent the Claude Code tools available to agents.
"""

from typing import Optional

from core.models.tool import Tool
from core.services.base import JSONFileServiceMixin


class ToolsService(JSONFileServiceMixin):
    """
    Service for managing Claude Code tool definitions.

    Provides CRUD operations for tools.json, which defines the tools
    that can be assigned to agents in their configuration.
    """

    COLLECTION_KEY = "claude_code_tools"

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize ToolsService.

        Args:
            data_dir: Path to data directory containing tools.json.
                     If None, uses default location via find_project_root().
        """
        self._init_data_path(data_dir, "tools.json")
        self._ensure_file_exists()

    def _get_default_data(self) -> dict:
        """Get default tools data structure."""
        return {
            self.COLLECTION_KEY: [
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

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def list_all(self) -> list[Tool]:
        """
        List all available tools.

        Returns:
            List of Tool objects
        """
        collection = self._read_collection(Tool, self.COLLECTION_KEY, "name")
        return list(collection.values())

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by its name.

        Args:
            name: The tool name (e.g., "Read", "Write", "Bash")

        Returns:
            Tool if found, None otherwise
        """
        collection = self._read_collection(Tool, self.COLLECTION_KEY, "name")
        return collection.get(name)

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
        collection = self._read_collection(Tool, self.COLLECTION_KEY, "name")

        # Check for existing tool with same name
        if tool.name in collection:
            raise ValueError(f"Tool already exists: {tool.name}")

        collection[tool.name] = tool
        self._write_collection(collection, self.COLLECTION_KEY)

        return tool.name

    def update(self, tool: Tool) -> bool:
        """
        Update an existing tool.

        Args:
            tool: Tool with updated data

        Returns:
            True if updated, False if tool not found
        """
        collection = self._read_collection(Tool, self.COLLECTION_KEY, "name")

        if tool.name not in collection:
            return False

        collection[tool.name] = tool
        self._write_collection(collection, self.COLLECTION_KEY)

        return True

    def delete(self, name: str) -> bool:
        """
        Delete a tool.

        Args:
            name: Name of tool to delete

        Returns:
            True if deleted, False if not found
        """
        collection = self._read_collection(Tool, self.COLLECTION_KEY, "name")

        if name not in collection:
            return False

        del collection[name]
        self._write_collection(collection, self.COLLECTION_KEY)

        return True

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
