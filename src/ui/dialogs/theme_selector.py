"""
Theme selector dialog for choosing UI themes.
"""

import tkinter as tk
from tkinter import ttk

from .base_dialog import BaseDialog


class ThemeSelectorDialog(BaseDialog):
    """Dialog for selecting UI theme from available ttkbootstrap themes."""

    # All available ttkbootstrap themes organized by type
    LIGHT_THEMES = [
        ("cosmo", "Cosmo - Clean and modern"),
        ("flatly", "Flatly - Flat design"),
        ("journal", "Journal - Crisp newspaper style"),
        ("litera", "Litera - Literary and clean"),
        ("lumen", "Lumen - Light and airy"),
        ("minty", "Minty - Fresh mint green accents"),
        ("pulse", "Pulse - Purple accents"),
        ("sandstone", "Sandstone - Warm earth tones"),
        ("united", "United - Ubuntu-inspired orange"),
        ("yeti", "Yeti - Friendly blue accents"),
    ]

    DARK_THEMES = [
        ("cyborg", "Cyborg - High contrast dark"),
        ("darkly", "Darkly - Classic dark theme"),
        ("solar", "Solar - Solarized dark"),
        ("superhero", "Superhero - Bold dark blue"),
        ("vapor", "Vapor - Retro neon dark"),
    ]

    def __init__(self, parent, theme_manager, on_theme_change=None):
        """Initialize theme selector dialog.

        Args:
            parent: Parent window (root)
            theme_manager: ThemeManager instance
            on_theme_change: Optional callback to update tk widgets when theme changes
        """
        self.theme_manager = theme_manager
        self.current_theme = theme_manager.get_theme()
        self.selected_theme = None
        self.on_theme_change = on_theme_change
        super().__init__(parent, "Select Theme", width=400, height=300)
        self.build_ui()
        self.show()

    def build_ui(self):
        """Build the theme selector UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="Choose a Theme",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 15))

        # Current theme indicator
        current_label = ttk.Label(
            main_frame,
            text=f"Current: {self.current_theme}",
            font=('Arial', 10)
        )
        current_label.pack(pady=(0, 15))

        # Theme selection frame
        select_frame = ttk.Frame(main_frame)
        select_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(select_frame, text="Theme:").pack(side="left", padx=(0, 10))

        # Build theme list with descriptions
        self.theme_var = tk.StringVar(value=self.current_theme)
        all_themes = self.LIGHT_THEMES + self.DARK_THEMES

        # Create combobox with theme names
        theme_names = [t[0] for t in all_themes]
        self.theme_combo = ttk.Combobox(
            select_frame,
            textvariable=self.theme_var,
            values=theme_names,
            state="readonly",
            width=25
        )
        self.theme_combo.pack(side="left", fill="x", expand=True)
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_selected)

        # Description label
        self.desc_label = ttk.Label(
            main_frame,
            text=self._get_theme_description(self.current_theme),
            font=('Arial', 9)
        )
        self.desc_label.pack(pady=(0, 10))

        # Theme type indicator
        self.type_label = ttk.Label(
            main_frame,
            text=self._get_theme_type(self.current_theme),
            font=('Arial', 9, 'italic')
        )
        self.type_label.pack(pady=(0, 20))

        # Separator
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=12
        ).pack(side="right", padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply_theme,
            width=12
        ).pack(side="right")


    def _get_theme_description(self, theme_name: str) -> str:
        """Get description for a theme."""
        all_themes = self.LIGHT_THEMES + self.DARK_THEMES
        for name, desc in all_themes:
            if name == theme_name:
                return desc
        return ""

    def _get_theme_type(self, theme_name: str) -> str:
        """Get theme type (Light/Dark)."""
        light_names = [t[0] for t in self.LIGHT_THEMES]
        if theme_name in light_names:
            return "Light Theme"
        return "Dark Theme"

    def _on_theme_selected(self, event=None):
        """Handle theme selection change."""
        theme_name = self.theme_var.get()
        self.desc_label.config(text=self._get_theme_description(theme_name))
        self.type_label.config(text=self._get_theme_type(theme_name))

        # Apply preview immediately
        self._preview_theme(theme_name)

    def _preview_theme(self, theme_name: str):
        """Preview the selected theme."""
        try:
            # Apply ttkbootstrap theme (auto-updates ttk widgets)
            self.parent.style.theme_use(theme_name)

            # Call callback to update tk widgets (listbox, text, etc.)
            if self.on_theme_change:
                self.on_theme_change(theme_name)
        except tk.TclError:
            # Ignore widget destruction errors during theme change
            pass
        except Exception as e:
            print(f"Could not preview theme: {e}")

    def _apply_theme(self):
        """Apply the selected theme and close."""
        self.selected_theme = self.theme_var.get()

        # Save to settings via theme manager
        self.theme_manager.set_theme_name(self.selected_theme)

        self.result = self.selected_theme
        self.dialog.destroy()

    def cancel(self):
        """Cancel and restore original theme."""
        # Restore original theme if changed during preview
        if self.theme_var.get() != self.current_theme:
            try:
                self.parent.style.theme_use(self.current_theme)
                # Restore tk widgets via callback
                if self.on_theme_change:
                    self.on_theme_change(self.current_theme)
            except tk.TclError:
                pass
            except Exception:
                pass
        super().cancel()