"""
Learnings Browser Dialog - View and manage CMAT RAG system learnings.

Provides interface for:
- Browsing all learnings
- Filtering by tags
- Viewing learning details
- Adding manual learnings
- Deleting learnings
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

from .base_dialog import BaseDialog


class LearningsBrowserDialog(BaseDialog):
    """Dialog for browsing and managing learnings from the RAG system."""

    def __init__(self, parent, queue):
        """
        Initialize learnings browser.

        Args:
            parent: Parent window
            queue: CMATInterface instance
        """
        self.queue = queue
        self.learnings = []
        self.selected_learning = None

        super().__init__(parent, "Learnings Browser", width=900, height=600)

        self.build_ui()
        # Don't call show() - this dialog doesn't return a result

    def build_ui(self):
        """Create the dialog widgets."""
        # Main container with two panes
        main_paned = ttk.PanedWindow(self.dialog, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top pane: List view
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=3)

        # Filter frame
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(filter_frame, text="Filter by tags:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_entry = ttk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.filter_entry.bind('<Return>', lambda e: self.apply_filter())

        ttk.Button(filter_frame, text="Apply", command=self.apply_filter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(filter_frame, text="Clear", command=self.clear_filter).pack(side=tk.LEFT, padx=(0, 5))

        # Add learning button
        ttk.Button(filter_frame, text="Add Learning", command=self.show_add_dialog).pack(side=tk.RIGHT)

        # Learnings list with scrollbar
        list_frame = ttk.Frame(top_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ('summary', 'tags', 'confidence', 'source', 'created')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')

        # Column headings
        self.tree.heading('summary', text='Summary')
        self.tree.heading('tags', text='Tags')
        self.tree.heading('confidence', text='Confidence')
        self.tree.heading('source', text='Source')
        self.tree.heading('created', text='Created')

        # Column widths
        self.tree.column('summary', width=300)
        self.tree.column('tags', width=150)
        self.tree.column('confidence', width=80)
        self.tree.column('source', width=120)
        self.tree.column('created', width=150)

        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Bottom pane: Details view
        bottom_frame = ttk.LabelFrame(main_paned, text="Learning Details")
        main_paned.add(bottom_frame, weight=2)

        # Details text widget
        self.details_text = scrolledtext.ScrolledText(
            bottom_frame,
            wrap=tk.WORD,
            width=80,
            height=10,
            state='disabled'
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Button frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        ttk.Button(button_frame, text="Delete", command=self.delete_learning).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Refresh", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Close", command=self.close).pack(side=tk.RIGHT)

        # Load initial data
        self.refresh()

    def refresh(self):
        """Refresh the learnings list."""
        try:
            self.learnings = self.queue.learnings.list_all()
            self.update_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load learnings: {e}")

    def apply_filter(self):
        """Apply tag filter to learnings list."""
        tags_str = self.filter_entry.get().strip()
        if not tags_str:
            self.refresh()
            return

        try:
            tags = [t.strip() for t in tags_str.split(',') if t.strip()]
            self.learnings = self.queue.learnings.list_by_tags(tags)
            self.update_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter learnings: {e}")

    def clear_filter(self):
        """Clear the filter and show all learnings."""
        self.filter_entry.delete(0, tk.END)
        self.refresh()

    def update_tree(self):
        """Update the treeview with current learnings."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add learnings
        for learning in self.learnings:
            # Format values
            summary = learning.summary[:80] + "..." if len(learning.summary) > 80 else learning.summary
            tags = ", ".join(learning.tags[:3])  # Show first 3 tags
            if len(learning.tags) > 3:
                tags += "..."
            confidence = f"{learning.confidence:.0%}"
            source = learning.source_type
            created = learning.created.split('T')[0] if 'T' in learning.created else learning.created[:10]

            self.tree.insert('', tk.END, iid=learning.id, values=(
                summary, tags, confidence, source, created
            ))

        # Update status
        count = len(self.learnings)
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', f"Loaded {count} learning{'s' if count != 1 else ''}")
        self.details_text.configure(state='disabled')

    def on_select(self, event):
        """Handle learning selection."""
        selection = self.tree.selection()
        if not selection:
            return

        learning_id = selection[0]
        self.selected_learning = next((l for l in self.learnings if l.id == learning_id), None)

        if self.selected_learning:
            self.show_details()

    def show_details(self):
        """Display details of selected learning."""
        if not self.selected_learning:
            return

        learning = self.selected_learning

        details = f"""Summary:
{learning.summary}

Content:
{learning.content}

Tags: {', '.join(learning.tags) if learning.tags else 'None'}

Applies To: {', '.join(learning.applies_to) if learning.applies_to else 'General'}

Source: {learning.source_type}
{f'Source Task: {learning.source_task_id}' if learning.source_task_id else ''}

Confidence: {learning.confidence:.0%}

Created: {learning.created}

ID: {learning.id}
"""

        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', details)
        self.details_text.configure(state='disabled')

    def delete_learning(self):
        """Delete the selected learning."""
        if not self.selected_learning:
            messagebox.showwarning("No Selection", "Please select a learning to delete.")
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Delete learning:\n\n{self.selected_learning.summary}\n\nThis cannot be undone."
        )

        if result:
            try:
                self.queue.learnings.delete(self.selected_learning.id)
                self.selected_learning = None
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete learning: {e}")

    def show_add_dialog(self):
        """Show dialog to add a new learning."""
        AddLearningDialog(self.dialog, self.queue, on_success=self.refresh)


class AddLearningDialog(BaseDialog):
    """Dialog for adding a new learning manually."""

    def __init__(self, parent, queue, on_success=None):
        """
        Initialize add learning dialog.

        Args:
            parent: Parent window
            queue: CMATInterface instance
            on_success: Callback to execute on successful add
        """
        self.queue = queue
        self.on_success = on_success
        super().__init__(parent, "Add Learning", width=600, height=400)

        self.build_ui()
        self.show()

    def build_ui(self):
        """Create the dialog widgets."""
        # Content label and text
        ttk.Label(self.dialog, text="Learning Content:").pack(anchor=tk.W, padx=10, pady=(10, 5))

        self.content_text = scrolledtext.ScrolledText(
            self.dialog,
            wrap=tk.WORD,
            width=70,
            height=12
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.content_text.focus()

        # Tags entry
        tags_frame = ttk.Frame(self.dialog)
        tags_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(tags_frame, text="Tags (comma-separated):").pack(side=tk.LEFT, padx=(0, 5))
        self.tags_entry = ttk.Entry(tags_frame, width=50)
        self.tags_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Help text
        help_text = "Example tags: python, architecture, testing, conventions, error-handling"
        ttk.Label(self.dialog, text=help_text, foreground='gray').pack(anchor=tk.W, padx=10)

        # Button frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 10))

        ttk.Button(button_frame, text="Save", command=self.save_learning).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.close).pack(side=tk.LEFT)

    def save_learning(self):
        """Save the new learning."""
        content = self.content_text.get("1.0", "end-1c").strip()

        if not content:
            messagebox.showwarning("Validation Error", "Please enter learning content.")
            self.content_text.focus()
            return

        # Parse tags
        tags_str = self.tags_entry.get().strip()
        tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

        try:
            # Create and store learning
            learning = self.queue.learnings.extract_from_user_input(content, tags)
            self.queue.learnings.store(learning)

            # Call success callback
            if self.on_success:
                self.on_success()

            self.close()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add learning: {e}")