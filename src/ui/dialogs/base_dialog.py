"""
Base Dialog class with common dialog functionality.
All dialogs should inherit from this to avoid code duplication.
"""

import tkinter as tk
from tkinter import ttk, messagebox
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

    # ========================================================================
    # Widget Factory Methods
    # ========================================================================

    def create_scrolled_treeview(
        self,
        parent: tk.Widget,
        columns: dict[str, tuple[str, int]],
        show_headings: bool = True,
        sortable: bool = True,
        selectmode: str = "browse",
        height: int = 10,
        dual_scroll: bool = False
    ) -> ttk.Treeview:
        """
        Create a Treeview with attached scrollbars.

        Args:
            parent: Parent widget
            columns: Dict mapping column_id to (heading_text, width)
            show_headings: Whether to show column headings
            sortable: Whether to enable column sorting
            selectmode: Selection mode ('browse', 'extended', 'none')
            height: Number of visible rows
            dual_scroll: If True, attach both vertical and horizontal scrollbars

        Returns:
            Configured ttk.Treeview instance (scrollbars auto-attached via grid)

        Example:
            tree = self.create_scrolled_treeview(
                frame,
                columns={
                    "name": ("Name", 200),
                    "role": ("Role", 150),
                    "description": ("Description", 300),
                },
                sortable=True
            )
        """
        # Create container frame for grid layout
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)

        # Configure grid weights
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        # Create treeview
        column_ids = list(columns.keys())
        show = "headings" if show_headings else ""
        tree = ttk.Treeview(
            container,
            columns=column_ids,
            show=show,
            selectmode=selectmode,
            height=height
        )

        # Configure columns
        for col_id, (heading, width) in columns.items():
            tree.heading(col_id, text=heading)
            tree.column(col_id, width=width)

        # Create and attach vertical scrollbar
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=v_scroll.set)

        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        # Optional horizontal scrollbar
        if dual_scroll:
            h_scroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
            tree.configure(xscrollcommand=h_scroll.set)
            h_scroll.grid(row=1, column=0, sticky="ew")

        # Make sortable if requested
        if sortable and show_headings:
            self.make_treeview_sortable(tree)

        return tree

    def create_scrolled_text(
        self,
        parent: tk.Widget,
        height: int = 10,
        width: int = 80,
        font: tuple = ("Courier", 9),
        wrap: str = "word",
        dual_scroll: bool = False,
        read_only: bool = False
    ) -> tuple[tk.Text, ttk.Frame]:
        """
        Create a Text widget with attached scrollbars.

        Args:
            parent: Parent widget
            height: Text widget height in lines
            width: Text widget width in characters
            font: Font tuple (family, size)
            wrap: Text wrapping mode ('word', 'char', 'none')
            dual_scroll: If True, attach both vertical and horizontal scrollbars
            read_only: If True, set state to DISABLED after creation

        Returns:
            (text_widget, container_frame) tuple

        Example:
            text, frame = self.create_scrolled_text(
                parent,
                height=20,
                dual_scroll=True,
                read_only=True
            )
            frame.pack(fill="both", expand=True)
        """
        # Create container frame for grid layout
        container = ttk.Frame(parent)

        # Configure grid weights
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        # Create text widget
        text = tk.Text(
            container,
            height=height,
            width=width,
            font=font,
            wrap=wrap
        )

        # Create and attach vertical scrollbar
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=v_scroll.set)

        # Grid layout
        text.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        # Optional horizontal scrollbar
        if dual_scroll:
            h_scroll = ttk.Scrollbar(container, orient="horizontal", command=text.xview)
            text.configure(xscrollcommand=h_scroll.set)
            h_scroll.grid(row=1, column=0, sticky="ew")

        # Set read-only if requested
        if read_only:
            text.configure(state="disabled")

        return text, container

    # ========================================================================
    # Tree Selection Helpers
    # ========================================================================

    def get_selected_tree_item(
        self,
        tree: ttk.Treeview,
        error_message: Optional[str] = None
    ) -> tuple[Optional[str], Optional[tuple]]:
        """
        Get the selected item from a treeview.

        Args:
            tree: Treeview widget
            error_message: Optional warning message if nothing selected

        Returns:
            (item_id, values) tuple, or (None, None) if nothing selected

        Example:
            item_id, values = self.get_selected_tree_item(
                self.tree,
                "Please select an agent to edit."
            )
            if item_id is None:
                return
            agent_name = values[0]
        """
        selection = tree.selection()
        if not selection:
            if error_message:
                self.show_warning("No Selection", error_message)
            return None, None

        item_id = selection[0]
        values = tree.item(item_id, 'values')
        return item_id, values

    def get_selected_tree_field(
        self,
        tree: ttk.Treeview,
        column_index: int,
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a specific field from the selected treeview item.

        Args:
            tree: Treeview widget
            column_index: Index of column to retrieve (0-based)
            error_message: Optional warning message if nothing selected

        Returns:
            Field value as string, or None if nothing selected

        Example:
            agent_name = self.get_selected_tree_field(self.tree, 0, "Please select an agent.")
            if agent_name is None:
                return
        """
        item_id, values = self.get_selected_tree_item(tree, error_message)
        if values is None:
            return None
        if column_index >= len(values):
            return None
        return values[column_index]

    # ========================================================================
    # Error Handling Methods
    # ========================================================================

    def show_error(self, title: str, message: str) -> None:
        """Show error messagebox centered on dialog."""
        messagebox.showerror(title, message, parent=self.dialog)

    def show_warning(self, title: str, message: str) -> None:
        """Show warning messagebox centered on dialog."""
        messagebox.showwarning(title, message, parent=self.dialog)

    def show_info(self, title: str, message: str) -> None:
        """Show info messagebox centered on dialog."""
        messagebox.showinfo(title, message, parent=self.dialog)

    def confirm_action(self, title: str, message: str) -> bool:
        """Show yes/no confirmation dialog centered on dialog."""
        return messagebox.askyesno(title, message, parent=self.dialog)

    def confirm_delete(self, item_type: str, item_name: str, details: str = "") -> bool:
        """
        Show standardized delete confirmation dialog.

        Args:
            item_type: Type of item (e.g., "agent", "skill", "workflow")
            item_name: Name of item being deleted
            details: Optional additional details

        Returns:
            True if user confirmed, False otherwise
        """
        message = f"Delete {item_type} '{item_name}'?"
        if details:
            message += f"\n\n{details}"
        message += "\n\nThis action cannot be undone."
        return messagebox.askyesno("Confirm Delete", message, parent=self.dialog)

    def show_selection_required(self, item_type: str = "item") -> None:
        """Show standardized 'nothing selected' warning."""
        self.show_warning("No Selection", f"Please select a {item_type} first.")

    # ========================================================================
    # Child Window Helper
    # ========================================================================

    def create_child_window(
        self,
        title: str,
        width: int = 800,
        height: int = 600,
        modal: bool = True
    ) -> tk.Toplevel:
        """
        Create a child window (nested modal or modeless).

        Automatically configures:
        - transient relationship to parent dialog
        - grab_set for modal behavior
        - Escape key binding to close
        - Initial focus

        Args:
            title: Window title
            width: Window width in pixels
            height: Window height in pixels
            modal: If True, grab input focus (blocks parent)

        Returns:
            Configured tk.Toplevel instance

        Example:
            preview = self.create_child_window("Preview", 800, 600)
            # Add content to preview
            text = tk.Text(preview)
            text.pack(fill="both", expand=True)
        """
        window = tk.Toplevel(self.dialog)
        window.title(title)
        window.geometry(f"{width}x{height}")
        window.transient(self.dialog)

        if modal:
            window.grab_set()

        window.bind('<Escape>', lambda e: window.destroy())
        window.focus_set()

        return window