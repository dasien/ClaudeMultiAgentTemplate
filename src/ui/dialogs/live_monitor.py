"""
Live Agent Monitor dialog for real-time agent execution monitoring.

Displays streaming events from Claude CLI in a structured treeview,
allowing users to watch agent progress in real-time.
"""

import re
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional

from .base_dialog import BaseDialog

# Event types that are shown by default (non-verbose mode)
DEFAULT_VISIBLE_TYPES = {"Header", "Session", "Assistant", "Complete", "Failed", "Error"}


class LiveMonitorDialog(BaseDialog):
    """
    Dialog for monitoring agent execution in real-time.

    Uses a treeview with columns for structured display of events.
    Can also load and display existing log files.
    """

    def __init__(
        self,
        parent,
        title: str = "Live Agent Monitor",
        log_file: Optional[str] = None,
    ):
        """
        Initialize the live monitor dialog.

        Args:
            parent: Parent window
            title: Dialog title
            log_file: Optional path to existing log file to display
        """
        super().__init__(parent, title, 1000, 600, resizable=True, modal=False)

        self.log_file = log_file
        self.auto_scroll = True
        self._all_events = []  # Store all parsed events for filtering
        self._full_details = {}  # Store full details by item ID
        self._refresh_job = None  # For auto-refresh timer
        self._last_content_hash = None  # Track content for change detection

        self.build_ui()

        # Load existing log file if provided
        if log_file:
            self.load_log_file(log_file)
            self._start_auto_refresh()

    def build_ui(self):
        """Build the monitor dialog UI."""
        # Header frame with status info
        header_frame = ttk.Frame(self.dialog, padding=10)
        header_frame.pack(fill="x")

        self.status_label = ttk.Label(header_frame, text="Waiting for events...")
        self.status_label.pack(side="left")

        # Verbose checkbox (show all event types)
        self.verbose_var = tk.BooleanVar(value=False)
        verbose_check = ttk.Checkbutton(
            header_frame,
            text="Verbose",
            variable=self.verbose_var,
            command=self._on_verbose_change,
        )
        verbose_check.pack(side="right", padx=5)

        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = ttk.Checkbutton(
            header_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll,
        )
        auto_scroll_check.pack(side="right", padx=5)

        # Main treeview with columns
        tree_frame = ttk.Frame(self.dialog, padding=(10, 0, 10, 10))
        tree_frame.pack(fill="both", expand=True)

        # Configure grid
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Create treeview with columns
        columns = ("time", "type", "details")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configure columns
        self.tree.heading("time", text="Time")
        self.tree.heading("type", text="Type")
        self.tree.heading("details", text="Details")

        self.tree.column("time", width=80, minwidth=80, stretch=False)
        self.tree.column("type", width=100, minwidth=80, stretch=False)
        self.tree.column("details", width=1500, minwidth=200, stretch=False)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Bind double-click to show full details panel
        self.tree.bind("<Double-1>", self._show_full_details)
        # Bind selection to update details panel if visible
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        # Detail text area (initially hidden, shown on double-click)
        self.detail_frame = ttk.LabelFrame(self.dialog, text="Full Details (double-click row to view)", padding=10)
        self.detail_text = tk.Text(
            self.detail_frame,
            wrap="word",
            font=("Courier", 10),
            height=10,
        )
        detail_scroll = ttk.Scrollbar(self.detail_frame, orient="vertical", command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scroll.set)
        self.detail_text.pack(side="left", fill="both", expand=True)
        detail_scroll.pack(side="right", fill="y")

        # Footer with buttons
        footer_frame = ttk.Frame(self.dialog, padding=10)
        footer_frame.pack(fill="x")

        ttk.Button(footer_frame, text="Clear", command=self._clear).pack(side="left", padx=5)
        ttk.Button(footer_frame, text="Copy All", command=self._copy_all).pack(side="left", padx=5)
        ttk.Button(footer_frame, text="Toggle Details", command=self._toggle_details).pack(side="left", padx=5)

        ttk.Button(footer_frame, text="Close", command=self.cancel).pack(side="right", padx=5)

    def _start_auto_refresh(self):
        """Start automatic refresh timer."""
        if self._refresh_job:
            self.dialog.after_cancel(self._refresh_job)
        self._refresh_job = self.dialog.after(1000, self._auto_refresh_tick)

    def _auto_refresh_tick(self):
        """Called periodically to check for log file updates."""
        if not self.log_file:
            return

        try:
            path = Path(self.log_file)
            if path.exists():
                content = path.read_text(encoding="utf-8")
                content_hash = hash(content)

                # Only refresh if content changed
                if content_hash != self._last_content_hash:
                    self._last_content_hash = content_hash
                    self._all_events.clear()
                    self._parse_log_content(content)
                    self._refresh_display()
                    visible_count = len(self.tree.get_children())
                    total_count = len(self._all_events)
                    if self.verbose_var.get():
                        self.status_label.config(text=f"Live: {path.name} ({total_count} events)")
                    else:
                        self.status_label.config(text=f"Live: {path.name} ({visible_count}/{total_count} events)")
        except Exception:
            pass  # Silently handle errors during auto-refresh

        # Schedule next tick
        self._refresh_job = self.dialog.after(1000, self._auto_refresh_tick)

    def _on_verbose_change(self):
        """Handle verbose checkbox change - refresh display with new filter."""
        self._refresh_display()
        visible_count = len(self.tree.get_children())
        total_count = len(self._all_events)
        if self.log_file:
            path = Path(self.log_file)
            if self.verbose_var.get():
                self.status_label.config(text=f"Live: {path.name} ({total_count} events)")
            else:
                self.status_label.config(text=f"Live: {path.name} ({visible_count}/{total_count} events)")

    def _refresh_display(self):
        """Refresh the treeview based on current filter settings."""
        # Clear current display
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._full_details.clear()

        # Re-add events based on verbose filter
        verbose = self.verbose_var.get()
        for event in self._all_events:
            event_type = event["type"]
            # In non-verbose mode, filter to only show default visible types
            if not verbose and event_type not in DEFAULT_VISIBLE_TYPES:
                continue

            self._add_event_to_tree(event["time"], event_type, event["details"])

    def _add_event_to_tree(self, time: str, event_type: str, details: str):
        """Add an event row to the treeview (internal, no filtering)."""
        # Truncate details for display (full content available on double-click)
        display_details = details.replace("\n", " ").strip()
        if len(display_details) > 300:
            display_details = display_details[:300] + "..."

        item_id = self.tree.insert("", "end", values=(time, event_type, display_details))

        # Store full details for later retrieval
        self._full_details[item_id] = details

        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.tree.see(item_id)

    def add_event(self, time: str, event_type: str, details: str, tag: str = ""):
        """
        Add an event to the internal store and optionally display it.

        Args:
            time: Timestamp string
            event_type: Type of event (Tool, Result, Assistant, etc.)
            details: Event details (full content)
            tag: Optional tag (unused, kept for API compatibility)
        """
        # Store in internal list for filtering
        self._all_events.append({
            "time": time,
            "type": event_type,
            "details": details,
        })

        # Check if should be displayed based on verbose setting
        verbose = self.verbose_var.get()
        if verbose or event_type in DEFAULT_VISIBLE_TYPES:
            self._add_event_to_tree(time, event_type, details)

    def load_log_file(self, log_file: str):
        """
        Load and display an existing log file.

        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        path = Path(log_file)

        if not path.exists():
            self.add_event("--:--:--", "Error", f"Log file not found: {log_file}")
            return

        try:
            content = path.read_text(encoding="utf-8")
            self._last_content_hash = hash(content)
            self._clear()
            self._parse_log_content(content)

            visible_count = len(self.tree.get_children())
            total_count = len(self._all_events)
            if self.verbose_var.get():
                self.status_label.config(text=f"Loaded: {path.name} ({total_count} events)")
            else:
                self.status_label.config(text=f"Loaded: {path.name} ({visible_count}/{total_count} events)")

        except Exception as e:
            self.add_event("--:--:--", "Error", f"Error loading log: {e}")

    def _parse_log_content(self, content: str):
        """Parse log content and add events to internal store."""
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Parse timestamped events
            time_match = re.match(r'\[(\d{2}:\d{2}:\d{2})\]\s*(.+)', line)
            if time_match:
                timestamp = time_match.group(1)
                rest = time_match.group(2)

                # Collect any indented continuation lines
                details_lines = []
                j = i + 1
                while j < len(lines) and lines[j].startswith("    "):
                    details_lines.append(lines[j][4:])  # Remove 4-space indent
                    j += 1

                # Determine event type and extract details
                if "=== Session Started ===" in rest:
                    session_info = rest.replace("=== Session Started === ", "")
                    self.add_event(timestamp, "Session", session_info)
                elif "=== COMPLETE ===" in rest:
                    clean_rest = rest.replace("=== ", "").replace(" ===", "")
                    self.add_event(timestamp, "Complete", clean_rest)
                elif "=== FAILED ===" in rest:
                    clean_rest = rest.replace("=== ", "").replace(" ===", "")
                    self.add_event(timestamp, "Failed", clean_rest)
                elif "Tool:" in rest:
                    # Extract tool name and input from "Tool:{name} | {input}"
                    if " | " in rest:
                        tool_type, tool_input = rest.split(" | ", 1)
                    else:
                        tool_type = rest
                        tool_input = ""
                    if details_lines:
                        tool_input += "\n" + "\n".join(details_lines) if tool_input else "\n".join(details_lines)
                    self.add_event(timestamp, tool_type, tool_input)
                elif rest.startswith("Result"):
                    # Strip timing info for details
                    result_info = re.sub(r'Result(\s*\(\d+ms\))?:\s*', '', rest)
                    if details_lines:
                        result_info += "\n" + "\n".join(details_lines)
                    # Show placeholder for empty results (e.g., mkdir success)
                    if not result_info.strip():
                        result_info = "(success - no output)"
                    self.add_event(timestamp, "Result", result_info)
                elif "Assistant:" in rest:
                    text = rest.replace("Assistant: ", "")
                    if details_lines:
                        text += "\n" + "\n".join(details_lines)
                    self.add_event(timestamp, "Assistant", text)
                elif "Error:" in rest:
                    error_text = rest.replace("Error: ", "")
                    if details_lines:
                        error_text += "\n" + "\n".join(details_lines)
                    self.add_event(timestamp, "Error", error_text)
                else:
                    # Unknown timestamped line
                    full_text = rest
                    if details_lines:
                        full_text += "\n" + "\n".join(details_lines)
                    # Check if this is an "Info: Result" type line
                    if full_text.startswith("Result:"):
                        info_details = full_text[7:].strip()  # Remove "Result:" prefix
                        self.add_event(timestamp, "Info: Result", info_details)
                    else:
                        self.add_event(timestamp, "Info", full_text)

                i = j  # Skip past continuation lines
                continue

            elif line.startswith("===") and ("Agent" in line or "Starting" in line or "Complete" in line):
                # Header lines like "=== Starting Agent ==="
                self.add_event("--:--:--", "Header", line)
            elif line.strip() and not line.startswith("    ") and not line.startswith("---"):
                # Non-timestamped, non-indented content (headers, prompt text, etc.)
                # Skip these as they're typically prompt headers
                pass

            i += 1

    def _on_selection_change(self, event):
        """Update detail panel when selection changes (if panel is visible)."""
        if not self.detail_frame.winfo_ismapped():
            return

        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            full_details = self._full_details.get(item_id, "")
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete("1.0", tk.END)
            self.detail_text.insert("1.0", full_details)
            self.detail_text.config(state=tk.DISABLED)

    def _show_full_details(self, event):
        """Show full details panel for selected row (on double-click)."""
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]
        full_details = self._full_details.get(item_id, "")

        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", full_details)
        self.detail_text.config(state=tk.DISABLED)

        # Show detail frame if hidden
        if not self.detail_frame.winfo_ismapped():
            self.detail_frame.pack(fill="x", padx=10, pady=(0, 10), before=self.dialog.winfo_children()[-1])

    def _toggle_details(self):
        """Toggle visibility of detail panel and show selected row's content."""
        if self.detail_frame.winfo_ismapped():
            self.detail_frame.pack_forget()
        else:
            # Show panel and populate with selected row's content
            self.detail_frame.pack(fill="x", padx=10, pady=(0, 10), before=self.dialog.winfo_children()[-1])
            selection = self.tree.selection()
            if selection:
                item_id = selection[0]
                full_details = self._full_details.get(item_id, "")
                self.detail_text.config(state=tk.NORMAL)
                self.detail_text.delete("1.0", tk.END)
                self.detail_text.insert("1.0", full_details)
                self.detail_text.config(state=tk.DISABLED)

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll behavior."""
        self.auto_scroll = self.auto_scroll_var.get()

    def _clear(self):
        """Clear the display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._full_details.clear()
        self._all_events.clear()
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.config(state=tk.DISABLED)
        self.status_label.config(text="Cleared")

    def _copy_all(self):
        """Copy all content to clipboard."""
        lines = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            full_details = self._full_details.get(item, values[2])
            lines.append(f"[{values[0]}] {values[1]}: {full_details}")
        content = "\n".join(lines)
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(content)
        self.status_label.config(text="Copied to clipboard")

    def on_close(self):
        """Called when dialog is closing."""
        # Cancel auto-refresh timer
        if self._refresh_job:
            self.dialog.after_cancel(self._refresh_job)
            self._refresh_job = None