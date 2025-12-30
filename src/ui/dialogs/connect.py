"""
Connect dialog for selecting a CMAT project.
Validates CMAT structure using the same validation as the installer.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from .base_dialog import BaseDialog
from ..utils import CMATInstaller


class ConnectDialog(BaseDialog):
    """Dialog for connecting to a CMAT project."""

    def __init__(self, parent):
        super().__init__(parent, "Connect to Project", 700, 550)
        self.build_ui()
        self.show()

    def build_ui(self):
        """Build UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Instructions
        ttk.Label(
            main_frame,
            text="Select the project root directory containing .claude/ folder:",
            wraplength=650
        ).pack(anchor="w", pady=(0, 10))

        # Path selection
        path_frame = ttk.LabelFrame(main_frame, text="Project Directory", padding=10)
        path_frame.pack(fill="x", pady=(0, 20))

        entry_frame = ttk.Frame(path_frame)
        entry_frame.pack(fill="x")

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(entry_frame, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(entry_frame, text="Browse...", command=self.browse).pack(side="left", padx=(5, 0))

        # Validation frame
        self.validation_frame = ttk.LabelFrame(main_frame, text="System Validation", padding=10)
        self.validation_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Validation items (updated for Python CMAT v8.2+)
        self.validation_items = {
            'project_root': ttk.Label(self.validation_frame, text="○ Project root directory", foreground='gray'),
            'cmat_package': ttk.Label(self.validation_frame, text="○ CMAT Python package (.claude/cmat/__init__.py)",
                                     foreground='gray'),
            'queue_file': ttk.Label(self.validation_frame, text="○ Task queue (.claude/data/task_queue.json)",
                                    foreground='gray'),
            'skills': ttk.Label(self.validation_frame, text="○ Skills system (.claude/skills/skills.json)",
                                foreground='gray'),
            'agents': ttk.Label(self.validation_frame, text="○ Agents (.claude/agents/agents.json)", foreground='gray'),
        }

        for label in self.validation_items.values():
            label.pack(anchor="w", pady=3)

        # Version info
        self.version_label = ttk.Label(
            self.validation_frame,
            text="",
            font=('Arial', 9, 'bold'),
            foreground='blue'
        )
        self.version_label.pack(anchor="w", pady=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.connect_btn = ttk.Button(
            button_frame,
            text="Connect",
            command=self.connect,
            state=tk.DISABLED
        )
        self.connect_btn.pack(side="left", padx=5)

        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side="left", padx=5)

        # Trace path changes
        self.path_var.trace_add('write', lambda *args: self.validate_path())

    def browse(self):
        """Browse for project directory."""
        directory = filedialog.askdirectory(
            parent=self.dialog,
            title="Select Project Root Directory",
            mustexist=True
        )

        if directory:
            self.path_var.set(directory)

    def validate_path(self):
        """Validate selected path using installer validation logic."""
        path_str = self.path_var.get()

        if not path_str:
            self.connect_btn.config(state=tk.DISABLED)
            return

        project_root = Path(path_str)

        # Validation checks (updated for Python CMAT v8.2+)
        checks = {
            'project_root': project_root.exists() and project_root.is_dir(),
            'cmat_package': (project_root / ".claude/cmat/__init__.py").exists(),
            'queue_file': (
                (project_root / ".claude/data/task_queue.json").exists() or
                (project_root / ".claude/queues/task_queue.json").exists()  # Fallback to old location
            ),
            'skills': (project_root / ".claude/skills/skills.json").exists(),
            'agents': (project_root / ".claude/agents/agents.json").exists(),
        }

        # Update validation labels
        for key, is_valid in checks.items():
            label = self.validation_items[key]
            if is_valid:
                label.config(text=f"✓ {label.cget('text')[2:]}", foreground='green')
            else:
                label.config(text=f"✗ {label.cget('text')[2:]}", foreground='red')

        # Use installer validation logic to check if this is a valid CMAT installation
        claude_dir = project_root / ".claude"
        is_valid_cmat = False

        if claude_dir.exists() and claude_dir.is_dir():
            try:
                installer = CMATInstaller(project_root)
                is_valid_cmat = installer._validate_structure(claude_dir)
            except Exception:
                is_valid_cmat = False

        # Optional but recommended
        optional = ['queue_file', 'agents']
        has_optional = all(checks[k] for k in optional)

        # Update version label
        if is_valid_cmat:
            if has_optional:
                self.version_label.config(text="✓ Valid CMAT Project", foreground='green')
                self.connect_btn.config(state=tk.NORMAL)
            else:
                self.version_label.config(
                    text="⚠ Valid CMAT structure (queue/agents will be created)",
                    foreground='orange'
                )
                self.connect_btn.config(state=tk.NORMAL)
        else:
            # Check if it's an older version
            if (project_root / ".claude/queues/queue_manager.sh").exists():
                self.version_label.config(
                    text="✗ This appears to be an older version - please reinstall template",
                    foreground='red'
                )
            else:
                self.version_label.config(
                    text="✗ Not a valid CMAT project",
                    foreground='red'
                )
            self.connect_btn.config(state=tk.DISABLED)

    def connect(self):
        """Connect to project."""
        project_root = Path(self.path_var.get())

        # For Python CMAT v8.2+, return project root instead of script path
        self.close(result=str(project_root))