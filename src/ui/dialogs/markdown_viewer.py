"""
Markdown viewer dialog for displaying .md files in-app.
"""

import re
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional

from .base_dialog import BaseDialog


class MarkdownViewerDialog(BaseDialog):
    """
    Dialog for viewing markdown files with basic rendering.

    Features:
    - Headings (h1-h4)
    - Bold and italic text
    - Code blocks and inline code
    - Bullet and numbered lists
    - Links (displayed, not clickable)
    """

    def __init__(self, parent, file_path: Path, title: Optional[str] = None):
        """
        Initialize the markdown viewer.

        Args:
            parent: Parent window
            file_path: Path to the markdown file to display
            title: Optional title for the dialog (defaults to filename)
        """
        self.file_path = Path(file_path)
        self.display_title = title or self.file_path.name

        super().__init__(parent, self.display_title, 900, 700, resizable=True)
        self.build_ui()
        self.load_content()

    def build_ui(self):
        """Build the markdown viewer UI."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Title label
        self.title_label = ttk.Label(
            main_frame,
            text=self.display_title,
            font=('Arial', 14, 'bold')
        )
        self.title_label.pack(anchor="w", pady=(0, 5))

        # File path label
        ttk.Label(
            main_frame,
            text=str(self.file_path),
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor="w", pady=(0, 5))

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=5)

        # Content area with scrollbar
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=10)

        # Vertical scrollbar
        y_scroll = ttk.Scrollbar(content_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        # Text widget for content
        self.content_text = tk.Text(
            content_frame,
            wrap="word",
            font=('Arial', 11),
            padx=10,
            pady=10,
            yscrollcommand=y_scroll.set,
            state="disabled",
            cursor="arrow"
        )
        self.content_text.pack(side="left", fill="both", expand=True)

        y_scroll.config(command=self.content_text.yview)

        # Configure text tags for markdown styling
        self._configure_tags()

        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=15
        ).pack(side="right")

    def _configure_tags(self):
        """Configure text tags for markdown rendering."""
        # Headings
        self.content_text.tag_configure("h1", font=('Arial', 18, 'bold'), spacing1=15, spacing3=10)
        self.content_text.tag_configure("h2", font=('Arial', 16, 'bold'), spacing1=12, spacing3=8)
        self.content_text.tag_configure("h3", font=('Arial', 14, 'bold'), spacing1=10, spacing3=6)
        self.content_text.tag_configure("h4", font=('Arial', 12, 'bold'), spacing1=8, spacing3=4)

        # Text formatting
        self.content_text.tag_configure("bold", font=('Arial', 11, 'bold'))
        self.content_text.tag_configure("italic", font=('Arial', 11, 'italic'))
        self.content_text.tag_configure("bold_italic", font=('Arial', 11, 'bold italic'))

        # Code
        self.content_text.tag_configure(
            "code",
            font=('Courier', 10),
            background='#f0f0f0'
        )
        self.content_text.tag_configure(
            "code_block",
            font=('Courier', 10),
            background='#f5f5f5',
            lmargin1=20,
            lmargin2=20,
            spacing1=5,
            spacing3=5
        )

        # Lists
        self.content_text.tag_configure("bullet", lmargin1=20, lmargin2=35)
        self.content_text.tag_configure("numbered", lmargin1=20, lmargin2=35)

        # Blockquote
        self.content_text.tag_configure(
            "blockquote",
            lmargin1=20,
            lmargin2=20,
            foreground='#666666',
            font=('Arial', 11, 'italic')
        )

        # Link (displayed as blue text)
        self.content_text.tag_configure(
            "link",
            foreground='#0066cc',
            underline=True
        )

        # Horizontal rule
        self.content_text.tag_configure(
            "hr",
            font=('Arial', 1),
            spacing1=10,
            spacing3=10
        )

    def load_content(self):
        """Load and render the markdown file."""
        try:
            content = self.file_path.read_text(encoding='utf-8')
        except Exception as e:
            content = f"Error loading file: {e}"

        self._render_markdown(content)

    def _render_markdown(self, content: str):
        """Render markdown content to the text widget."""
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", tk.END)

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
                    self._insert_text(code_text + '\n', "code_block")
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
                # Empty line
                self._insert_text('\n')
            elif line.startswith('####'):
                self._insert_heading(line[4:].strip(), "h4")
            elif line.startswith('###'):
                self._insert_heading(line[3:].strip(), "h3")
            elif line.startswith('##'):
                self._insert_heading(line[2:].strip(), "h2")
            elif line.startswith('#'):
                self._insert_heading(line[1:].strip(), "h1")
            elif line.startswith('> '):
                self._insert_text(line[2:] + '\n', "blockquote")
            elif line.startswith('---') or line.startswith('***') or line.startswith('___'):
                self._insert_text('─' * 60 + '\n', "hr")
            elif re.match(r'^(\s*)[-*+]\s', line):
                # Bullet list
                match = re.match(r'^(\s*)[-*+]\s(.*)$', line)
                if match:
                    indent = len(match.group(1)) // 2
                    bullet = '  ' * indent + '• '
                    self._render_inline(bullet + match.group(2) + '\n', "bullet")
            elif re.match(r'^(\s*)\d+\.\s', line):
                # Numbered list
                match = re.match(r'^(\s*)(\d+)\.\s(.*)$', line)
                if match:
                    indent = len(match.group(1)) // 2
                    num = '  ' * indent + match.group(2) + '. '
                    self._render_inline(num + match.group(3) + '\n', "numbered")
            else:
                # Regular paragraph
                self._render_inline(line + '\n')

            i += 1

        self.content_text.config(state="disabled")

    def _insert_text(self, text: str, tag: str = None):
        """Insert text with optional tag."""
        if tag:
            self.content_text.insert(tk.END, text, tag)
        else:
            self.content_text.insert(tk.END, text)

    def _insert_heading(self, text: str, tag: str):
        """Insert a heading."""
        self.content_text.insert(tk.END, text + '\n', tag)

    def _render_inline(self, text: str, base_tag: str = None):
        """Render inline markdown elements (bold, italic, code, links)."""
        pos = 0

        # Patterns for inline elements
        patterns = [
            (r'\*\*\*(.+?)\*\*\*', 'bold_italic'),  # ***bold italic***
            (r'\*\*(.+?)\*\*', 'bold'),  # **bold**
            (r'__(.+?)__', 'bold'),  # __bold__
            (r'\*(.+?)\*', 'italic'),  # *italic*
            (r'_(.+?)_', 'italic'),  # _italic_
            (r'`([^`]+)`', 'code'),  # `code`
            (r'\[([^\]]+)\]\(([^)]+)\)', 'link'),  # [text](url)
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
                self.content_text.insert(tk.END, plain_text, tags)

            # Insert the matched content
            if tag == 'link':
                link_text = match.group(1)
                # Just display the link text with link styling
                tags = ('link', base_tag) if base_tag else ('link',)
                self.content_text.insert(tk.END, link_text, tags)
            else:
                content = match.group(1)
                tags = (tag, base_tag) if base_tag else (tag,)
                self.content_text.insert(tk.END, content, tags)

            last_end = end

        # Insert remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            tags = (base_tag,) if base_tag else ()
            self.content_text.insert(tk.END, remaining, tags)