"""
Agent Manager dialog for viewing and managing agents.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_dialog import BaseDialog


class AgentListDialog(BaseDialog):
    """Dialog for managing agents (create, edit, delete)."""

    def __init__(self, parent, queue_interface, settings=None):
        super().__init__(parent, "Agent Manager", 900, 600)
        self.queue = queue_interface
        self.settings = settings

        self.build_ui()
        self.load_agents()
        # Don't call show() - this dialog doesn't return a result

    def build_ui(self):
        """Build the agent manager UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Manage Agents", font=('Arial', 14, 'bold')).pack(pady=(0, 10))

        # Agent list
        list_frame = ttk.LabelFrame(main_frame, text="Agents", padding=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Treeview - Enhanced with skills column
        columns = ('name', 'file', 'skills_count', 'description')
        self.agent_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.agent_tree.heading('name', text='Name')
        self.agent_tree.heading('file', text='File')
        self.agent_tree.heading('skills_count', text='Skills')
        self.agent_tree.heading('description', text='Description')

        self.agent_tree.column('name', width=180)
        self.agent_tree.column('file', width=150)
        self.agent_tree.column('skills_count', width=60)
        self.agent_tree.column('description', width=400)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.agent_tree.yview)
        self.agent_tree.configure(yscrollcommand=scrollbar.set)

        self.agent_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind double-click
        self.agent_tree.bind('<Double-Button-1>', lambda e: self.edit_agent())

        # Make columns sortable
        self.make_treeview_sortable(self.agent_tree)

        # Buttons - Using BaseDialog helper
        self.create_button_frame(main_frame, [
            ("Create New Agent", self.create_agent),
            ("Edit Selected", self.edit_agent),
            ("Delete Selected", self.delete_agent),
            ("Refresh", self.load_agents),
            ("Close", self.dialog.destroy)
        ])

    def load_agents(self):
        """Load agents via CMAT service."""
        for item in self.agent_tree.get_children():
            self.agent_tree.delete(item)

        try:
            agents_data = self.queue.get_agents_data()
            agents = agents_data.get('agents', []) if agents_data else []

            for agent in agents:
                name = agent.get('name', '')
                agent_file = agent.get('agent-file', '')
                description = agent.get('description', '')

                # Show skills count
                skills = agent.get('skills', [])
                skills_count = len(skills) if skills else 0

                self.agent_tree.insert(
                    '',
                    tk.END,
                    values=(name, agent_file, skills_count, description)
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load agents: {e}")

    def create_agent(self):
        """Open dialog to create a new agent."""
        from .agent_details import AgentDetailsDialog
        dialog = AgentDetailsDialog(
            self.dialog,
            self.queue,
            mode='create'
        )
        if dialog.result:
            self.load_agents()

    def edit_agent(self):
        """Open dialog to edit the selected agent."""
        selection = self.agent_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an agent to edit.")
            return

        item = selection[0]
        values = self.agent_tree.item(item, 'values')
        agent_file = values[1]

        from .agent_details import AgentDetailsDialog
        dialog = AgentDetailsDialog(
            self.dialog,
            self.queue,
            mode='edit',
            agent_file=agent_file
        )
        if dialog.result:
            self.load_agents()

    def delete_agent(self):
        """Delete the selected agent via CMAT service."""
        selection = self.agent_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an agent to delete.")
            return

        item = selection[0]
        values = self.agent_tree.item(item, 'values')
        agent_name = values[0]
        agent_file = values[1]

        # Check if agent is used in any workflow templates
        workflows_using_agent = self._get_workflows_using_agent(agent_file)
        if workflows_using_agent:
            workflow_list = "\n".join(f"  • {w}" for w in workflows_using_agent)
            messagebox.showerror(
                "Cannot Delete",
                f"Agent '{agent_name}' is used in the following workflow templates:\n\n"
                f"{workflow_list}\n\n"
                f"Remove the agent from these workflows before deleting."
            )
            return

        if not messagebox.askyesno(
                "Confirm Delete",
                f"Delete agent '{agent_name}'?\n\n"
                f"This will remove the agent and its configuration."
        ):
            return

        try:
            self.queue.delete_agent(agent_file)
            self.load_agents()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")

    def _get_workflows_using_agent(self, agent_file: str) -> list:
        """Get list of workflow template names that use this agent."""
        workflows = []
        try:
            templates = self.queue.get_workflow_templates()
            for template in templates:
                for step in template.steps:
                    if step.agent == agent_file:
                        workflows.append(template.name)
                        break  # Only add template once even if agent used in multiple steps
        except Exception:
            pass  # If we can't check, allow deletion
        return workflows