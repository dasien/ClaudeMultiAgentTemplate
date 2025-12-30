"""
Enhanced Create Task Dialog with skills preview and quick workflows (v5.0).
Updated validation to work without agent contracts.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from .base_dialog import BaseDialog
from ..utils import PathUtils


class CreateTaskDialog(BaseDialog):
    """Enhanced dialog for creating tasks (v5.0)."""

    def __init__(self, parent, queue_interface):
        # Initialize base class
        BaseDialog.__init__(self, parent, "Create New Task", 900, 800)

        self.queue = queue_interface
        self.should_start = False

        # Get agents map
        self.agents_map = self.queue.get_agent_list()
        self.task_types_map = self.queue.get_task_types()

        self.build_ui()
        self.show()

    def build_ui(self):
        """Build the UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(main_frame, text="Title: *").pack(anchor="w")
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var, width=70)
        self.title_entry.pack(fill="x", pady=(0, 10))

        # Agent, Priority, and Task Type on same line
        config_frame = ttk.Frame(main_frame)
        config_frame.pack(fill="x", pady=(0, 10))

        # Agent
        agent_col = ttk.Frame(config_frame)
        agent_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(agent_col, text="Agent: *").pack(anchor="w")
        self.agent_var = tk.StringVar()
        self.agent_combo = ttk.Combobox(agent_col, textvariable=self.agent_var, state='readonly')
        self.agent_combo['values'] = list(self.agents_map.values())
        if self.agent_combo['values']:
            self.agent_combo.current(0)
        self.agent_combo.pack(fill="x")
        self.agent_combo.bind('<<ComboboxSelected>>', self.on_agent_selected)

        # Priority
        priority_col = ttk.Frame(config_frame)
        priority_col.pack(side="left", fill="x", expand=True, padx=(5, 5))
        ttk.Label(priority_col, text="Priority: *").pack(anchor="w")
        self.priority_var = tk.StringVar()
        priority_combo = ttk.Combobox(priority_col, textvariable=self.priority_var, state='readonly')
        priority_combo['values'] = self.queue.get_priorities()
        priority_combo.current(1)
        priority_combo.pack(fill="x")

        # Task Type
        type_col = ttk.Frame(config_frame)
        type_col.pack(side="left", fill="x", expand=True, padx=(5, 5))
        ttk.Label(type_col, text="Task Type: *").pack(anchor="w")
        self.task_type_var = tk.StringVar()
        task_type_combo = ttk.Combobox(type_col, textvariable=self.task_type_var, state='readonly')
        task_type_combo['values'] = list(self.task_types_map.values())
        task_type_combo.current(0)
        task_type_combo.pack(fill="x")

        # Model Selection
        model_col = ttk.Frame(config_frame)
        model_col.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ttk.Label(model_col, text="Model:").pack(anchor="w")

        from ..components.model_selector import ModelSelectorFrame
        self.model_selector = ModelSelectorFrame(model_col, self.queue, show_default_option=True)
        self.model_selector.pack(fill="x")

        # Skills Preview Frame
        self.skills_frame = ttk.LabelFrame(main_frame, text="🎯 Agent Skills", padding=10)
        self.skills_frame.pack(fill="x", pady=(0, 10))

        self.skills_list_label = ttk.Label(
            self.skills_frame,
            text="Select an agent to see available skills",
            font=('Arial', 9),
            foreground='gray'
        )
        self.skills_list_label.pack(anchor="w")

        self.preview_btn = ttk.Button(
            self.skills_frame,
            text="Preview Full Skills Prompt",
            command=self.preview_skills_prompt,
            state=tk.DISABLED
        )
        self.preview_btn.pack(anchor="w", pady=(5, 0))

        # Source File (optional)
        ttk.Label(main_frame, text="Source File (optional):").pack(anchor="w")
        source_frame = ttk.Frame(main_frame)
        source_frame.pack(fill="x", pady=(0, 5))

        self.source_var = tk.StringVar()
        self.source_entry = ttk.Entry(source_frame, textvariable=self.source_var)
        self.source_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(source_frame, text="Browse...", command=self.browse_source).pack(side="left", padx=(5, 0))

        self.source_var.trace_add('write', lambda *args: self.validate_source_file())

        self.source_validation_label = ttk.Label(
            main_frame,
            text="If not specified, output will be saved to enhancements/<task_id>/",
            font=('Arial', 8),
            foreground='gray'
        )
        self.source_validation_label.pack(anchor="w", pady=(0, 10))

        # Task Description
        ttk.Label(main_frame, text="Task Description: *").pack(anchor="w")
        self.description_text = tk.Text(main_frame, height=8, wrap="word")
        self.description_text.pack(fill="both", expand=True, pady=(0, 10))

        # Note about automation
        note_label = ttk.Label(
            main_frame,
            text="Note: Tasks will auto-complete but will not auto-chain to other agents.",
            font=('Arial', 9, 'italic'),
            foreground='gray'
        )
        note_label.pack(anchor="w", pady=(0, 10))

        # Buttons
        self.create_button_frame(main_frame, [
            ("Create Task", self.create_task),
            ("Create & Start", self.create_and_start),
            ("Cancel", self.cancel)
        ])

    def on_show(self):
        """Called after dialog shown - set initial focus and trigger agent selection."""
        self.set_focus(self.title_entry)

        # Trigger initial agent selection
        if self.agent_combo['values']:
            self.on_agent_selected()

    def on_agent_selected(self, event=None):
        """Handle agent selection - show skills."""
        agent_display = self.agent_var.get()
        agent_key = self.get_agent_key(agent_display)

        if not agent_key:
            return

        # Get agent's skills
        skills = self.queue.get_agent_skills(agent_key)

        # Update skills display
        for widget in self.skills_frame.winfo_children():
            widget.destroy()

        if skills:
            ttk.Label(
                self.skills_frame,
                text=f"This agent has {len(skills)} skill(s) available:",
                font=('Arial', 9, 'bold')
            ).pack(anchor="w", pady=(0, 5))

            # Get skill names from skills.json
            skills_data = self.queue.get_skills_list()
            if skills_data:
                for skill_dir in skills:
                    skill_info = next(
                        (s for s in skills_data.get('skills', [])
                         if s.get('skill-directory') == skill_dir),
                        None
                    )
                    if skill_info:
                        name = skill_info.get('name', skill_dir)
                        category = skill_info.get('category', 'unknown')
                        ttk.Label(
                            self.skills_frame,
                            text=f"  • {name} ({category})",
                            font=('Arial', 9)
                        ).pack(anchor="w", pady=1)

            # Preview button
            self.preview_btn = ttk.Button(
                self.skills_frame,
                text="📄 Preview Full Skills Prompt",
                command=self.preview_skills_prompt
            )
            self.preview_btn.pack(anchor="w", pady=(10, 0))

        else:
            ttk.Label(
                self.skills_frame,
                text="This agent has no skills assigned",
                font=('Arial', 9),
                foreground='gray'
            ).pack(anchor="w")

        # Trigger source validation
        self.validate_source_file()

    def preview_skills_prompt(self):
        """Show preview of skills that will be injected into agent prompt."""
        agent_display = self.agent_var.get()
        agent_key = self.get_agent_key(agent_display)

        if not agent_key:
            return

        try:
            skills_prompt = self.queue.get_skills_prompt(agent_key)

            if not skills_prompt:
                messagebox.showinfo("No Skills", "This agent has no skills assigned.")
                return

            # Create preview window
            preview = tk.Toplevel(self.dialog)
            preview.title(f"Skills Prompt Preview: {agent_display}")
            preview.geometry("800x600")
            preview.transient(self.dialog)

            # Text widget with scrollbar
            text_frame = ttk.Frame(preview, padding=10)
            text_frame.pack(fill="both", expand=True)

            text_widget = tk.Text(text_frame, wrap="word", font=('Courier', 9))
            scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scroll.set)

            text_widget.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")

            text_widget.insert('1.0', skills_prompt)
            # Keep text widget editable so user can select and copy

            # Button frame
            button_frame = ttk.Frame(preview)
            button_frame.pack(pady=10)

            def copy_to_clipboard():
                preview.clipboard_clear()
                preview.clipboard_append(skills_prompt)
                messagebox.showinfo("Copied", "Skills prompt copied to clipboard!")

            ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Close", command=preview.destroy).pack(side="left", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load skills prompt: {e}")

    def validate_source_file(self):
        """Validate source file (v5.0 - simplified validation)."""
        source_file = self.source_var.get().strip()

        if not source_file:
            self.source_validation_label.config(text="", foreground='black')
            return

        # Convert to absolute path if relative
        source_path = Path(source_file)
        if not source_path.is_absolute():
            source_path = self.queue.project_root / source_path

        # Basic validation: check if file/directory exists
        if source_path.exists():
            if source_path.is_file():
                self.source_validation_label.config(
                    text="✓ File exists",
                    foreground='green'
                )
            elif source_path.is_dir():
                self.source_validation_label.config(
                    text="✓ Directory exists",
                    foreground='green'
                )
        else:
            self.source_validation_label.config(
                text="⚠ File/directory not found",
                foreground='orange'
            )

    def browse_source(self):
        """Browse for source file."""
        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select Source File",
            initialdir=str(self.queue.project_root),
            filetypes=[("Markdown", "*.md"), ("All Files", "*.*")]
        )

        if filename:
            rel_path = PathUtils.relative_to_project(Path(filename), self.queue.project_root)
            self.source_var.set(rel_path)

    def get_agent_key(self, display_name: str) -> str:
        """Convert agent display name to agent-file key."""
        for key, value in self.agents_map.items():
            if value == display_name:
                return key
        return display_name

    def get_task_type_key(self, display_name: str) -> str:
        """Convert task type display name to internal key."""
        for key, value in self.task_types_map.items():
            if value == display_name:
                return key
        return display_name

    def validate(self) -> bool:
        """Validate form before creating task."""
        title = self.title_var.get().strip()
        agent_display = self.agent_var.get()
        priority = self.priority_var.get()
        task_type_display = self.task_type_var.get()
        description = self.description_text.get('1.0', tk.END).strip()

        # Source file is now optional
        if not all([title, agent_display, priority, task_type_display, description]):
            messagebox.showwarning("Validation Error", "Title, Agent, Priority, Task Type, and Description are required.")
            return False

        # If source file is provided, validate it exists (optional warning)
        source_file = self.source_var.get().strip()
        if source_file:
            source_path = Path(source_file)
            if not source_path.is_absolute():
                source_path = self.queue.project_root / source_path

            if not source_path.exists():
                response = messagebox.askyesno(
                    "File Not Found",
                    f"Source file does not exist: {source_file}\n\nCreate task anyway?"
                )
                if not response:
                    return False

        return True

    def create_task(self):
        """Create the task."""
        if not self.validate():
            return

        # Get values
        title = self.title_var.get().strip()
        agent_display = self.agent_var.get()
        priority = self.priority_var.get()
        task_type_display = self.task_type_var.get()
        source_file = self.source_var.get().strip()
        description = self.description_text.get('1.0', tk.END).strip()

        # Get selected model (None = use default)
        model = self.model_selector.get_selected_model()

        # Convert to keys
        agent = self.get_agent_key(agent_display)
        task_type = self.get_task_type_key(task_type_display)

        # If no source file provided, use empty string (CMAT will handle it)
        if not source_file:
            source_file = ""

        try:
            task_id = self.queue.add_task(
                title=title,
                agent=agent,
                priority=priority,
                task_type=task_type,
                source_file=source_file,
                description=description,
                model=model,  # Pass selected model to CMAT
                auto_complete=True,  # Always true for standalone tasks
                auto_chain=False     # Always false for standalone tasks
            )
            self.close(result=task_id)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create task: {e}")

    def create_and_start(self):
        """Create task and mark to start immediately."""
        self.should_start = True
        self.create_task()