"""
Claude Working Dialog - Minimal borderless working indicator.
Shows spinner and whimsical working words in a single line.
"""

import tkinter as tk
import random


class WorkingDialog:
    """Minimal animated working indicator - borderless, single line."""

    # Unicode spinner frames (braille patterns)
    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    # Claude's whimsical working words
    WORKING_WORDS = [
        "Claudeifying", "Bedazzling", "Cogitating", "Pondering", "Ruminating",
        "Contemplating", "Synthesizing", "Analyzing", "Processing", "Computing",
        "Brainstorming", "Ideating", "Conceptualizing", "Envisioning", "Imagining",
        "Innovating", "Designing", "Crafting", "Composing", "Formulating",
        "Tokenizing", "Embedding", "Inferring", "Predicting", "Modeling",
        "Optimizing", "Calibrating", "Fine-tuning", "Training", "Learning",
        "Sprinkling magic", "Weaving spells", "Conjuring", "Enchanting", "Transmuting",
        "Alchemizing", "Mystifying", "Hexing (nicely)", "Bewitching", "Sorcerizing",
        "Architecting", "Engineering", "Constructing", "Assembling", "Fabricating",
        "Manufacturing", "Producing", "Generating", "Creating", "Building",
        "Deliberating", "Meditating", "Reflecting", "Considering", "Evaluating",
        "Examining", "Studying", "Investigating", "Researching", "Exploring",
        "Drafting", "Authoring", "Penning", "Scribing", "Documenting",
        "Chronicling", "Recording", "Transcribing", "Noting", "Inscribing",
        "Organizing", "Structuring", "Arranging", "Categorizing", "Sorting",
        "Classifying", "Ordering", "Systematizing", "Coordinating", "Orchestrating",
        "Refining", "Polishing", "Perfecting", "Enhancing", "Improving",
        "Upgrading", "Elevating", "Enriching", "Beautifying", "Optimizing",
        "Compiling", "Parsing", "Rendering", "Transpiling", "Minifying",
        "Bundling", "Deploying", "Initializing", "Bootstrapping", "Instantiating",
        "Pixel-pushing", "Bit-twiddling", "Quantum-leaping", "Neural-netting",
        "Cyber-spacing", "Matrix-diving",
    ]

    def __init__(self, parent, message="Generating", estimated_time="15-30 seconds"):
        """Initialize the working dialog.

        Args:
            parent: Parent window
            message: Not displayed (kept for backward compatibility)
            estimated_time: Not displayed (kept for backward compatibility)
        """
        self.parent = parent
        self.dialog = None
        self.spinner_index = 0
        self.current_word = random.choice(self.WORKING_WORDS)
        self.spinner_id = None
        self.word_id = None

    def show(self):
        """Show the minimal working dialog and start animations."""
        if self.dialog:
            return

        self.dialog = tk.Toplevel(self.parent)

        # Remove window decorations - no title bar or buttons
        self.dialog.overrideredirect(True)

        # Small size - single line
        self.dialog.geometry("240x60")

        # Stay on top of other windows
        self.dialog.attributes('-topmost', True)

        # White background with subtle gray border
        self.dialog.configure(bg='#FFFFFF', highlightbackground='#CCCCCC', highlightthickness=1)

        self.center_on_parent()
        self.build_ui()
        self.start_animation()

    def center_on_parent(self):
        """Center dialog on parent window."""
        if not self.dialog:
            return

        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width // 2) - 175  # Half of 350
        y = parent_y + (parent_height // 2) - 30  # Half of 60

        self.dialog.geometry(f"+{x}+{y}")

    def build_ui(self):
        """Build minimal UI - just spinner and text on one line."""
        # Main frame
        main_frame = tk.Frame(self.dialog, bg='#FFFFFF', padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)

        # Horizontal layout
        content_frame = tk.Frame(main_frame, bg='#FFFFFF')
        content_frame.pack(expand=True)

        # Spinner (left)
        self.spinner_label = tk.Label(
            content_frame,
            text="⠋",
            font=('Arial', 20),
            foreground='#6366f1',
            bg='#FFFFFF'
        )
        self.spinner_label.pack(side="left", padx=(0, 10))

        # Working word (right)
        self.working_label = tk.Label(
            content_frame,
            text=f"{self.current_word}...",
            font=('Arial', 11, 'bold'),
            foreground='#6366f1',
            bg='#FFFFFF'
        )
        self.working_label.pack(side="left")

    def start_animation(self):
        """Start both animations."""
        self.animate_spinner()
        self.animate_word()

    def animate_spinner(self):
        """Animate the spinner character."""
        if not self.dialog or not self.dialog.winfo_exists():
            return

        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_FRAMES)
        self.spinner_label.config(text=self.SPINNER_FRAMES[self.spinner_index])

        self.spinner_id = self.dialog.after(80, self.animate_spinner)

    def animate_word(self):
        """Change the working word every 10 seconds."""
        if not self.dialog or not self.dialog.winfo_exists():
            return

        new_word = random.choice(self.WORKING_WORDS)
        while new_word == self.current_word and len(self.WORKING_WORDS) > 1:
            new_word = random.choice(self.WORKING_WORDS)

        self.current_word = new_word
        self.working_label.config(text=f"{self.current_word}...")

        self.word_id = self.dialog.after(10000, self.animate_word)

    def stop_animation(self):
        """Stop all animations."""
        if self.spinner_id:
            self.dialog.after_cancel(self.spinner_id)
            self.spinner_id = None
        if self.word_id:
            self.dialog.after_cancel(self.word_id)
            self.word_id = None

    def close(self):
        """Close the dialog."""
        self.stop_animation()
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()
            self.dialog = None