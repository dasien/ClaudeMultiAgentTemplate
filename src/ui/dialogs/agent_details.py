"""
Enhanced Agent Manager with skills editing support (v5.0).
Simplified - agents are just capabilities, no workflow orchestration.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_dialog import BaseDialog
from ..utils import to_slug, validate_slug


class AgentDetailsDialog(BaseDialog):
    """Enhanced dialog for creating/editing agents (v5.0 - simplified)."""

    def __init__(self, parent, queue_interface, mode='create', agent_file=None):
        # Initialize base class
        BaseDialog.__init__(self, parent,
                            "Create New Agent" if mode == 'create' else "Edit Agent",
                            800, 850)

        self.queue = queue_interface
        self.mode = mode
        self.agent_file = agent_file

        # Load data
        self.tools_data = self.queue.get_tools_data()
        self.skills_data = self.queue.get_skills_list()
        self.agents_map = self.queue.get_agent_list()

        # UI state
        self.tool_checkboxes = {}
        self.skill_checkboxes = {}

        self.build_ui()

        if mode == 'edit' and agent_file:
            self.load_agent_data()

        self.show()

    def build_ui(self):
        """Build the UI with tabbed interface."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Tabs (removed Workflow tab)
        basic_tab = ttk.Frame(notebook, padding=20)
        tools_tab = ttk.Frame(notebook, padding=20)
        skills_tab = ttk.Frame(notebook, padding=20)

        notebook.add(basic_tab, text="Basic Info")
        notebook.add(tools_tab, text="Tools")
        notebook.add(skills_tab, text="Skills")

        self.build_basic_tab(basic_tab)
        self.build_tools_tab(tools_tab)
        self.build_skills_tab(skills_tab)

        # Bottom buttons
        self.create_button_frame(main_frame, [
            ("Save", self.save_agent),
            ("Cancel", self.cancel)
        ])

        ttk.Label(main_frame, text="* Required fields", font=('Arial', 9), foreground='gray').pack()

    def build_basic_tab(self, parent):
        """Build basic information tab."""
        # Name and File on same line
        name_file_frame = ttk.Frame(parent)
        name_file_frame.pack(fill="x", pady=(0, 15))

        # Name column
        name_col = ttk.Frame(name_file_frame)
        name_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(name_col, text="Agent Name: *", font=('Arial', 10, 'bold')).pack(anchor="w")
        self.name_var = tk.StringVar()
        self.name_var.trace_add('write', self.on_name_changed)
        ttk.Entry(name_col, textvariable=self.name_var, width=30).pack(fill="x")

        # File column
        file_col = ttk.Frame(name_file_frame)
        file_col.pack(side="left", fill="x", expand=True, padx=(5, 0))

        file_header = ttk.Frame(file_col)
        file_header.pack(fill="x")

        ttk.Label(file_header, text="File Name (slug): *", font=('Arial', 10, 'bold')).pack(side="left")

        if self.mode == 'create':
            self.auto_filename_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                file_header,
                text="Auto",
                variable=self.auto_filename_var,
                command=self.toggle_filename_auto
            ).pack(side="right")

        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_col, textvariable=self.file_var, width=30)
        self.file_entry.pack(fill="x")
        if self.mode == 'edit':
            self.file_entry.config(state='readonly')
        elif self.mode == 'create':
            self.file_entry.config(state='readonly')

        ttk.Label(parent, text="(lowercase, hyphens only)", font=('Arial', 8), foreground='gray').pack(anchor="w",
                                                                                                       pady=(0, 15))

        # Description
        ttk.Label(parent, text="Description: *", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        self.description_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.description_var, width=70).pack(fill="x", pady=(0, 15))

        # Role (simplified - just categorization)
        ttk.Label(parent, text="Role: *", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            parent,
            text="Role is used for categorization and task type suggestions",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w")

        self.role_var = tk.StringVar()
        role_combo = ttk.Combobox(parent, textvariable=self.role_var, state='readonly', width=40)
        role_combo['values'] = [
            'analysis',
            'technical_design',
            'implementation',
            'testing',
            'documentation',
            'integration'
        ]
        role_combo.pack(fill="x", pady=(5, 15))

        # Agent Details
        ttk.Label(parent, text="Agent Instructions: *", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            parent,
            text="Describe what this agent does, its responsibilities, and output standards",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 5))

        details_frame = ttk.Frame(parent)
        details_frame.pack(fill="both", expand=True)

        self.details_text = tk.Text(details_frame, wrap="word", font=('Courier', 9))
        details_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)

        self.details_text.pack(side="left", fill="both", expand=True)
        details_scroll.pack(side="right", fill="y")

        # Note about workflow configuration
        note_frame = ttk.Frame(parent)
        note_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(
            note_frame,
            text="ℹ️  Note: Workflow orchestration (inputs, outputs, next steps) is configured in Workflow Templates.",
            font=('Arial', 9),
            foreground='blue',
            wraplength=700
        ).pack(anchor="w")

    def build_tools_tab(self, parent):
        """Build tools selection tab."""
        ttk.Label(parent, text="Available Tools: *", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 10))

        # Agent persona quick selection
        if self.tools_data and 'agent_personas' in self.tools_data:
            persona_frame = ttk.LabelFrame(parent, text="Quick Select from Persona", padding=10)
            persona_frame.pack(fill="x", pady=(0, 15))

            self.persona_var = tk.StringVar(value="")
            persona_combo = ttk.Combobox(persona_frame, textvariable=self.persona_var, state='readonly', width=30)

            personas = self.tools_data['agent_personas']
            persona_names = ["(none)"] + [personas[p]['display_name'] for p in personas.keys()]
            persona_combo['values'] = persona_names
            persona_combo.pack(fill="x")
            persona_combo.bind('<<ComboboxSelected>>', self.on_persona_selected)

        # Tools grid
        tools_frame = ttk.Frame(parent)
        tools_frame.pack(fill="both", expand=True)

        if self.tools_data and 'claude_code_tools' in self.tools_data:
            tools_list = self.tools_data['claude_code_tools']

            for idx, tool in enumerate(tools_list):
                row = idx // 3
                col = idx % 3

                var = tk.BooleanVar(value=False)
                self.tool_checkboxes[tool['name']] = var

                cb = ttk.Checkbutton(
                    tools_frame,
                    text=tool.get('display_name', tool['name']),
                    variable=var
                )
                cb.grid(row=row, column=col, sticky=tk.W, padx=15, pady=3)

    def build_skills_tab(self, parent):
        """Build skills selection tab."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Assign Skills to Agent",
            font=('Arial', 11, 'bold')
        ).pack(side="left")

        ttk.Button(
            header_frame,
            text="Preview Skills Prompt",
            command=self.preview_agent_skills
        ).pack(side="right")

        # Category filter
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_frame, text="Filter by category:").pack(side="left", padx=(0, 5))
        self.skills_category_var = tk.StringVar(value="All")
        self.skills_category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.skills_category_var,
            state='readonly',
            width=20
        )
        self.skills_category_combo.pack(side="left")
        self.skills_category_combo.bind('<<ComboboxSelected>>', self.filter_skills_list)

        # Populate categories
        if self.skills_data:
            categories = set(['All'])
            for skill in self.skills_data.get('skills', []):
                cat = skill.get('category', 'uncategorized')
                categories.add(cat.replace('-', ' ').title())
            self.skills_category_combo['values'] = sorted(list(categories))

        # Skills checkboxes frame
        self.skills_checkboxes_frame = ttk.Frame(parent)
        self.skills_checkboxes_frame.pack(fill="both", expand=True)

        self.populate_skills_checkboxes()

        # Summary
        self.skills_summary_label = ttk.Label(
            parent,
            text="0 skills selected",
            font=('Arial', 9),
            foreground='gray'
        )
        self.skills_summary_label.pack(anchor="w", pady=(10, 0))

    def populate_skills_checkboxes(self):
        """Populate skills checkboxes with filtering."""
        for widget in self.skills_checkboxes_frame.winfo_children():
            widget.destroy()

        if not self.skills_data:
            ttk.Label(
                self.skills_checkboxes_frame,
                text="Skills system not available",
                foreground='red'
            ).pack(anchor="w")
            return

        category_filter = self.skills_category_var.get()
        skills_list = self.skills_data.get('skills', [])

        canvas = tk.Canvas(self.skills_checkboxes_frame, height=400)
        scrollbar = ttk.Scrollbar(self.skills_checkboxes_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind('<Configure>', on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = 0
        for skill in skills_list:
            category = skill.get('category', 'uncategorized')

            if category_filter != 'All':
                if category.replace('-', ' ').title() != category_filter:
                    continue

            skill_dir = skill.get('skill-directory', '')
            name = skill.get('name', skill_dir)
            description = skill.get('description', '')
            cat_display = category.replace('-', ' ').title()

            if skill_dir not in self.skill_checkboxes:
                var = tk.BooleanVar(value=False)
                self.skill_checkboxes[skill_dir] = var
                var.trace_add('write', lambda *args: self.update_skills_summary())
            else:
                var = self.skill_checkboxes[skill_dir]

            cb_frame = ttk.Frame(scrollable_frame)
            cb_frame.grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)

            cb = ttk.Checkbutton(cb_frame, text=f"{name} ({cat_display})", variable=var)
            cb.pack(anchor="w")

            if description:
                ttk.Label(
                    cb_frame,
                    text=description,
                    font=('Arial', 8),
                    foreground='gray',
                    wraplength=700
                ).pack(anchor="w", padx=(20, 0))

            row += 1

    def filter_skills_list(self, event=None):
        """Re-populate skills checkboxes with filter applied."""
        self.populate_skills_checkboxes()

    def update_skills_summary(self):
        """Update skills selection summary."""
        selected = sum(1 for var in self.skill_checkboxes.values() if var.get())
        self.skills_summary_label.config(text=f"{selected} skill(s) selected")

    def preview_agent_skills(self):
        """Preview what the skills prompt will look like for this agent."""
        selected_skills = [skill_dir for skill_dir, var in self.skill_checkboxes.items() if var.get()]

        if not selected_skills:
            messagebox.showinfo("No Skills", "No skills selected. Select skills first to preview.")
            return

        try:
            preview_content = []
            preview_content.append("=" * 80)
            preview_content.append("## SPECIALIZED SKILLS AVAILABLE")
            preview_content.append("=" * 80)
            preview_content.append("")
            preview_content.append("You have access to the following specialized skills:")
            preview_content.append("")

            for skill_dir in selected_skills:
                skill_content = self.queue.load_skill_content(skill_dir)
                if skill_content:
                    preview_content.append("---")
                    preview_content.append("")
                    preview_content.append(skill_content)
                    preview_content.append("")

            preview_content.append("---")
            preview_content.append("")
            preview_content.append("**Using Skills**: Apply the above skills as appropriate.")

            # Show preview window
            preview = tk.Toplevel(self.dialog)
            preview.title("Skills Prompt Preview")
            preview.geometry("800x600")
            preview.transient(self.dialog)

            text_frame = ttk.Frame(preview, padding=10)
            text_frame.pack(fill="both", expand=True)

            text_widget = tk.Text(text_frame, wrap="word", font=('Courier', 9))
            scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scroll.set)

            text_widget.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")

            text_widget.insert('1.0', '\n'.join(preview_content))
            text_widget.config(state=tk.DISABLED)

            ttk.Button(preview, text="Close", command=preview.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to build preview: {e}")

    def on_name_changed(self, *args):
        """Auto-generate filename from name if enabled."""
        if self.mode == 'create' and self.auto_filename_var.get():
            name = self.name_var.get().strip()
            slug = to_slug(name)
            self.file_var.set(slug)

    def toggle_filename_auto(self):
        """Toggle auto-generation of filename."""
        if self.auto_filename_var.get():
            self.file_entry.config(state='readonly')
            self.on_name_changed()
        else:
            self.file_entry.config(state='normal')

    def validate(self) -> bool:
        """Validate agent form before saving."""
        name = self.name_var.get().strip()
        file_slug = self.file_var.get().strip()
        description = self.description_var.get().strip()
        role = self.role_var.get().strip()
        details = self.details_text.get('1.0', tk.END).strip()

        tools = [name for name, var in self.tool_checkboxes.items() if var.get()]
        skills = [skill_dir for skill_dir, var in self.skill_checkboxes.items() if var.get()]

        if not all([name, file_slug, description, role, details]):
            messagebox.showwarning("Validation", "All required fields must be filled.")
            return False

        if not tools:
            messagebox.showwarning("Validation", "Select at least one tool.")
            return False

        if not validate_slug(file_slug):
            messagebox.showerror("Invalid File Name", "File name must be lowercase with hyphens only.")
            return False

        return True

    def load_agent_data(self):
        """Load existing agent for editing via CMAT service."""
        try:
            # Get agent from CMAT service
            agents_data = self.queue.get_agents_data()
            agents = agents_data.get('agents', []) if agents_data else []
            agent_data = next((a for a in agents if a.get('agent-file') == self.agent_file), None)

            if not agent_data:
                messagebox.showerror("Error", f"Agent '{self.agent_file}' not found")
                self.cancel()
                return

            # Set basic fields
            self.name_var.set(agent_data.get('name', ''))
            self.file_var.set(self.agent_file)
            self.description_var.set(agent_data.get('description', ''))
            self.role_var.set(agent_data.get('role', ''))

            # Set tools
            tools = agent_data.get('tools', [])
            for tool_name, var in self.tool_checkboxes.items():
                var.set(tool_name in tools)

            # Set skills
            skills = agent_data.get('skills', [])
            for skill_dir, var in self.skill_checkboxes.items():
                var.set(skill_dir in skills)
            self.update_skills_summary()

            # Load agent instructions via CMAT interface
            agent_full = self.queue.get_agent(self.agent_file)
            if agent_full and agent_full.get('instructions'):
                self.details_text.insert('1.0', agent_full['instructions'])

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
            self.cancel()

    def save_agent(self):
        """Save the agent via CMAT service."""
        if not self.validate():
            return

        # Get validated values
        name = self.name_var.get().strip()
        file_slug = self.file_var.get().strip()
        description = self.description_var.get().strip()
        role = self.role_var.get().strip()
        details = self.details_text.get('1.0', tk.END).strip()

        tools = [t for t, var in self.tool_checkboxes.items() if var.get()]
        skills = [skill_dir for skill_dir, var in self.skill_checkboxes.items() if var.get()]

        try:
            # Build agent data
            agent_data = {
                "name": name,
                "agent-file": file_slug,
                "role": role,
                "tools": tools,
                "skills": skills,
                "description": description,
                "instructions": details,
                "validations": {
                    "metadata_required": True
                }
            }

            # Save via CMAT service
            if self.mode == 'create':
                # Check for duplicates
                existing = self.queue.get_agent_list()
                if file_slug in existing:
                    messagebox.showerror("Duplicate", f"Agent '{file_slug}' already exists.")
                    return
                self.queue.create_agent(agent_data)
            else:
                self.queue.update_agent(file_slug, agent_data)

            # Success
            self.close(result=file_slug)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def on_persona_selected(self, event=None):
        """Apply persona tool selection."""
        if not self.tools_data or 'agent_personas' not in self.tools_data:
            return

        selected = self.persona_var.get()
        if not selected or selected == "(none)":
            for var in self.tool_checkboxes.values():
                var.set(False)
            return

        personas = self.tools_data['agent_personas']
        persona_key = None
        for key, persona in personas.items():
            if persona['display_name'] == selected:
                persona_key = key
                break

        if not persona_key:
            return

        persona_tools = personas[persona_key].get('tools', [])
        for tool_name in self.tool_checkboxes.keys():
            self.tool_checkboxes[tool_name].set(tool_name in persona_tools)