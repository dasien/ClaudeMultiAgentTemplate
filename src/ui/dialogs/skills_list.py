"""
Skills Manager Dialog - Browse, create, edit, and delete skills.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict

from .base_dialog import BaseDialog


class SkillsManagerDialog(BaseDialog):
    """Dialog for managing skills (create, edit, delete)."""

    def __init__(self, parent, queue_interface):
        super().__init__(parent, "Skills Manager", 1100, 750)
        self.queue = queue_interface
        self.skills_data = None
        self.current_skill = None

        self.build_ui()
        self.load_skills()
        # Don't call show() - this dialog doesn't return a result

    def build_ui(self):
        """Build the skills manager UI."""
        # Filter controls at top
        filter_frame = ttk.Frame(self.dialog, padding=10)
        filter_frame.pack(fill="x")

        ttk.Label(filter_frame, text="Category:").pack(side="left", padx=(0, 5))
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            state='readonly',
            width=15
        )
        self.category_combo['values'] = ['All']
        self.category_combo.pack(side="left", padx=(0, 10))
        self.category_combo.bind('<<ComboboxSelected>>', self.filter_skills)

        # Main content - two panes
        content_frame = ttk.Frame(self.dialog, padding=10)
        content_frame.pack(fill="both", expand=True)

        # Left pane - Skills list
        left_frame = ttk.LabelFrame(content_frame, text="Available Skills", padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Treeview for skills
        columns = ('name', 'category', 'directory')
        self.skills_tree = ttk.Treeview(
            left_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.skills_tree.heading('name', text='Skill Name')
        self.skills_tree.heading('category', text='Category')
        self.skills_tree.heading('directory', text='Directory')

        self.skills_tree.column('name', width=200)
        self.skills_tree.column('category', width=120)
        self.skills_tree.column('directory', width=150)

        # Scrollbar
        skills_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.skills_tree.yview)
        self.skills_tree.configure(yscrollcommand=skills_scroll.set)

        self.skills_tree.pack(side="left", fill="both", expand=True)
        skills_scroll.pack(side="right", fill="y")

        # Bind selection and double-click
        self.skills_tree.bind('<<TreeviewSelect>>', self.on_skill_selected)
        self.skills_tree.bind('<Double-Button-1>', lambda e: self.edit_skill())

        # Make columns sortable
        self.make_treeview_sortable(self.skills_tree)

        # Right pane - Skill preview
        right_frame = ttk.LabelFrame(content_frame, text="Skill Details", padding=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Skill info section
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill="x", pady=(0, 10))

        self.skill_name_label = ttk.Label(
            info_frame,
            text="Select a skill to view details",
            font=('Arial', 12, 'bold')
        )
        self.skill_name_label.pack(anchor="w")

        self.skill_desc_label = ttk.Label(
            info_frame,
            text="",
            font=('Arial', 9),
            foreground='gray',
            wraplength=400
        )
        self.skill_desc_label.pack(anchor="w", pady=(5, 0))

        ttk.Separator(right_frame, orient="horizontal").pack(fill="x", pady=10)

        # Skill content preview
        ttk.Label(right_frame, text="Content:", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))

        preview_frame = ttk.Frame(right_frame)
        preview_frame.pack(fill="both", expand=True)

        self.preview_text = tk.Text(
            preview_frame,
            wrap="word",
            font=('Courier', 9),
            state=tk.DISABLED
        )
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)

        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")

        ttk.Separator(right_frame, orient="horizontal").pack(fill="x", pady=10)

        # Agents using this skill
        ttk.Label(right_frame, text="Agents Using This Skill:", font=('Arial', 10, 'bold')).pack(anchor="w",
                                                                                                 pady=(0, 5))

        self.agents_frame = ttk.Frame(right_frame)
        self.agents_frame.pack(fill="x")

        self.agents_label = ttk.Label(
            self.agents_frame,
            text="(none)",
            font=('Arial', 9),
            foreground='gray'
        )
        self.agents_label.pack(anchor="w")

        # Bottom buttons - CRUD operations
        self.create_button_frame(self.dialog, [
            ("Create New Skill", self.create_skill),
            ("Edit Selected", self.edit_skill),
            ("Delete Selected", self.delete_skill),
            ("Refresh", self.load_skills),
            ("Close", self.dialog.destroy)
        ])

    def load_skills(self):
        """Load skills from skills.json."""
        try:
            self.skills_data = self.queue.get_skills_list()

            if not self.skills_data:
                messagebox.showerror("Error", "Could not load skills.json")
                return

            # Extract categories
            categories = set(['All'])
            skills_list = self.skills_data.get('skills', [])

            for skill in skills_list:
                category = skill.get('category', 'uncategorized')
                categories.add(category.replace('-', ' ').title())

            self.category_combo['values'] = sorted(list(categories))

            # Populate tree
            self.populate_skills_tree(skills_list)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load skills: {e}")

    def populate_skills_tree(self, skills_list: List[Dict]):
        """Populate the skills tree with filtered skills."""
        for item in self.skills_tree.get_children():
            self.skills_tree.delete(item)

        category_filter = self.category_var.get()

        for skill in skills_list:
            name = skill.get('name', '')
            category = skill.get('category', 'uncategorized')
            skill_dir = skill.get('directory', '') or skill.get('skill-directory', '')

            # Apply category filter
            if category_filter != 'All':
                if category.replace('-', ' ').title() != category_filter:
                    continue

            # Add to tree
            category_display = category.replace('-', ' ').title()
            self.skills_tree.insert(
                '',
                tk.END,
                values=(name, category_display, skill_dir),
                tags=(category,)
            )

    def filter_skills(self, event=None):
        """Apply filters to skills list."""
        if self.skills_data:
            skills_list = self.skills_data.get('skills', [])
            self.populate_skills_tree(skills_list)

    def on_skill_selected(self, event):
        """Handle skill selection."""
        selection = self.skills_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.skills_tree.item(item, 'values')
        skill_name = values[0]
        skill_dir = values[2]

        # Store current skill
        self.current_skill = {
            'name': skill_name,
            'directory': skill_dir
        }

        # Update info labels
        self.skill_name_label.config(text=skill_name)

        # Get description from skills data
        skills_list = self.skills_data.get('skills', [])
        skill_data = next((s for s in skills_list if (s.get('directory') or s.get('skill-directory')) == skill_dir), None)

        if skill_data:
            description = skill_data.get('description', '')
            self.skill_desc_label.config(text=description)
        else:
            self.skill_desc_label.config(text="")

        # Load skill content
        self.load_skill_content(skill_dir)

        # Load agents using this skill
        self.load_agents_using_skill(skill_dir)

    def load_skill_content(self, skill_directory: str):
        """Load and display skill content."""
        try:
            content = self.queue.load_skill_content(skill_directory)

            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete('1.0', tk.END)

            if content:
                self.preview_text.insert('1.0', content)
            else:
                self.preview_text.insert('1.0', "Could not load skill content.")

            self.preview_text.config(state=tk.DISABLED)

        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"Error loading skill: {e}")
            self.preview_text.config(state=tk.DISABLED)

    def load_agents_using_skill(self, skill_directory: str):
        """Find and display which agents use this skill."""
        for widget in self.agents_frame.winfo_children():
            widget.destroy()

        try:
            agents_using_skill = self._get_agents_using_skill(skill_directory)

            if agents_using_skill:
                for agent_name in sorted(agents_using_skill):
                    ttk.Label(
                        self.agents_frame,
                        text=f"• {agent_name}",
                        font=('Arial', 9)
                    ).pack(anchor="w", pady=1)
            else:
                ttk.Label(
                    self.agents_frame,
                    text="(no agents currently use this skill)",
                    font=('Arial', 9),
                    foreground='gray'
                ).pack(anchor="w")

        except Exception as e:
            ttk.Label(
                self.agents_frame,
                text=f"Error: {e}",
                font=('Arial', 9),
                foreground='red'
            ).pack(anchor="w")

    def _get_agents_using_skill(self, skill_directory: str) -> List[str]:
        """Get list of agent names that use this skill."""
        agents_using_skill = []
        agents_map = self.queue.get_agent_list()

        for agent_file, agent_name in agents_map.items():
            agent_skills = self.queue.get_agent_skills(agent_file)
            if skill_directory in agent_skills:
                agents_using_skill.append(agent_name)

        return agents_using_skill

    def create_skill(self):
        """Open dialog to create a new skill."""
        from .skill_details import SkillDetailsDialog
        dialog = SkillDetailsDialog(
            self.dialog,
            self.queue,
            mode='create'
        )
        if dialog.result:
            self.load_skills()

    def edit_skill(self):
        """Open dialog to edit the selected skill."""
        selection = self.skills_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a skill to edit.")
            return

        item = selection[0]
        values = self.skills_tree.item(item, 'values')
        skill_dir = values[2]

        from .skill_details import SkillDetailsDialog
        dialog = SkillDetailsDialog(
            self.dialog,
            self.queue,
            mode='edit',
            skill_directory=skill_dir
        )
        if dialog.result:
            self.load_skills()

    def delete_skill(self):
        """Delete the selected skill."""
        selection = self.skills_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a skill to delete.")
            return

        item = selection[0]
        values = self.skills_tree.item(item, 'values')
        skill_name = values[0]
        skill_dir = values[2]

        # Check if any agents use this skill
        agents_using_skill = self._get_agents_using_skill(skill_dir)

        if agents_using_skill:
            agents_list = "\n".join(f"  • {name}" for name in sorted(agents_using_skill))
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Delete skill '{skill_name}'?\n\n"
                f"This skill is used by the following agents:\n{agents_list}\n\n"
                f"It will be removed from these agents."
            )
        else:
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Delete skill '{skill_name}'?\n\n"
                f"This will remove the skill and its files."
            )

        if not result:
            return

        try:
            # Remove skill from agents first
            if agents_using_skill:
                self.queue.remove_skill_from_agents(skill_dir)

            # Delete the skill
            self.queue.delete_skill(skill_dir)

            # Clear selection state
            self.current_skill = None
            self.skill_name_label.config(text="Select a skill to view details")
            self.skill_desc_label.config(text="")
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.config(state=tk.DISABLED)

            # Refresh list
            self.load_skills()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete skill: {e}")


# Keep old name as alias for backwards compatibility
SkillsViewerDialog = SkillsManagerDialog
