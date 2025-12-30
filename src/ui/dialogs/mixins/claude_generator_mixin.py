"""
Mixin for dialogs that generate content with Claude API.
Combines BaseDialog with threaded API calling and working dialog.
"""

import threading
from typing import Optional, Callable
from tkinter import messagebox

from ..working import  WorkingDialog
from ...utils.claude_api_client import ClaudeAPIClient


class ClaudeGeneratorMixin:
    """
    Mixin for dialogs that call Claude API to generate content.

    Provides:
    - Threaded API calls (non-blocking UI)
    - Working dialog with animation
    - Success/error callback handling
    - API client management

    Requirements:
    - Class must have self.dialog (Toplevel window)
    - Class must have self.settings (Settings object)

    Usage:
        class MyDialog(BaseDialog, ClaudeGeneratorMixin):
            def __init__(self, parent, settings):
                BaseDialog.__init__(self, parent, "Title", 600, 400)
                ClaudeGeneratorMixin.__init__(self, settings)

            def generate_something(self):
                self.call_claude_async(
                    context="Generate something cool",
                    system_prompt="You are an expert...",
                    on_success=self.on_generated,
                    on_error=self.on_error
                )

            def on_generated(self, content):
                print(f"Got: {content}")
    """

    def __init__(self, settings):
        """
        Initialize the mixin.

        Args:
            settings: Settings object
        """
        self.settings = settings
        self.api_client = ClaudeAPIClient(settings)
        self.working_dialog = None

    def call_claude_async(self,
                          context: str,
                          system_prompt: Optional[str] = None,
                          message: str = "Generating",
                          estimate: str = "30-60 seconds",
                          timeout: Optional[int] = None,
                          on_success: Optional[Callable[[str], None]] = None,
                          on_error: Optional[Callable[[Exception], None]] = None):
        """
        Call Claude API asynchronously with working dialog.

        Args:
            context: User message/prompt
            system_prompt: Optional system prompt
            message: Message for working dialog
            estimate: Time estimate for working dialog
            timeout: API timeout in seconds (uses configured timeout if None)
            on_success: Callback called with result on success
            on_error: Callback called with exception on error
        """
        # Check if API is configured
        if not self.api_client.is_configured():
            messagebox.showwarning(
                "No API Key",
                "Claude API key not configured.\n\n"
                "Go to Settings > Claude Settings..."
            )
            return

        # Show working dialog
        self.working_dialog = WorkingDialog(self.dialog, message, estimate)
        self.working_dialog.show()

        # Run API call in background thread
        def api_thread():
            try:
                result = self.api_client.call(context, system_prompt, timeout)
                # Schedule success callback on UI thread (use self.dialog not working_dialog!)
                self.dialog.after(0, lambda: self._handle_success(result, on_success))
            except Exception as error:
                # Schedule error callback on UI thread
                self.dialog.after(0, lambda err=error: self._handle_error(err, on_error))

        thread = threading.Thread(target=api_thread, daemon=True)
        thread.start()

    def _handle_success(self, result: str, callback: Optional[Callable]):
        """Handle successful API call (runs on UI thread)."""
        if self.working_dialog:
            self.working_dialog.close()
            self.working_dialog = None

        if callback:
            callback(result)

    def _handle_error(self, error: Exception, callback: Optional[Callable]):
        """Handle API call error (runs on UI thread)."""
        if self.working_dialog:
            self.working_dialog.close()
            self.working_dialog = None

        if callback:
            callback(error)
        else:
            # Default error handling
            messagebox.showerror(
                "API Error",
                f"Failed to generate content:\n\n{error}"
            )