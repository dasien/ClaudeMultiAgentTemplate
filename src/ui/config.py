"""
Configuration settings for the CMAT system.
"""

from typing import Dict, List


class Config:
    """Application configuration."""

    # Application info
    APP_NAME = "Claude Multi-Agent Manager"
    VERSION = "10.2.0"

    # Auto-refresh settings for main task view
    AUTO_REFRESH_INTERVAL = 3  # seconds
    AUTO_REFRESH_ENABLED_DEFAULT = True

    # Operations log settings
    MAX_LOG_LINES = 1000

    # UI settings
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 500

    # Status colors
    STATUS_COLORS = {
        'pending': '#2196F3',  # Blue
        'active': '#FF9800',  # Orange
        'completed': '#4CAF50',  # Green
        'failed': '#F44336',  # Red
        'cancelled': '#9E9E9E'  # Grey
    }

    # Priority colors
    PRIORITY_COLORS = {
        'critical': '#F44336',  # Red
        'high': '#FF9800',  # Orange
        'normal': '#000000',  # Black
        'low': '#9E9E9E'  # Gray
    }

    # Row background colors (subtle)
    ROW_COLORS = {
        'pending': '#FFFFFF',  # White
        'active': '#FFF9E6',  # Light yellow
        'completed': '#E8F5E9',  # Light green
        'failed': '#FFEBEE',  # Light red
        'cancelled': '#F5F5F5'  # Light grey
    }


class ClaudeConfig:
    """
    Centralized Claude API configuration.
    Single source of truth for Claude models and defaults.
    """

    # Default Claude settings
    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    DEFAULT_MAX_TOKENS = 8192
    DEFAULT_TIMEOUT = 300  # seconds - generous for long generations

    # Available Claude models with their specifications
    MODELS = {
        "claude-opus-4-20250514": {
            "name": "Claude Opus 4",
            "max_tokens": 16384,
            "description": "Most capable model, 16K output"
        },
        "claude-sonnet-4-5-20250929": {
            "name": "Claude Sonnet 4.5",
            "max_tokens": 8192,
            "description": "Smartest model, efficient, 8K output"
        },
        "claude-sonnet-4-20250514": {
            "name": "Claude Sonnet 4",
            "max_tokens": 8192,
            "description": "Balanced performance, 8K output"
        },
        "claude-haiku-4-20250514": {
            "name": "Claude Haiku 4",
            "max_tokens": 8192,
            "description": "Fastest and most cost-effective, 8K output"
        },
    }

    @classmethod
    def get_display_name(cls, model_id: str) -> str:
        """
        Get formatted display name for a model.

        Args:
            model_id: Model identifier (e.g., 'claude-opus-4-20250514')

        Returns:
            Formatted display name (e.g., 'Claude Opus 4 — Most capable model, 16K output')
        """
        if model_id not in cls.MODELS:
            model_id = cls.DEFAULT_MODEL

        info = cls.MODELS[model_id]
        return f"{info['name']} — {info['description']}"

    @classmethod
    def get_all_display_names(cls) -> List[str]:
        """
        Get all model display names for dropdown.

        Returns:
            List of formatted display names
        """
        return [cls.get_display_name(mid) for mid in cls.MODELS.keys()]

    @classmethod
    def get_model_from_display(cls, display_name: str) -> str:
        """
        Convert display name back to model ID.

        Args:
            display_name: Formatted display name

        Returns:
            Model ID or default model if not found
        """
        for model_id in cls.MODELS.keys():
            if cls.get_display_name(model_id) == display_name:
                return model_id
        return cls.DEFAULT_MODEL

    @classmethod
    def get_model_info(cls, model_id: str) -> Dict:
        """
        Get complete model information.

        Args:
            model_id: Model identifier

        Returns:
            Dictionary with 'name', 'max_tokens', 'description'
        """
        return cls.MODELS.get(model_id, cls.MODELS[cls.DEFAULT_MODEL])

    @classmethod
    def get_max_tokens(cls, model_id: str) -> int:
        """
        Get maximum tokens for a model.

        Args:
            model_id: Model identifier

        Returns:
            Maximum tokens for the model
        """
        return cls.get_model_info(model_id)['max_tokens']