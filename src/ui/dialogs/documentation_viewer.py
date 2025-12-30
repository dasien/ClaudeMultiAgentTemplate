"""
Documentation viewer dialog with markdown rendering.
"""

import re
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional

from .base_dialog import BaseDialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class DocumentationViewerDialog(BaseDialog):
    """
    Dialog for viewing documentation files with markdown rendering.

    Features:
    - Document list sidebar
    - Markdown rendering with:
      - Headings (h1-h4)
      - Bold and italic text
      - Code blocks and inline code
      - Bullet and numbered lists
      - Images (if PIL available)
      - Links (clickable)
    """

    def __init__(self, parent, docs_dir: Optional[Path] = None):
        self.docs_dir = docs_dir or Path(__file__).parent.parent.parent.parent / "docs"
        self.doc_files: list[Path] = []
        self.current_doc: Optional[Path] = None
        self.images: list = []  # Keep references to prevent garbage collection
        self.anchors: dict[str, str] = {}  # anchor_id -> text position index
        self.link_counter = 0  # For unique link tag names

        super().__init__(parent, "Documentation", 1000, 700, resizable=True)
        self.build_ui()
        self.load_doc_list()
        # Don't call show() - documentation viewer doesn't return results

    def build_ui(self):
        """Build the documentation viewer UI."""
        # Main container with PanedWindow for resizable split
        paned = ttk.PanedWindow(self.dialog, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Document list
        left_frame = ttk.Frame(paned, width=200)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Documents", font=('Arial', 11, 'bold')).pack(
            anchor="w", padx=5, pady=5
        )

        # Document listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        list_scroll = ttk.Scrollbar(list_frame)
        list_scroll.pack(side="right", fill="y")

        self.doc_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=list_scroll.set,
            font=('Arial', 10),
            selectmode="single",
            activestyle="dotbox"
        )
        self.doc_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=self.doc_listbox.yview)

        self.doc_listbox.bind('<<ListboxSelect>>', self.on_doc_select)

        # Right panel - Document content
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=4)

        # Title label
        self.title_label = ttk.Label(
            right_frame,
            text="Select a document",
            font=('Arial', 14, 'bold')
        )
        self.title_label.pack(anchor="w", padx=10, pady=(10, 5))

        ttk.Separator(right_frame, orient="horizontal").pack(fill="x", padx=10)

        # Content area with scrollbar
        content_frame = ttk.Frame(right_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Vertical scrollbar
        y_scroll = ttk.Scrollbar(content_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        # Horizontal scrollbar
        x_scroll = ttk.Scrollbar(content_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        # Text widget for content
        self.content_text = tk.Text(
            content_frame,
            wrap="word",
            font=('Arial', 11),
            padx=10,
            pady=10,
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            state="disabled",
            cursor="arrow"
        )
        self.content_text.pack(side="left", fill="both", expand=True)

        y_scroll.config(command=self.content_text.yview)
        x_scroll.config(command=self.content_text.xview)

        # Configure text tags for markdown styling
        self._configure_tags()

        # Close button
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)

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
            background='#f0f0f0',
            relief="solid",
            borderwidth=1
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

        # Horizontal rule
        self.content_text.tag_configure(
            "hr",
            font=('Arial', 1),
            spacing1=10,
            spacing3=10
        )

    def load_doc_list(self):
        """Load list of documentation files."""
        self.doc_files = []
        self.doc_listbox.delete(0, tk.END)

        if not self.docs_dir.exists():
            self.doc_listbox.insert(tk.END, "(No docs folder found)")
            return

        # Find all markdown files
        md_files = sorted(self.docs_dir.glob("*.md"))

        # Prioritize certain files
        priority_files = ["README.md", "QUICKSTART.md", "USER_GUIDE.md"]
        prioritized = []
        others = []

        for f in md_files:
            if f.name in priority_files:
                prioritized.append(f)
            else:
                others.append(f)

        # Sort prioritized by the priority order
        prioritized.sort(key=lambda f: priority_files.index(f.name) if f.name in priority_files else 999)

        self.doc_files = prioritized + others

        for doc_file in self.doc_files:
            # Display name without .md extension
            display_name = doc_file.stem.replace("_", " ")
            self.doc_listbox.insert(tk.END, display_name)

        # Select first item if available
        if self.doc_files:
            self.doc_listbox.selection_set(0)
            self.load_document(self.doc_files[0])

    def on_doc_select(self, event):
        """Handle document selection."""
        selection = self.doc_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.doc_files):
                self.load_document(self.doc_files[index])

    def load_document(self, doc_path: Path):
        """Load and render a markdown document."""
        self.current_doc = doc_path
        self.images = []  # Clear image references
        self.anchors = {}  # Clear anchors
        self.link_counter = 0  # Reset link counter

        # Update title
        self.title_label.config(text=doc_path.stem.replace("_", " "))

        # Read content
        try:
            content = doc_path.read_text(encoding='utf-8')
        except Exception as e:
            content = f"Error loading document: {e}"

        # Render markdown
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
            elif line.startswith('!['):
                # Image
                self._render_image(line)
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
        """Insert a heading and create an anchor for it."""
        # Create anchor ID from heading text (lowercase, replace spaces with hyphens)
        anchor_id = re.sub(r'[^\w\s-]', '', text.lower())
        anchor_id = re.sub(r'[\s]+', '-', anchor_id)

        # Get current position BEFORE inserting (this is where the heading will be)
        current_pos = self.content_text.index(tk.END + "-1c")

        # Store the position for this anchor
        self.anchors[anchor_id] = current_pos

        # Insert the heading text
        self.content_text.insert(tk.END, text, tag)

        # Add back-to-top link for h2 and h3 headings (not h1 or h4)
        if tag in ("h2") and "table-of-contents" in self.anchors:
            back_tag = self._create_link_tag("#table-of-contents")
            self.content_text.insert(tk.END, "  ")
            self.content_text.insert(tk.END, "[top]", back_tag)

        self.content_text.insert(tk.END, '\n')

    def _create_link_tag(self, url: str) -> str:
        """Create a unique tag for a clickable link."""
        tag_name = f"link_{self.link_counter}"
        self.link_counter += 1

        # Configure the tag
        self.content_text.tag_configure(
            tag_name,
            foreground='#0066cc',
            underline=True
        )

        # Bind click and hover events
        self.content_text.tag_bind(tag_name, "<Button-1>",
            lambda e, u=url: self._on_link_click(u))
        self.content_text.tag_bind(tag_name, "<Enter>",
            lambda e: self.content_text.config(cursor="hand2"))
        self.content_text.tag_bind(tag_name, "<Leave>",
            lambda e: self.content_text.config(cursor="arrow"))

        return tag_name

    def _on_link_click(self, url: str):
        """Handle link click - navigate to anchor or load document."""
        if url.startswith('#'):
            # Internal anchor link
            anchor_id = url[1:]  # Remove the #
            if anchor_id in self.anchors:
                position = self.anchors[anchor_id]
                self.content_text.see(position)
        elif url.endswith('.md'):
            # Link to another document
            doc_name = url.replace('.md', '')
            for i, doc_file in enumerate(self.doc_files):
                if doc_file.stem == doc_name or doc_file.name == url:
                    self.doc_listbox.selection_clear(0, tk.END)
                    self.doc_listbox.selection_set(i)
                    self.doc_listbox.see(i)
                    self.load_document(doc_file)
                    break

    def _render_inline(self, text: str, base_tag: str = None):
        """Render inline markdown elements (bold, italic, code, links)."""
        # Process the line for inline elements
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
                link_url = match.group(2)
                link_tag = self._create_link_tag(link_url)
                tags = (link_tag, base_tag) if base_tag else (link_tag,)
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

    def _render_image(self, line: str):
        """Render an image from markdown syntax."""
        match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if not match:
            self._insert_text(line + '\n')
            return

        alt_text = match.group(1)
        image_path = match.group(2)

        if not PIL_AVAILABLE:
            self._insert_text(f'[Image: {alt_text or image_path}]\n', "italic")
            return

        # Resolve image path relative to current document
        if self.current_doc:
            if image_path.startswith(('http://', 'https://')):
                self._insert_text(f'[Image: {alt_text or image_path}]\n', "italic")
                return

            # Try relative to doc, then relative to docs_dir
            img_path = self.current_doc.parent / image_path
            if not img_path.exists():
                img_path = self.docs_dir / image_path

            if img_path.exists():
                try:
                    img = Image.open(img_path)

                    # Resize if too large (max width 600)
                    max_width = 600
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_size = (max_width, int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)

                    photo = ImageTk.PhotoImage(img)
                    self.images.append(photo)  # Keep reference

                    self.content_text.image_create(tk.END, image=photo)
                    self._insert_text('\n')

                    if alt_text:
                        self._insert_text(f'{alt_text}\n', "italic")
                    return
                except Exception as e:
                    pass

        # Fallback: show alt text
        self._insert_text(f'[Image: {alt_text or image_path}]\n', "italic")
