"""
Operations log dialog for viewing queue operations log.
"""

import tkinter as tk
from tkinter import ttk

from .base_dialog import BaseDialog


class LogViewerDialog(BaseDialog):
    """Dialog for viewing operations log."""

    def __init__(self, parent, queue_interface):
        super().__init__(parent, "Queue Operations Log", 900, 600)
        self.queue = queue_interface
        self.build_ui()
        self.load_log()
        # Don't call show() - log dialogs don't return results

    def build_ui(self):
        """Build the operations log UI."""
        # Header
        header_frame = ttk.Frame(self.dialog, padding=10)
        header_frame.pack(fill="x")

        ttk.Label(header_frame, text="Log File: .claude/logs/queue_operations.log").pack(side="left")

        # Log text
        text_frame = ttk.Frame(self.dialog, padding=10)
        text_frame.pack(fill="both", expand=True)

        self.text_widget = tk.Text(text_frame, wrap="none", font=('Courier', 9))
        scrollbar_y = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_widget.yview)
        scrollbar_x = ttk.Scrollbar(text_frame, orient="horizontal", command=self.text_widget.xview)
        self.text_widget.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.text_widget.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # Footer
        footer_frame = ttk.Frame(self.dialog, padding=10)
        footer_frame.pack(fill="x")

        self.status_label = ttk.Label(footer_frame, text="")
        self.status_label.pack(side="left")

        # Buttons - Using BaseDialog helper
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(side="right")

        ttk.Button(button_frame, text="Refresh", command=self.load_log).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side="left", padx=5)

    def load_log(self):
        """Load and display operations log."""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete('1.0', tk.END)

        try:
            log_content = self.queue.get_operations_log(max_lines=1000)
            self.text_widget.insert('1.0', log_content)

            # Auto-scroll to bottom
            self.text_widget.see(tk.END)

            # Update status
            lines = log_content.count('\n')
            self.status_label.config(text=f"Showing last {lines} lines")

        except Exception as e:
            self.text_widget.insert('1.0', f"Error loading log: {e}")
            self.status_label.config(text="Error")

        self.text_widget.config(state=tk.DISABLED)