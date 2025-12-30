# src/utils/web_utils.py
"""
Web utility functions for fetching external content.
"""

import urllib.request
import json
import re
from typing import Optional, Tuple


class WebUtils:
    """Utilities for fetching content from web sources."""

    # src/utils/web_utils.py
    """
    Web utility functions for fetching external content.
    """

    import urllib.request
    import json
    import re
    from typing import Optional, Tuple

    # Timeouts
    DEFAULT_TIMEOUT = 10  # seconds

    # User agent
    DEFAULT_USER_AGENT = 'ClaudeMultiAgentUI/1.0'

    # Size limits
    MAX_CONTENT_LENGTH = 100_000  # 100KB max for web content
    MAX_FILE_SIZE = 100_000  # 100KB max for local files
    TRUNCATE_THRESHOLD = 10_000  # Truncate content above this size

    @staticmethod
    def fetch_github_issue(url: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[str, str]:
        """
        Fetch GitHub issue content via API.

        Args:
            url: GitHub issue URL (e.g., https://github.com/owner/repo/issues/123)
            timeout: Request timeout in seconds

        Returns:
            Tuple of (title, body_content)

        Raises:
            ValueError: If URL is invalid
            urllib.error.URLError: If request fails

        Examples:
            >>> title, body = WebUtils.fetch_github_issue("https://github.com/owner/repo/issues/123")
        """
        # Extract owner, repo, issue number from URL
        match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
        if not match:
            raise ValueError("Invalid GitHub issue URL")

        owner, repo, issue_num = match.groups()

        # Use GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', WebUtils.DEFAULT_USER_AGENT)
        req.add_header('Accept', 'application/vnd.github.v3+json')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))

            title = data.get('title', '')
            body = data.get('body', '') or ''

            return title, body

    @staticmethod
    def parse_github_issue_url(url: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse GitHub issue URL into components.

        Args:
            url: GitHub issue URL

        Returns:
            Tuple of (owner, repo, issue_number) or None if invalid

        Examples:
            >>> WebUtils.parse_github_issue_url("https://github.com/owner/repo/issues/123")
            ('owner', 'repo', '123')
        """
        match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
        if match:
            return match.groups()
        return None

    @staticmethod
    def is_github_issue_url(url: str) -> bool:
        """
        Check if URL is a valid GitHub issue URL.

        Args:
            url: URL to check

        Returns:
            True if valid GitHub issue URL

        Examples:
            >>> WebUtils.is_github_issue_url("https://github.com/owner/repo/issues/123")
            True
        """
        return WebUtils.parse_github_issue_url(url) is not None

    @staticmethod
    def fetch_web_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Fetch web page content with basic HTML stripping.

        Args:
            url: Web page URL
            timeout: Request timeout in seconds

        Returns:
            Plain text content (HTML stripped)

        Raises:
            ValueError: If URL is invalid
            urllib.error.URLError: If request fails

        Examples:
            >>> content = WebUtils.fetch_web_page("https://example.com/article")
        """
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")

        req = urllib.request.Request(url)
        req.add_header('User-Agent', WebUtils.DEFAULT_USER_AGENT)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Check content length
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > WebUtils.MAX_CONTENT_LENGTH:
                raise ValueError(f"Content too large: {content_length} bytes")

            html = response.read().decode('utf-8', errors='ignore')

            # Basic HTML stripping
            text = WebUtils._strip_html(html)

            # Limit size
            if len(text) > WebUtils.MAX_CONTENT_LENGTH:
                text = text[:WebUtils.MAX_CONTENT_LENGTH] + "\n...[truncated]"

            return text

    @staticmethod
    def _strip_html(html: str) -> str:
        """
        Basic HTML tag stripping.

        Args:
            html: HTML content

        Returns:
            Plain text with HTML tags removed

        Note:
            This is a basic implementation. For production use,
            consider using a library like BeautifulSoup or html2text.
        """
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        text = WebUtils._decode_html_entities(text)

        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines -> double newline
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces -> single space

        return text.strip()

    @staticmethod
    def _decode_html_entities(text: str) -> str:
        """
        Decode common HTML entities.

        Args:
            text: Text with HTML entities

        Returns:
            Text with entities decoded
        """
        import html
        return html.unescape(text)

    @staticmethod
    def format_github_issue_content(title: str, body: str) -> str:
        """
        Format GitHub issue into markdown.

        Args:
            title: Issue title
            body: Issue body

        Returns:
            Formatted markdown content

        Examples:
            >>> content = WebUtils.format_github_issue_content("Bug: Login fails", "Steps to reproduce...")
        """
        parts = [f"# {title}"]

        if body:
            parts.append("")
            parts.append(body)

        return "\n".join(parts)

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format and accessibility.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)

        Examples:
            >>> valid, error = WebUtils.validate_url("https://example.com")
            >>> if not valid:
            ...     print(f"Invalid URL: {error}")
        """
        if not url:
            return False, "URL cannot be empty"

        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"

        # Basic URL pattern check
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            return False, "URL format is invalid"

        return True, None