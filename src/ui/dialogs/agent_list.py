"""
Agent Manager dialog for viewing and managing agents.
"""

import tkinter as tk
from tkinter import ttk

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

        # Treeview with scrollbar using BaseDialog helper
        self.agent_tree = self.create_scrolled_treeview(
            list_frame,
            columns={
                'name': ('Name', 180),
                'file': ('File', 150),
                'skills_count': ('Skills', 60),
                'description': ('Description', 400),
            },
            sortable=True
        )

        # Bind double-click
        self.agent_tree.bind('<Double-Button-1>', lambda e: self.edit_agent())

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
                display_name = agent.get('display_name', '') or agent.get('name', '')
                agent_file = agent.get('agent-file', '')
                description = agent.get('description', '')

                # Show skills count
                skills = agent.get('skills', [])
                skills_count = len(skills) if skills else 0

                self.agent_tree.insert(
                    '',
                    tk.END,
                    values=(display_name, agent_file, skills_count, description)
                )

        except Exception as e:
            self.show_error("Error", f"Failed to load agents: {e}")

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
        agent_file = self.get_selected_tree_field(
            self.agent_tree, 1, "Please select an agent to edit."
        )
        if agent_file is None:
            return

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
        _, values = self.get_selected_tree_item(
            self.agent_tree, "Please select an agent to delete."
        )
        if values is None:
            return

        agent_name = values[0]
        agent_file = values[1]

        # Check if agent is used in any workflow templates
        workflows_using_agent = self._get_workflows_using_agent(agent_file)
        if workflows_using_agent:
            workflow_list = "\n".join(f"  • {w}" for w in workflows_using_agent)
            self.show_error(
                "Cannot Delete",
                f"Agent '{agent_name}' is used in the following workflow templates:\n\n"
                f"{workflow_list}\n\n"
                f"Remove the agent from these workflows before deleting."
            )
            return

        if not self.confirm_action(
                "Confirm Delete",
                f"Delete agent '{agent_name}'?\n\n"
                f"This will remove the agent and its configuration."
        ):
            return

        try:
            self.queue.delete_agent(agent_file)
            self.load_agents()

        except Exception as e:
            self.show_error("Error", f"Failed to delete: {e}")

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