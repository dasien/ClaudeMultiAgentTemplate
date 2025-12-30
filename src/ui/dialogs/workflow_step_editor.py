"""
Workflow Step Editor Dialog - Configure input/output/transitions for a workflow step.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .workflow_transition_editor import WorkflowTransitionEditorDialog
from .base_dialog import BaseDialog


class WorkflowStepEditorDialog(BaseDialog):
    """Dialog for editing a single workflow step configuration."""

    def __init__(self, parent, queue_interface, existing_step=None,
                 step_index=None, all_steps=None):
        """
        Initialize step editor.

        Args:
            parent: Parent window
            queue_interface: Queue interface for accessing agents
            existing_step: Existing step data dict (for edit mode)
            step_index: Index of step in workflow (for context)
            all_steps: List of all workflow steps (for validation)
        """
        self.queue = queue_interface
        self.existing_step = existing_step
        self.step_index = step_index
        self.all_steps = all_steps or []

        # Initialize step data
        self.transitions = existing_step.get('on_status', {}).copy() if existing_step else {}

        mode_text = "Edit" if existing_step else "Add"
        super().__init__(parent, f"{mode_text} Workflow Step", 650, 550)

        self.build_ui()
        self.show()

    def build_ui(self):
        """Build the step editor UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Agent selection
        ttk.Label(main_frame, text="Agent: *", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))

        self.agent_var = tk.StringVar()
        agent_combo = ttk.Combobox(main_frame, textvariable=self.agent_var, state='readonly', width=40)

        agents_map = self.queue.get_agent_list()
        agent_combo['values'] = list(agents_map.values())

        if self.existing_step:
            agent_name = agents_map.get(self.existing_step['agent'], self.existing_step['agent'])
            self.agent_var.set(agent_name)
        elif agent_combo['values']:
            agent_combo.current(0)

        agent_combo.pack(fill="x", pady=(0, 15))
        agent_combo.bind('<<ComboboxSelected>>', self.on_agent_selected)

        # Model Selection (optional)
        ttk.Label(main_frame, text="Model (optional):", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            main_frame,
            text="Leave as default to use project's default model",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 5))

        from ..components.model_selector import ModelSelectorFrame
        self.model_selector = ModelSelectorFrame(main_frame, self.queue, show_default_option=True)
        self.model_selector.pack(fill="x", pady=(0, 15))

        # Load existing model if editing
        if self.existing_step and self.existing_step.get('model'):
            self.model_selector.set_model(self.existing_step['model'])

        # Input pattern
        ttk.Label(main_frame, text="Input Pattern: *", font=('Arial', 10, 'bold')).pack(anchor="w")

        ttk.Label(
            main_frame,
            text="Specify where this step reads its input from",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 5))

        # Placeholder buttons
        placeholder_frame = ttk.Frame(main_frame)
        placeholder_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(
            placeholder_frame,
            text="Insert:",
            font=('Arial', 8),
            foreground='gray'
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            placeholder_frame,
            text="{enhancement_name}",
            command=lambda: self.insert_placeholder("{enhancement_name}")
        ).pack(side="left", padx=2)

        ttk.Button(
            placeholder_frame,
            text="{previous_step}",
            command=lambda: self.insert_placeholder("{previous_step}")
        ).pack(side="left", padx=2)

        self.input_var = tk.StringVar()
        if self.existing_step:
            self.input_var.set(self.existing_step.get('input', ''))
        elif self.step_index == 0 or len(self.all_steps) == 0:
            # First step default
            self.input_var.set('enhancements/{enhancement_name}/{enhancement_name}.md')
        else:
            # Subsequent step default
            self.input_var.set('{previous_step}/required_output/')

        self.input_entry = ttk.Entry(main_frame, textvariable=self.input_var, width=50)
        self.input_entry.pack(fill="x", pady=(0, 5))

        # Input preview
        self.input_preview = ttk.Label(
            main_frame,
            text="",
            font=('Arial', 8),
            foreground='blue'
        )
        self.input_preview.pack(anchor="w", pady=(0, 15))

        # Update preview on change
        self.input_var.trace_add('write', self.update_input_preview)
        self.update_input_preview()

        # Required output
        ttk.Label(main_frame, text="Required Output Filename: *", font=('Arial', 10, 'bold')).pack(anchor="w")
        ttk.Label(
            main_frame,
            text="Filename only (must end with .md, no path separators)",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 5))

        self.output_var = tk.StringVar()
        if self.existing_step:
            self.output_var.set(self.existing_step.get('required_output', ''))
        else:
            # Auto-suggest based on agent
            self.update_output_suggestion()

        ttk.Entry(main_frame, textvariable=self.output_var, width=50).pack(fill="x", pady=(0, 15))

        # Status transitions
        ttk.Label(main_frame, text="Status Transitions:", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            main_frame,
            text="Configure what happens when agent outputs specific status codes",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 5))

        transitions_frame = ttk.Frame(main_frame)
        transitions_frame.pack(fill="x", pady=(0, 15))

        ttk.Button(
            transitions_frame,
            text="Manage Transitions...",
            command=self.manage_transitions
        ).pack(side="left")

        self.transitions_summary = ttk.Label(
            transitions_frame,
            text=self._format_transitions_summary(),
            font=('Arial', 9),
            foreground='gray'
        )
        self.transitions_summary.pack(side="left", padx=(10, 0))

        # Buttons
        self.create_button_frame(main_frame, [
            ("Save Step", self.save_step),
            ("Cancel", self.cancel)
        ])

    def insert_placeholder(self, placeholder: str):
        """Insert placeholder at cursor position."""
        self.input_entry.insert(tk.INSERT, placeholder)
        self.input_entry.focus_set()

    def update_input_preview(self, *args):
        """Update input pattern preview with example."""
        pattern = self.input_var.get()
        example = pattern.replace('{enhancement_name}', 'my-feature')

        # If using {previous_step} and we know previous step
        if '{previous_step}' in example and self.step_index and self.step_index > 0:
            prev_step = self.all_steps[self.step_index - 1]
            prev_agent = prev_step.get('agent', 'prev-agent')
            example = example.replace('{previous_step}', f"enhancements/my-feature/{prev_agent}")

        self.input_preview.config(text=f"Example: {example}")

    def on_agent_selected(self, event=None):
        """Update output suggestion when agent changes."""
        self.update_output_suggestion()

    def update_output_suggestion(self):
        """Suggest output filename based on agent."""
        if self.output_var.get():
            return  # Don't override if user has set something

        agent_display = self.agent_var.get()
        if not agent_display:
            return

        agents_map = self.queue.get_agent_list()
        agent_key = next((k for k, v in agents_map.items() if v == agent_display), None)

        if agent_key:
            # Suggest filename based on agent
            suggested = f"{agent_key.replace('-', '_')}_output.md"
            self.output_var.set(suggested)

    def manage_transitions(self):
        """Open transition manager dialog."""

        # Get all agents in current workflow for next step options
        workflow_agents = [step.get('agent') for step in self.all_steps if step.get('agent')]

        dialog = WorkflowTransitionEditorDialog(
            self.dialog,
            self.queue,
            self.transitions,
            workflow_agents
        )

        if dialog.result is not None:
            # Update transitions
            self.transitions = dialog.result
            self.transitions_summary.config(text=self._format_transitions_summary())

    def _format_transitions_summary(self):
        """Format transitions for summary display."""
        if not self.transitions:
            return "(no transitions configured)"

        count = len(self.transitions)
        return f"{count} transition{'s' if count != 1 else ''} configured"

    def validate(self) -> bool:
        """Validate step configuration."""
        agent = self.agent_var.get().strip()
        input_pattern = self.input_var.get().strip()
        output_filename = self.output_var.get().strip()

        if not agent:
            messagebox.showwarning("Validation", "Agent is required.")
            return False

        if not input_pattern:
            messagebox.showwarning("Validation", "Input pattern is required.")
            return False

        if not output_filename:
            messagebox.showwarning("Validation", "Output filename is required.")
            return False

        # Validate output filename
        if not output_filename.endswith('.md'):
            messagebox.showwarning("Validation", "Output filename must end with .md")
            return False

        if '/' in output_filename or '\\' in output_filename:
            messagebox.showwarning("Validation", "Output should be filename only (no path separators)")
            return False

        # Warn if no transitions
        if not self.transitions:
            response = messagebox.askyesno(
                "No Transitions",
                "This step has no status transitions configured.\n\n"
                "The workflow will stop at this step unless you add transitions.\n\n"
                "Continue anyway?"
            )
            if not response:
                return False

        return True

    def save_step(self):
        """Save the step configuration."""
        if not self.validate():
            return

        agent_display = self.agent_var.get()
        agents_map = self.queue.get_agent_list()
        agent_key = next((k for k, v in agents_map.items() if v == agent_display), None)

        if not agent_key:
            messagebox.showerror("Error", "Agent not found")
            return

        # Get selected model (None = use default)
        model = self.model_selector.get_selected_model()

        # Build result
        result = {
            'agent': agent_key,
            'input': self.input_var.get().strip(),
            'required_output': self.output_var.get().strip(),
            'model': model,  # Add model selection
            'on_status': self.transitions.copy()
        }

        self.close(result=result)