# src/models/enhancement_source.py
"""
Enhancement source data model.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class SourceType(Enum):
    """Types of enhancement sources."""
    FILE = "file"
    GITHUB_ISSUE = "github_issue"
    WEB_URL = "web_url"


@dataclass
class EnhancementSource:
    """Enhancement source data model."""
    type: SourceType
    value: str  # File path, URL, etc.
    display_name: str
    status: str = 'pending'  # pending, fetching, success, error
    error_message: Optional[str] = None

    @staticmethod
    def from_file(file_path: str, display_name: str) -> 'EnhancementSource':
        """Create source from local file."""
        return EnhancementSource(
            type=SourceType.FILE,
            value=file_path,
            display_name=display_name,
            status='success'  # Files are immediately available
        )

    @staticmethod
    def from_github_issue(url: str, issue_title: str) -> 'EnhancementSource':
        """Create source from GitHub issue URL."""
        return EnhancementSource(
            type=SourceType.GITHUB_ISSUE,
            value=url,
            display_name=f"GitHub: {issue_title}",
            status='pending'
        )

    @staticmethod
    def from_web_url(url: str, page_title: Optional[str] = None) -> 'EnhancementSource':
        """Create source from web URL."""
        display = page_title if page_title else url
        return EnhancementSource(
            type=SourceType.WEB_URL,
            value=url,
            display_name=f"Web: {display}",
            status='pending'
        )

    def get_icon(self) -> str:
        """Get emoji icon for source type."""
        icons = {
            SourceType.FILE: "📄",
            SourceType.GITHUB_ISSUE: "🔗",
            SourceType.WEB_URL: "🌐"
        }
        return icons.get(self.type, "📋")