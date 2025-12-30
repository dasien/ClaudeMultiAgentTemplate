"""
Claude API Key Dialog
Manages Claude API key configuration.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_dialog import BaseDialog


class ClaudeSettingsDialog(BaseDialog):
    """Dialog for configuring Claude API key."""

    def __init__(self, parent, settings):
        super().__init__(parent, "Set Claude API Key", 500, 280, resizable=False)
        self.settings = settings
        self.build_ui()
        self.load_current_settings()
        self.show()

    def build_ui(self):
        """Build the settings UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="Set Claude API Key",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 20))

        # API Key Section
        key_frame = ttk.LabelFrame(main_frame, text="API Key", padding=15)
        key_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            key_frame,
            text="Your Claude API key (get one at console.anthropic.com):",
            font=('Arial', 9)
        ).pack(anchor="w", pady=(0, 5))

        key_entry_frame = ttk.Frame(key_frame)
        key_entry_frame.pack(fill="x", pady=(0, 10))

        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            key_entry_frame,
            textvariable=self.api_key_var,
            width=50,
            show="•"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True)

        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            key_frame,
            text="Show API Key",
            variable=self.show_key_var,
            command=self.toggle_api_key_visibility
        ).pack(anchor="w")

        # Buttons - Using BaseDialog helper
        self.create_button_frame(main_frame, [
            ("Save", self.save_settings),
            ("Cancel", self.cancel)
        ])

    def toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="•")

    def load_current_settings(self):
        """Load current settings from Settings object."""
        # Load API key
        api_key = self.settings.get_claude_api_key()
        if api_key:
            self.api_key_var.set(api_key)

    def validate(self) -> bool:
        """Validate settings before saving."""
        # Validate API key
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning(
                "API Key Required",
                "Please enter your Claude API key.\n\n"
                "Get one at: console.anthropic.com"
            )
            return False

        return True

    def save_settings(self):
        """Save settings to Settings object."""
        if not self.validate():
            return

        try:
            # Save API key
            api_key = self.api_key_var.get().strip()
            self.settings.set_claude_api_key(api_key)

            # Use BaseDialog.close() with result
            self.close(result=True)

        except Exception as e:
            messagebox.showerror(
                "Save Error",
                f"Failed to save settings:\n\n{e}"
            )