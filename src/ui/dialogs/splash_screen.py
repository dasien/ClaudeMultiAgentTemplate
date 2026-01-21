"""
Splash screen shown on application startup.

Supports running background initialization during display.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading
import time

from ..config import Config

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SplashScreen:
    """A splash screen that displays during startup while running background initialization."""

    def __init__(self, root, min_duration_ms=1000, on_close=None, init_func=None):
        """Create splash screen.

        Args:
            root: The main Tk root window (visible behind splash)
            min_duration_ms: Minimum time to show splash (allows init to complete)
            on_close: Optional callback to invoke when splash closes, receives init_func result
            init_func: Optional function to run in background during splash display.
                       Should return a result that will be passed to on_close callback.
        """
        self.root = root
        self.min_duration_ms = min_duration_ms
        self.on_close = on_close
        self.init_func = init_func
        self.splash = None
        self.photo = None

        # Threading state
        self.init_result = None
        self.init_complete = False
        self.init_error = None
        self.min_time_elapsed = False

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
        self.loading_label = tk.Label(
            frame,
            text="Loading...",
            font=('Arial', 9),
            fg=fg_loading,
            bg=bg_color
        )
        self.loading_label.pack(side="bottom", pady=(10, 0))

        # Click to dismiss early (only if init is complete)
        self.splash.bind('<Button-1>', lambda e: self._try_close())

        # Ensure splash is on top
        self.splash.lift()
        self.splash.attributes('-topmost', True)

        # Update to ensure it's drawn
        self.splash.update()

        # Start background initialization if provided
        if self.init_func:
            init_thread = threading.Thread(target=self._run_init, daemon=True)
            init_thread.start()
        else:
            self.init_complete = True

        # Schedule minimum duration check
        self.splash.after(self.min_duration_ms, self._on_min_time_elapsed)

        # Start polling for completion
        self._poll_completion()

    def _run_init(self):
        """Run initialization function in background thread."""
        try:
            self.init_result = self.init_func()
        except Exception as e:
            self.init_error = e
            print(f"Splash init error: {e}")
        finally:
            self.init_complete = True

    def _on_min_time_elapsed(self):
        """Called when minimum display time has elapsed."""
        self.min_time_elapsed = True

    def _poll_completion(self):
        """Poll for both init completion and minimum time elapsed."""
        if not self.splash or not self.splash.winfo_exists():
            return

        # Check if both conditions are met
        if self.init_complete and self.min_time_elapsed:
            self.close()
        else:
            # Poll again in 50ms
            self.splash.after(50, self._poll_completion)

    def _try_close(self):
        """Try to close splash (only works if init is complete)."""
        if self.init_complete:
            self.close()

    def close(self):
        """Close splash and bring main window to front."""
        if self.splash and self.splash.winfo_exists():
            self.splash.destroy()
            self.splash = None

        # Bring main window to front
        self.root.lift()
        self.root.focus_force()

        # Invoke callback if provided, passing init result
        if self.on_close:
            self.on_close(self.init_result)