"""
Base Dialog class with common dialog functionality.
All dialogs should inherit from this to avoid code duplication.
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseDialog(ABC):
    """
    Abstract base class for all application dialogs.

    Provides:
    - Automatic centering on parent (concrete)
    - Standard initialization (concrete)
    - Result pattern (concrete)
    - Common dialog behaviors (concrete)

    Requires subclasses to implement:
    - build_ui() - Build the dialog's user interface

    Usage:
        class MyDialog(BaseDialog):
            def __init__(self, parent, my_param):
                super().__init__(parent, "My Dialog", 600, 400)
                self.my_param = my_param
                self.build_ui()
                self.show()

            def build_ui(self):
                # MUST implement - build your dialog UI here
                main_frame = ttk.Frame(self.dialog, padding=20)
                main_frame.pack(fill="both", expand=True)
                # ... your UI code ...
    """

    def __init__(self, parent, title: str, width: int, height: int,
                 resizable: bool = True, modal: bool = True):
        """
        Initialize base dialog.

        Args:
            parent: Parent window
            title: Dialog title
            width: Dialog width in pixels
            height: Dialog height in pixels
            resizable: Whether dialog can be resized
            modal: Whether dialog is modal (blocks parent)
        """
        self.parent = parent
        self.result: Optional[Any] = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.transient(parent)

        if modal:
            self.dialog.grab_set()

        if not resizable:
            self.dialog.resizable(False, False)

        # Bind Escape key to cancel
        self.dialog.bind('<Escape>', lambda e: self.cancel())

        # Center on parent
        self.center_on_parent()

    @abstractmethod
    def build_ui(self):
        """
        Build the dialog user interface.

        MUST be implemented by subclasses.

        This is where you create all the widgets, frames, buttons, etc.
        for your dialog.
        """
        pass

    def validate(self) -> bool:
        """
        Validate dialog state before saving/submitting.

        Override in subclasses that need validation logic.
        Default implementation returns True (always valid).

        Returns:
            True if dialog state is valid, False otherwise

        Example:
            def validate(self) -> bool:
                if not self.name_var.get().strip():
                    messagebox.showwarning("Validation", "Name is required")
                    return False
                return True
        """
        return True

    def on_show(self):
        """
        Called after dialog is shown and centered.

        Override to perform actions after dialog is visible.
        Useful for setting initial focus, loading data, etc.

        Example:
            def on_show(self):
                self.set_focus(self.name_entry)
                self.load_data()
        """
        pass

    def on_close(self):
        """
        Called before dialog is destroyed.

        Override to perform cleanup, save state, etc.

        Example:
            def on_close(self):
                self.cleanup_resources()
                self.save_draft()
        """
        pass

    def show(self) -> Any:
        """
        Show dialog and wait for it to close, then return result.

        Call this after build_ui() in __init__:
            def __init__(self, parent):
                super().__init__(parent, "Title", 600, 400)
                self.build_ui()
                self.show()  # Shows and waits

        Calls on_show() hook before waiting.

        Returns:
            The result set by the dialog (typically by save/ok button)
        """
        # Call optional hook
        self.on_show()

        # Wait for dialog to close
        self.dialog.wait_window()
        return self.result

    def center_on_parent(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)

        self.dialog.geometry(f"+{x}+{y}")

    def close(self, result: Any = None):
        """
        Close dialog with optional result.

        Calls on_close() hook before destroying.

        Args:
            result: Result to return from dialog
        """
        # Call optional cleanup hook
        self.on_close()

        self.result = result
        self.dialog.destroy()

    def cancel(self):
        """
        Cancel dialog without result (sets result to None).

        Calls on_close() hook before destroying.
        """
        # Call optional cleanup hook
        self.on_close()

        self.result = None
        self.dialog.destroy()

    def set_focus(self, widget, delay: int = 100):
        """
        Set focus to a widget after a short delay.

        Args:
            widget: Widget to focus
            delay: Delay in ms (default 100)
        """
        self.dialog.after(delay, widget.focus_set)

    def create_button_frame(self, parent, buttons: list) -> ttk.Frame:
        """
        Create a standard button frame with multiple buttons.

        Args:
            parent: Parent widget
            buttons: List of (text, command) tuples

        Returns:
            Frame containing buttons

        Example:
            self.create_button_frame(main_frame, [
                ("Save", self.save),
                ("Cancel", self.cancel)
            ])
        """
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)

        for text, command in buttons:
            ttk.Button(
                button_frame,
                text=text,
                command=command,
                width=15
            ).pack(side="left", padx=5)

        return button_frame

    def create_label_entry_pair(self, parent, label_text: str,
                                var: tk.StringVar = None,
                                width: int = 50,
                                required: bool = False) -> tuple:
        """
        Create a label and entry widget pair.

        Args:
            parent: Parent widget
            label_text: Label text
            var: StringVar for entry (creates new if None)
            width: Entry width
            required: Whether to show * for required field

        Returns:
            (label, entry, var) tuple

        Example:
            label, entry, var = self.create_label_entry_pair(
                parent, "Name", required=True
            )
        """
        if var is None:
            var = tk.StringVar()

        label_suffix = ": *" if required else ":"
        label = ttk.Label(parent, text=f"{label_text}{label_suffix}")
        label.pack(anchor="w")

        entry = ttk.Entry(parent, textvariable=var, width=width)
        entry.pack(fill="x", pady=(0, 10))

        return label, entry, var

    def make_treeview_sortable(self, tree: ttk.Treeview):
        """
        Make a Treeview's columns sortable by clicking headers.

        Args:
            tree: Treeview widget to make sortable

        Example:
            self.tree = ttk.Treeview(parent, columns=('name', 'date'))
            self.make_treeview_sortable(self.tree)
        """
        def sort_column(col, reverse):
            # Get all items with their values
            items = [(tree.set(k, col), k) for k in tree.get_children('')]

            # Try numeric sort first, fall back to string sort
            try:
                items.sort(key=lambda t: float(t[0].rstrip('%')), reverse=reverse)
            except (ValueError, TypeError):
                items.sort(key=lambda t: t[0].lower(), reverse=reverse)

            # Reorder items
            for index, (_, k) in enumerate(items):
                tree.move(k, '', index)

            # Update heading to sort in reverse next time
            tree.heading(col, command=lambda: sort_column(col, not reverse))

        # Bind each column heading
        for col in tree['columns']:
            tree.heading(col, command=lambda c=col: sort_column(c, False))