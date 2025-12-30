"""
Path utility functions.
"""

from pathlib import Path
from typing import Union


class PathUtils:
    """Utilities for working with file paths."""

    @staticmethod
    def find_output_file(output_dir: Union[str, Path]) -> Path:
        """
        Find the primary output file from agent execution.

        Looks for known output patterns from different agents:
        - enhancement-spec.md (Product Analyst)
        - agent-definition.md (Agent Architect)
        - tasks.md (Task Planner)
        - output.md (generic fallback)

        Falls back to first .md file found if no known patterns match.

        Args:
            output_dir: Directory to search for output files

        Returns:
            Path to the primary output file

        Raises:
            FileNotFoundError: If no output file found

        Examples:
            >>> PathUtils.find_output_file("/tmp/product-analyst")
            Path('/tmp/product-analyst/enhancement-spec.md')
        """
        output_dir = Path(output_dir)

        # Try known output file names in priority order
        known_outputs = [
            "enhancement-spec.md",  # Product Analyst
            "agent-definition.md",  # Agent Architect
            "tasks.md",  # Task Planner
            "output.md"  # Generic fallback
        ]

        for filename in known_outputs:
            output_file = output_dir / filename
            if output_file.exists():
                return output_file

        # Fall back to first .md file
        md_files = list(output_dir.glob("*.md"))
        if md_files:
            return md_files[0]

        raise FileNotFoundError(
            f"No output file found in {output_dir}. "
            "Agent may not have produced expected output."
        )

    @staticmethod
    def relative_to_project(file_path: Union[str, Path], 
                           project_root: Union[str, Path]) -> str:
        """
        Get path relative to project root, or fallback to absolute/name.
        
        Args:
            file_path: File path to convert
            project_root: Project root directory
        
        Returns:
            Relative path if possible, otherwise absolute path
        
        Examples:
            >>> PathUtils.relative_to_project("/home/user/project/src/file.py", "/home/user/project")
            'src/file.py'
            
            >>> PathUtils.relative_to_project("/other/file.py", "/home/user/project")
            '/other/file.py'
        """
        file_path = Path(file_path)
        project_root = Path(project_root)
        
        try:
            return str(file_path.relative_to(project_root))
        except ValueError:
            return str(file_path)
    
    @staticmethod
    def relative_or_name(file_path: Union[str, Path], 
                        project_root: Union[str, Path]) -> str:
        """
        Get path relative to project root, or just the filename.
        
        Args:
            file_path: File path to convert
            project_root: Project root directory
        
        Returns:
            Relative path if possible, otherwise just the filename
        
        Examples:
            >>> PathUtils.relative_or_name("/home/user/project/src/file.py", "/home/user/project")
            'src/file.py'
            
            >>> PathUtils.relative_or_name("/other/location/file.py", "/home/user/project")
            'file.py'
        """
        file_path = Path(file_path)
        project_root = Path(project_root)
        
        try:
            return str(file_path.relative_to(project_root))
        except ValueError:
            return file_path.name
