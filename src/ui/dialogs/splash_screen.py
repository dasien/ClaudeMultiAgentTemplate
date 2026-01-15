"""
Splash screen shown on application startup.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from ..config import Config

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SplashScreen:
    """A simple splash screen that displays briefly on startup."""

    def __init__(self, root, duration_ms=2500, on_close=None):
        """Create splash screen.

        Args:
            root: The main Tk root window (visible behind splash)
            duration_ms: How long to show splash in milliseconds
            on_close: Optional callback to invoke when splash closes
        """
        self.root = root
        self.duration_ms = duration_ms
        self.on_close = on_close
        self.splash = None
        self.photo = None

    def _is_dark_theme(self) -> bool:
        """Check if the current ttkbootstrap theme is dark."""
        dark_themes = {'darkly', 'cyborg', 'solar', 'superhero', 'vapor'}
        try:
            current_theme = self.root.style.theme_use()
            return current_theme in dark_themes
        except (AttributeError, Exception):
            return False

    def show(self):
        """Show the splash screen overlaying the main window."""
        # Show main window in background (don't hide it)
        self.root.update()

        # Create splash window
        self.splash = tk.Toplevel(self.root)
        self.splash.title("")
        self.splash.overrideredirect(True)  # No window decorations

        # Size and center on main window (not screen)
        width, height = 320, 200
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        x = main_x + (main_width - width) // 2
        y = main_y + (main_height - height) // 2
        self.splash.geometry(f"{width}x{height}+{x}+{y}")

        # Style - theme-aware colors
        is_dark = self._is_dark_theme()
        if is_dark:
            bg_color = '#212529'
            fg_title = '#f8f9fa'
            fg_version = '#adb5bd'
            fg_loading = '#6c757d'
        else:
            bg_color = '#f5f5f5'
            fg_title = '#333333'
            fg_version = '#666666'
            fg_loading = '#888888'

        self.splash.configure(bg=bg_color)

        # Main frame
        frame = tk.Frame(self.splash, bg=bg_color)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Load and display icon
        try:
            icon_path = Path(__file__).parent.parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists() and PIL_AVAILABLE:
                img = Image.open(icon_path)
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)

                icon_label = tk.Label(frame, image=self.photo, bg=bg_color)
                icon_label.pack(pady=(10, 15))
        except Exception as e:
            print(f"Splash: Could not load icon: {e}")

        # App name
        tk.Label(
            frame,
            text="Claude Multi-Agent Template",
            font=('Arial', 14, 'bold'),
            fg=fg_title,
            bg=bg_color
        ).pack(pady=(0, 5))

        # Version
        tk.Label(
            frame,
            text=f"v{Config.VERSION}",
            font=('Arial', 10),
            fg=fg_version,
            bg=bg_color
        ).pack()

        # Loading indicator
        tk.Label(
            frame,
            text="Loading...",
            font=('Arial', 9),
            fg=fg_loading,
            bg=bg_color
        ).pack(side="bottom", pady=(10, 0))

        # Click to dismiss early
        self.splash.bind('<Button-1>', lambda e: self.close())

        # Auto-close after duration
        self.splash.after(self.duration_ms, self.close)

        # Ensure splash is on top
        self.splash.lift()
        self.splash.attributes('-topmost', True)

        # Update to ensure it's drawn
        self.splash.update()

    def close(self):
        """Close splash and bring main window to front."""
        if self.splash and self.splash.winfo_exists():
            self.splash.destroy()
            self.splash = None

        # Bring main window to front
        self.root.lift()
        self.root.focus_force()

        # Invoke callback if provided
        if self.on_close:
            self.on_close()