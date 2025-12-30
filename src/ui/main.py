#!/usr/bin/env python3
"""
Claude Multi-Agent Manager.
Enhanced with Skills, Workflows, and Integration features.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from .utils import CMATInterface
from .models import ConnectionState, QueueUIState
from .config import Config
from .settings import Settings
from .utils import TimeUtils
from .dialogs import WorkflowTemplateManagerDialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class MainView:
    """Main application window for Task Queue Manager."""

    def __init__(self, root):
        self.root = root
        self.root.title("Claude Multi-Agent Manager")
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)

        # Set window icon
        self.set_window_icon()

        # Settings
        self.settings = Settings()

        # State
        self.state = QueueUIState()
        self.state.connection_state = ConnectionState.DISCONNECTED
        self.state.auto_refresh_interval = Config.AUTO_REFRESH_INTERVAL
        self.auto_refresh_timer = None

        # Queue interface
        self.queue = None

        # Build UI
        self.build_menu_bar()
        self.build_connection_header()
        self.build_task_table()
        self.build_status_bar()
        self.configure_styles()

        # Initial state
        self.update_ui_state()

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Try auto-connect
        self.try_auto_connect()

    def set_window_icon(self):
        """Set the window icon."""
        try:
            # Get icon path (assets/ at project root)
            assets_dir = Path(__file__).parent.parent.parent / "assets"
            icon_png = assets_dir / "icon.png"

            # Try to load PNG icon with PIL
            if icon_png.exists() and PIL_AVAILABLE:
                # Load original image
                img = Image.open(icon_png)

                # Create icons at multiple sizes including high-res for dialogs
                # Start with largest first for better quality fallback
                sizes = [256, 128, 64, 48, 32, 16]
                photos = []

                for size in sizes:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(resized)
                    photos.append(photo)

                # Set all icon sizes (largest first)
                # The True parameter makes it default for all child windows (messageboxes)
                self.root.iconphoto(True, *photos)

                # Keep references to prevent garbage collection
                self.root._icon_photos = photos
                print(f"Icon loaded successfully from {icon_png} ({len(sizes)} sizes)")
            else:
                if not icon_png.exists():
                    print(f"Icon file not found: {icon_png}")
                if not PIL_AVAILABLE:
                    print("PIL/Pillow not available for icon loading")

        except Exception as e:
            # Icon is optional, don't fail if it doesn't work
            print(f"Could not set window icon: {e}")

    def build_menu_bar(self):
        """Create enhanced menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Store menu references for enabling/disabling
        self.menus = {}

        # File menu (always enabled)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Install...", command=self.show_install_cmat_dialog)
        file_menu.add_command(label="Connect...", command=self.show_connect_dialog, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Reset Queue...", command=self.reset_queue)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit_app, accelerator="Ctrl+Q")

        # Workflows menu (requires connection)
        workflows_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Workflows", menu=workflows_menu, state="disabled")
        workflows_menu.add_command(label="Start...", command=self.show_workflow_launcher,accelerator="Ctrl+Shift+W")
        workflows_menu.add_separator()
        workflows_menu.add_command(label="Manage Templates...", command=self.show_workflow_template_manager)
        self.menus['workflows'] = menubar.index("Workflows")

        # Enhancements menu (requires connection)
        enhancements_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Enhancements", menu=enhancements_menu, state="disabled")
        enhancements_menu.add_command(label="Create...", command=self.show_enhancement_generator, accelerator="Ctrl+E")
        self.menus['enhancements'] = menubar.index("Enhancements")

        # Tasks menu (requires connection)
        tasks_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tasks", menu=tasks_menu, state="disabled")
        tasks_menu.add_command(label="Create...", command=self.create_task, accelerator="Ctrl+N")
        tasks_menu.add_separator()
        tasks_menu.add_command(label="Cancel All", command=self.cancel_all_tasks)
        tasks_menu.add_command(label="Clear Finished...", command=self.clear_finished_tasks)
        tasks_menu.add_command(label="Clear Cancelled...", command=self.clear_cancelled_tasks)
        tasks_menu.add_separator()
        tasks_menu.add_command(label="Refresh List", command=self.refresh, accelerator="F5")
        self.menus['tasks'] = menubar.index("Tasks")

        # Agents menu (requires connection)
        agents_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Agents", menu=agents_menu, state="disabled")
        agents_menu.add_command(label="Manage...", command=self.show_agent_manager)
        self.menus['agents'] = menubar.index("Agents")

        # Skills menu (requires connection)
        skills_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Skills", menu=skills_menu, state="disabled")
        skills_menu.add_command(label="View...", command=self.show_skills_viewer, accelerator="Ctrl+K")
        skills_menu.add_separator()
        skills_menu.add_command(label="View Agent Skills...", command=self.show_agent_skills)
        self.menus['skills'] = menubar.index("Skills")

        # Learnings menu (requires connection)
        learnings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Learnings", menu=learnings_menu, state="disabled")
        learnings_menu.add_command(label="Browse...", command=self.show_learnings_browser, accelerator="Ctrl+R")
        self.menus['learnings'] = menubar.index("Learnings")

        # Integration menu (requires connection)
        integration_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Integration", menu=integration_menu, state="disabled")
        integration_menu.add_command(label="Integration Dashboard...", command=self.show_integration_dashboard,
                                     accelerator="Ctrl+I")
        integration_menu.add_separator()
        integration_menu.add_command(label="Sync All Unsynced Tasks", command=self.sync_all_tasks)
        self.menus['integration'] = menubar.index("Integration")

        # Logs menu (requires connection)
        logs_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Logs", menu=logs_menu, state="disabled")
        logs_menu.add_command(label="View Operations Log", command=self.show_operations_log, accelerator="Ctrl+L")
        self.menus['logs'] = menubar.index("Logs")

        # Claude menu (always enabled for API key, models requires connection)
        self.claude_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Claude", menu=self.claude_menu)
        self.claude_menu.add_command(label="Set API Key...", command=self.configure_api_key)
        self.claude_menu.add_separator()
        self.claude_menu.add_command(label="Manage Models...", command=self.show_models_manager, state="disabled")

        # About menu (always enabled)
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="Documentation...", command=self.show_documentation)
        about_menu.add_separator()
        about_menu.add_command(label="About Task Queue UI", command=self.show_about_dialog)

        # Store menubar reference
        self.menubar = menubar

    def update_menu_states(self, connected: bool):
        """Enable or disable menus based on connection state."""
        state = "normal" if connected else "disabled"

        for menu_name in ['workflows', 'enhancements', 'tasks', 'agents', 'skills', 'learnings', 'integration', 'logs']:
            if menu_name in self.menus:
                self.menubar.entryconfig(self.menus[menu_name], state=state)

        # Enable/disable "Manage Models..." in Claude menu (index 2)
        self.claude_menu.entryconfig(2, state=state)

        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.show_connect_dialog())
        self.root.bind('<Control-q>', lambda e: self.quit_app())
        self.root.bind('<Control-n>', lambda e: self.create_task())
        self.root.bind('<Control-e>', lambda e: self.show_enhancement_generator())
        self.root.bind('<Control-w>', lambda e: self.show_workflow_launcher())
        self.root.bind('<Control-k>', lambda e: self.show_skills_viewer())
        self.root.bind('<Control-i>', lambda e: self.show_integration_dashboard())
        self.root.bind('<Control-l>', lambda e: self.show_operations_log())
        self.root.bind('<F5>', lambda e: self.refresh())
        self.root.bind('<Delete>', lambda e: self.cancel_task())
        self.root.bind('<Return>', lambda e: self.start_task())

    def build_connection_header(self):
        """Create connection status header."""
        self.connection_frame = ttk.Frame(self.root, style='Connection.TFrame', padding=5)
        self.connection_frame.pack(fill="x")

        self.connection_label = ttk.Label(
            self.connection_frame,
            text="Not connected to CMAT. Install for new project or Connect to select project",
            font=('Arial', 9),
            style='Connection.TLabel'
        )
        self.connection_label.pack(side="left")

        # System version indicator
        self.version_label = ttk.Label(
            self.connection_frame,
            text="",
            font=('Arial', 9),
            style='Connection.TLabel'
        )
        self.version_label.pack(side="right", padx=10)

    def build_task_table(self):
        """Create split-pane task view with status list and task details."""
        table_frame = ttk.Frame(self.root, padding=10)
        table_frame.pack(fill="both", expand=True)

        label_frame = ttk.LabelFrame(table_frame, text="TASK QUEUE", padding=5)
        label_frame.pack(fill="both", expand=True)

        # Create horizontal paned window
        self.paned = ttk.PanedWindow(label_frame, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        # === Left Pane: Status List ===
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=0)

        # Status listbox with scrollbar
        status_label = ttk.Label(left_frame, text="Status", font=('Arial', 10, 'bold'))
        status_label.pack(pady=(0, 5))

        status_list_frame = ttk.Frame(left_frame)
        status_list_frame.pack(fill="both", expand=True)

        self.status_listbox = tk.Listbox(
            status_list_frame,
            font=('Arial', 11),
            selectmode='browse',
            activestyle='dotbox',
            width=20,
            exportselection=False
        )
        status_scrollbar = ttk.Scrollbar(status_list_frame, orient="vertical", command=self.status_listbox.yview)
        self.status_listbox.configure(yscrollcommand=status_scrollbar.set)

        self.status_listbox.pack(side="left", fill="both", expand=True)
        status_scrollbar.pack(side="right", fill="y")

        # Bind status selection
        self.status_listbox.bind('<<ListboxSelect>>', self.on_status_select)

        # Define status configuration
        self.status_config = [
            ('pending', 'Pending', '#E3F2FD'),      # Light blue
            ('active', 'Active', '#FFF3E0'),        # Light orange
            ('completed', 'Completed', '#E8F5E9'),  # Light green
            ('failed', 'Failed', '#FFEBEE'),        # Light red
            ('cancelled', 'Cancelled', '#EEEEEE'),  # Light grey
        ]

        # Track current status selection
        self.current_status = 'pending'

        # === Right Pane: Task Details ===
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=1)

        # Task tree
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill="both", expand=True)

        # Columns: Task ID, Workflow, Title, Enhancement, Agent
        columns = ('task_id', 'workflow', 'title', 'enhancement', 'agent')
        self.task_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.task_tree.heading('task_id', text='Task ID', command=lambda: self.sort_by('task_id'))
        self.task_tree.heading('workflow', text='Workflow', command=lambda: self.sort_by('workflow'))
        self.task_tree.heading('title', text='Title', command=lambda: self.sort_by('title'))
        self.task_tree.heading('enhancement', text='Enhancement', command=lambda: self.sort_by('enhancement'))
        self.task_tree.heading('agent', text='Agent', command=lambda: self.sort_by('agent'))

        self.task_tree.column('task_id', width=160, minwidth=120)
        self.task_tree.column('workflow', width=180, minwidth=150)
        self.task_tree.column('title', width=300, minwidth=200)
        self.task_tree.column('enhancement', width=200, minwidth=150)
        self.task_tree.column('agent', width=150, minwidth=120)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.task_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.task_tree.xview)
        self.task_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.task_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Empty state label (shown when no tasks in selected status)
        self.empty_label = ttk.Label(
            right_frame,
            text="No tasks",
            font=('Arial', 12),
            foreground='gray'
        )

        # Hint
        ttk.Label(
            label_frame,
            text="[Right-click for actions | Double-click for details | Ctrl+W for workflows]",
            font=('Arial', 9),
            foreground='gray'
        ).pack(pady=(5, 0))

        # Events
        self.task_tree.bind('<Double-Button-1>', self.on_double_click)
        self.task_tree.bind('<Button-3>', self.show_context_menu)
        self.task_tree.bind('<Button-2>', self.show_context_menu)
        self.task_tree.bind('<Control-Button-1>', self.show_context_menu)

        self.sort_column = None
        self.sort_reverse = False

        # Store tasks by status for quick access
        self.tasks_by_status = {}

    def on_status_select(self, event=None):
        """Handle status selection change."""
        selection = self.status_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.status_config):
            self.current_status = self.status_config[index][0]
            self.update_task_list()

    def build_status_bar(self):
        """Create status bar."""
        status_frame = ttk.Frame(self.root, relief="sunken", padding=2)
        status_frame.pack(fill="x", side="bottom")

        self.status_label = ttk.Label(status_frame, text="Not connected", font=('Arial', 9))
        self.status_label.pack(side="left", padx=5)

        self.refresh_label = ttk.Label(status_frame, text=f"Auto-refresh: {Config.AUTO_REFRESH_INTERVAL}s", font=('Arial', 9))
        self.refresh_label.pack(side="right", padx=5)

    def configure_styles(self):
        """Configure styles."""
        style = ttk.Style()
        style.configure('Connection.TFrame', background='#F0F0F0')
        style.configure('Connection.TLabel', background='#F0F0F0')

        # Status group header styles (parent rows)
        self.task_tree.tag_configure('header_pending', background='#E3F2FD', font=('Arial', 10, 'bold'))  # Light blue
        self.task_tree.tag_configure('header_active', background='#FFF3E0', font=('Arial', 10, 'bold'))   # Light orange
        self.task_tree.tag_configure('header_completed', background='#E8F5E9', font=('Arial', 10, 'bold'))  # Light green
        self.task_tree.tag_configure('header_failed', background='#FFEBEE', font=('Arial', 10, 'bold'))    # Light red
        self.task_tree.tag_configure('header_cancelled', background='#EEEEEE', font=('Arial', 10, 'bold'))  # Light grey

        # Task row styles (child rows) - plain white, no colors
        self.task_tree.tag_configure('task', background='white')
        self.task_tree.tag_configure('task_blocked', background='#FFF3CD')  # Yellow - blocked/warning

    def update_ui_state(self):
        """Update UI based on connection state."""
        if self.state.connection_state == ConnectionState.DISCONNECTED:
            self.connection_label.config(text="Not connected - File > Connect")
            self.version_label.config(text="")
            self.status_label.config(text="Not connected")

            for item in self.task_tree.get_children():
                self.task_tree.delete(item)

            # Disable menus that require connection
            self.update_menu_states(connected=False)

        elif self.state.connection_state == ConnectionState.CONNECTED:
            # Reset foreground color (in case it was red from error)
            self.connection_label.config(
                text=f"Connected: {self.state.project_root}",
                foreground='black'
            )

            # Show system version
            version = self.queue.get_version()
            self.version_label.config(text=f"CMAT v{version}")

            # Start auto-refresh (always on)
            self.start_auto_refresh()

            # Enable menus that require connection
            self.update_menu_states(connected=True)

        elif self.state.connection_state == ConnectionState.ERROR:
            self.connection_label.config(text=f"Error: {self.state.error_message}", foreground='red')

            # Disable menus on error
            self.update_menu_states(connected=False)

    def show_connect_dialog(self):
        """Show connect dialog."""
        from .dialogs import ConnectDialog
        dialog = ConnectDialog(self.root)
        if dialog.result:
            # Result is now project_root (not script path)
            self.connect_to_project(dialog.result)

    def show_install_cmat_dialog(self):
        """Show CMAT installer dialog."""
        from .dialogs.install_cmat import InstallCMATDialog

        dialog = InstallCMATDialog(self.root, self.settings)

        # If installation succeeded and user wants to connect
        if dialog.result and dialog.result.get("success") and dialog.result.get("connect"):
            project_root = dialog.result["project_root"]
            # Connect using project root (Python CMAT v8.2+)
            self.connect_to_project(str(project_root))

    def try_auto_connect(self):
        """Try to auto-connect to last project."""
        last_path = self.settings.get_last_queue_manager()
        if last_path and Path(last_path).exists():
            try:
                # Check if path is a directory (project root) or old script path
                path_obj = Path(last_path)
                if path_obj.is_dir():
                    # New format: project root
                    self.connect_to_project(str(path_obj), silent=True)
                elif path_obj.name == 'cmat.sh' and path_obj.parent.name == 'scripts':
                    # Old format: convert script path to project root
                    project_root = path_obj.parent.parent.parent
                    self.connect_to_project(str(project_root), silent=True)
                else:
                    # Invalid path
                    raise ValueError(f"Invalid path format: {last_path}")
            except Exception as e:
                print(f"Auto-connect failed: {e}")
                self.settings.clear_last_queue_manager()

    def connect_to_project(self, project_root: str, silent=False):
        """Connect to a project using Python CMAT v8.2+.

        Args:
            project_root: Path to project root directory (contains .claude/)
            silent: If True, suppress error dialogs
        """
        try:
            # Initialize queue interface with project root
            self.queue = CMATInterface(project_root)

            # Update state
            self.state.connection_state = ConnectionState.CONNECTED
            self.state.project_root = self.queue.project_root
            self.state.queue_file = self.queue.queue_file
            self.state.logs_dir = self.queue.logs_dir

            # Save path (now saves project root, not script path)
            self.settings.set_last_queue_manager(str(project_root))

            # Update UI
            self.update_ui_state()
            self.refresh()

        except Exception as e:
            self.state.connection_state = ConnectionState.ERROR
            self.state.error_message = str(e)
            self.update_ui_state()
            if not silent:
                messagebox.showerror("Connection Error", f"Failed to connect: {e}")

    def is_blocked_status(self, task):
        """Check if a completed task has a blocked/warning status.

        Args:
            task: Task object to check

        Returns:
            bool: True if task completed with a blocked/warning status
        """
        if task.status != 'completed':
            return False

        result = task.result or ''

        # Check for explicit BLOCKED status
        if result.startswith('BLOCKED'):
            return True

        # If task is part of a workflow, check if status has a defined transition
        if task.metadata and isinstance(task.metadata, dict):
            workflow_name = task.metadata.get('workflow_name')
            workflow_step = task.metadata.get('workflow_step')

            if workflow_name and workflow_step is not None:
                # Get workflow definition and check if result status has a transition
                try:
                    workflow_info = self.queue.get_workflow_template(workflow_name)
                    if workflow_info and 'steps' in workflow_info:
                        step_index = int(workflow_step)
                        if step_index < len(workflow_info['steps']):
                            step = workflow_info['steps'][step_index]
                            on_status = step.get('on_status', {})

                            # If the result status is NOT in the defined transitions, it's blocked
                            if result and result not in on_status:
                                return True
                except:
                    # If we can't determine workflow status, assume not blocked
                    pass

        return False

    def refresh(self):
        """Refresh task list with split-pane status view."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            return

        try:
            # Preserve task selection
            selected_task_id = None
            selection = self.task_tree.selection()
            if selection:
                values = self.task_tree.item(selection[0], 'values')
                if values and values[0]:
                    selected_task_id = values[0]

            # Get queue state
            queue_state = self.queue.get_queue_state()

            # Store tasks by status
            self.tasks_by_status = {
                'pending': queue_state.pending_tasks,
                'active': queue_state.active_workflows,
                'completed': queue_state.completed_tasks[-50:],  # Limit completed
                'failed': queue_state.failed_tasks,
                'cancelled': queue_state.cancelled_tasks,
            }

            # Update status listbox
            self.status_listbox.delete(0, tk.END)
            for i, (status_key, status_label, _) in enumerate(self.status_config):
                count = len(self.tasks_by_status.get(status_key, []))
                self.status_listbox.insert(tk.END, f"{status_label} ({count})")

            # Select current status in listbox
            for i, (status_key, _, _) in enumerate(self.status_config):
                if status_key == self.current_status:
                    self.status_listbox.selection_set(i)
                    break

            # Update task list for current status
            self.update_task_list(selected_task_id)

            # Update status bar
            self.status_label.config(
                text=f"{len(queue_state.pending_tasks)} Pending | "
                     f"{len(queue_state.active_workflows)} Active | "
                     f"{len(queue_state.completed_tasks)} Completed | "
                     f"{len(queue_state.failed_tasks)} Failed | "
                     f"{len(queue_state.cancelled_tasks)} Cancelled"
            )

        except Exception as e:
            messagebox.showerror("Refresh Error", f"Failed to refresh: {e}")

    def update_task_list(self, selected_task_id=None):
        """Update the task list for the currently selected status."""
        # Clear task tree
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # Get tasks for current status
        tasks = self.tasks_by_status.get(self.current_status, [])

        if not tasks:
            # Show empty state
            self.empty_label.place(relx=0.5, rely=0.5, anchor='center')
            status_label = dict((k, l) for k, l, _ in self.status_config).get(self.current_status, self.current_status)
            self.empty_label.config(text=f"No {status_label.lower()} tasks")
            return
        else:
            # Hide empty state
            self.empty_label.place_forget()

        # Sort tasks by ID descending (newest first)
        sorted_tasks = sorted(tasks, key=lambda t: t.id, reverse=True)

        # Populate task tree
        task_id_to_item = {}
        for task in sorted_tasks:
            # Extract workflow name and enhancement title from metadata
            workflow_name = ''
            enhancement_title = ''
            if task.metadata and isinstance(task.metadata, dict):
                workflow_name = task.metadata.get('workflow_name', '')
                enhancement_title = task.metadata.get('enhancement_title', '')

            # Determine tag - use task_blocked for blocked completed tasks
            if self.current_status == 'completed' and self.is_blocked_status(task):
                tag = 'task_blocked'
            else:
                tag = 'task'

            item_id = self.task_tree.insert(
                '',
                tk.END,
                values=(
                    task.id,
                    workflow_name,
                    task.title,
                    enhancement_title,
                    task.assigned_agent,
                ),
                tags=(tag,)
            )
            task_id_to_item[task.id] = item_id

        # Restore selection if task still exists
        if selected_task_id and selected_task_id in task_id_to_item:
            self.task_tree.selection_set(task_id_to_item[selected_task_id])

    def format_runtime(self, seconds):
        """Format runtime using TimeUtils."""
        return TimeUtils.format_runtime(seconds)

    def format_cost(self, task):
        """Format cost from task metadata."""
        if not task.metadata or not isinstance(task.metadata, dict):
            return "-"

        # Check for nested cost structure (future format)
        cost_data = task.metadata.get('cost')
        if cost_data and isinstance(cost_data, dict):
            total_cost = cost_data.get('total_cost')
            if total_cost is not None:
                return f"${total_cost:.4f}"

        # Check for flat cost structure (current CMAT format)
        cost_usd = task.metadata.get('cost_usd')
        if cost_usd is not None:
            # Handle both string and numeric values
            try:
                cost_value = float(cost_usd)
                return f"${cost_value:.4f}"
            except (ValueError, TypeError):
                return "-"

        return "-"

    def start_auto_refresh(self):
        """Start auto-refresh timer (always on when connected)."""
        if self.auto_refresh_timer:
            self.root.after_cancel(self.auto_refresh_timer)

        if self.state.connection_state == ConnectionState.CONNECTED:
            self.refresh()
            interval_ms = self.state.auto_refresh_interval * 1000
            self.auto_refresh_timer = self.root.after(interval_ms, self.start_auto_refresh)

    def on_double_click(self, event):
        """Handle double-click - show enhanced details."""
        task = self.get_selected_task()
        if task:
            from .dialogs import TaskDetailsDialog
            TaskDetailsDialog(self.root, task, self.queue)

    def show_context_menu(self, event):
        """Show context menu."""
        item = self.task_tree.identify_row(event.y)
        menu = tk.Menu(self.root, tearoff=0)

        if item:
            self.task_tree.selection_set(item)
            task = self.get_selected_task()

            if task:
                # Task row - show task-specific menu
                can_start = task.status == 'pending'
                can_cancel = task.status in ['pending', 'active']
                can_rerun = task.status not in ['pending', 'active']

                menu.add_command(label="Start Task", command=self.start_task,
                                 state="normal" if can_start else "disabled")
                menu.add_command(label="Re-Run Task", command=self.rerun_task,
                                 state="normal" if can_rerun else "disabled")
                menu.add_command(label="Cancel Task", command=self.cancel_task,
                                 state="normal" if can_cancel else "disabled")
                menu.add_separator()
                menu.add_command(label="View Details...", command=self.show_task_details)

                if self.queue.task_log_exists(task.id, task.source_file):
                    menu.add_command(label="View Log...", command=self.show_task_log)

                menu.add_separator()

                # Integration options
                if task.status == 'completed' and task.metadata:
                    if not task.metadata.get('github_issue'):
                        menu.add_command(label="Sync to External Systems", command=lambda: self.sync_task(task.id))

                menu.add_separator()
                menu.add_command(label="Copy Task ID", command=self.copy_task_id)
            else:
                # Parent row (status group header) - show generic menu
                menu.add_command(label="Create Task...", command=self.create_task)
                menu.add_separator()
                menu.add_command(label="Refresh", command=self.refresh)
        else:
            # Empty area - show generic menu
            menu.add_command(label="Create Task...", command=self.create_task)
            menu.add_separator()
            menu.add_command(label="Refresh", command=self.refresh)

        menu.post(event.x_root, event.y_root)

    def get_selected_task(self):
        """Get selected task."""
        selection = self.task_tree.selection()
        if not selection:
            return None

        values = self.task_tree.item(selection[0], 'values')
        if not values:
            return None

        task_id = values[0]
        queue_state = self.queue.get_queue_state()

        for task in (queue_state.pending_tasks + queue_state.active_workflows +
                     queue_state.completed_tasks + queue_state.failed_tasks +
                     queue_state.cancelled_tasks):
            if task.id == task_id:
                return task
        return None

    def create_task(self):
        """Show enhanced create task dialog."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs import CreateTaskDialog
        dialog = CreateTaskDialog(self.root, self.queue)

        if dialog.result:
            if dialog.should_start:
                try:
                    self.queue.start_task(dialog.result)
                except Exception as e:
                    messagebox.showerror("Error", f"Created but failed to start: {e}")
            self.refresh()

    def quick_workflow(self, agent: str, workflow_name: str):
        """Quick start a workflow."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        # This would open Create Task dialog with pre-filled workflow settings
        self.create_task()

    def start_task(self):
        """Start selected task."""
        task = self.get_selected_task()
        if not task:
            messagebox.showwarning("No Selection", "Select a task to start.")
            return

        if task.status != 'pending':
            messagebox.showwarning("Invalid Status", "Only pending tasks can be started.")
            return

        if messagebox.askyesno("Confirm", f"Start task {task.id}?"):
            try:
                self.queue.start_task(task.id)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start: {e}")

    def rerun_task(self):
        """Re-run a completed or failed task."""
        task = self.get_selected_task()
        if not task:
            messagebox.showwarning("No Selection", "Select a task to re-run.")
            return

        if task.status in ['pending', 'active']:
            messagebox.showwarning("Invalid Status", "Cannot re-run pending or active tasks.")
            return

        if messagebox.askyesno("Confirm Re-Run", f"Re-run task {task.id}?\n\nThis will move it back to pending and restart execution."):
            try:
                self.queue.rerun_task(task.id)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to re-run: {e}")

    def cancel_task(self):
        """Cancel selected task."""
        task = self.get_selected_task()
        if not task or task.status not in ['pending', 'active']:
            return

        if messagebox.askyesno("Confirm", f"Cancel task {task.id}?"):
            try:
                self.queue.cancel_task(task.id, "Cancelled by user")
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to cancel: {e}")

    def cancel_all_tasks(self):
        """Cancel all tasks."""
        if messagebox.askyesno("Confirm", "Cancel ALL pending and active tasks?"):
            try:
                self.queue.cancel_all_tasks("Bulk cancellation")
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

    def clear_finished_tasks(self):
        """Clear all completed and failed tasks from the queue."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        response = messagebox.askyesno(
            "Clear Finished Tasks",
            "This will clear all Completed and Failed tasks from the queue.\n\n"
            "Pending and Active tasks will remain.\n\n"
            "Are you sure you want to proceed?"
        )

        if response:
            try:
                self.queue.clear_finished_tasks()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear finished tasks: {e}")

    def clear_cancelled_tasks(self):
        """Clear all cancelled tasks from the queue."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        response = messagebox.askyesno(
            "Clear Cancelled Tasks",
            "This will permanently delete all Cancelled tasks from the queue.\n\n"
            "Are you sure you want to proceed?"
        )

        if response:
            try:
                self.queue.clear_cancelled_tasks()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear cancelled tasks: {e}")

    def reset_queue(self):
        """Reset the entire queue system to empty state."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        response = messagebox.askyesno(
            "Reset Queue",
            "Reset all queues and logs to an empty state?"
        )

        if response:
            try:
                self.queue.reset_queue()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset queue: {e}")

    def sync_task(self, task_id: str):
        """Sync task to external systems."""
        try:
            self.queue.sync_task_external(task_id)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sync: {e}")

    def sync_all_tasks(self):
        """Sync all unsynced tasks."""
        if messagebox.askyesno("Confirm", "Sync all unsynced tasks?"):
            try:
                self.queue.sync_all_external()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

    def show_task_details(self):
        """Show enhanced task details."""
        task = self.get_selected_task()
        if task:
            from .dialogs import TaskDetailsDialog
            TaskDetailsDialog(self.root, task, self.queue)

    def show_task_log(self):
        """Show task log."""
        task = self.get_selected_task()
        if task:
            # Use enhanced details which has better log viewer
            self.show_task_details()

    def copy_task_id(self):
        """Copy task ID."""
        task = self.get_selected_task()
        if task:
            self.root.clipboard_clear()
            self.root.clipboard_append(task.id)

    def show_skills_viewer(self):
        """Show skills viewer dialog."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs import SkillsViewerDialog
        SkillsViewerDialog(self.root, self.queue)

    def show_agent_skills(self):
        """Show agent skills summary."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        # Create summary window
        window = tk.Toplevel(self.root)
        window.title("Agent Skills Summary")
        window.geometry("600x500")

        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Agent Skills Summary", font=('Arial', 14, 'bold')).pack(pady=(0, 10))

        text_widget = tk.Text(frame, wrap="word", font=('Courier', 9))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Build summary
        agents = self.queue.get_agent_list()
        for agent_file, agent_name in sorted(agents.items(), key=lambda x: x[1]):
            skills = self.queue.get_agent_skills(agent_file)
            text_widget.insert(tk.END, f"{agent_name}:\n", 'bold')

            if skills:
                for skill in skills:
                    text_widget.insert(tk.END, f"  • {skill}\n")
            else:
                text_widget.insert(tk.END, "  (no skills assigned)\n", 'gray')

            text_widget.insert(tk.END, "\n")

        text_widget.tag_config('bold', font=('Courier', 9, 'bold'))
        text_widget.tag_config('gray', foreground='gray')
        text_widget.config(state="disabled")

        ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)

    def show_workflow_launcher(self):
        """Show workflow starter dialog."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs import WorkflowLauncherDialog
        dialog = WorkflowLauncherDialog(self.root, self.queue, self.settings)

        if dialog.result:
            # Workflow started - refresh to show first task
            self.refresh()

    def show_workflow_template_manager(self):
        """Show workflow template manager."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        try:
            dialog = WorkflowTemplateManagerDialog(self.root, self.queue)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open workflow templates: {e}")

    def show_enhancement_generator(self):
        """Show enhancement generator dialog."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect to a project first.")
            return

        from .dialogs import CreateEnhancementDialog
        dialog = CreateEnhancementDialog(self.root, self.queue, self.settings)

    def show_integration_dashboard(self):
        """Show integration dashboard."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs import IntegrationDashboardDialog
        IntegrationDashboardDialog(self.root, self.queue)

    def show_agent_manager(self):
        """Show enhanced agent manager."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs import AgentListDialog
        AgentListDialog(self.root, self.queue, self.settings)

    def show_operations_log(self):
        """Show operations log."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs import LogViewerDialog
        LogViewerDialog(self.root, self.queue)

    def show_learnings_browser(self):
        """Show learnings browser dialog."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs.learnings_browser import LearningsBrowserDialog
        LearningsBrowserDialog(self.root, self.queue).show()

    def show_models_manager(self):
        """Show models manager dialog."""
        if self.state.connection_state != ConnectionState.CONNECTED:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        from .dialogs.models_manager import ModelsManagerDialog
        ModelsManagerDialog(self.root, self.queue).show()

    def configure_api_key(self):
        """Configure Claude API settings."""
        from .dialogs import ClaudeSettingsDialog
        ClaudeSettingsDialog(self.root, self.settings)

    def show_about_dialog(self):
        """Show about dialog."""
        from .dialogs import AboutDialog
        AboutDialog(self.root)

    def show_documentation(self):
        """Show documentation viewer."""
        from .dialogs import DocumentationViewerDialog
        DocumentationViewerDialog(self.root)

    def sort_by(self, column):
        """Sort table by column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        items = [(self.task_tree.set(item, column), item) for item in self.task_tree.get_children('')]
        items.sort(reverse=self.sort_reverse)

        for index, (val, item) in enumerate(items):
            self.task_tree.move(item, '', index)

    def quit_app(self):
        """Quit application."""
        if messagebox.askyesno("Quit", "Are you sure?"):
            self.root.quit()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = MainView(root)
    root.mainloop()


if __name__ == "__main__":
    main()