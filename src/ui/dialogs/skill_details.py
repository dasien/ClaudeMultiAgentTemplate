"""
Skill Details Dialog - Create and edit skills.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_dialog import BaseDialog
from ..utils import to_slug, validate_slug


class SkillDetailsDialog(BaseDialog):
    """Dialog for creating/editing skills."""

    def __init__(self, parent, queue_interface, mode='create', skill_directory=None):
        # Initialize base class
        BaseDialog.__init__(self, parent,
                            "Create New Skill" if mode == 'create' else "Edit Skill",
                            800, 700)

        self.queue = queue_interface
        self.mode = mode
        self.skill_directory = skill_directory

        # Load categories
        self.categories = self.queue.get_skill_categories()

        self.build_ui()

        if mode == 'edit' and skill_directory:
            self.load_skill_data()

        self.show()

    def build_ui(self):
        """Build the UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Basic Info Section
        info_frame = ttk.LabelFrame(main_frame, text="Skill Information", padding=10)
        info_frame.pack(fill="x", pady=(0, 10))

        # Name
        ttk.Label(info_frame, text="Name: *").pack(anchor="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(info_frame, textvariable=self.name_var, width=60)
        self.name_entry.pack(fill="x", pady=(0, 10))

        # Auto-generate directory from name
        self.auto_dir_var = tk.BooleanVar(value=True)
        self.name_var.trace_add('write', self.on_name_changed)

        # Directory (slug)
        dir_frame = ttk.Frame(info_frame)
        dir_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(dir_frame, text="Directory: *").pack(anchor="w")
        dir_input_frame = ttk.Frame(dir_frame)
        dir_input_frame.pack(fill="x")

        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_input_frame, textvariable=self.dir_var, width=40)
        self.dir_entry.pack(side="left", fill="x", expand=True)

        self.auto_dir_check = ttk.Checkbutton(
            dir_input_frame,
            text="Auto from name",
            variable=self.auto_dir_var,
            command=self.toggle_dir_auto
        )
        self.auto_dir_check.pack(side="left", padx=(10, 0))

        ttk.Label(
            info_frame,
            text="Directory name (lowercase, hyphens only). Creates .claude/skills/<directory>/SKILL.md",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 10))

        # Category
        ttk.Label(info_frame, text="Category: *").pack(anchor="w")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            info_frame,
            textvariable=self.category_var,
            state='readonly',
            width=30
        )
        # Populate with existing categories
        if self.categories:
            self.category_combo['values'] = sorted(self.categories)
        else:
            self.category_combo['values'] = ['analysis', 'architecture', 'implementation', 'testing', 'documentation']
        self.category_combo.pack(anchor="w", pady=(0, 10))

        # Description
        ttk.Label(info_frame, text="Description: *").pack(anchor="w")
        self.desc_var = tk.StringVar()
        self.desc_entry = ttk.Entry(info_frame, textvariable=self.desc_var, width=60)
        self.desc_entry.pack(fill="x", pady=(0, 5))

        ttk.Label(
            info_frame,
            text="Brief description of what this skill provides",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w")

        # Content Section
        content_frame = ttk.LabelFrame(main_frame, text="Skill Content (SKILL.md)", padding=10)
        content_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(
            content_frame,
            text="The skill content provides guidance and methodology for the agent. "
                 "Write in markdown format.",
            font=('Arial', 9),
            foreground='gray',
            wraplength=700
        ).pack(anchor="w", pady=(0, 10))

        # Content text area
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill="both", expand=True)

        self.content_text = tk.Text(
            text_frame,
            wrap="word",
            font=('Courier', 10),
            height=15
        )
        content_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scroll.set)

        self.content_text.pack(side="left", fill="both", expand=True)
        content_scroll.pack(side="right", fill="y")

        # Template hint for new skills
        if self.mode == 'create':
            template = """# Skill Name

## Purpose
What this skill helps the agent accomplish.

## When to Use
Situations where this skill should be applied.

## Approach
Step-by-step methodology:
1. First step
2. Second step
3. Third step

## Best Practices
- Do this
- Avoid that

## Examples
Concrete examples of applying this skill.
"""
            self.content_text.insert('1.0', template)

        # Buttons
        self.create_button_frame(main_frame, [
            ("Save", self.save_skill),
            ("Cancel", self.cancel)
        ])

    def on_name_changed(self, *args):
        """Auto-generate directory from name if enabled."""
        if self.mode == 'create' and self.auto_dir_var.get():
            name = self.name_var.get().strip()
            slug = to_slug(name)
            self.dir_var.set(slug)

    def toggle_dir_auto(self):
        """Toggle auto-directory generation."""
        if self.auto_dir_var.get():
            # Re-sync with current name
            self.on_name_changed()
            self.dir_entry.config(state='disabled')
        else:
            self.dir_entry.config(state='normal')

    def load_skill_data(self):
        """Load existing skill for editing."""
        try:
            skill_data = self.queue.get_skill(self.skill_directory)

            if not skill_data:
                messagebox.showerror("Error", f"Skill '{self.skill_directory}' not found")
                self.cancel()
                return

            # Populate fields
            self.name_var.set(skill_data.get('name', ''))
            self.dir_var.set(skill_data.get('directory', ''))
            self.category_var.set(skill_data.get('category', ''))
            self.desc_var.set(skill_data.get('description', ''))

            # Load content
            content = skill_data.get('content', '')
            if content:
                self.content_text.delete('1.0', tk.END)
                self.content_text.insert('1.0', content)

            # Disable auto-dir for edit mode
            self.auto_dir_var.set(False)
            self.dir_entry.config(state='disabled')  # Don't allow changing directory in edit mode
            self.auto_dir_check.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load skill: {e}")
            self.cancel()

    def validate(self) -> bool:
        """Validate form before saving."""
        name = self.name_var.get().strip()
        directory = self.dir_var.get().strip()
        category = self.category_var.get().strip()
        description = self.desc_var.get().strip()
        content = self.content_text.get('1.0', 'end-1c').strip()

        if not name:
            messagebox.showwarning("Validation", "Name is required.")
            return False

        if not directory:
            messagebox.showwarning("Validation", "Directory is required.")
            return False

        if not validate_slug(directory):
            messagebox.showwarning("Validation", "Directory must be lowercase with hyphens only.")
            return False

        if not category:
            messagebox.showwarning("Validation", "Category is required.")
            return False

        if not description:
            messagebox.showwarning("Validation", "Description is required.")
            return False

        if not content:
            messagebox.showwarning("Validation", "Content is required.")
            return False

        # Check for duplicate directory on create
        if self.mode == 'create':
            existing = self.queue.get_skill(directory)
            if existing:
                messagebox.showwarning("Validation", f"A skill with directory '{directory}' already exists.")
                return False

        return True

    def save_skill(self):
        """Save the skill."""
        if not self.validate():
            return

        skill_data = {
            'name': self.name_var.get().strip(),
            'directory': self.dir_var.get().strip(),
            'category': self.category_var.get().strip(),
            'description': self.desc_var.get().strip(),
            'content': self.content_text.get('1.0', 'end-1c'),
            'required_tools': [],  # Can be extended later
        }

        try:
            if self.mode == 'create':
                self.queue.create_skill(skill_data)
            else:
                self.queue.update_skill(self.skill_directory, skill_data)

            self.close(result=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save skill: {e}")
