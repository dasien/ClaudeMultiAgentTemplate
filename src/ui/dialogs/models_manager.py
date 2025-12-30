"""
Models Manager Dialog - Manage Claude model configurations.

Provides interface for:
- Viewing all configured models
- Adding new models
- Editing model pricing and settings
- Deleting models
- Setting default model
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional


from .base_dialog import BaseDialog


class ModelsManagerDialog(BaseDialog):
    """Dialog for managing Claude model configurations."""

    def __init__(self, parent, queue):
        """
        Initialize models manager.

        Args:
            parent: Parent window
            queue: CMATInterface instance
        """
        self.queue = queue
        self.models = []
        self.selected_model = None
        self.default_model_id = None

        super().__init__(parent, "Models Manager", width=900, height=600)

        self.build_ui()
        # Don't call show() - this dialog doesn't return a result

    def build_ui(self):
        """Create the dialog widgets."""
        # Main container with two panes
        main_paned = ttk.PanedWindow(self.dialog, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top pane: List view
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=2)

        # Toolbar
        toolbar = ttk.Frame(top_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="Add Model", command=self.show_add_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Edit Model", command=self.show_edit_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Set as Default", command=self.set_default).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        # Models list with scrollbar
        list_frame = ttk.Frame(top_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ('name', 'pattern', 'max_tokens', 'input_price', 'output_price')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')

        # Column headings
        self.tree.heading('name', text='Name')
        self.tree.heading('pattern', text='Pattern')
        self.tree.heading('max_tokens', text='Max Tokens')
        self.tree.heading('input_price', text='Input ($/1M)')
        self.tree.heading('output_price', text='Output ($/1M)')

        # Column widths
        self.tree.column('name', width=200)
        self.tree.column('pattern', width=200)
        self.tree.column('max_tokens', width=100)
        self.tree.column('input_price', width=100)
        self.tree.column('output_price', width=100)

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
        bottom_frame = ttk.LabelFrame(main_paned, text="Model Details")
        main_paned.add(bottom_frame, weight=1)

        # Details text widget
        self.details_text = scrolledtext.ScrolledText(
            bottom_frame,
            wrap=tk.WORD,
            width=80,
            height=8,
            state='disabled'
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Button frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        ttk.Button(button_frame, text="Delete Model", command=self.delete_model).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Close", command=self.close).pack(side=tk.RIGHT)

        # Load initial data
        self.refresh()

    def refresh(self):
        """Refresh the models list."""
        try:
            self.models = self.queue.models.list_all()
            default_model = self.queue.models.get_default()
            self.default_model_id = default_model.id if default_model else None
            self.update_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load models: {e}")

    def update_tree(self):
        """Update the treeview with current models."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add models
        for model in self.models:
            # Add default indicator
            name = model.name
            if model.id == self.default_model_id:
                name = f"⭐ {name}"

            self.tree.insert('', tk.END, iid=model.id, values=(
                name,
                model.pattern,
                f"{model.max_tokens:,}",
                f"${model.pricing.input:.2f}",
                f"${model.pricing.output:.2f}"
            ))

        # Update status
        count = len(self.models)
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', f"Loaded {count} model{'s' if count != 1 else ''}")
        self.details_text.configure(state='disabled')

    def on_select(self, event):
        """Handle model selection."""
        selection = self.tree.selection()
        if not selection:
            return

        model_id = selection[0]
        self.selected_model = next((m for m in self.models if m.id == model_id), None)

        if self.selected_model:
            self.show_details()

    def show_details(self):
        """Display details of selected model."""
        if not self.selected_model:
            return

        model = self.selected_model
        is_default = model.id == self.default_model_id

        details = f"""ID: {model.id}
Name: {model.name}
{'⭐ DEFAULT MODEL' if is_default else ''}

Description: {model.description}

Pattern: {model.pattern}
Max Tokens: {model.max_tokens:,}

Pricing (per {model.pricing.per_tokens:,} tokens):
  Input:       ${model.pricing.input:.2f}
  Output:      ${model.pricing.output:.2f}
  Cache Write: ${model.pricing.cache_write:.2f}
  Cache Read:  ${model.pricing.cache_read:.2f}
  Currency:    {model.pricing.currency}
"""

        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', details)
        self.details_text.configure(state='disabled')

    def set_default(self):
        """Set the selected model as default."""
        if not self.selected_model:
            messagebox.showwarning("No Selection", "Please select a model to set as default.")
            return

        try:
            self.queue.models.set_default(self.selected_model.id)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set default model: {e}")

    def delete_model(self):
        """Delete the selected model."""
        if not self.selected_model:
            messagebox.showwarning("No Selection", "Please select a model to delete.")
            return

        # Check if it's the default
        if self.selected_model.id == self.default_model_id:
            messagebox.showwarning(
                "Cannot Delete",
                "Cannot delete the default model. Set another model as default first."
            )
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Delete model:\n\n{self.selected_model.name}\n\nThis cannot be undone."
        )

        if result:
            try:
                self.queue.models.delete(self.selected_model.id)
                self.selected_model = None
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete model: {e}")

    def show_add_dialog(self):
        """Show dialog to add a new model."""
        ModelEditDialog(self.dialog, self.queue, mode='add', on_success=self.refresh)

    def show_edit_dialog(self):
        """Show dialog to edit the selected model."""
        if not self.selected_model:
            messagebox.showwarning("No Selection", "Please select a model to edit.")
            return

        ModelEditDialog(
            self.dialog, self.queue,
            mode='edit',
            model=self.selected_model,
            on_success=self.refresh
        )


