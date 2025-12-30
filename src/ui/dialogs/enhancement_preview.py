"""
Enhancement Preview Dialog - Preview and save generated enhancements.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import shutil

from .base_dialog import BaseDialog


class EnhancementPreviewDialog(BaseDialog):
    """Dialog for previewing and saving generated enhancement specifications."""

    def __init__(self, parent, queue_interface, settings,
                 content: str, title: str, filename: str,
                 output_directory: str, staging_dir: Path = None):
        """
        Initialize preview dialog.

        Args:
            parent: Parent window
            queue_interface: CMATInterface instance
            settings: Settings object
            content: Generated enhancement content
            title: Enhancement title
            filename: Enhancement filename (slug)
            output_directory: Final output directory path
            staging_dir: Staging directory to cleanup (optional)
        """
        BaseDialog.__init__(self, parent, f"Preview: {title}", 900, 700)

        self.queue = queue_interface
        self.settings = settings
        self.content = content
        self.enhancement_title = title
        self.filename = filename
        self.output_directory = output_directory
        self.staging_dir = staging_dir

        self.build_ui()
        self.show()

    def build_ui(self):
        """Build the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main_frame,
            text=f"Preview: {self.enhancement_title}",
            font=('Arial', 12, 'bold')
        ).pack(pady=(0, 10))

        # Text area with scrollbars
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.text_widget = tk.Text(text_frame, wrap="word", font=('Courier', 9))
        text_scroll_y = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_widget.yview)
        text_scroll_x = ttk.Scrollbar(text_frame, orient="horizontal", command=self.text_widget.xview)
        self.text_widget.configure(yscrollcommand=text_scroll_y.set, xscrollcommand=text_scroll_x.set)

        self.text_widget.grid(row=0, column=0, sticky='nsew')
        text_scroll_y.grid(row=0, column=1, sticky='ns')
        text_scroll_x.grid(row=1, column=0, sticky='ew')

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # Insert content
        self.text_widget.insert('1.0', self.content)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="💾 Save",
            command=self.save_only,
            width=20
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="💾 Save & Start Workflow...",
            command=self.save_and_start_workflow,
            width=25
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="🔄 Regenerate",
            command=self.regenerate,
            width=15
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_preview,
            width=12
        ).pack(side="left", padx=5)

        # Help text
        ttk.Label(
            main_frame,
            text="You can edit the content above before saving",
            font=('Arial', 8),
            foreground='gray'
        ).pack()

    def save_enhancement(self) -> Path:
        """
        Save enhancement to final location.

        Returns:
            Path to saved enhancement file, or None if save failed
        """
        try:
            # Create final directory structure
            output_dir = Path(self.output_directory) / self.filename
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save the edited content from preview
            output_file = output_dir / f"{self.filename}.md"
            final_content = self.text_widget.get('1.0', tk.END).strip()
            output_file.write_text(final_content, encoding='utf-8')

            # Cleanup staging directory
            if self.staging_dir and self.staging_dir.exists():
                shutil.rmtree(self.staging_dir, ignore_errors=True)

            return output_file

        except Exception as e:
            messagebox.showerror(
                "Save Error",
                f"Failed to save enhancement:\n\n{e}",
                parent=self.dialog
            )
            return None

    def save_only(self):
        """Save enhancement without starting workflow."""
        output_file = self.save_enhancement()
        if output_file:
            self.close(result=str(output_file))

    def save_and_start_workflow(self):
        """Save enhancement and open workflow start dialog."""
        output_file = self.save_enhancement()
        if output_file:
            # Close this dialog
            self.close(result=str(output_file))

            # Open workflow start dialog
            try:
                from .workflow_start import WorkflowStartDialog

                workflow_dialog = WorkflowStartDialog(
                    self.parent,
                    self.queue,
                    self.settings,
                    preselected_enhancement=str(output_file)
                )
            except ImportError:
                messagebox.showinfo(
                    "Workflow Dialog Not Found",
                    f"Enhancement saved to:\n{output_file}\n\n"
                    "Please use the Workflow menu to start a workflow.",
                    parent=self.parent
                )

    def cancel_preview(self):
        """Cancel and cleanup staging."""
        # Cleanup staging on cancel
        if self.staging_dir and self.staging_dir.exists():
            shutil.rmtree(self.staging_dir, ignore_errors=True)

        # Close dialog without result
        self.cancel()

    def regenerate(self):
        """Request regeneration from parent dialog."""
        # Close this preview dialog and signal regeneration
        # The enhancement creation dialog should handle this
        self.close(result="REGENERATE")