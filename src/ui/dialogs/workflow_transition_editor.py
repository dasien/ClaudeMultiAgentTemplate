"""
Workflow Transition Editor Dialog - Manage status transitions for a workflow step.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_dialog import BaseDialog


class WorkflowTransitionEditorDialog(BaseDialog):
    """Dialog for managing status transitions."""

    def __init__(self, parent, queue_interface, transitions_dict, workflow_agents):
        """
        Initialize transition manager.

        Args:
            parent: Parent window
            queue_interface: Queue interface
            transitions_dict: Current transitions {status: {next_step, auto_chain}}
            workflow_agents: List of agent keys in the workflow
        """
        self.queue = queue_interface
        self.transitions = transitions_dict.copy()  # Work on a copy
        self.workflow_agents = workflow_agents
        self.agents_map = self.queue.get_agent_list()
        self.editing_status = None  # Track which status we're editing

        super().__init__(parent, "Manage Status Transitions", 720, 710)

        self.build_ui()
        self.show()

    def build_ui(self):
        """Build the transition manager UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title and description
        ttk.Label(
            main_frame,
            text="Status Transitions",
            font=('Arial', 12, 'bold')
        ).pack(pady=(0, 5))

        ttk.Label(
            main_frame,
            text="Configure what happens when the agent outputs each status code",
            font=('Arial', 9),
            foreground='gray'
        ).pack(pady=(0, 15))

        # Current transitions list
        list_frame = ttk.LabelFrame(main_frame, text="Current Transitions", padding=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ('status', 'next_step', 'auto_chain', 'auto_start')
        self.trans_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.trans_tree.heading('status', text='Status Code')
        self.trans_tree.heading('next_step', text='Next Step')
        self.trans_tree.heading('auto_chain', text='Auto-Chain')
        self.trans_tree.heading('auto_start', text='Auto-Start')

        self.trans_tree.column('status', width=180)
        self.trans_tree.column('next_step', width=180)
        self.trans_tree.column('auto_chain', width=85)
        self.trans_tree.column('auto_start', width=85)

        trans_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.trans_tree.yview)
        self.trans_tree.configure(yscrollcommand=trans_scroll.set)

        self.trans_tree.pack(side="left", fill="both", expand=True)
        trans_scroll.pack(side="right", fill="y")

        # Bind double-click to edit
        self.trans_tree.bind('<Double-Button-1>', self.on_transition_double_click)

        # Refresh display
        self.refresh_transitions()

        # Helper text below the list frame (outside list_frame, in main_frame)
        ttk.Label(
            main_frame,
            text="💡 Tip: Double-click a transition in the list above to edit it",
            font=('Arial', 8),
            foreground='blue'
        ).pack(anchor="w", pady=(0, 10))

        # Add/Edit transition form
        form_frame = ttk.LabelFrame(main_frame, text="Add/Edit Transition", padding=10)
        form_frame.pack(fill="x", pady=(0, 10))

        # Status code
        ttk.Label(form_frame, text="Status Code:").pack(anchor="w")
        self.status_var = tk.StringVar()
        self.status_entry = ttk.Entry(form_frame, textvariable=self.status_var, width=40)
        self.status_entry.pack(fill="x", pady=(0, 5))

        ttk.Label(
            form_frame,
            text="Examples: READY_FOR_DEVELOPMENT, TESTING_COMPLETE, BLOCKED",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 10))

        # Next step
        ttk.Label(form_frame, text="Next Step:").pack(anchor="w")
        self.next_step_var = tk.StringVar()
        next_step_combo = ttk.Combobox(form_frame, textvariable=self.next_step_var, state='readonly', width=40)

        # Build next step options
        next_options = ['(end workflow)']
        for agent_key in self.workflow_agents:
            agent_name = self.agents_map.get(agent_key, agent_key)
            next_options.append(agent_name)

        next_step_combo['values'] = next_options
        next_step_combo.current(0)
        next_step_combo.pack(fill="x", pady=(0, 10))

        # Auto-chain
        self.auto_chain_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            form_frame,
            text="Auto-chain (automatically create next task when this status is output)",
            variable=self.auto_chain_var
        ).pack(anchor="w", pady=(0, 5))

        # Auto-start
        self.auto_start_var = tk.BooleanVar(value=True)
        self.auto_start_cb = ttk.Checkbutton(
            form_frame,
            text="Auto-start (immediately start next task; uncheck to leave pending for review)",
            variable=self.auto_start_var
        )
        self.auto_start_cb.pack(anchor="w", pady=(0, 10))

        # Bind auto_chain to enable/disable auto_start
        self.auto_chain_var.trace_add('write', self._on_auto_chain_changed)

        # Form buttons
        form_button_frame = ttk.Frame(form_frame)
        form_button_frame.pack()

        ttk.Button(
            form_button_frame,
            text="Apply",
            command=self.add_or_update_transition,
            width=15
        ).pack(side="left", padx=2)

        ttk.Button(
            form_button_frame,
            text="Remove Selected",
            command=self.remove_transition,
            width=15
        ).pack(side="left", padx=2)

        # Bottom buttons
        self.create_button_frame(main_frame, [
            ("Close", lambda: self.close(result=self.transitions))
        ])

    def refresh_transitions(self):
        """Refresh the transitions list."""
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)

        for status, config in self.transitions.items():
            next_step = config.get('next_step')
            auto_chain = 'Yes' if config.get('auto_chain', False) else 'No'
            auto_start = 'Yes' if config.get('auto_start', True) else 'No'

            # Format next step display
            if next_step and next_step != 'null':
                next_display = self.agents_map.get(next_step, next_step)
            else:
                next_display = '(end workflow)'

            self.trans_tree.insert('', tk.END, values=(status, next_display, auto_chain, auto_start))

    def on_transition_double_click(self, event):
        """Handle double-click to edit transition."""
        selection = self.trans_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.trans_tree.item(item, 'values')
        status = values[0]

        # Populate form with existing values
        existing = self.transitions.get(status)
        if existing:
            self.editing_status = status  # Remember we're editing this status
            self.status_var.set(status)
            self.status_entry.config(state='normal')  # Allow editing status code

            # Set next step
            next_step = existing.get('next_step')
            if next_step and next_step != 'null':
                next_name = self.agents_map.get(next_step, next_step)
                self.next_step_var.set(next_name)
            else:
                self.next_step_var.set('(end workflow)')

            # Set auto-chain and auto-start
            self.auto_chain_var.set(existing.get('auto_chain', False))
            self.auto_start_var.set(existing.get('auto_start', True))

    def add_or_update_transition(self):
        """Add new transition or update existing one."""
        status = self.status_var.get().strip().upper()
        next_step_display = self.next_step_var.get()
        auto_chain = self.auto_chain_var.get()

        if not status:
            messagebox.showwarning("Validation", "Status code is required.")
            return

        # Validate status code format
        if not all(c.isalnum() or c == '_' for c in status):
            messagebox.showwarning(
                "Validation",
                "Status code should contain only uppercase letters, numbers, and underscores."
            )
            return

        # Get agent key for next step
        if next_step_display == '(end workflow)':
            next_step_key = None
        else:
            next_step_key = next((k for k, v in self.agents_map.items() if v == next_step_display), None)

        # If we're editing and the status changed, remove the old one
        if self.editing_status and self.editing_status != status:
            if self.editing_status in self.transitions:
                del self.transitions[self.editing_status]

        # Add or update transition
        self.transitions[status] = {
            'next_step': next_step_key,
            'auto_chain': auto_chain,
            'auto_start': self.auto_start_var.get()
        }

        # Refresh display
        self.refresh_transitions()

        # Clear form
        self.editing_status = None
        self.status_var.set('')
        self.status_entry.config(state='normal')
        self.next_step_var.set('(end workflow)')
        self.auto_chain_var.set(True)
        self.auto_start_var.set(True)

    def remove_transition(self):
        """Remove selected transition."""
        selection = self.trans_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a transition to remove.")
            return

        item = selection[0]
        values = self.trans_tree.item(item, 'values')
        status = values[0]

        if messagebox.askyesno("Confirm", f"Remove transition for status '{status}'?"):
            del self.transitions[status]
            self.refresh_transitions()
            self.clear_form()

    def clear_form(self):
        """Clear the add/edit transition form."""
        self.editing_status = None
        self.status_var.set('')
        self.status_entry.config(state='normal')
        self.next_step_var.set('(end workflow)')
        self.auto_chain_var.set(True)
        self.auto_start_var.set(True)

    def _on_auto_chain_changed(self, *args):
        """Enable/disable auto_start based on auto_chain state."""
        if self.auto_chain_var.get():
            self.auto_start_cb.config(state='normal')
        else:
            self.auto_start_cb.config(state='disabled')
            self.auto_start_var.set(True)  # Reset to default when disabled