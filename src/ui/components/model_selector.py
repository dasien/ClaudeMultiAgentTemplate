"""
Model Selector Component - Reusable dropdown for selecting Claude models.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class ModelSelectorFrame(ttk.Frame):
    """Reusable model selection component."""

    def __init__(self, parent, queue_interface, show_default_option=True):
        """
        Initialize model selector.

        Args:
            parent: Parent tkinter widget
            queue_interface: CMATInterface instance for accessing models
            show_default_option: If True, show "Use Default" as first option
        """
        super().__init__(parent)
        self.queue = queue_interface
        self.show_default_option = show_default_option
        self.model_map = {}  # Maps display text → model ID
        self.default_key = None

        self._build_ui()

    def _build_ui(self):
        """Build the model selector UI."""
        try:
            # Load models from CMAT
            models = self.queue.models.list_all()
            default_model = self.queue.models.get_default()

            # Build display options
            options = []

            if self.show_default_option and default_model:
                # First option: Show default model name with (Default) suffix
                self.default_key = f"⭐ {default_model.name} (Default)"
                options.append(self.default_key)
                self.model_map[self.default_key] = None  # None = use default

            # Add all models
            for model in models:
                display_text = model.name
                options.append(display_text)
                self.model_map[display_text] = model.id

            # Create dropdown
            self.selected_var = tk.StringVar()
            self.combo = ttk.Combobox(
                self,
                textvariable=self.selected_var,
                values=options,
                state='readonly',
                width=40
            )
            self.combo.pack(fill='x')

            # Set default selection
            if options:
                self.combo.current(0)

        except Exception as e:
            # Fallback if model loading fails
            ttk.Label(
                self,
                text=f"Error loading models: {e}",
                foreground='red',
                font=('Arial', 9)
            ).pack()

    def get_selected_model(self) -> Optional[str]:
        """
        Get the selected model ID.

        Returns:
            Model ID string, or None if "Use Default" is selected
        """
        display_text = self.selected_var.get()
        return self.model_map.get(display_text)

    def set_model(self, model_id: Optional[str]):
        """
        Set the selected model by ID.

        Args:
            model_id: Model ID to select, or None for default
        """
        if model_id is None:
            # Select default option if available
            if self.default_key:
                self.selected_var.set(self.default_key)
                return

        # Find matching display text for this model ID
        for display_text, stored_id in self.model_map.items():
            if stored_id == model_id:
                self.selected_var.set(display_text)
                return

        # Model not found - select default or first option
        if self.combo['values']:
            self.combo.current(0)
