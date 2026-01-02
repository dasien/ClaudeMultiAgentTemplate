"""
Workflow Template Editor Dialog - Create and edit workflow templates (v5.0 - Modular).
Uses separate dialogs for step and transition editing.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json

from .base_dialog import BaseDialog
from ..utils import to_slug, validate_slug


class WorkflowTemplateEditorDialog(BaseDialog):
    """Dialog for creating/editing workflow templates (v5.0)."""

    def __init__(self, parent, queue_interface, mode='create', template_slug=None):
        self.queue = queue_interface
        self.mode = mode
        self.template_slug = template_slug
        self.steps = []

        title = "Create Workflow Template" if mode == 'create' else f"Edit Template: {template_slug}"
        super().__init__(parent, title, 980, 750)

        self.build_ui()

        if mode == 'edit' and template_slug:
            self.load_template_data()

        self.show()

    def build_ui(self):
        """Build the template editor UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Template name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(name_frame, text="Template Name: *", font=('Arial', 10, 'bold')).pack(anchor="w")
        self.name_var = tk.StringVar()
        self.name_var.trace_add('write', self.on_name_changed)
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=50)
        self.name_entry.pack(fill="x", pady=(0, 5))

        # Slug (auto-generated)
        slug_header = ttk.Frame(name_frame)
        slug_header.pack(fill="x")

        ttk.Label(slug_header, text="Slug (auto-generated): *", font=('Arial', 10, 'bold')).pack(side="left")

        if self.mode == 'create':
            self.auto_slug_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                slug_header,
                text="Auto",
                variable=self.auto_slug_var,
                command=self.toggle_slug_auto
            ).pack(side="right")

        self.slug_var = tk.StringVar()
        self.slug_entry = ttk.Entry(name_frame, textvariable=self.slug_var, width=50)
        self.slug_entry.pack(fill="x")

        if self.mode == 'create':
            self.slug_entry.config(state='readonly')
        else:
            self.slug_entry.config(state='readonly')

        ttk.Label(
            name_frame,
            text="(lowercase, hyphens only: my-custom-workflow)",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 10))

        # Description
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(desc_frame, text="Description: *", font=('Arial', 10, 'bold')).pack(anchor="w")
        self.description_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.description_var, width=50).pack(fill="x")

        # Steps section
        steps_label_frame = ttk.Frame(main_frame)
        steps_label_frame.pack(fill="x", pady=(10, 5))

        ttk.Label(
            steps_label_frame,
            text="Workflow Steps:",
            font=('Arial', 10, 'bold')
        ).pack(side="left")

        # Steps list
        steps_frame = ttk.Frame(main_frame)
        steps_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Left: Steps list
        list_frame = ttk.Frame(steps_frame)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        columns = ('step', 'agent', 'input', 'output', 'transitions')
        self.steps_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.steps_tree.heading('step', text='#')
        self.steps_tree.heading('agent', text='Agent')
        self.steps_tree.heading('input', text='Input Pattern')
        self.steps_tree.heading('output', text='Output')
        self.steps_tree.heading('transitions', text='Transitions')

        self.steps_tree.column('step', width=40)
        self.steps_tree.column('agent', width=150)
        self.steps_tree.column('input', width=280)
        self.steps_tree.column('output', width=150)
        self.steps_tree.column('transitions', width=150)

        # Configure tags
        self.steps_tree.tag_configure('complete', background='#E8F5E9')
        self.steps_tree.tag_configure('incomplete', background='#FFF9E6')
        self.steps_tree.tag_configure('first', background='#E3F2FD')

        steps_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.steps_tree.yview)
        self.steps_tree.configure(yscrollcommand=steps_scroll.set)

        self.steps_tree.pack(side="left", fill="both", expand=True)
        steps_scroll.pack(side="right", fill="y")

        # Bind double-click to edit
        self.steps_tree.bind('<Double-Button-1>', self.edit_step)

        # Right: Step controls
        controls_frame = ttk.Frame(steps_frame)
        controls_frame.pack(side="right", fill="y", padx=(5, 0))

        ttk.Button(
            controls_frame,
            text="Add Step",
            command=self.add_step,
            width=15
        ).pack(pady=2)

        ttk.Button(
            controls_frame,
            text="Edit Step",
            command=self.edit_step,
            width=15
        ).pack(pady=2)

        ttk.Button(
            controls_frame,
            text="Move Up",
            command=self.move_step_up,
            width=15
        ).pack(pady=2)

        ttk.Button(
            controls_frame,
            text="Move Down",
            command=self.move_step_down,
            width=15
        ).pack(pady=2)

        ttk.Button(
            controls_frame,
            text="Remove Step",
            command=self.remove_step,
            width=15
        ).pack(pady=2)

        ttk.Separator(controls_frame, orient="horizontal").pack(fill="x", pady=10)

        ttk.Button(
            controls_frame,
            text="Validate Workflow",
            command=self.validate_workflow,
            width=15
        ).pack(pady=2)

        # Bottom buttons
        self.create_button_frame(main_frame, [
            ("Save Template", self.save_template),
            ("Cancel", self.cancel)
        ])

        ttk.Label(main_frame, text="* Required fields", font=('Arial', 9), foreground='gray').pack()

    def on_name_changed(self, *args):
        """Auto-generate slug from name if enabled."""
        if self.mode == 'create' and self.auto_slug_var.get():
            name = self.name_var.get().strip()
            slug = to_slug(name)
            self.slug_var.set(slug)

    def toggle_slug_auto(self):
        """Toggle auto-generation of slug."""
        if self.auto_slug_var.get():
            self.slug_entry.config(state='readonly')
            self.on_name_changed()
        else:
            self.slug_entry.config(state='normal')

    def load_template_data(self):
        """Load existing template data."""
        try:
            template = self.queue.get_workflow_template(self.template_slug)

            if not template:
                messagebox.showerror("Error", "Template not found")
                self.cancel()
                return

            # Load basic fields
            self.name_var.set(template.name)
            self.slug_var.set(template.slug)
            self.description_var.set(template.description)

            # Load steps (v5.0 format)
            self.steps = []
            for step in template.steps:
                self.steps.append({
                    'agent': step.agent,
                    'input': step.input,
                    'required_output': step.required_output,
                    'model': step.model,
                    'on_status': step.on_status
                })

            self.refresh_steps_list()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load template: {e}")
            self.cancel()

    def add_step(self):
        """Add a new step using StepEditorDialog."""
        from .workflow_step_editor import WorkflowStepEditorDialog

        dialog = WorkflowStepEditorDialog(
            self.dialog,
            self.queue,
            existing_step=None,
            step_index=len(self.steps),
            all_steps=self.steps
        )

        if dialog.result:
            self.steps.append(dialog.result)
            self.refresh_steps_list()

    def edit_step(self, event=None):
        """Edit selected step using StepEditorDialog."""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to edit.")
            return

        item = selection[0]
        values = self.steps_tree.item(item, 'values')
        step_num = int(values[0])
        step_index = step_num - 1

        from .workflow_step_editor import WorkflowStepEditorDialog

        dialog = WorkflowStepEditorDialog(
            self.dialog,
            self.queue,
            existing_step=self.steps[step_index],
            step_index=step_index,
            all_steps=self.steps
        )

        if dialog.result:
            self.steps[step_index] = dialog.result
            self.refresh_steps_list()

    def remove_step(self):
        """Remove selected step."""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to remove.")
            return

        item = selection[0]
        values = self.steps_tree.item(item, 'values')
        step_num = int(values[0])

        if messagebox.askyesno("Confirm", f"Remove step {step_num}?"):
            self.steps.pop(step_num - 1)
            self.refresh_steps_list()

    def move_step_up(self):
        """Move selected step up in order."""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to move.")
            return

        item = selection[0]
        values = self.steps_tree.item(item, 'values')
        step_num = int(values[0])

        if step_num == 1:
            messagebox.showinfo("Info", "Step is already at the top.")
            return

        idx = step_num - 1
        self.steps[idx], self.steps[idx - 1] = self.steps[idx - 1], self.steps[idx]
        self.refresh_steps_list()

        # Re-select moved item
        new_item = self.steps_tree.get_children()[idx - 1]
        self.steps_tree.selection_set(new_item)

    def move_step_down(self):
        """Move selected step down in order."""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to move.")
            return

        item = selection[0]
        values = self.steps_tree.item(item, 'values')
        step_num = int(values[0])

        if step_num >= len(self.steps):
            messagebox.showinfo("Info", "Step is already at the bottom.")
            return

        idx = step_num - 1
        self.steps[idx], self.steps[idx + 1] = self.steps[idx + 1], self.steps[idx]
        self.refresh_steps_list()

        # Re-select moved item
        new_item = self.steps_tree.get_children()[idx + 1]
        self.steps_tree.selection_set(new_item)

    def refresh_steps_list(self):
        """Refresh the steps list display."""
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)

        agents_map = self.queue.get_agent_list()

        for idx, step in enumerate(self.steps):
            agent_key = step['agent']
            agent_name = agents_map.get(agent_key, agent_key)

            input_pattern = step.get('input', '(not configured)')
            output_file = step.get('required_output', '(not configured)')
            transitions = step.get('on_status', {})

            # Show full input pattern (no truncation)
            input_display = input_pattern

            # Format transitions - just show count
            trans_display = str(len(transitions)) if transitions else "0"

            # Determine tag based on configuration completeness
            has_input = bool(step.get('input'))
            has_output = bool(step.get('required_output'))
            has_transitions = bool(transitions)

            if has_input and has_output and has_transitions:
                tag = 'complete'
            elif idx == 0:
                tag = 'first'
            else:
                tag = 'incomplete'

            self.steps_tree.insert(
                '',
                tk.END,
                values=(
                    str(idx + 1),
                    agent_name,
                    input_display,
                    output_file,
                    trans_display
                ),
                tags=(tag,)
            )

    def validate_workflow(self):
        """Validate the entire workflow and show results."""
        issues = []

        # Check basic fields
        if not self.name_var.get().strip():
            issues.append("Template name is required")
        if not self.slug_var.get().strip():
            issues.append("Slug is required")
        if not self.description_var.get().strip():
            issues.append("Description is required")
        if not self.steps:
            issues.append("At least one step is required")

        # Check each step
        for idx, step in enumerate(self.steps):
            step_num = idx + 1

            if not step.get('input'):
                issues.append(f"Step {step_num}: Missing input pattern")
            if not step.get('required_output'):
                issues.append(f"Step {step_num}: Missing required output")
            if not step.get('on_status'):
                issues.append(f"Step {step_num}: No status transitions configured")

            # Validate transitions reference valid agents
            on_status = step.get('on_status', {})
            for status, config in on_status.items():
                next_step = config.get('next_step')
                if next_step and next_step != 'null':
                    # Check if next step exists in workflow
                    if not any(s['agent'] == next_step for s in self.steps):
                        issues.append(
                            f"Step {step_num}: Transition '{status}' references "
                            f"non-existent agent '{next_step}'"
                        )

        # Show results
        if issues:
            result = "Validation Issues Found:\n\n" + "\n".join(f"• {issue}" for issue in issues)
            messagebox.showwarning("Validation Issues", result)
        else:
            messagebox.showinfo("Validation Passed", "Workflow template is valid.")

    def validate(self) -> bool:
        """Validate template before saving."""
        name = self.name_var.get().strip()
        slug = self.slug_var.get().strip()
        description = self.description_var.get().strip()

        if not name:
            messagebox.showwarning("Validation", "Template name is required.")
            return False

        if not slug:
            messagebox.showwarning("Validation", "Slug is required.")
            return False

        if not validate_slug(slug):
            messagebox.showwarning("Validation", "Slug must be lowercase with hyphens only.")
            return False

        if not description:
            messagebox.showwarning("Validation", "Description is required.")
            return False

        if not self.steps:
            messagebox.showwarning("Validation", "At least one step is required.")
            return False

        # Check for incomplete steps
        incomplete_steps = []
        for idx, step in enumerate(self.steps):
            if not step.get('input') or not step.get('required_output'):
                incomplete_steps.append(idx + 1)

        if incomplete_steps:
            if not messagebox.askyesno(
                    "Incomplete Steps",
                    f"Steps {', '.join(map(str, incomplete_steps))} are missing input/output configuration.\n\n"
                    "These steps won't work properly in workflows.\n\n"
                    "Continue anyway?"
            ):
                return False

        return True

    def save_template(self):
        """Save the template via CMAT service."""
        if not self.validate():
            return

        name = self.name_var.get().strip()
        slug = self.slug_var.get().strip()
        description = self.description_var.get().strip()

        try:
            # Build workflow data
            workflow_data = {
                'name': name,
                'description': description,
                'steps': []
            }

            # Add all steps (including model field)
            for step in self.steps:
                step_data = {
                    'agent': step['agent'],
                    'input': step.get('input', ''),
                    'required_output': step.get('required_output', ''),
                    'model': step.get('model'),
                    'on_status': step.get('on_status', {})
                }
                workflow_data['steps'].append(step_data)

            # Save via CMAT service
            if self.mode == 'create':
                self.queue.create_workflow_template(slug, workflow_data)
            else:
                self.queue.save_workflow_template(slug, workflow_data)

            self.close(result=slug)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {e}")