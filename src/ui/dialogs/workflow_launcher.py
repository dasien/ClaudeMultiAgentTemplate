"""
Workflow Launcher Dialog - Quick workflow launcher with validation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from .base_dialog import BaseDialog


class WorkflowLauncherDialog(BaseDialog):
    """Dialog for starting workflows with pre-flight validation."""

    def __init__(self, parent, queue_interface, settings=None):
        """
        Initialize workflow starter.

        Args:
            parent: Parent window
            queue_interface: Queue interface
            settings: Settings object (for enhancement generation)
        """
        self.queue = queue_interface
        self.settings = settings
        self.selected_template = None
        self.enhancement_file = None

        super().__init__(parent, "Start Workflow", 650, 650)

        self.build_ui()
        self.load_workflows()
        self.show()

    def build_ui(self):
        """Build the workflow starter UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="🚀 Start Workflow",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 15))

        # Workflow selection
        ttk.Label(main_frame, text="Workflow Template: *", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))

        self.workflow_var = tk.StringVar()
        self.workflow_combo = ttk.Combobox(
            main_frame,
            textvariable=self.workflow_var,
            state='readonly',
            width=60
        )
        self.workflow_combo.pack(fill="x", pady=(0, 5))
        self.workflow_combo.bind('<<ComboboxSelected>>', self.on_workflow_selected)

        # Workflow description
        self.workflow_desc_label = ttk.Label(
            main_frame,
            text="",
            font=('Arial', 9),
            foreground='gray',
            wraplength=600
        )
        self.workflow_desc_label.pack(anchor="w", pady=(0, 5))

        # Workflow step summary
        self.workflow_steps_label = ttk.Label(
            main_frame,
            text="",
            font=('Arial', 9),
            foreground='blue'
        )
        self.workflow_steps_label.pack(anchor="w", pady=(0, 20))

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=(0, 15))

        # Enhancement file selection
        ttk.Label(main_frame, text="Enhancement Specification: *", font=('Arial', 10, 'bold')).pack(anchor="w",
                                                                                                    pady=(0, 5))

        enhancement_frame = ttk.Frame(main_frame)
        enhancement_frame.pack(fill="x", pady=(0, 5))

        # Left side: text entry
        entry_frame = ttk.Frame(enhancement_frame)
        entry_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.enhancement_var = tk.StringVar()
        self.enhancement_entry = ttk.Entry(
            entry_frame,
            textvariable=self.enhancement_var,
            state='readonly'
        )
        self.enhancement_entry.pack(fill="x")

        # Right side: buttons stacked vertically
        buttons_frame = ttk.Frame(enhancement_frame)
        buttons_frame.pack(side="right")

        ttk.Button(
            buttons_frame,
            text="Browse...",
            command=self.browse_enhancement,
            width=10
        ).pack(pady=(0, 3))

        ttk.Button(
            buttons_frame,
            text="Create...",
            command=self.create_enhancement,
            width=10
        ).pack()

        # Enhancement info
        self.enhancement_info_label = ttk.Label(
            main_frame,
            text="Select or create an enhancement specification file",
            font=('Arial', 8),
            foreground='gray'
        )
        self.enhancement_info_label.pack(anchor="w", pady=(0, 20))

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=(0, 15))

        # Pre-flight checks
        checks_frame = ttk.LabelFrame(main_frame, text="✅ Pre-flight Checks", padding=10)
        checks_frame.pack(fill="x", pady=(0, 15))

        self.check_labels = {
            'workflow_valid': ttk.Label(checks_frame, text="○ Workflow template validation", foreground='gray'),
            'agents_exist': ttk.Label(checks_frame, text="○ Agent availability", foreground='gray'),
            'enhancement_exists': ttk.Label(checks_frame, text="○ Enhancement specification file", foreground='gray'),
            'no_conflicts': ttk.Label(checks_frame, text="○ No conflicting workflows", foreground='gray'),
        }

        for label in self.check_labels.values():
            label.pack(anchor="w", pady=2)

        # Status summary
        self.status_label = ttk.Label(
            main_frame,
            text="Status: Select workflow and enhancement to begin",
            font=('Arial', 10, 'bold'),
            foreground='gray'
        )
        self.status_label.pack(anchor="w", pady=(5, 15))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.start_button = ttk.Button(
            button_frame,
            text="Start Workflow",
            command=self.start_workflow,
            state=tk.DISABLED,
            width=15
        )
        self.start_button.pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=15
        ).pack(side="left", padx=5)

    def load_workflows(self):
        """Load available workflows."""
        try:
            templates = self.queue.get_workflow_templates()

            if not templates:
                self.workflow_combo['values'] = ["(no workflows available)"]
                self.workflow_combo.current(0)
                return

            # Build display names
            workflow_names = []
            self.workflow_map = {}

            for template in templates:
                # Use same icon logic as task_create
                display_name = self._get_workflow_display_name(template)
                workflow_names.append(display_name)
                self.workflow_map[display_name] = template

            self.workflow_combo['values'] = workflow_names
            if workflow_names:
                self.workflow_combo.current(0)
                self.on_workflow_selected()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load workflows: {e}")
            self.workflow_combo['values'] = ["(error loading workflows)"]

    def _get_workflow_display_name(self, template) -> str:
        """Get display name with icon."""
        name_lower = template.name.lower()

        if 'feature' in name_lower or 'development' in name_lower:
            icon = "📋"
        elif 'bug' in name_lower and 'hot' not in name_lower:
            icon = "🐛"
        elif 'hotfix' in name_lower or 'emergency' in name_lower:
            icon = "🔥"
        elif 'refactor' in name_lower or 'optimization' in name_lower:
            icon = "🔧"
        elif 'doc' in name_lower:
            icon = "📝"
        elif 'performance' in name_lower:
            icon = "⚡"
        else:
            icon = "🔄"

        return f"{icon} {template.name}"

    def on_workflow_selected(self, event=None):
        """Handle workflow selection."""
        display_name = self.workflow_var.get()
        self.selected_template = self.workflow_map.get(display_name)

        if self.selected_template:
            # Update description
            self.workflow_desc_label.config(text=self.selected_template.description)

            # Update step summary
            agents_map = self.queue.get_agent_list()
            step_count = len(self.selected_template.steps)
            agent_names = [agents_map.get(s.agent, s.agent) for s in self.selected_template.steps]
            step_summary = f"Steps: {step_count} ({' → '.join(agent_names)})"
            self.workflow_steps_label.config(text=step_summary)

        # Run checks
        self.run_preflight_checks()

    def browse_enhancement(self):
        """Browse for existing enhancement file."""
        enhancements_dir = self.queue.project_root / "enhancements"

        # Find enhancement spec files
        if enhancements_dir.exists():
            initial_dir = enhancements_dir
        else:
            initial_dir = self.queue.project_root

        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select Enhancement Specification",
            initialdir=str(initial_dir),
            filetypes=[
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )

        if filename:
            self.enhancement_file = Path(filename)
            self.enhancement_var.set(str(self.enhancement_file))

            # Extract enhancement name from path
            rel_path = self.enhancement_file.relative_to(self.queue.project_root)
            self.enhancement_info_label.config(
                text=f"Selected: {rel_path}",
                foreground='green'
            )

            self.run_preflight_checks()

    def create_enhancement(self):
        """Create new enhancement using enhancement generator."""
        from .enhancement_create import CreateEnhancementDialog

        dialog = CreateEnhancementDialog(self.dialog, self.queue, self.settings)

        if dialog.result:
            # Enhancement created successfully
            self.enhancement_file = Path(dialog.result)
            self.enhancement_var.set(str(self.enhancement_file))

            rel_path = self.enhancement_file.relative_to(self.queue.project_root)
            self.enhancement_info_label.config(
                text=f"Created: {rel_path}",
                foreground='green'
            )

            self.run_preflight_checks()

    def run_preflight_checks(self):
        """Run all pre-flight checks and update UI."""
        all_checks_pass = True

        # Check 1: Workflow template valid
        if self.selected_template:
            issues = self.selected_template.validate_chain()
            if issues:
                self.check_labels['workflow_valid'].config(
                    text="⚠ Workflow template has warnings",
                    foreground='orange'
                )
            else:
                self.check_labels['workflow_valid'].config(
                    text="✓ Workflow template is valid",
                    foreground='green'
                )
        else:
            self.check_labels['workflow_valid'].config(
                text="✗ No workflow selected",
                foreground='red'
            )
            all_checks_pass = False

        # Check 2: All agents exist
        if self.selected_template:
            agents_map = self.queue.get_agent_list()
            missing_agents = []

            for step in self.selected_template.steps:
                if step.agent not in agents_map:
                    missing_agents.append(step.agent)

            if missing_agents:
                self.check_labels['agents_exist'].config(
                    text=f"✗ Missing agents: {', '.join(missing_agents)}",
                    foreground='red'
                )
                all_checks_pass = False
            else:
                agent_count = len(self.selected_template.steps)
                self.check_labels['agents_exist'].config(
                    text=f"✓ All {agent_count} agents are available",
                    foreground='green'
                )
        else:
            self.check_labels['agents_exist'].config(
                text="○ Agent availability check pending",
                foreground='gray'
            )

        # Check 3: Enhancement spec exists
        if self.enhancement_file:
            if self.enhancement_file.exists():
                self.check_labels['enhancement_exists'].config(
                    text=f"✓ Enhancement spec found: {self.enhancement_file.name}",
                    foreground='green'
                )
            else:
                self.check_labels['enhancement_exists'].config(
                    text=f"✗ Enhancement spec not found: {self.enhancement_file}",
                    foreground='red'
                )
                all_checks_pass = False
        else:
            self.check_labels['enhancement_exists'].config(
                text="✗ No enhancement spec selected",
                foreground='red'
            )
            all_checks_pass = False

        # Check 4: No conflicting workflows
        if self.enhancement_file and self.selected_template:
            # Extract enhancement name from file path
            enhancement_name = self._extract_enhancement_name(self.enhancement_file)

            if enhancement_name:
                # Check for active workflows on this enhancement
                queue_state = self.queue.get_queue_state()
                conflicting = []

                for task in queue_state.active_workflows:
                    if task.source_file.startswith(f'enhancements/{enhancement_name}/'):
                        conflicting.append(task.id)

                if conflicting:
                    self.check_labels['no_conflicts'].config(
                        text=f"⚠ {len(conflicting)} active task(s) for this enhancement",
                        foreground='orange'
                    )
                    # Don't block, just warn
                else:
                    self.check_labels['no_conflicts'].config(
                        text="✓ No conflicting workflows",
                        foreground='green'
                    )
            else:
                self.check_labels['no_conflicts'].config(
                    text="○ Cannot determine enhancement name",
                    foreground='gray'
                )
        else:
            self.check_labels['no_conflicts'].config(
                text="○ Conflict check pending",
                foreground='gray'
            )

        # Update status and button
        if all_checks_pass:
            self.status_label.config(
                text="Status: ✓ Ready to start",
                foreground='green'
            )
            self.start_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(
                text="Status: ✗ Cannot start - resolve issues above",
                foreground='red'
            )
            self.start_button.config(state=tk.DISABLED)

    def _extract_enhancement_name(self, file_path: Path) -> str:
        """Extract enhancement name from file path."""
        try:
            # Enhancement spec should be: enhancements/{name}/{name}.md
            rel_path = file_path.relative_to(self.queue.project_root)
            parts = rel_path.parts

            if parts[0] == 'enhancements' and len(parts) >= 2:
                return parts[1]

            # Fallback: use filename without extension
            return file_path.stem
        except (ValueError, IndexError):
            return file_path.stem

    def start_workflow(self):
        """Start the workflow."""
        if not self.selected_template or not self.enhancement_file:
            messagebox.showerror("Error", "Select workflow and enhancement first.")
            return

        # Extract enhancement name
        enhancement_name = self._extract_enhancement_name(self.enhancement_file)

        # Confirm
        response = messagebox.askyesno(
            "Confirm Start",
            f"Start workflow '{self.selected_template.name}'?"
        )

        if not response:
            return

        try:
            # Start workflow
            self.queue.start_workflow(self.selected_template.id, enhancement_name)

            # Success - close dialog and return to main view
            self.close(result=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start workflow: {e}")