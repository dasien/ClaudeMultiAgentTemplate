"""
Install CMAT Template Dialog - UI for installing CMAT to a project directory.

Provides:
- Directory selection with validation
- Progress tracking during installation
- Error handling with user-friendly messages
- Success confirmation with auto-connect option
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import threading
import queue as queuemod
from typing import Optional

from .base_dialog import BaseDialog
from ..utils import CMATInstaller
from ..utils.cmat_installer import get_templates_dir


class InstallCMATDialog(BaseDialog):
    """Dialog for installing CMAT template from GitHub."""

    # UI States
    STATE_SELECTING = "selecting"
    STATE_VALIDATING = "validating"
    STATE_READY = "ready"
    STATE_INSTALLING = "installing"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"

    def __init__(self, parent, settings=None, current_project: str = None, disconnect_callback=None):
        """
        Initialize dialog.

        Args:
            parent: Parent window (MainWindow)
            settings: Settings object for persisting last directory
            current_project: Path to currently connected project (if any)
            disconnect_callback: Callback to disconnect from current project
                                (called before installing to prevent ChromaDB conflicts)
        """
        self.settings = settings
        self.current_project = current_project
        self.disconnect_callback = disconnect_callback
        self.installer: Optional[CMATInstaller] = None
        self.installation_thread: Optional[threading.Thread] = None
        self.result_queue = queuemod.Queue()
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
            text=""
        )
        self.status_label.pack(anchor="w", pady=(0, 5))

        # Info note
        self.info_label = ttk.Label(
            dir_frame,
            text="",
            font=('Arial', 9)
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
            text="Ready to install"
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
        """Update validation status labels using ttkbootstrap bootstyle."""
        # Map color names to bootstyle
        bootstyle_map = {
            "gray": "",  # default
            "green": "success",
            "red": "danger",
            "orange": "warning",
            "blue": "info"
        }
        bootstyle = bootstyle_map.get(color, "")
        if bootstyle:
            self.status_label.config(text=status, bootstyle=bootstyle)
        else:
            self.status_label.config(text=status)
        self.info_label.config(text=info)

    def start_installation(self):
        """Begin installation in background thread."""
        if self.current_state != self.STATE_READY or not self.installer:
            return

        # Confirm overwrite if existing .claude exists
        if self.installer.check_existing_installation():
            if not self.confirm_action(
                "Confirm Overwrite",
                "A .claude folder already exists in this directory.  Overwrite?\n\n"

            ):
                return

        # Disconnect from current project if installing to same directory
        # This prevents ChromaDB "readonly database" errors from concurrent access
        target_path = str(self.installer.target_directory)
        if self.current_project and self.disconnect_callback:
            # Normalize paths for comparison
            current_normalized = str(Path(self.current_project).resolve())
            target_normalized = str(Path(target_path).resolve())
            if current_normalized == target_normalized:
                self.disconnect_callback()

        # Save last directory
        if self.settings:
            self.settings.set_last_install_directory(str(self.installer.target_directory))

        # Update UI state
        self.current_state = self.STATE_INSTALLING
        self.install_btn.config(state=tk.DISABLED)
        self.path_entry.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.progress_label.config(text="Starting installation...", bootstyle="info")

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

            # Phase 1: Copy files (0-80%)
            def scaled_progress(message: str, percent: int):
                # Scale file copy progress to 0-80%
                scaled = int(percent * 0.8)
                self._progress_callback(message, scaled)

            self.installer.install_local(
                progress_callback=scaled_progress,
                overwrite=overwrite
            )

            # Phase 2: Initialize services (80-100%)
            self._progress_callback("Initializing services...", 85)

            from ..utils.cmat_interface import CMATInterface
            project_root = str(self.installer.target_directory)

            # Force delete any existing embeddings directory to ensure fresh database
            # This prevents "readonly database" errors from stale ChromaDB connections
            import shutil
            import gc
            embeddings_dir = Path(project_root) / ".claude" / "data" / "embeddings"
            if embeddings_dir.exists():
                # Force garbage collection to release any lingering file handles
                gc.collect()
                try:
                    shutil.rmtree(embeddings_dir)
                except Exception:
                    pass  # Continue even if delete fails - recovery will handle it

            # This initializes ChromaDB, loads embedding model, runs migrations
            self._progress_callback("Setting up knowledge base...", 90)
            cmat_interface = CMATInterface(project_root)

            self._progress_callback("Ready!", 100)

            # Pass the initialized interface to avoid re-initialization
            self.result_queue.put(("success", cmat_interface))
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
        self.progress_label.config(text=message, bootstyle="info")
        self.dialog.update_idletasks()

    def _poll_installation_result(self):
        """Poll queue for installation result (runs on main thread)."""
        try:
            result_type, data = self.result_queue.get_nowait()
            if result_type == "success":
                self.on_installation_complete(data)  # data is the CMATInterface
            elif result_type == "error":
                self.handle_error(data)
        except queuemod.Empty:
            # Not done yet, poll again
            self.dialog.after(100, self._poll_installation_result)

    def on_installation_complete(self, cmat_interface):
        """Handle installation completion."""
        self.current_state = self.STATE_COMPLETED

        # Save CMAT root path for hooks to use
        if self.settings:
            templates_dir = get_templates_dir()
            if templates_dir:
                cmat_root = templates_dir.parent
                self.settings.set_cmat_root(str(cmat_root))

        # Show simple success message
        self.show_info(
            "Installation Complete",
            "CMAT installed successfully."
        )

        # Close dialog and pass the pre-initialized interface
        self.result = {
            "success": True,
            "connect": True,
            "project_root": str(self.installer.target_directory),
            "cmat_interface": cmat_interface  # Pre-initialized, no re-init needed
        }
        self.close(self.result)

    def handle_error(self, error: Exception):
        """Display error message to user using exception title and message."""
        self.current_state = self.STATE_FAILED
        self.progress_label.config(text="Installation failed", bootstyle="danger")
        self.progress_var.set(0)

        # Get title from error_title attribute if present, otherwise use default
        error_title = getattr(error, 'error_title', "Installation Failed: Unexpected Error")

        # Get message from exception string
        error_msg = str(error)
        if not error_msg:
            error_msg = "Please try again or contact support if the problem persists."

        self.show_error(error_title, error_msg)

        self._reset_ui()

    def _reset_ui(self):
        """Reset UI to allow retry."""
        self.install_btn.config(state=tk.NORMAL)
        self.path_entry.config(state=tk.NORMAL)
        self.current_state = self.STATE_READY
