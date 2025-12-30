"""
Enhanced Task Details Dialog with workflow context display (v5.0).
Shows workflow information from task metadata.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import subprocess
import sys
from typing import Optional

from .base_dialog import BaseDialog
from ..utils import TimeUtils


class TaskDetailsDialog(BaseDialog):
    """Enhanced dialog for viewing task details with workflow context (v5.0)."""

    def __init__(self, parent, task, queue_interface):
        super().__init__(parent, "Task Details", 770, 950)
        self.task = task
        self.queue = queue_interface
        self.root = parent

        self.build_ui()

    def build_ui(self):
        """Build the task details UI."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Tab 1: General Info
        general_tab = self.build_general_tab(notebook)
        notebook.add(general_tab, text="General Info")

        # Tab 2: Prompt
        details_tab = self.build_details_tab(notebook)
        notebook.add(details_tab, text="Prompt")

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        if self.queue.task_log_exists(self.task.id, self.task.source_file):
            ttk.Button(button_frame, text="📄 View Full Log", command=self.view_log).pack(side="left", padx=5)

        # Try to get output path
        output_path = self._get_output_path()
        if output_path and output_path.exists():
            ttk.Button(
                button_frame,
                text="📁 Open Output Folder",
                command=lambda: self.open_folder(output_path)
            ).pack(side="left", padx=5)

        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side="left", padx=5)

    def build_general_tab(self, parent):
        """Build General Info tab with workflow context."""
        scrollable_frame = ttk.Frame(parent, padding=20)
        scrollable_frame.pack(fill="both", expand=True)

        # Task ID with copy button
        id_frame = ttk.Frame(scrollable_frame)
        id_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(id_frame, text="Task ID:", font=('Arial', 10, 'bold')).pack(side="left")
        ttk.Label(id_frame, text=self.task.id, font=('Courier', 9)).pack(side="left", padx=(10, 0))
        ttk.Button(id_frame, text="Copy", command=self.copy_id).pack(side="right")

        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=10)

        # WORKFLOW CONTEXT (NEW in v5.0)
        workflow_name = self.task.metadata.get('workflow_name') if self.task.metadata else None
        if workflow_name:
            self._build_workflow_section(scrollable_frame, workflow_name)

        # MODEL INFORMATION
        self._build_model_section(scrollable_frame)

        # Two-column layout for task info and cost
        columns_frame = ttk.Frame(scrollable_frame)
        columns_frame.pack(fill="x", pady=(0, 10))

        # Left column: Task Information
        left_column = ttk.LabelFrame(columns_frame, text="TASK INFORMATION", padding=10)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))

        fields = [
            ("Title", self.task.title),
            ("Agent", self.task.assigned_agent),
            ("Status", f"● {self.task.status}"),
            ("Priority", self.task.priority.upper()),
            ("Type", self.task.task_type),
            ("Created", self.task.created),
            ("Started", self.task.started or "(not started)"),
            ("Completed", self.task.completed or "(not completed)"),
            ("Runtime", TimeUtils.format_runtime(self.task.runtime_seconds) or "(not available)"),
        ]

        for i, (label, value) in enumerate(fields):
            row_frame = ttk.Frame(left_column)
            row_frame.pack(fill="x", pady=2)

            ttk.Label(row_frame, text=f"{label}:", font=('Arial', 9, 'bold'), width=12).pack(side="left")
            ttk.Label(row_frame, text=str(value), font=('Arial', 9)).pack(side="left")

        # Right column: Cost Information
        # Show model name in header if available
        cost_model = self.task.metadata.get('cost_model') if self.task.metadata else None
        header_text = "COST INFORMATION"
        if cost_model:
            # Try to get short model name
            try:
                model_obj = self.queue.models.get(cost_model)
                model_name = model_obj.name if model_obj else cost_model
            except:
                model_name = cost_model
            header_text = f"COST INFORMATION ({model_name})"

        right_column = ttk.LabelFrame(columns_frame, text=header_text, padding=10)
        right_column.pack(side="left", fill="both", expand=True, padx=(5, 0))

        cost_data = self.get_cost_data()

        if cost_data:
            cost_fields = [
                ("Total Cost", self.format_cost(cost_data.get('total_cost'))),
                ("Input Tokens", self.format_tokens(cost_data.get('input_tokens'))),
                ("Output Tokens", self.format_tokens(cost_data.get('output_tokens'))),
                ("Cache Read", self.format_tokens(cost_data.get('cache_read_tokens'))),
                ("Cache Write", self.format_tokens(cost_data.get('cache_write_tokens'))),
            ]

            for label, value in cost_fields:
                row_frame = ttk.Frame(right_column)
                row_frame.pack(fill="x", pady=2)

                ttk.Label(row_frame, text=f"{label}:", font=('Arial', 9, 'bold'), width=13).pack(side="left")
                ttk.Label(row_frame, text=value, font=('Arial', 9)).pack(side="left")
        else:
            ttk.Label(
                right_column,
                text="No cost data available",
                font=('Arial', 9),
                foreground='gray'
            ).pack(anchor="w")

        # Source file with open button
        source_frame = ttk.Frame(scrollable_frame)
        source_frame.pack(fill="x", pady=5)

        ttk.Label(source_frame, text="Source File:", font=('Arial', 9, 'bold'), width=12).pack(side="left")
        ttk.Label(source_frame, text=self.task.source_file, wraplength=500).pack(side="left")
        ttk.Button(source_frame, text="Open", command=self.open_file).pack(side="right")

        # Automation flags
        auto_frame = ttk.Frame(scrollable_frame)
        auto_frame.pack(fill="x", pady=5)

        ttk.Label(auto_frame, text="Automation:", font=('Arial', 9, 'bold'), width=12).pack(side="left")

        auto_text = []
        if self.task.auto_complete:
            auto_text.append("Auto-Complete")
        if self.task.auto_chain:
            auto_text.append("Auto-Chain")

        ttk.Label(
            auto_frame,
            text=" | ".join(auto_text) if auto_text else "Manual",
            font=('Arial', 9)
        ).pack(side="left")

        # Result
        if self.task.result:
            ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=15)
            ttk.Label(scrollable_frame, text="Result:", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
            ttk.Label(scrollable_frame, text=self.task.result, wraplength=650).pack(anchor="w")

        # SKILLS SECTION
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=15)
        skills_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Skills", padding=10)
        skills_frame.pack(fill="x", pady=(0, 15))

        # Get available skills and skills used
        agent_skills = self.queue.get_agent_skills(self.task.assigned_agent)
        skills_used = []

        # Extract skills used from log for completed/failed tasks
        if self.task.status in ['completed', 'failed']:
            log_content = self.queue.get_task_log(self.task.id, self.task.source_file)
            if log_content:
                skills_used_raw = self.queue.extract_skills_used(log_content)
                skills_used = [s.strip().lower() for s in skills_used_raw]

        if agent_skills:
            used_count = 0
            skills_data = self.queue.get_skills_list()

            # Count used skills
            for skill_dir in agent_skills:
                skill_dir_normalized = skill_dir.strip().lower()
                if skill_dir_normalized in skills_used:
                    used_count += 1

            # Display header
            header_text = f"Agent Skills ({len(agent_skills)})"
            if used_count > 0:
                header_text += f" - {used_count} Used"

            ttk.Label(
                skills_frame,
                text=header_text,
                font=('Arial', 9, 'bold')
            ).pack(anchor="w", pady=(0, 5))

            # Display skills with indicators
            for skill_dir in agent_skills:
                if skills_data:
                    skill_info = next(
                        (s for s in skills_data.get('skills', [])
                         if s.get('skill-directory') == skill_dir),
                        None
                    )
                    if skill_info:
                        skill_name = skill_info.get('name', skill_dir)

                        skill_dir_normalized = skill_dir.strip().lower()
                        was_used = skill_dir_normalized in skills_used

                        if was_used:
                            ttk.Label(
                                skills_frame,
                                text=f"  ✓ {skill_name} (Used!)",
                                font=('Arial', 9),
                                foreground='green'
                            ).pack(anchor="w")
                        else:
                            ttk.Label(
                                skills_frame,
                                text=f"  • {skill_name}",
                                font=('Arial', 9),
                                foreground='gray'
                            ).pack(anchor="w")
        else:
            ttk.Label(
                skills_frame,
                text="This agent has no skills assigned",
                font=('Arial', 9),
                foreground='gray'
            ).pack(anchor="w")

        return scrollable_frame

    def _build_workflow_section(self, parent, workflow_name):
        """Build workflow context section (NEW in v5.0)."""
        workflow_frame = ttk.LabelFrame(parent, text="🔄 WORKFLOW CONTEXT", padding=10)
        workflow_frame.pack(fill="x", pady=(0, 10))

        # Get workflow details (convert to int if it's a string)
        workflow_step = self.task.metadata.get('workflow_step', 0)
        if isinstance(workflow_step, str):
            workflow_step = int(workflow_step)

        # Load workflow template
        workflow = self.queue.get_workflow_template(workflow_name)

        if workflow:
            # Workflow info
            info_frame = ttk.Frame(workflow_frame)
            info_frame.pack(fill="x", pady=(0, 5))

            ttk.Label(
                info_frame,
                text=f"Workflow: {workflow.name}",
                font=('Arial', 10, 'bold')
            ).pack(side="left")

            ttk.Label(
                info_frame,
                text=f"Step {workflow_step + 1} of {workflow.get_total_steps()}",
                font=('Arial', 9),
                foreground='blue'
            ).pack(side="right")

            # Current step details
            current_step = workflow.get_step(workflow_step)
            if current_step:
                step_details_frame = ttk.Frame(workflow_frame)
                step_details_frame.pack(fill="x", pady=(5, 5))

                # Input pattern
                ttk.Label(
                    step_details_frame,
                    text="Input:",
                    font=('Arial', 9, 'bold'),
                    width=15
                ).grid(row=0, column=0, sticky="w")
                ttk.Label(
                    step_details_frame,
                    text=current_step.input,
                    font=('Arial', 9),
                    foreground='gray'
                ).grid(row=0, column=1, sticky="w")

                # Expected output
                ttk.Label(
                    step_details_frame,
                    text="Expected Output:",
                    font=('Arial', 9, 'bold'),
                    width=15
                ).grid(row=1, column=0, sticky="w")
                ttk.Label(
                    step_details_frame,
                    text=current_step.required_output,
                    font=('Arial', 9),
                    foreground='gray'
                ).grid(row=1, column=1, sticky="w")

                # Expected statuses
                expected_statuses = current_step.get_expected_statuses()
                if expected_statuses:
                    ttk.Label(
                        step_details_frame,
                        text="Expected Statuses:",
                        font=('Arial', 9, 'bold'),
                        width=15
                    ).grid(row=2, column=0, sticky="w")
                    ttk.Label(
                        step_details_frame,
                        text=", ".join(expected_statuses),
                        font=('Arial', 9),
                        foreground='gray'
                    ).grid(row=2, column=1, sticky="w")
        else:
            ttk.Label(
                workflow_frame,
                text=f"Workflow: {workflow_name} (template not found)",
                font=('Arial', 10),
                foreground='orange'
            ).pack(anchor="w")

    def _build_model_section(self, parent):
        """Build model information section."""
        requested_model = self.task.metadata.get('requested_model') if self.task.metadata else None
        cost_model = self.task.metadata.get('cost_model') if self.task.metadata else None

        # Only show section if we have model info
        if not (requested_model or cost_model):
            return

        model_frame = ttk.LabelFrame(parent, text="🤖 MODEL INFORMATION", padding=10)
        model_frame.pack(fill="x", pady=(0, 10))

        if requested_model:
            # Try to get model details from CMAT
            try:
                model_obj = self.queue.models.get(requested_model)
                display_name = f"{model_obj.name} ({requested_model})" if model_obj else requested_model
            except:
                display_name = requested_model

            row = ttk.Frame(model_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text="Requested Model:", font=('Arial', 9, 'bold'), width=16).pack(side="left")
            ttk.Label(row, text=display_name, font=('Arial', 9)).pack(side="left")

        if cost_model and cost_model != requested_model:
            # Show actual model if different from requested
            try:
                model_obj = self.queue.models.get(cost_model)
                display_name = f"{model_obj.name} ({cost_model})" if model_obj else cost_model
            except:
                display_name = cost_model

            row = ttk.Frame(model_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text="Actual Model Used:", font=('Arial', 9, 'bold'), width=16).pack(side="left")
            ttk.Label(row, text=display_name, font=('Arial', 9), foreground='blue').pack(side="left")

    def build_details_tab(self, parent):
        """Build Prompt tab."""
        scrollable_frame = ttk.Frame(parent, padding=20)
        scrollable_frame.pack(fill="both", expand=True)

        # Try to extract full prompt from log file
        full_prompt = self._extract_prompt_from_log()

        if full_prompt:
            ttk.Label(scrollable_frame, text="Full Prompt Sent to Claude:", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
            prompt_to_show = full_prompt
        else:
            ttk.Label(scrollable_frame, text="Task Description:", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
            ttk.Label(
                scrollable_frame,
                text="(Full prompt not available - showing task description only)",
                font=('Arial', 8),
                foreground='gray'
            ).pack(anchor="w", pady=(0, 5))
            prompt_to_show = self.task.description

        desc_frame = ttk.Frame(scrollable_frame)
        desc_frame.pack(fill="both", expand=True, pady=(0, 15))

        desc_text = tk.Text(desc_frame, wrap="word", state=tk.NORMAL, font=('Courier', 9))
        desc_scroll = ttk.Scrollbar(desc_frame, command=desc_text.yview)
        desc_text.configure(yscrollcommand=desc_scroll.set)

        desc_text.pack(side="left", fill="both", expand=True)
        desc_scroll.pack(side="right", fill="y")

        desc_text.insert('1.0', prompt_to_show)
        desc_text.config(state=tk.DISABLED)

        return scrollable_frame

    def _extract_prompt_from_log(self) -> Optional[str]:
        """Extract the full prompt from the task log file."""
        log_content = self.queue.get_task_log(self.task.id, self.task.source_file)
        if not log_content:
            return None

        # Look for the prompt section in the log
        # The log format has separator lines with "PROMPT SENT TO AGENT" and "END OF PROMPT"
        start_marker = "PROMPT SENT TO AGENT"
        end_marker = "END OF PROMPT"

        if start_marker not in log_content or end_marker not in log_content:
            return None

        # Find the start of the prompt (after the header line with equals signs)
        start_idx = log_content.find(start_marker)
        if start_idx == -1:
            return None

        # Skip past the marker line and any following separator line
        start_idx = log_content.find('\n', start_idx)
        if start_idx == -1:
            return None
        start_idx += 1

        # Skip any separator lines (lines with ===)
        while start_idx < len(log_content) and log_content[start_idx:start_idx+5] == '=====':
            start_idx = log_content.find('\n', start_idx)
            if start_idx == -1:
                return None
            start_idx += 1

        # Find the end marker
        end_idx = log_content.find(end_marker, start_idx)
        if end_idx == -1:
            return None

        # Back up to before the separator line before END OF PROMPT
        # Look backward for the last newline before the === separator
        temp_idx = end_idx - 1
        while temp_idx > start_idx and log_content[temp_idx] in '\n=':
            temp_idx -= 1

        # Find the newline before the separator
        while temp_idx > start_idx and log_content[temp_idx] != '\n':
            temp_idx -= 1

        if temp_idx > start_idx:
            end_idx = temp_idx

        if start_idx < end_idx:
            prompt = log_content[start_idx:end_idx].strip()
            return prompt

        return None

    def _get_output_path(self) -> Path:
        """Get output path for this task."""
        # Try to get from workflow if available
        if self.task.metadata:
            workflow_name = self.task.metadata.get('workflow_name')
            workflow_step = self.task.metadata.get('workflow_step')
            enhancement_name = self.task.metadata.get('enhancement_title')

            if workflow_name and workflow_step is not None and enhancement_name:
                output_path_str = self.queue.get_step_output_path(
                    workflow_name,
                    workflow_step,
                    enhancement_name,
                    self.task.assigned_agent
                )
                if output_path_str:
                    output_path = self.queue.project_root / Path(output_path_str).parent
                    return output_path

        # Fallback: try to extract from source file
        source_path = Path(self.task.source_file)
        if source_path.parts[0] == 'enhancements' and len(source_path.parts) >= 2:
            enhancement_name = source_path.parts[1]
            output_path = self.queue.project_root / "enhancements" / enhancement_name / self.task.assigned_agent
            return output_path

        return None

    def copy_id(self):
        """Copy task ID to clipboard."""
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(self.task.id)

    def open_file(self):
        """Open source file."""
        source_path = Path(self.task.source_file)
        if not source_path.is_absolute():
            source_path = self.queue.project_root / source_path

        if not source_path.exists():
            messagebox.showerror("Error", f"File not found: {source_path}")
            return

        if sys.platform == 'darwin':
            subprocess.run(['open', str(source_path)])
        elif sys.platform == 'win32':
            subprocess.run(['start', str(source_path)], shell=True)
        else:
            subprocess.run(['xdg-open', str(source_path)])

    def open_folder(self, folder_path: Path):
        """Open folder in file browser."""
        if not folder_path.exists():
            messagebox.showerror("Error", f"Folder not found: {folder_path}")
            return

        if sys.platform == 'darwin':
            subprocess.run(['open', str(folder_path)])
        elif sys.platform == 'win32':
            subprocess.run(['explorer', str(folder_path)])
        else:
            subprocess.run(['xdg-open', str(folder_path)])

    def view_log(self):
        """View full task log."""
        log_content = self.queue.get_task_log(self.task.id, self.task.source_file)
        if not log_content:
            messagebox.showinfo("No Log", "Log file not found")
            return

        # Create log viewer window
        log_window = tk.Toplevel(self.dialog)
        log_window.title(f"Task Log: {self.task.id}")
        log_window.geometry("1000x700")

        log_window.transient(self.dialog)
        log_window.grab_set()
        log_window.bind('<Escape>', lambda e: log_window.destroy())
        log_window.focus_set()

        # Header with search
        header = ttk.Frame(log_window, padding=10)
        header.pack(fill="x")

        ttk.Label(header, text="Search:", font=('Arial', 9)).pack(side="left", padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(header, textvariable=search_var, width=30)
        search_entry.pack(side="left")

        def search_log():
            query = search_var.get()
            if query:
                text_widget.tag_remove('search', '1.0', tk.END)
                idx = '1.0'
                while True:
                    idx = text_widget.search(query, idx, tk.END, nocase=True)
                    if not idx:
                        break
                    end_idx = f"{idx}+{len(query)}c"
                    text_widget.tag_add('search', idx, end_idx)
                    idx = end_idx
                text_widget.tag_config('search', background='yellow')

        ttk.Button(header, text="Find", command=search_log).pack(side="left", padx=5)

        # Text area
        text_frame = ttk.Frame(log_window, padding=10)
        text_frame.pack(fill="both", expand=True)

        text_widget = tk.Text(text_frame, wrap="none", font=('Courier', 9), state='normal')
        scroll_y = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        scroll_x = ttk.Scrollbar(text_frame, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        text_widget.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        text_widget.insert('1.0', log_content)
        text_widget.config(state='disabled')

        # Bottom buttons
        button_frame = ttk.Frame(log_window, padding=10)
        button_frame.pack(fill="x")

        ttk.Button(button_frame, text="Close", command=log_window.destroy).pack(side="right")

    def get_cost_data(self):
        """Extract cost data from task metadata."""
        if not self.task.metadata or not isinstance(self.task.metadata, dict):
            return None

        # Check for nested cost structure
        cost_data = self.task.metadata.get('cost')
        if cost_data and isinstance(cost_data, dict):
            return cost_data

        # Check for flat cost structure (CMAT format)
        if 'cost_usd' in self.task.metadata:
            try:
                return {
                    'total_cost': float(self.task.metadata.get('cost_usd', 0)),
                    'input_tokens': int(self.task.metadata.get('cost_input_tokens', 0)),
                    'output_tokens': int(self.task.metadata.get('cost_output_tokens', 0)),
                    'cache_read_tokens': int(self.task.metadata.get('cost_cache_read_tokens', 0)),
                    'cache_write_tokens': int(self.task.metadata.get('cost_cache_creation_tokens', 0)),
                }
            except (ValueError, TypeError):
                return None

        return None

    def format_cost(self, cost_value):
        """Format cost as currency."""
        if cost_value is None:
            return "-"
        return f"${cost_value:.4f}"

    def format_tokens(self, token_count):
        """Format token count with thousand separators."""
        if token_count is None:
            return "-"
        return f"{token_count:,}"