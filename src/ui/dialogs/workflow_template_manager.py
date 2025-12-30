"""
Workflow Template Manager Dialog - List, create, edit, and delete workflow templates.
"""

import tkinter as tk
import json
from tkinter import ttk, messagebox
from .base_dialog import BaseDialog
from .workflow_template_editor import WorkflowTemplateEditorDialog


class WorkflowTemplateManagerDialog(BaseDialog):
    """Dialog for managing workflow templates."""

    def __init__(self, parent, queue_interface):
        super().__init__(parent, "Workflow Template Manager", 900, 600, modal=False)
        self.queue = queue_interface
        self.build_ui()
        self.load_templates()

    def build_ui(self):
        """Build the workflow template manager UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="Workflow Template Manager",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))

        # Template list
        list_frame = ttk.LabelFrame(main_frame, text="Workflow Templates", padding=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Treeview
        columns = ('name', 'slug', 'description', 'steps')
        self.template_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.template_tree.heading('name', text='Template Name')
        self.template_tree.heading('slug', text='Slug')
        self.template_tree.heading('description', text='Description')
        self.template_tree.heading('steps', text='Steps')

        self.template_tree.column('name', width=200)
        self.template_tree.column('slug', width=150)
        self.template_tree.column('description', width=400)
        self.template_tree.column('steps', width=200)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.template_tree.yview)
        self.template_tree.configure(yscrollcommand=scrollbar.set)

        self.template_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind double-click to edit
        self.template_tree.bind('<Double-Button-1>', lambda e: self.edit_template())

        # Buttons
        self.create_button_frame(main_frame, [
            ("Create New Template", self.create_template),
            ("Edit Selected", self.edit_template),
                ("Delete Selected", self.delete_template),
            ("Refresh", self.load_templates),
            ("Close", self.dialog.destroy)
        ])

    def load_templates(self):
        """Load templates using WorkflowTemplate model."""
        for item in self.template_tree.get_children():
            self.template_tree.delete(item)

        try:
            templates = self.queue.get_workflow_templates()

            for template in templates:
                step_count = f"{len(template.steps)} step{'s' if len(template.steps) != 1 else ''}"

                self.template_tree.insert(
                    '',
                    tk.END,
                    values=(template.name, template.slug, template.description, step_count)
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load templates: {e}")

    def create_template(self):
        """Open dialog to create a new template."""
        dialog = WorkflowTemplateEditorDialog(
            self.dialog,
            self.queue,
            mode='create'
        )
        if dialog.result:
            self.load_templates()

    def edit_template(self):
        """Open dialog to edit the selected template."""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a template to edit.")
            return

        item = selection[0]
        values = self.template_tree.item(item, 'values')

        template_slug = values[1]

        dialog = WorkflowTemplateEditorDialog(
            self.dialog,
            self.queue,
            mode='edit',
            template_slug=template_slug
        )

        if dialog.result:
            self.load_templates()

    def view_steps(self):
        """View steps for selected template."""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a template to view.")
            return

        item = selection[0]
        values = self.template_tree.item(item, 'values')
        template_name = values[0]

        try:
            # Get template details
            import subprocess
            result = subprocess.run(
                [str(self.queue.script_path), "workflow", "show", template_name],
                cwd=str(self.queue.project_root),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Create view window
                view_window = tk.Toplevel(self.dialog)
                view_window.title(f"Template: {template_name}")
                view_window.geometry("600x400")
                view_window.transient(self.dialog)

                text_frame = ttk.Frame(view_window, padding=10)
                text_frame.pack(fill="both", expand=True)

                text_widget = tk.Text(text_frame, wrap="word", font=('Courier', 9))
                scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
                text_widget.configure(yscrollcommand=scroll.set)

                text_widget.pack(side="left", fill="both", expand=True)
                scroll.pack(side="right", fill="y")

                text_widget.insert('1.0', result.stdout)
                text_widget.config(state=tk.DISABLED)

                ttk.Button(view_window, text="Close", command=view_window.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to view template: {e}")

    def delete_template(self):
        """Delete the selected template."""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a template to delete.")
            return

        item = selection[0]
        values = self.template_tree.item(item, 'values')
        template_name = values[0]

        if not messagebox.askyesno(
                "Confirm Delete",
                f"Delete workflow template '{template_name}'?\n\n"
                f"This cannot be undone."
        ):
            return

        try:
            import subprocess
            result = subprocess.run(
                [str(self.queue.script_path), "workflow", "delete", template_name],
                cwd=str(self.queue.project_root),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.load_templates()
            else:
                messagebox.showerror("Error", f"Failed to delete: {result.stderr}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")