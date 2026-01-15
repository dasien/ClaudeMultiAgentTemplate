"""
Theme manager for UI theming support.

Centralizes theme management for the CMAT UI using ttkbootstrap.
ttkbootstrap provides theme colors via `root.style.colors` which includes:
- colors.primary, colors.secondary, colors.success, colors.info
- colors.warning, colors.danger, colors.light, colors.dark
- colors.bg, colors.fg, colors.selectbg, colors.selectfg
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..settings import Settings


class ThemeManager:
    """Manages application theme selection."""

    # Default themes for quick toggle
    DEFAULT_LIGHT = "litera"
    DEFAULT_DARK = "darkly"

    # All light themes from ttkbootstrap
    LIGHT_THEMES = {
        "cosmo", "flatly", "journal", "litera", "lumen",
        "minty", "pulse", "sandstone", "united", "yeti"
    }

    # All dark themes from ttkbootstrap
    DARK_THEMES = {
        "cyborg", "darkly", "solar", "superhero", "vapor"
    }

    def __init__(self, settings: "Settings"):
        """Initialize theme manager.

        Args:
            settings: Settings instance for persisting theme preference
        """
        self.settings = settings

    def get_theme(self) -> str:
        """Get current ttkbootstrap theme name.

        Returns:
            The ttkbootstrap theme name (e.g., 'litera', 'darkly')
        """
        theme = self.settings.get_theme()
        # Handle legacy 'light'/'dark' values
        if theme == "light":
            return self.DEFAULT_LIGHT
        elif theme == "dark":
            return self.DEFAULT_DARK
        elif theme in self.LIGHT_THEMES or theme in self.DARK_THEMES:
            return theme
        else:
            return self.DEFAULT_LIGHT

    def set_theme(self, theme: str) -> None:
        """Set and persist theme preference (legacy light/dark toggle).

        Args:
            theme: Theme type ('light' or 'dark')
        """
        if theme == "light":
            self.settings.set_theme(self.DEFAULT_LIGHT)
        elif theme == "dark":
            self.settings.set_theme(self.DEFAULT_DARK)
        else:
            self.settings.set_theme(theme)

    def set_theme_name(self, theme_name: str) -> None:
        """Set and persist a specific ttkbootstrap theme name.

        Args:
            theme_name: ttkbootstrap theme name (e.g., 'litera', 'darkly')
        """
        self.settings.set_theme(theme_name)

    def get_ttkbootstrap_theme(self) -> str:
        """Get the ttkbootstrap theme name for current theme.

        Returns:
            The ttkbootstrap theme name
        """
        return self.get_theme()

    def is_dark(self) -> bool:
        """Check if current theme is a dark theme."""
        return self.get_theme() in self.DARK_THEMES

    def toggle(self) -> str:
        """Toggle between default light and dark themes.

        Returns:
            The new theme name after toggling
        """
        if self.is_dark():
            new_theme = self.DEFAULT_LIGHT
        else:
            new_theme = self.DEFAULT_DARK
        self.set_theme_name(new_theme)
        return new_theme

    def get_theme_type(self) -> str:
        """Get the current theme type.

        Returns:
            'light' or 'dark'
        """
        return "dark" if self.is_dark() else "light"