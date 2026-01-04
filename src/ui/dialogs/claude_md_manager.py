"""
CLAUDE.md Management Dialog - Manage project CLAUDE.md file.
"""

import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from .base_dialog import BaseDialog
from .working import WorkingDialog


class ClaudeMdManagerDialog(BaseDialog):
    """Dialog for managing CLAUDE.md file."""

    def __init__(self, parent, queue_interface, settings):
        """
        Initialize CLAUDE.md manager dialog.

        Args:
            parent: Parent widget
            queue_interface: CMATInterface backend
            settings: Settings (for Claude API key)
        """
        self.queue = queue_interface
        self.settings = settings
        self.original_content = ""
        self.working_dialog = None

        BaseDialog.__init__(self, parent, "CLAUDE.md Manager", 800, 600)

        self.build_ui()
        self.load_content()

    def build_ui(self):
        """Build dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill="both", expand=True)

        # Status section
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(0, 10))

        self.status_label = ttk.Label(
            status_frame,
            text="Status: Checking...",
            font=('Arial', 10)
        )
        self.status_label.pack(anchor="w")

        self.path_label = ttk.Label(
            status_frame,
            text=f"File: {self.queue.project_root / 'CLAUDE.md'}",
            font=('Arial', 9),
            foreground='gray'
        )
        self.path_label.pack(anchor="w")

        # Text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.content_text = tk.Text(
            text_frame,
            wrap="word",
            font=('Courier', 10),
            undo=True
        )
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=scrollbar.set)

        self.content_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind text changes to track unsaved changes
        self.content_text.bind('<<Modified>>', self.on_text_modified)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")

        # Left buttons
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side="left")

        self.create_btn = ttk.Button(
            left_buttons,
            text="Create",
            command=self.on_create,
            width=12
        )
        self.create_btn.pack(side="left", padx=(0, 5))

        self.load_btn = ttk.Button(
            left_buttons,
            text="Load",
            command=self.on_load,
            width=12
        )
        self.load_btn.pack(side="left", padx=(0, 5))

        self.render_btn = ttk.Button(
            left_buttons,
            text="Render",
            command=self.on_render,
            width=12
        )
        self.render_btn.pack(side="left")

        # Right buttons
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side="right")

        self.save_btn = ttk.Button(
            right_buttons,
            text="Save",
            command=self.on_save,
            width=10
        )
        self.save_btn.pack(side="left", padx=(0, 5))

        ttk.Button(
            right_buttons,
            text="Close",
            command=self.on_close,
            width=10
        ).pack(side="left")

    def load_content(self):
        """Load CLAUDE.md content if exists."""
        status = self.queue.check_claude_md_status()

        if status["exists"]:
            path = self.queue.project_root / "CLAUDE.md"
            try:
                self.original_content = path.read_text()
                self.set_text_content(self.original_content)
                self.status_label.config(text="Status: Present")
            except Exception as e:
                self.original_content = ""
                self.set_text_content("")
                self.status_label.config(text=f"Status: Error reading file - {e}")
        else:
            self.original_content = ""
            self.set_text_content("")
            self.status_label.config(text="Status: Not configured")

        self.update_button_states()

    def set_text_content(self, content: str):
        """Set text area content."""
        self.content_text.delete("1.0", tk.END)
        if content:
            self.content_text.insert("1.0", content)
        self.content_text.edit_modified(False)

    def get_text_content(self) -> str:
        """Get text area content."""
        return self.content_text.get("1.0", "end-1c")

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self.get_text_content() != self.original_content

    def on_text_modified(self, event):
        """Handle text modification."""
        if self.content_text.edit_modified():
            self.update_button_states()
            self.content_text.edit_modified(False)

    def update_button_states(self):
        """Update button enabled/disabled states."""
        has_content = bool(self.get_text_content().strip())

        # Render only enabled if there's content
        self.render_btn.config(state="normal" if has_content else "disabled")

        # Save only enabled if there's content
        self.save_btn.config(state="normal" if has_content else "disabled")

    def on_create(self):
        """Handle Create button - generate CLAUDE.md via agent."""
        # Warn about unsaved changes
        if self.has_unsaved_changes():
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Generating will replace them.\n\nContinue?",
                parent=self.dialog
            ):
                return

        # Confirm
        if not messagebox.askyesno(
            "Generate CLAUDE.md",
            "This will analyze your project structure and generate a CLAUDE.md file.\n\n"
            "This may take a few minutes.\n\nContinue?",
            parent=self.dialog
        ):
            return

        # Create staging directory
        staging_dir = self.queue.project_root / ".claude" / ".staging" / "claude-md-generator"

        # Clean up any previous staging
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)

        staging_dir.mkdir(parents=True, exist_ok=True)

        # Store staging_dir for cleanup later
        self.staging_dir = staging_dir

        # Show working dialog
        self.working_dialog = WorkingDialog(
            self.dialog,
            "Generating CLAUDE.md",
            "180-300 seconds"
        )
        self.working_dialog.show()

        # Run agent with staging directory
        self.queue.run_agent_async(
            agent_name="claude-md-creator-agent",
            input_file=None,
            output_dir=staging_dir,
            task_description="Generate CLAUDE.md for project",
            task_type="documentation",
            on_success=self._on_agent_success,
            on_error=self._on_agent_error
        )

    def _on_agent_success(self, result_dir):
        """Handle successful agent generation."""
        if self.working_dialog:
            self.working_dialog.close()
            self.working_dialog = None

        try:
            # Look for generated CLAUDE.md in various locations
            content = None
            staging_dir = getattr(self, 'staging_dir', None)

            # Priority 1: Agent's required_output directory
            if staging_dir:
                agent_output = staging_dir / "claude-md-creator-agent" / "required_output"
                if agent_output.exists():
                    # Look for any .md file
                    for md_file in agent_output.glob("*.md"):
                        content = md_file.read_text()
                        break

                # Priority 2: CLAUDE.md in staging dir
                if not content:
                    staging_claude_md = staging_dir / "CLAUDE.md"
                    if staging_claude_md.exists():
                        content = staging_claude_md.read_text()

            # Priority 3: CLAUDE.md written directly to project root
            if not content:
                project_claude_md = self.queue.project_root / "CLAUDE.md"
                if project_claude_md.exists():
                    content = project_claude_md.read_text()

            if content:
                self.set_text_content(content)
                self.update_button_states()
            else:
                messagebox.showerror(
                    "Error",
                    "Agent completed but no CLAUDE.md output was found.",
                    parent=self.dialog
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read generated content:\n\n{e}",
                parent=self.dialog
            )
        finally:
            # Clean up staging directory
            self._cleanup_staging()

    def _on_agent_error(self, error: Exception):
        """Handle agent generation failure."""
        if self.working_dialog:
            self.working_dialog.close()
            self.working_dialog = None

        # Clean up staging directory
        self._cleanup_staging()

        error_msg = str(error)

        if "timeout" in error_msg.lower():
            response = messagebox.askyesno(
                "Timeout",
                "Agent timed out. Project may be too large.\n\nTry again?",
                parent=self.dialog
            )
            if response:
                self.on_create()
                return
        else:
            messagebox.showerror(
                "Generation Failed",
                f"Failed to generate CLAUDE.md:\n\n{error}",
                parent=self.dialog
            )

    def _cleanup_staging(self):
        """Clean up the staging directory."""
        staging_dir = getattr(self, 'staging_dir', None)
        if staging_dir and staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
        self.staging_dir = None

    def on_load(self):
        """Handle Load button - load from external file."""
        # Warn about unsaved changes
        if self.has_unsaved_changes():
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Loading a file will replace them.\n\nContinue?",
                parent=self.dialog
            ):
                return

        # Show file picker
        file_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select CLAUDE.md File",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            content = Path(file_path).read_text()
            self.set_text_content(content)
            self.update_button_states()
            messagebox.showinfo(
                "Loaded",
                f"Content loaded from:\n{file_path}\n\nClick Save to copy to project.",
                parent=self.dialog
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read file:\n\n{e}",
                parent=self.dialog
            )

    def on_render(self):
        """Handle Render button - show markdown preview dialog."""
        content = self.get_text_content()
        if not content.strip():
            return

        # Create preview dialog
        preview = tk.Toplevel(self.dialog)
        preview.title("CLAUDE.md Preview")
        preview.geometry("800x600")
        preview.transient(self.dialog)
        preview.grab_set()

        # Center on parent
        preview.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - 400
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - 300
        preview.geometry(f"800x600+{x}+{y}")

        # Content frame
        frame = ttk.Frame(preview, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="CLAUDE.md Preview",
            font=('Arial', 12, 'bold')
        ).pack(anchor="w", pady=(0, 10))

        # Text display with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 10))

        text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=('Arial', 11),
            padx=10,
            pady=10,
            state="normal",
            cursor="arrow"
        )
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configure markdown tags
        self._configure_preview_tags(text_widget)

        # Render markdown content
        self._render_markdown(text_widget, content)

        text_widget.configure(state="disabled")

        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=preview.destroy,
            width=10
        ).pack(anchor="e")

    def _configure_preview_tags(self, text_widget: tk.Text):
        """Configure text tags for markdown rendering."""
        # Headings
        text_widget.tag_configure("h1", font=('Arial', 18, 'bold'), spacing1=15, spacing3=10)
        text_widget.tag_configure("h2", font=('Arial', 16, 'bold'), spacing1=12, spacing3=8)
        text_widget.tag_configure("h3", font=('Arial', 14, 'bold'), spacing1=10, spacing3=6)
        text_widget.tag_configure("h4", font=('Arial', 12, 'bold'), spacing1=8, spacing3=4)

        # Text formatting
        text_widget.tag_configure("bold", font=('Arial', 11, 'bold'))
        text_widget.tag_configure("italic", font=('Arial', 11, 'italic'))
        text_widget.tag_configure("bold_italic", font=('Arial', 11, 'bold italic'))

        # Code
        text_widget.tag_configure(
            "code",
            font=('Courier', 10),
            background='#f0f0f0'
        )
        text_widget.tag_configure(
            "code_block",
            font=('Courier', 10),
            background='#f5f5f5',
            lmargin1=20,
            lmargin2=20,
            spacing1=5,
            spacing3=5
        )

        # Lists
        text_widget.tag_configure("bullet", lmargin1=20, lmargin2=35)
        text_widget.tag_configure("numbered", lmargin1=20, lmargin2=35)

        # Blockquote
        text_widget.tag_configure(
            "blockquote",
            lmargin1=20,
            lmargin2=20,
            foreground='#666666',
            font=('Arial', 11, 'italic')
        )

        # Horizontal rule
        text_widget.tag_configure("hr", font=('Arial', 1), spacing1=10, spacing3=10)

    def _render_markdown(self, text_widget: tk.Text, content: str):
        """Render markdown content to the text widget."""
        lines = content.split('\n')
        i = 0
        in_code_block = False
        code_block_content = []

        while i < len(lines):
            line = lines[i]

            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    # End of code block
                    code_text = '\n'.join(code_block_content)
                    text_widget.insert(tk.END, code_text + '\n', "code_block")
                    code_block_content = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                i += 1
                continue

            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue

            # Handle different markdown elements
            if not line.strip():
                text_widget.insert(tk.END, '\n')
            elif line.startswith('####'):
                text_widget.insert(tk.END, line[4:].strip() + '\n', "h4")
            elif line.startswith('###'):
                text_widget.insert(tk.END, line[3:].strip() + '\n', "h3")
            elif line.startswith('##'):
                text_widget.insert(tk.END, line[2:].strip() + '\n', "h2")
            elif line.startswith('#'):
                text_widget.insert(tk.END, line[1:].strip() + '\n', "h1")
            elif line.startswith('> '):
                text_widget.insert(tk.END, line[2:] + '\n', "blockquote")
            elif line.startswith('---') or line.startswith('***'):
                text_widget.insert(tk.END, '─' * 60 + '\n', "hr")
            elif re.match(r'^(\s*)[-*+]\s', line):
                # Bullet list
                match = re.match(r'^(\s*)[-*+]\s(.*)$', line)
                if match:
                    indent = len(match.group(1)) // 2
                    bullet = '  ' * indent + '• '
                    self._render_inline(text_widget, bullet + match.group(2) + '\n', "bullet")
            elif re.match(r'^(\s*)\d+\.\s', line):
                # Numbered list
                match = re.match(r'^(\s*)(\d+)\.\s(.*)$', line)
                if match:
                    indent = len(match.group(1)) // 2
                    num = '  ' * indent + match.group(2) + '. '
                    self._render_inline(text_widget, num + match.group(3) + '\n', "numbered")
            else:
                # Regular paragraph
                self._render_inline(text_widget, line + '\n')

            i += 1

    def _render_inline(self, text_widget: tk.Text, text: str, base_tag: str = None):
        """Render inline markdown elements (bold, italic, code)."""
        # Patterns for inline elements
        patterns = [
            (r'\*\*\*(.+?)\*\*\*', 'bold_italic'),
            (r'\*\*(.+?)\*\*', 'bold'),
            (r'__(.+?)__', 'bold'),
            (r'\*(.+?)\*', 'italic'),
            (r'_(.+?)_', 'italic'),
            (r'`([^`]+)`', 'code'),
        ]

        # Find all matches and their positions
        matches = []
        for pattern, tag in patterns:
            for match in re.finditer(pattern, text):
                matches.append((match.start(), match.end(), match, tag))

        # Sort by position
        matches.sort(key=lambda x: x[0])

        # Render text with formatting
        last_end = 0
        for start, end, match, tag in matches:
            # Skip overlapping matches
            if start < last_end:
                continue

            # Insert text before this match
            if start > last_end:
                plain_text = text[last_end:start]
                tags = (base_tag,) if base_tag else ()
                text_widget.insert(tk.END, plain_text, tags)

            # Insert the matched content
            content_text = match.group(1)
            tags = (tag, base_tag) if base_tag else (tag,)
            text_widget.insert(tk.END, content_text, tags)

            last_end = end

        # Insert remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            tags = (base_tag,) if base_tag else ()
            text_widget.insert(tk.END, remaining, tags)

    def on_save(self):
        """Handle Save button - write to project."""
        content = self.get_text_content()
        if not content.strip():
            messagebox.showwarning(
                "No Content",
                "Nothing to save. Add content first.",
                parent=self.dialog
            )
            return

        try:
            path = self.queue.project_root / "CLAUDE.md"
            path.write_text(content)
            self.original_content = content
            self.status_label.config(text="Status: Present")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save file:\n\n{e}",
                parent=self.dialog
            )

    def on_close(self):
        """Handle Close button."""
        if self.has_unsaved_changes():
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes.\n\nDiscard and close?",
                parent=self.dialog
            ):
                return

        self.dialog.destroy()
