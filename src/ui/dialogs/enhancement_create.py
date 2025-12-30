"""
Enhancement Generator Dialog - Create enhancement files with Claude API assistance.
Supports multiple source types: local files, GitHub issues, and web URLs.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List
from .working import WorkingDialog
from .base_dialog import BaseDialog
from .mixins.claude_generator_mixin import ClaudeGeneratorMixin
from ..models import EnhancementSource, SourceType
from ..utils import to_slug, validate_slug, PathUtils, WebUtils


class CreateEnhancementDialog(BaseDialog, ClaudeGeneratorMixin):
    """Dialog for generating enhancement files with Claude API."""

    def __init__(self, parent, queue_interface, settings):
        # Initialize both base classes
        BaseDialog.__init__(self, parent, "Generate New Enhancement", 750, 700)
        ClaudeGeneratorMixin.__init__(self, settings)

        self.queue = queue_interface
        self.sources: List[EnhancementSource] = []

        self.build_ui()
        self.show()

    def build_ui(self):
        """Build the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="Generate Enhancement Specification",
            font=('Arial', 12, 'bold')
        ).pack(pady=(0, 15))

        # Enhancement Title
        _, self.title_entry, self.title_var = self.create_label_entry_pair(
            main_frame,
            "Enhancement Title",
            width=70,
            required=True
        )
        self.title_var.trace_add('write', self.on_title_changed)

        # Filename with auto-generate
        filename_frame = ttk.Frame(main_frame)
        filename_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(filename_frame, text="Filename (slug): *").pack(side="left")
        self.auto_filename_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filename_frame,
            text="Auto-generate from title",
            variable=self.auto_filename_var,
            command=self.toggle_filename_auto
        ).pack(side="right")

        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(main_frame, textvariable=self.filename_var, width=70)
        self.filename_entry.pack(fill="x", pady=(0, 5))
        self.filename_entry.config(state='readonly')

        self.filename_validation_label = ttk.Label(
            main_frame,
            text="(lowercase, hyphens only: my-feature-name)",
            font=('Arial', 8),
            foreground='gray'
        )
        self.filename_validation_label.pack(anchor="w", pady=(0, 10))

        # Output Directory
        ttk.Label(main_frame, text="Output Directory: *").pack(anchor="w")
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill="x", pady=(0, 10))

        self.directory_var = tk.StringVar()
        default_dir = self.queue.project_root / "enhancements"
        self.directory_var.set(str(default_dir))

        dir_entry = ttk.Entry(dir_frame, textvariable=self.directory_var)
        dir_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).pack(side="left", padx=(5, 0))

        # Sources Section (replaces Reference Files)
        ttk.Label(main_frame, text="Sources (optional):").pack(anchor="w", pady=(0, 5))

        sources_frame = ttk.Frame(main_frame)
        sources_frame.pack(fill="x", pady=(0, 10))

        # Listbox for sources
        list_frame = ttk.Frame(sources_frame)
        list_frame.pack(side="left", fill="both", expand=True)

        self.sources_listbox = tk.Listbox(list_frame, height=5, relief='flat', borderwidth=1, highlightthickness=1)
        sources_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.sources_listbox.yview)
        self.sources_listbox.configure(yscrollcommand=sources_scroll.set)

        self.sources_listbox.pack(side="left", fill="both", expand=True)
        sources_scroll.pack(side="right", fill="y")

        # Buttons for sources
        sources_buttons = ttk.Frame(sources_frame)
        sources_buttons.pack(side="right", fill="y", padx=(5, 0))

        # Add Source dropdown menu
        self.add_source_menu = tk.Menu(self.dialog, tearoff=0)
        self.add_source_menu.add_command(label="Add File(s)...", command=self.add_file_sources)
        self.add_source_menu.add_command(label="Add GitHub Issue...", command=self.add_github_source)
        self.add_source_menu.add_command(label="Add Web URL...", command=self.add_web_source)

        self.add_source_btn = ttk.Button(
            sources_buttons,
            text="Add Source ▼",
            command=self.show_add_source_menu,
            width=15
        )
        self.add_source_btn.pack(pady=2)

        ttk.Button(sources_buttons, text="Remove", command=self.remove_source, width=15).pack(pady=2)
        ttk.Button(sources_buttons, text="Clear All", command=self.clear_sources, width=15).pack(pady=2)

        # Description
        desc_header = ttk.Frame(main_frame)
        desc_header.pack(fill="x", pady=(0, 5))

        ttk.Label(desc_header, text="Description: *").pack(side="left")

        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="both", expand=True, pady=(0, 5))

        self.description_text = tk.Text(desc_frame, height=5, wrap="word")
        desc_scroll = ttk.Scrollbar(desc_frame, orient="vertical", command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scroll.set)

        self.description_text.pack(side="left", fill="both", expand=True)
        desc_scroll.pack(side="right", fill="y")

        ttk.Label(
            main_frame,
            text="Describe what you want to accomplish and why",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(5, 15))

        # Generate Button
        self.generate_btn = ttk.Button(
            main_frame,
            text="Generate with Claude",
            command=self.generate_enhancement,
            state=tk.DISABLED
        )
        self.generate_btn.pack(pady=10)

        # Bottom buttons
        self.create_button_frame(main_frame, [("Cancel", self.cancel)])

        ttk.Label(main_frame, text="* Required fields", font=('Arial', 8), foreground='gray').pack(pady=(10, 0))

        # Validate initially
        self.validate_form()

        # Set focus
        self.set_focus(self.title_entry)

    def on_title_changed(self, *args):
        """Auto-generate filename from title if enabled."""
        if self.auto_filename_var.get():
            title = self.title_var.get().strip()
            slug = to_slug(title)
            self.filename_var.set(slug)
        self.validate_form()

    def toggle_filename_auto(self):
        """Toggle auto-generation of filename."""
        if self.auto_filename_var.get():
            self.filename_entry.config(state='readonly')
            self.on_title_changed()
        else:
            self.filename_entry.config(state='normal')

    def browse_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            parent=self.dialog,
            title="Select Enhancement Output Directory",
            initialdir=self.directory_var.get(),
            mustexist=False
        )
        if directory:
            self.directory_var.set(directory)

    # =========================================================================
    # Source Management
    # =========================================================================

    def show_add_source_menu(self):
        """Show the add source dropdown menu."""
        try:
            # Position menu below the button
            x = self.add_source_btn.winfo_rootx()
            y = self.add_source_btn.winfo_rooty() + self.add_source_btn.winfo_height()
            self.add_source_menu.post(x, y)
        except:
            # Fallback to mouse position
            self.add_source_menu.post(
                self.dialog.winfo_pointerx(),
                self.dialog.winfo_pointery()
            )

    def add_file_sources(self):
        """Add local file sources."""
        files = filedialog.askopenfilenames(
            parent=self.dialog,
            title="Select Reference Files",
            initialdir=str(self.queue.project_root),
            filetypes=[
                ("All Files", "*.*"),
                ("Markdown", "*.md"),
                ("Python", "*.py"),
                ("Text", "*.txt"),
                ("JSON", "*.json")
            ]
        )

        for file in files:
            rel_path = PathUtils.relative_or_name(Path(file), self.queue.project_root)
            source = EnhancementSource.from_file(file, rel_path)
            self.sources.append(source)
            self.sources_listbox.insert(tk.END, f"{source.get_icon()} {source.display_name}")

    def add_github_source(self):
        """Add GitHub issue source."""
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add GitHub Issue")
        dialog.geometry("500x150")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="GitHub Issue URL:").pack(anchor="w", pady=(0, 5))
        url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=url_var, width=60)
        url_entry.pack(fill="x", pady=(0, 10))
        url_entry.focus()

        ttk.Label(
            main_frame,
            text="Example: https://github.com/owner/repo/issues/123",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 10))

        def add_url():
            url = url_var.get().strip()
            if not url:
                messagebox.showwarning("Missing URL", "Please enter a GitHub issue URL", parent=dialog)
                return

            # Validate using WebUtils
            if not WebUtils.is_github_issue_url(url):
                messagebox.showwarning(
                    "Invalid URL",
                    "Please enter a valid GitHub issue URL\n"
                    "Example: https://github.com/owner/repo/issues/123",
                    parent=dialog
                )
                return

            # Extract issue number for display
            parsed = WebUtils.parse_github_issue_url(url)
            if parsed:
                _, _, issue_num = parsed
                source = EnhancementSource.from_github_issue(url, f"#{issue_num}")
                self.sources.append(source)
                self.sources_listbox.insert(tk.END, f"{source.get_icon()} {source.display_name}")
                dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        ttk.Button(button_frame, text="Add", command=add_url, width=12).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=12).pack(side="left", padx=5)

        url_entry.bind('<Return>', lambda e: add_url())

    def add_web_source(self):
        """Add web URL source."""
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add Web URL")
        dialog.geometry("500x180")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Web Page URL:").pack(anchor="w", pady=(0, 5))
        url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=url_var, width=60)
        url_entry.pack(fill="x", pady=(0, 10))
        url_entry.focus()

        ttk.Label(
            main_frame,
            text="Example: https://example.com/documentation/feature",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 10))

        def add_url():
            url = url_var.get().strip()
            if not url:
                messagebox.showwarning("Missing URL", "Please enter a web page URL", parent=dialog)
                return

            # Validate using WebUtils
            valid, error = WebUtils.validate_url(url)
            if not valid:
                messagebox.showwarning("Invalid URL", error, parent=dialog)
                return

            source = EnhancementSource.from_web_url(url)
            self.sources.append(source)
            self.sources_listbox.insert(tk.END, f"{source.get_icon()} {source.display_name}")
            dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        ttk.Button(button_frame, text="Add", command=add_url, width=12).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=12).pack(side="left", padx=5)

        url_entry.bind('<Return>', lambda e: add_url())

    def remove_source(self):
        """Remove selected source."""
        selection = self.sources_listbox.curselection()
        if selection:
            index = selection[0]
            self.sources_listbox.delete(index)
            del self.sources[index]

    def clear_sources(self):
        """Clear all sources."""
        self.sources_listbox.delete(0, tk.END)
        self.sources.clear()

    # =========================================================================
    # Form Validation
    # =========================================================================

    def validate_form(self):
        """Validate form and enable/disable generate button."""
        title = self.title_var.get().strip()
        filename = self.filename_var.get().strip()
        description = self.description_text.get('1.0', tk.END).strip()

        # Check required fields
        has_title = bool(title)
        has_filename = bool(filename) and validate_slug(filename)
        has_description = bool(description)

        # Update filename validation label
        if filename and not validate_slug(filename):
            self.filename_validation_label.config(
                text="✗ Invalid format (use lowercase and hyphens only)",
                foreground='red'
            )
        elif filename:
            self.filename_validation_label.config(
                text="✓ Valid slug format",
                foreground='green'
            )
        else:
            self.filename_validation_label.config(
                text="(lowercase, hyphens only: my-feature-name)",
                foreground='gray'
            )

        # Enable/disable generate button
        if has_title and has_filename and has_description:
            self.generate_btn.config(state=tk.NORMAL)
        else:
            self.generate_btn.config(state=tk.DISABLED)

        # Schedule next validation
        self.dialog.after(500, self.validate_form)

    # =========================================================================
    # Enhancement Generation
    # =========================================================================

    def generate_enhancement(self):
        """Generate enhancement using Product Analyst agent."""
        # Gather form data
        title = self.title_var.get().strip()
        filename = self.filename_var.get().strip()
        directory = self.directory_var.get().strip()
        description = self.description_text.get('1.0', tk.END).strip()

        # Build context document with all sources
        context_content = self.build_generation_context(title, description)

        try:
            import shutil

            # Use staging directory within enhancements
            staging_dir = self.queue.project_root / "enhancements" / ".staging" / filename

            # Clean up any previous staging for this enhancement
            if staging_dir.exists():
                shutil.rmtree(staging_dir)

            staging_dir.mkdir(parents=True, exist_ok=True)

            # Write context file
            context_file = staging_dir / f"{filename}.md"
            context_file.write_text(context_content, encoding='utf-8')

            # Show working dialog
            working = WorkingDialog(
                self.dialog,
                message="Generating Enhancement",
                estimated_time="30-60 seconds"
            )
            working.show()
            self.dialog.update()

            # Define success handler
            def on_success(result_dir):
                """Handle successful agent execution."""
                try:
                    # Agent writes to: staging_dir/product-analyst/required_output/output.md
                    output_file = staging_dir / "product-analyst" / "required_output" / "output.md"

                    if not output_file.exists():
                        # Try to find output in required_output directory
                        required_output_dir = staging_dir / "product-analyst" / "required_output"
                        if required_output_dir.exists():
                            output_file = PathUtils.find_output_file(required_output_dir)
                        else:
                            raise FileNotFoundError(f"No output found in {staging_dir / 'product-analyst'}")

                    # Read generated content
                    content = output_file.read_text(encoding='utf-8')

                    # Close working dialog
                    working.close()

                    # Show preview dialog
                    self.show_preview(content, title, filename, directory, staging_dir)

                except Exception as e:
                    working.close()
                    # Cleanup staging on error
                    if staging_dir.exists():
                        shutil.rmtree(staging_dir, ignore_errors=True)
                    messagebox.showerror(
                        "Error",
                        f"Failed to read agent output:\n\n{e}"
                    )

            # Define error handler
            def on_error(error):
                """Handle agent execution error."""
                working.close()
                # Cleanup staging on error
                if staging_dir.exists():
                    shutil.rmtree(staging_dir, ignore_errors=True)
                messagebox.showerror(
                    "Generation Error",
                    f"Failed to generate enhancement:\n\n{error}"
                )

            # Run agent asynchronously
            self.queue.run_agent_async(
                agent_name="product-analyst",
                input_file=context_file,
                output_dir=staging_dir,
                task_description=f"Generate enhancement spec: {title}",
                on_success=on_success,
                on_error=on_error
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to prepare enhancement generation:\n\n{e}"
            )

    def on_generation_complete(self, content: str, title: str, filename: str, directory: str):
        """Handle successful generation."""
        self.show_preview(content, title, filename, directory)

    def on_generation_error(self, error: Exception):
        """Handle generation error."""
        messagebox.showerror("Generation Error", f"Failed to generate enhancement:\n\n{error}")

    def build_generation_context(self, title: str, description: str) -> str:
        """Build context for Claude API including all sources."""
        context_parts = [
            f"Enhancement Title: {title}",
            f"\nDescription: {description}"
        ]

        if self.sources:
            context_parts.append("\n\nReference Documents:")

            for source in self.sources:
                try:
                    if source.type == SourceType.FILE:
                        # Read local file
                        path = Path(source.value)
                        if path.exists() and path.stat().st_size < WebUtils.MAX_CONTENT_LENGTH:
                            with open(path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if len(content) > WebUtils.TRUNCATE_THRESHOLD:
                                    content = content[:WebUtils.TRUNCATE_THRESHOLD] + "\n...[truncated]"
                                context_parts.append(f"\n--- {source.display_name} ---")
                                context_parts.append(content)

                    elif source.type == SourceType.GITHUB_ISSUE:
                        # Fetch GitHub issue content using WebUtils
                        issue_title, body = WebUtils.fetch_github_issue(source.value)
                        content = WebUtils.format_github_issue_content(issue_title, body)
                        if len(content) > WebUtils.TRUNCATE_THRESHOLD:
                            content = content[:WebUtils.TRUNCATE_THRESHOLD] + "\n...[truncated]"
                        context_parts.append(f"\n--- {source.display_name} ---")
                        context_parts.append(content)

                    elif source.type == SourceType.WEB_URL:
                        # Fetch web page content using WebUtils (already truncates internally)
                        content = WebUtils.fetch_web_page(source.value)
                        context_parts.append(f"\n--- {source.display_name} ---")
                        context_parts.append(content)

                except Exception as e:
                    # Log error but continue with other sources
                    print(f"Could not fetch source {source.display_name}: {e}")
                    context_parts.append(f"\n--- {source.display_name} (failed to fetch) ---")

        return "\n".join(context_parts)

    def show_preview(self, content: str, title: str, filename: str, directory: str, staging_dir: Path):
        """
        Show preview dialog for generated enhancement.

        Args:
            content: Generated enhancement content
            title: Enhancement title
            filename: Enhancement filename (slug)
            directory: Final output directory
            staging_dir: Staging directory to cleanup
        """
        from .enhancement_preview import EnhancementPreviewDialog

        preview_dialog = EnhancementPreviewDialog(
            parent=self.dialog,
            queue_interface=self.queue,
            settings=self.settings,
            content=content,
            title=title,
            filename=filename,
            output_directory=directory,
            staging_dir=staging_dir
        )

        # Check result after preview dialog closes
        if preview_dialog.result == "REGENERATE":
            # User clicked regenerate - run generation again
            self.generate_enhancement()
        elif preview_dialog.result:
            # User saved - close creation dialog and return saved file path
            self.close(result=preview_dialog.result)