class ModelEditDialog(BaseDialog):
    """Dialog for adding or editing a model."""

    def __init__(self, parent, queue, mode='add', model=None, on_success=None):
        """
        Initialize model edit dialog.

        Args:
            parent: Parent window
            queue: CMATInterface instance
            mode: 'add' or 'edit'
            model: ClaudeModel instance (for edit mode)
            on_success: Callback to execute on successful save
        """
        self.queue = queue
        self.mode = mode
        self.model = model
        self.on_success = on_success

        title = "Add Model" if mode == 'add' else "Edit Model"
        super().__init__(parent, title, width=500, height=550)

        self.build_ui()
        self.show()

    def build_ui(self):
        """Create the dialog widgets."""
        # Create form fields
        fields_frame = ttk.Frame(self.dialog)
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0

        # Model ID
        ttk.Label(fields_frame, text="Model ID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.id_entry = ttk.Entry(fields_frame, width=40)
        self.id_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.id_entry.insert(0, self.model.id)
            self.id_entry.configure(state='disabled')
        row += 1

        # Name
        ttk.Label(fields_frame, text="Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(fields_frame, width=40)
        self.name_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.name_entry.insert(0, self.model.name)
        row += 1

        # Description
        ttk.Label(fields_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.description_entry = ttk.Entry(fields_frame, width=40)
        self.description_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.description_entry.insert(0, self.model.description)
        row += 1

        # Pattern
        ttk.Label(fields_frame, text="Pattern:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.pattern_entry = ttk.Entry(fields_frame, width=40)
        self.pattern_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.pattern_entry.insert(0, self.model.pattern)
        ttk.Label(fields_frame, text="(e.g., *sonnet-4*|*sonnet-4-5*)", foreground='gray').grid(
            row=row+1, column=1, sticky=tk.W
        )
        row += 2

        # Max Tokens
        ttk.Label(fields_frame, text="Max Tokens:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_tokens_entry = ttk.Entry(fields_frame, width=40)
        self.max_tokens_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.max_tokens_entry.insert(0, str(self.model.max_tokens))
        else:
            self.max_tokens_entry.insert(0, "200000")
        row += 1

        # Pricing section
        ttk.Separator(fields_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(fields_frame, text="Pricing (USD per 1M tokens):", font=('TkDefaultFont', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        row += 1

        # Input price
        ttk.Label(fields_frame, text="Input:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.input_price_entry = ttk.Entry(fields_frame, width=40)
        self.input_price_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.input_price_entry.insert(0, str(self.model.pricing.input))
        else:
            self.input_price_entry.insert(0, "3.00")
        row += 1

        # Output price
        ttk.Label(fields_frame, text="Output:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.output_price_entry = ttk.Entry(fields_frame, width=40)
        self.output_price_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.output_price_entry.insert(0, str(self.model.pricing.output))
        else:
            self.output_price_entry.insert(0, "15.00")
        row += 1

        # Cache write price
        ttk.Label(fields_frame, text="Cache Write:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cache_write_entry = ttk.Entry(fields_frame, width=40)
        self.cache_write_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.cache_write_entry.insert(0, str(self.model.pricing.cache_write))
        else:
            self.cache_write_entry.insert(0, "3.75")
        row += 1

        # Cache read price
        ttk.Label(fields_frame, text="Cache Read:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cache_read_entry = ttk.Entry(fields_frame, width=40)
        self.cache_read_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == 'edit':
            self.cache_read_entry.insert(0, str(self.model.pricing.cache_read))
        else:
            self.cache_read_entry.insert(0, "0.30")
        row += 1

        # Configure grid
        fields_frame.columnconfigure(1, weight=1)

        # Button frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        ttk.Button(button_frame, text="Save", command=self.save_model).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.close).pack(side=tk.LEFT)

    def save_model(self):
        """Save the model."""
        # Validate and collect data
        try:
            model_id = self.id_entry.get().strip()
            if not model_id:
                raise ValueError("Model ID is required")

            name = self.name_entry.get().strip()
            if not name:
                raise ValueError("Name is required")

            description = self.description_entry.get().strip()
            pattern = self.pattern_entry.get().strip()
            if not pattern:
                raise ValueError("Pattern is required")

            max_tokens = int(self.max_tokens_entry.get())
            input_price = float(self.input_price_entry.get())
            output_price = float(self.output_price_entry.get())
            cache_write = float(self.cache_write_entry.get())
            cache_read = float(self.cache_read_entry.get())

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        try:
            # Import model classes
            from core.models.claude_model import ClaudeModel, ModelPricing

            # Create pricing object
            pricing = ModelPricing(
                input=input_price,
                output=output_price,
                cache_write=cache_write,
                cache_read=cache_read,
                currency="USD",
                per_tokens=1000000
            )

            # Create model object
            model = ClaudeModel(
                id=model_id,
                name=name,
                description=description,
                pattern=pattern,
                max_tokens=max_tokens,
                pricing=pricing
            )

            # Save to service
            if self.mode == 'add':
                self.queue.models.add(model)
            else:
                self.queue.models.update(model)

            # Call success callback
            if self.on_success:
                self.on_success()

            self.close()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save model: {e}")