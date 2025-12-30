"""
Settings management for Claude Queue UI.
"""

import json
from pathlib import Path
from typing import Optional

class Settings:
    """Manages application settings persistence."""

    def __init__(self, settings_dir: Optional[Path] = None):
        """Initialize settings manager.

        Args:
            settings_dir: Directory to store settings (defaults to ~/.claude_queue_ui)
        """
        if settings_dir is None:
            settings_dir = Path.home() / ".claude_queue_ui"

        self.settings_dir = settings_dir
        self.settings_file = settings_dir / "settings.json"

        # Ensure settings directory exists
        self.settings_dir.mkdir(parents=True, exist_ok=True)

        # Load settings
        self._data = self._load()

    def _load(self) -> dict:
        """Load settings from file.

        Returns:
            Settings dictionary
        """
        if not self.settings_file.exists():
            return {}

        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, start fresh
            return {}

    def _save(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self._data, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save settings: {e}")

    # =============================================================================
    # Queue Manager Settings
    # =============================================================================

    def get_last_queue_manager(self) -> Optional[str]:
        """Get the last connected queue manager path.

        Returns:
            Path to queue_manager.sh or None if not set
        """
        return self._data.get('last_queue_manager')

    def set_last_queue_manager(self, path: str):
        """Set the last connected queue manager path.

        Args:
            path: Path to queue_manager.sh
        """
        self._data['last_queue_manager'] = path
        self._save()

    def clear_last_queue_manager(self):
        """Clear the last connected queue manager path."""
        if 'last_queue_manager' in self._data:
            del self._data['last_queue_manager']
            self._save()

    # =============================================================================
    # Claude API Settings
    # =============================================================================

    def get_claude_api_key(self) -> Optional[str]:
        """Get the Claude API key.

        Returns:
            API key or None if not set
        """
        return self._data.get('claude_api_key')

    def set_claude_api_key(self, api_key: str):
        """Set the Claude API key.

        Args:
            api_key: Claude API key
        """
        self._data['claude_api_key'] = api_key
        self._save()

    def clear_claude_api_key(self):
        """Clear the Claude API key."""
        if 'claude_api_key' in self._data:
            del self._data['claude_api_key']
            self._save()

    def get_claude_model(self) -> Optional[str]:
        """Get the selected Claude model.

        Returns:
            Model ID (e.g., 'claude-opus-4-20250514') or None if not set
        """
        return self._data.get('claude_model')

    def set_claude_model(self, model: str):
        """Set the Claude model to use.

        Args:
            model: Model ID (e.g., 'claude-opus-4-20250514')
        """
        self._data['claude_model'] = model
        self._save()

    def get_claude_max_tokens(self) -> Optional[int]:
        """Get the max tokens setting for Claude API.

        Returns:
            Max tokens or None if not set
        """
        return self._data.get('claude_max_tokens')

    def set_claude_max_tokens(self, max_tokens: int):
        """Set the max tokens for Claude API calls.

        Args:
            max_tokens: Maximum tokens for response
        """
        self._data['claude_max_tokens'] = max_tokens
        self._save()

    def get_claude_timeout(self) -> Optional[int]:
        """Get the timeout setting for Claude API calls.

        Returns:
            Timeout in seconds or None if not set
        """
        return self._data.get('claude_timeout')

    def set_claude_timeout(self, timeout: int):
        """Set the timeout for Claude API calls.

        Args:
            timeout: Timeout in seconds
        """
        self._data['claude_timeout'] = timeout
        self._save()

    def get_claude_config(self) -> dict:
        """Get complete Claude API configuration.

        Returns:
            Dictionary with 'api_key', 'model', and 'max_tokens'
            Uses defaults if values not set
        """
        # Default values
        DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
        DEFAULT_MAX_TOKENS = 8192

        return {
            'api_key': self.get_claude_api_key(),
            'model': self.get_claude_model() or DEFAULT_MODEL,
            'max_tokens': self.get_claude_max_tokens() or DEFAULT_MAX_TOKENS
        }

    # =============================================================================
    # CMAT Installation Settings
    # =============================================================================

    def get_last_install_directory(self) -> Optional[str]:
        """Get the last used CMAT installation directory.

        Returns:
            Path to last install directory or None if not set
        """
        return self._data.get('last_install_directory')

    def set_last_install_directory(self, path: str):
        """Set the last used CMAT installation directory.

        Args:
            path: Path to directory
        """
        self._data['last_install_directory'] = path
        self._save()

    def clear_last_install_directory(self):
        """Clear the last install directory."""
        if 'last_install_directory' in self._data:
            del self._data['last_install_directory']
            self._save()