"""
About dialog showing application information.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from .base_dialog import BaseDialog
from ..config import Config

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class AboutDialog(BaseDialog):
    """About dialog."""

    def __init__(self, parent):
        super().__init__(parent, "About", 500, 400, resizable=False)
        self.build_ui()
        # Don't call show() - about dialogs don't return results

    def build_ui(self):
        """Build the about dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=30)
        main_frame.pack(fill="both", expand=True)

        # Icon
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists() and PIL_AVAILABLE:
                img = Image.open(icon_path)
                img = img.resize((96, 96), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                icon_label = ttk.Label(main_frame, image=photo)
                icon_label.image = photo  # Keep reference
                icon_label.pack(pady=(0, 10))
        except Exception as e:
            print(f"Could not load icon: {e}")

        # Title
        ttk.Label(
            main_frame,
            text="Claude Multi-Agent Manager",
            font=('Arial', 16, 'bold')
        ).pack(pady=10)

        ttk.Label(
            main_frame,
            text=f"Version {Config.VERSION}",
            font=('Arial', 12)
        ).pack(pady=5)

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=20)

        # Description
        desc_text = (
            "A graphical interface for managing multi-agent\n"
            "development workflows using Claude Code.\n\n"
            "Part of the Claude Multi-Agent Development Template"
        )
        ttk.Label(
            main_frame,
            text=desc_text,
            justify=tk.CENTER,
            font=('Arial', 10)
        ).pack(pady=10)

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=20)

        # Credits
        ttk.Label(
            main_frame,
            text="Built with Python and Tkinter",
            font=('Arial', 9)
        ).pack(pady=5)

        ttk.Label(
            main_frame,
            text="© 2025 Claude Multi-Agent Template Project",
            font=('Arial', 9),
            foreground='gray'
        ).pack(pady=5)

        # Close button
        ttk.Button(
            main_frame,
            text="Close",
            command=self.dialog.destroy  # Just destroy, no result
        ).pack(pady=20)