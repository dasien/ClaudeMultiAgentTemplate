"""
Install CMAT Template Dialog - UI for installing CMAT to a project directory.

Provides:
- Directory selection with validation
- Progress tracking during installation
- Error handling with user-friendly messages
- Success confirmation with auto-connect option
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import queue
from typing import Optional

from .base_dialog import BaseDialog
from ..utils import CMATInstaller


class InstallCMATDialog(BaseDialog):
    """Dialog for installing CMAT template from GitHub."""

    # UI States
    STATE_SELECTING = "selecting"
    STATE_VALIDATING = "validating"
    STATE_READY = "ready"
    STATE_INSTALLING = "installing"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"

    def __init__(self, parent, settings=None):
        """
        Initialize dialog.

        Args:
            parent: Parent window (MainWindow)
            settings: Settings object for persisting last directory
        """
        self.settings = settings
        self.installer: Optional[CMATInstaller] = None
        self.installation_thread: Optional[threading.Thread] = None
        self.result_queue = queue.Queue()
        self.current_state = self.STATE_SELECTING

        super().__init__(parent, "Install CMAT Template", 700, 550)
        self.build_ui()
        self.load_last_directory()
        self.show()

    def build_ui(self):
        """Build dialog UI with directory selection and progress display."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Instructions
        instructions = (
            "Select the directory where you want to install the Claude Multi-Agent Template (CMAT).\n"
            "A .claude/ folder will be created in the selected directory with all necessary files."
        )
        ttk.Label(
            main_frame,
            text=instructions,
            wraplength=650,
            justify="left"
        ).pack(anchor="w", pady=(0, 20))

        # Directory selection frame
        dir_frame = ttk.LabelFrame(main_frame, text="Installation Directory", padding=15)
        dir_frame.pack(fill="x", pady=(0, 20))

        # Path entry
        path_entry_frame = ttk.Frame(dir_frame)
        path_entry_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(path_entry_frame, text="Path:").pack(side="left", padx=(0, 5))

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_entry_frame, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(
            path_entry_frame,
            text="Browse...",
            command=self.browse_directory
        ).pack(side="left")

        # Validation status
        self.status_label = ttk.Label(
            dir_frame,
            text="",
            foreground="gray"
        )
        self.status_label.pack(anchor="w", pady=(0, 5))

        # Info note
        self.info_label = ttk.Label(
            dir_frame,
            text="",
            font=('Arial', 9),
            foreground="blue"
        )
        self.info_label.pack(anchor="w")

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Installation Progress", padding=15)
        progress_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Progress bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=600,
            mode="determinate"
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # Progress message
        self.progress_label = ttk.Label(
            progress_frame,
            text="Ready to install",
            foreground="gray"
        )
        self.progress_label.pack(anchor="w")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.install_btn = ttk.Button(
            button_frame,
            text="Install",
            command=self.start_installation,
            state=tk.DISABLED,
            width=15
        )
        self.install_btn.pack(side="left", padx=5)

        self.close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=lambda: self.close(result=None),
            width=15
        )
        self.close_btn.pack(side="left", padx=5)

        # Trace path changes for validation
        self.path_var.trace_add('write', lambda *args: self.validate_directory())

    def load_last_directory(self):
        """Load last used installation directory from settings."""
        if self.settings:
            last_dir = self.settings.get_last_install_directory()
            if last_dir:
                self.path_var.set(last_dir)

    def browse_directory(self):
        """Open directory picker dialog."""
        initial_dir = self.path_var.get() or str(Path.home())

        directory = filedialog.askdirectory(
            parent=self.dialog,
            title="Select Installation Directory",
            initialdir=initial_dir,
            mustexist=True
        )

        if directory:
            self.path_var.set(directory)

    def validate_directory(self):
        """Validate selected directory and update UI."""
        path_str = self.path_var.get().strip()

        if not path_str:
            self._update_validation_status("", "gray", "")
            self.install_btn.config(state=tk.DISABLED)
            self.current_state = self.STATE_SELECTING
            return

        self.current_state = self.STATE_VALIDATING

        try:
            target_dir = Path(path_str)

            # Create installer instance for validation
            temp_installer = CMATInstaller(target_dir)

            # Validate directory
            is_valid, error_msg = temp_installer.validate_target_directory()

            if not is_valid:
                self._update_validation_status(
                    f"✗ Invalid: {error_msg}",
                    "red",
                    ""
                )
                self.install_btn.config(state=tk.DISABLED)
                self.current_state = self.STATE_SELECTING
                return

            # Check for existing installation
            has_existing = temp_installer.check_existing_installation()

            if has_existing:
                self._update_validation_status(
                    "⚠ Warning: .claude folder already exists",
                    "orange",
                    "Installation will overwrite existing files"
                )
                self.install_btn.config(state=tk.NORMAL)
                self.current_state = self.STATE_READY
            else:
                self._update_validation_status(
                    "✓ Valid directory",
                    "green",
                    "A .claude/ folder will be created here"
                )
                self.install_btn.config(state=tk.NORMAL)
                self.current_state = self.STATE_READY

            # Store valid installer
            self.installer = temp_installer

        except Exception as e:
            self._update_validation_status(
                f"✗ Error: {str(e)}",
                "red",
                ""
            )
            self.install_btn.config(state=tk.DISABLED)
            self.current_state = self.STATE_SELECTING

    def _update_validation_status(self, status: str, color: str, info: str):
        """Update validation status labels."""
        self.status_label.config(text=status, foreground=color)
        self.info_label.config(text=info)

    def start_installation(self):
        """Begin installation in background thread."""
        if self.current_state != self.STATE_READY or not self.installer:
            return

        # Confirm overwrite if existing .claude exists
        if self.installer.check_existing_installation():
            response = messagebox.askyesno(
                "Confirm Overwrite",
                "A .claude folder already exists in this directory.\n\n"
                "Do you want to overwrite it? (A backup will be created)",
                parent=self.dialog
            )
            if not response:
                return

        # Save last directory
        if self.settings:
            self.settings.set_last_install_directory(str(self.installer.target_directory))

        # Update UI state
        self.current_state = self.STATE_INSTALLING
        self.install_btn.config(state=tk.DISABLED)
        self.path_entry.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.progress_label.config(text="Starting installation...", foreground="blue")

        # Start installation thread
        self.installation_thread = threading.Thread(
            target=self._run_installation,
            daemon=True
        )
        self.installation_thread.start()

        # Start polling for results
        self._poll_installation_result()

    def _run_installation(self):
        """Run installation in background thread (do not call directly)."""
        try:
            overwrite = self.installer.check_existing_installation()
            # Use local installation (copies from bundled templates)
            self.installer.install_local(
                progress_callback=self._progress_callback,
                overwrite=overwrite
            )
            self.result_queue.put(("success", None))
        except Exception as e:
            self.result_queue.put(("error", e))

    def _progress_callback(self, message: str, percent: int):
        """
        Progress callback invoked from background thread.
        Marshals update to main thread using dialog.after().
        """
        # Schedule UI update on main thread
        self.dialog.after(0, self._update_progress_ui, message, percent)

    def _update_progress_ui(self, message: str, percent: int):
        """Update progress UI components (runs on main thread only)."""
        self.progress_var.set(percent)
        self.progress_label.config(text=message, foreground="blue")
        self.dialog.update_idletasks()

    def _poll_installation_result(self):
        """Poll queue for installation result (runs on main thread)."""
        try:
            result_type, data = self.result_queue.get_nowait()
            if result_type == "success":
                self.on_installation_complete(True)
            elif result_type == "error":
                self.handle_error(data)
        except queue.Empty:
            # Not done yet, poll again
            self.dialog.after(100, self._poll_installation_result)

    def on_installation_complete(self, success: bool):
        """Handle installation completion."""
        if success:
            self.current_state = self.STATE_COMPLETED

            # Show simple success message
            messagebox.showinfo(
                "Installation Complete",
                f"CMAT installed successfully.",
                parent=self.dialog
            )

            # Close dialog and connect
            self.result = {
                "success": True,
                "connect": True,
                "project_root": str(self.installer.target_directory)
            }
            self.close(self.result)
        else:
            self.current_state = self.STATE_FAILED
            self.progress_label.config(text="Installation failed", foreground="red")
            self._reset_ui()

    def handle_error(self, error: Exception):
        """Display error message to user using exception title and message."""
        self.current_state = self.STATE_FAILED
        self.progress_label.config(text="Installation failed", foreground="red")
        self.progress_var.set(0)

        # Get title from error_title attribute if present, otherwise use default
        error_title = getattr(error, 'error_title', "Installation Failed: Unexpected Error")

        # Get message from exception string
        error_msg = str(error)
        if not error_msg:
            error_msg = "Please try again or contact support if the problem persists."

        messagebox.showerror(
            error_title,
            error_msg,
            parent=self.dialog
        )

        self._reset_ui()

    def _reset_ui(self):
        """Reset UI to allow retry."""
        self.install_btn.config(state=tk.NORMAL)
        self.path_entry.config(state=tk.NORMAL)
        self.current_state = self.STATE_READY
