---
enhancement: claude-md-feature-plan
agent: architect
task_id: task_1767463062_51800
timestamp: 2026-01-03T23:15:00Z
status: READY_FOR_IMPLEMENTATION
---

# Implementation Plan: CLAUDE.md Management Feature

## Executive Summary

This implementation plan defines the technical architecture for adding CLAUDE.md file management capabilities to the CMAT Desktop UI. The feature enables users to create, reference, edit, and monitor project-specific Claude Code context files through a clean, integrated UI experience.

**Key Architectural Decisions:**
1. **Agent Invocation**: Use existing `TaskService.execute_direct()` method for one-off agent execution
2. **Menu Location**: Create new "Project" top-level menu for project-level features
3. **Editor Approach**: Use system default editor via platform-specific commands
4. **Status Updates**: On-demand status checking triggered by UI actions
5. **Dialog Pattern**: Follow existing `BaseDialog` + `ClaudeGeneratorMixin` pattern

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         MainView (main.py)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Menu Bar                                                  │  │
│  │  - Project Menu (NEW)                                     │  │
│  │    └─ CLAUDE.md submenu                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Connection Header                                         │  │
│  │  - Project path + CLAUDE.md status indicator (ENHANCED)   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ invokes dialogs
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ClaudeMdDialog (NEW)                           │
│  - Create flow: Invoke agent → Review → Save                    │
│  - Uses ClaudeGeneratorMixin for async execution               │
│  - Uses WorkingDialog for progress indication                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ calls backend
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CMATInterface (ENHANCED)                     │
│  - run_claude_md_agent() method (NEW)                          │
│  - check_claude_md_status() method (NEW)                       │
│  - open_claude_md_in_editor() method (NEW)                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ uses existing service
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              TaskService.execute_direct() (EXISTING)            │
│  - Executes claude-md-creator agent                            │
│  - Provides tools access (Read, Glob, Grep, Bash, Write)       │
│  - Returns ExecutionResult with status and output              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ invokes
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│          claude-md-creator agent (EXISTING)                     │
│  - Analyzes project structure                                  │
│  - Generates CLAUDE.md content                                 │
│  - Writes to project root                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. MainView (src/ui/main.py)
**Changes Required:**
- Add "Project" top-level menu with CLAUDE.md submenu
- Add menu command handlers (create, reference, edit)
- Enhance connection header to show CLAUDE.md status
- Update status display after CLAUDE.md operations

**New Methods:**
```python
def build_project_menu(self):
    """Build new Project menu with CLAUDE.md options."""

def show_create_claude_md(self):
    """Handler for Create CLAUDE.md menu item."""

def show_reference_claude_md(self):
    """Handler for Reference Existing menu item."""

def show_edit_claude_md(self):
    """Handler for Edit CLAUDE.md menu item."""

def update_claude_md_status(self):
    """Update CLAUDE.md status indicator in header."""
```

#### 2. ClaudeMdDialog (src/ui/dialogs/claude_md_manager.py) - NEW FILE
**Purpose:** Dialog for creating CLAUDE.md via agent with review/approval flow

**Inherits From:**
- `BaseDialog` - Standard dialog behavior
- `ClaudeGeneratorMixin` - Async agent execution

**Methods:**
```python
def __init__(self, parent, queue_interface, settings):
    """Initialize dialog."""

def build_ui(self):
    """Build dialog UI (working message only)."""

def start_generation(self):
    """Start agent execution in background thread."""

def on_agent_complete(self, result: ExecutionResult):
    """Handle agent completion - show review dialog."""

def on_agent_error(self, error: Exception):
    """Handle agent failure - show error dialog."""

def show_review_dialog(self, content: str):
    """Show generated CLAUDE.md for approval."""

def save_claude_md(self, content: str):
    """Save approved CLAUDE.md to project root."""
```

**UI Flow:**
```
1. Dialog opens with "Generating CLAUDE.md..." message
2. Agent executes in background (60-90 seconds)
3. On completion:
   → Show review dialog with generated content
   → User can approve (save) or cancel
4. On approval:
   → Write to {project_root}/CLAUDE.md
   → Show success message
   → Close dialog
```

#### 3. CMATInterface (src/ui/utils/cmat_interface.py) - ENHANCED
**New Methods:**

```python
def run_claude_md_agent(self, callback: Callable[[ExecutionResult], None]) -> None:
    """
    Execute claude-md-creator agent asynchronously.

    Args:
        callback: Function called with ExecutionResult when done

    Uses TaskService.execute_direct() to invoke agent without queue.
    Runs in background thread to avoid blocking UI.
    """

def check_claude_md_status(self) -> dict:
    """
    Check if CLAUDE.md exists in project.

    Returns:
        {
            "exists": bool,
            "path": str | None,
            "size": int,
            "modified": datetime | None
        }
    """

def open_claude_md_in_editor(self) -> bool:
    """
    Open CLAUDE.md in system default editor.

    Returns:
        True if opened successfully, False otherwise

    Platform-specific implementation:
    - macOS: open command
    - Windows: os.startfile()
    - Linux: xdg-open
    """

def copy_file_to_claude_md(self, source_path: str) -> Tuple[bool, str]:
    """
    Copy a file to project root as CLAUDE.md.

    Args:
        source_path: Path to source .md file

    Returns:
        (success: bool, message: str)

    Checks:
    - Source file exists and is readable
    - Target location is writable
    - Warns if file is > 50KB (should be concise)
    """
```

#### 4. TaskService (src/core/services/task_service.py) - NO CHANGES
**Existing Method Used:** `execute_direct()`

This method already provides exactly what we need:
- Executes agent without task queue
- Provides full tools access
- Returns ExecutionResult with status
- Logs to `.claude/logs/`

**Usage Pattern:**
```python
result = self.tasks.execute_direct(
    agent_name="claude-md-creator",
    input_file=None,  # Agent analyzes project structure
    output_dir=str(self.project_root),
    task_description="Generate CLAUDE.md for project",
    task_type="documentation"
)
```

## Technical Design Decisions

### Decision 1: Agent Invocation Pattern

**Chosen Approach:** Use existing `TaskService.execute_direct()`

**Rationale:**
- Already implemented and tested
- Provides full tools access (Read, Glob, Grep, Bash, Write)
- Handles logging and error capture
- Returns structured ExecutionResult
- No need to create new invocation mechanism

**Alternative Considered:**
- Direct Claude API call via ClaudeGeneratorMixin
- **Rejected:** Would bypass agent's tool access, requiring reimplementation of analysis logic

### Decision 2: Menu Structure

**Chosen Approach:** New "Project" top-level menu

```
Project (NEW)
├── CLAUDE.md ▶
│   ├── Create...
│   ├── Reference Existing...
│   └── Edit              (enabled only if exists)
├── ──────────
└── (room for future project features)
```

**Rationale:**
- Keeps feature discoverable at top level
- Scalable for future project-level features (settings, info, etc.)
- Semantically correct - CLAUDE.md is project configuration
- Doesn't clutter File menu

**Alternative Considered:**
- Submenu under File menu
- **Rejected:** File menu already crowded; project config deserves own space

### Decision 3: Editor Selection

**Chosen Approach:** System default editor

**Implementation:**
```python
import subprocess
import platform

def open_in_system_editor(file_path: str):
    """Open file in system default editor."""
    system = platform.system()

    if system == "Darwin":  # macOS
        subprocess.Popen(["open", file_path])
    elif system == "Windows":
        os.startfile(file_path)
    else:  # Linux/Unix
        subprocess.Popen(["xdg-open", file_path])
```

**Rationale:**
- Simple, platform-native
- Respects user's editor preferences
- No need to build in-app editor
- Users comfortable editing in their chosen environment

**Alternative Considered:**
- In-app text editor widget
- **Rejected:** Scope creep; adds complexity without clear user benefit

### Decision 4: Status Update Mechanism

**Chosen Approach:** On-demand status checks triggered by UI actions

**When Status Updates:**
1. After successful connection to project
2. After CLAUDE.md create action completes
3. After CLAUDE.md reference action completes
4. When Project menu is opened (check if file exists to enable/disable Edit)

**Rationale:**
- Simple, no polling overhead
- Status changes are always user-initiated
- File system operations are fast (< 1ms)
- No stale status issues in practice

**Alternative Considered:**
- File system watcher (watchdog library)
- **Rejected:** Overkill for feature scope; adds dependency

### Decision 5: Review/Approval Flow

**Chosen Approach:** Modal dialog with generated content preview

**Flow:**
```
┌─────────────────────────────────────────────────────┐
│  Generated CLAUDE.md                           [×]  │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────┐ │
│ │ # Project: ClaudeMultiAgentTemplate            │ │
│ │                                                 │ │
│ │ Python-based multi-agent task management...    │ │
│ │ ...                                             │ │
│ │ (full generated content, scrollable)            │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│                      [Cancel]  [Save to Project]    │
└─────────────────────────────────────────────────────┘
```

**Rationale:**
- User sees what will be saved before committing
- Follows existing pattern (enhancement preview dialog)
- Simple approve/reject flow
- Can cancel if output is not satisfactory

## Data Models

### CLAUDE.md Status Model

```python
@dataclass
class ClaudeMdStatus:
    """Status of CLAUDE.md file in project."""
    exists: bool
    path: Optional[Path] = None
    size_bytes: int = 0
    modified_at: Optional[datetime] = None

    @property
    def is_large(self) -> bool:
        """Check if file exceeds recommended size (50KB)."""
        return self.size_bytes > 50 * 1024

    @property
    def status_text(self) -> str:
        """Human-readable status text."""
        return "Present" if self.exists else "Not configured"
```

## File Structure

### New Files

```
src/ui/dialogs/claude_md_manager.py      # New dialog for CLAUDE.md operations
```

### Modified Files

```
src/ui/main.py                           # Add menu, handlers, status display
src/ui/utils/cmat_interface.py           # Add CLAUDE.md methods
```

### Agent Files (Already Exist)

```
.claude/agents/claude-md-creator-agent.md   # Agent definition (no changes)
templates/.claude/agents/claude-md-creator-agent.md  # Template version
```

## API/Interface Specifications

### CMATInterface CLAUDE.md Methods

```python
class CMATInterface:
    """CMAT backend interface."""

    def run_claude_md_agent(self, callback: Callable[[ExecutionResult], None]) -> None:
        """
        Execute claude-md-creator agent to generate CLAUDE.md.

        Process:
        1. Validates project root is writable
        2. Invokes TaskService.execute_direct() with claude-md-creator agent
        3. Agent analyzes project (uses Read, Glob, Grep, Bash)
        4. Agent generates CLAUDE.md content
        5. Calls callback with ExecutionResult

        Args:
            callback: Function(result: ExecutionResult) called when done

        Runs asynchronously in background thread.
        """

    def check_claude_md_status(self) -> ClaudeMdStatus:
        """
        Check CLAUDE.md file status.

        Returns:
            ClaudeMdStatus with existence, path, size, modification time

        Fast operation (< 1ms), safe to call frequently.
        """

    def open_claude_md_in_editor(self) -> Tuple[bool, str]:
        """
        Open CLAUDE.md in system default editor.

        Returns:
            (success: bool, message: str)

        Raises:
            FileNotFoundError: If CLAUDE.md doesn't exist
        """

    def copy_file_to_claude_md(
        self,
        source_path: str,
        overwrite_existing: bool = False
    ) -> Tuple[bool, str]:
        """
        Copy a markdown file to project root as CLAUDE.md.

        Args:
            source_path: Path to source .md file
            overwrite_existing: If True, overwrite without confirmation

        Returns:
            (success: bool, message: str)

        Validations:
        - Source file exists and is readable
        - Source file is .md extension
        - Target directory is writable
        - Warns if source > 50KB
        """
```

### Dialog Interface

```python
class ClaudeMdDialog(BaseDialog, ClaudeGeneratorMixin):
    """Dialog for creating CLAUDE.md via agent."""

    def __init__(
        self,
        parent: tk.Widget,
        queue_interface: CMATInterface,
        settings: Settings
    ):
        """
        Initialize CLAUDE.md creation dialog.

        Args:
            parent: Parent widget
            queue_interface: Backend interface
            settings: Settings (for Claude API key)
        """
```

## Integration Strategy

### Phase 1: Backend Methods (Foundation)

**Goal:** Implement core backend functionality

**Tasks:**
1. Add `check_claude_md_status()` to CMATInterface
2. Add `open_claude_md_in_editor()` to CMATInterface
3. Add `copy_file_to_claude_md()` to CMATInterface
4. Add unit tests for file operations

**Deliverables:**
- Backend methods working and tested
- Platform-specific editor launching tested

**Integration Points:**
- Uses existing `self.project_root` from CMATInterface
- Uses existing `Path` utilities

### Phase 2: Agent Invocation (Core Feature)

**Goal:** Enable agent-based CLAUDE.md generation

**Tasks:**
1. Add `run_claude_md_agent()` to CMATInterface
2. Wire up `TaskService.execute_direct()` call
3. Add threading for async execution
4. Test agent execution end-to-end

**Deliverables:**
- Agent can be invoked from backend
- Returns ExecutionResult with generated content
- Logs to `.claude/logs/`

**Integration Points:**
- Uses existing `TaskService.execute_direct()` method
- Uses existing `claude-md-creator` agent definition
- Follows existing async execution pattern

### Phase 3: Dialog UI (User Interface)

**Goal:** Build user-facing dialog for create flow

**Tasks:**
1. Create `ClaudeMdDialog` class
2. Implement working dialog with progress
3. Implement review dialog with approval flow
4. Add error handling and user feedback
5. Test dialog flows

**Deliverables:**
- Dialog opens and shows progress
- Review dialog displays generated content
- Save operation writes to project root
- Error cases handled gracefully

**Integration Points:**
- Inherits from `BaseDialog` (existing)
- Uses `ClaudeGeneratorMixin` pattern (existing)
- Uses `WorkingDialog` for progress (existing)

### Phase 4: Menu Integration (Discoverability)

**Goal:** Add menu items and wire up UI

**Tasks:**
1. Add "Project" menu to menu bar
2. Add CLAUDE.md submenu with Create/Reference/Edit
3. Add menu command handlers
4. Implement Edit (system editor launch)
5. Implement Reference (file picker + copy)
6. Update menu states based on connection

**Deliverables:**
- Menu items visible and functional
- Items enabled/disabled appropriately
- All menu actions work end-to-end

**Integration Points:**
- Follows existing menu pattern in `main.py`
- Uses existing connection state management
- Uses existing file picker dialogs

### Phase 5: Status Display (Visibility)

**Goal:** Show CLAUDE.md status in UI

**Tasks:**
1. Enhance connection header with status indicator
2. Update status after CLAUDE.md operations
3. Add visual feedback (icon or text badge)

**Deliverables:**
- Status shows "Present" or "Not configured"
- Updates dynamically after operations
- Visually integrated with existing header

**Integration Points:**
- Modifies existing connection header in `main.py`
- Uses `check_claude_md_status()` backend method

## Error Handling Strategy

### Error Categories

#### 1. Agent Execution Errors

**Scenarios:**
- Claude API timeout
- Claude API rate limit
- Agent fails to generate valid output
- Permission denied writing to project root

**Handling:**
```python
def on_agent_error(self, error: Exception):
    """Handle agent execution failure."""
    if isinstance(error, TimeoutError):
        message = "Agent timed out. Project may be too large.\n\nTry again?"
        if messagebox.askyesno("Timeout", message):
            self.start_generation()  # Retry
    elif "permission" in str(error).lower():
        message = f"Cannot write to project root:\n{self.queue.project_root}\n\nCheck file permissions."
        messagebox.showerror("Permission Denied", message)
    else:
        message = f"Failed to generate CLAUDE.md:\n\n{error}"
        messagebox.showerror("Generation Failed", message)
```

#### 2. File Operation Errors

**Scenarios:**
- Source file doesn't exist
- Target directory not writable
- File too large (> 50KB)
- CLAUDE.md already exists (overwrite confirmation)

**Handling:**
```python
def copy_file_to_claude_md(self, source_path: str) -> Tuple[bool, str]:
    """Copy file with comprehensive error handling."""
    source = Path(source_path)
    target = self.project_root / "CLAUDE.md"

    # Validation
    if not source.exists():
        return (False, f"Source file not found: {source}")

    if not source.suffix == ".md":
        return (False, "Source file must be a .md file")

    # Size warning
    if source.stat().st_size > 50 * 1024:
        response = messagebox.askyesno(
            "Large File Warning",
            f"File is {source.stat().st_size // 1024}KB.\n\n"
            "CLAUDE.md should be concise (< 50KB).\n\n"
            "Continue anyway?"
        )
        if not response:
            return (False, "Cancelled by user")

    # Overwrite confirmation
    if target.exists():
        response = messagebox.askyesno(
            "Overwrite Existing File",
            f"CLAUDE.md already exists.\n\nOverwrite?"
        )
        if not response:
            return (False, "Cancelled by user")

    # Copy operation
    try:
        shutil.copy2(source, target)
        return (True, f"Copied to {target}")
    except PermissionError as e:
        return (False, f"Permission denied: {e}")
    except Exception as e:
        return (False, f"Copy failed: {e}")
```

#### 3. Platform-Specific Errors

**Scenarios:**
- Editor command not found
- Editor fails to launch
- File path contains special characters

**Handling:**
```python
def open_claude_md_in_editor(self) -> Tuple[bool, str]:
    """Open in editor with platform-specific error handling."""
    claude_md = self.project_root / "CLAUDE.md"

    if not claude_md.exists():
        return (False, "CLAUDE.md not found in project")

    try:
        system = platform.system()

        if system == "Darwin":
            subprocess.Popen(["open", str(claude_md)])
        elif system == "Windows":
            os.startfile(str(claude_md))
        else:
            subprocess.Popen(["xdg-open", str(claude_md)])

        return (True, "Opened in system editor")

    except FileNotFoundError:
        return (False, f"Editor command not found for {system}")
    except Exception as e:
        return (False, f"Failed to open editor: {e}")
```

### Error Recovery

**User Actions:**
- **Retry:** Agent timeout → Offer retry button
- **Fix Permissions:** Permission errors → Show path and suggested fix
- **Choose Different File:** File validation errors → Return to file picker
- **Cancel:** Any error → Allow user to cancel operation cleanly

**Logging:**
- All errors logged to `.claude/logs/ui_operations.log`
- Include full stack trace for debugging
- Include user actions taken (retry, cancel)

## Testing Strategy

### Unit Tests

**Test Coverage:**

```python
# test_claude_md_backend.py
class TestClaudeMdBackend:
    def test_check_status_when_exists(self):
        """Status correctly identifies existing CLAUDE.md."""

    def test_check_status_when_missing(self):
        """Status correctly identifies missing CLAUDE.md."""

    def test_copy_file_success(self):
        """File copies successfully to project root."""

    def test_copy_file_overwrite_declined(self):
        """Copy cancelled when user declines overwrite."""

    def test_copy_file_permission_error(self):
        """Copy fails gracefully with permission error."""

    def test_copy_file_large_warning(self):
        """Warning shown for files > 50KB."""

    def test_open_editor_macos(self, mock_platform, mock_popen):
        """Editor opens with 'open' command on macOS."""

    def test_open_editor_windows(self, mock_platform, mock_startfile):
        """Editor opens with os.startfile on Windows."""

    def test_open_editor_linux(self, mock_platform, mock_popen):
        """Editor opens with 'xdg-open' on Linux."""
```

### Integration Tests

**Test Scenarios:**

```python
# test_claude_md_integration.py
class TestClaudeMdIntegration:
    def test_agent_execution_end_to_end(self, temp_project):
        """Agent generates valid CLAUDE.md file."""

    def test_create_review_save_flow(self, temp_project):
        """Full create flow from dialog to saved file."""

    def test_reference_existing_flow(self, temp_project, sample_md):
        """File picker → copy → verify saved."""

    def test_edit_opens_in_editor(self, temp_project):
        """Edit action launches system editor."""

    def test_status_updates_after_create(self, temp_project):
        """Status indicator updates after CLAUDE.md created."""
```

### Manual Test Plan

**Platform Testing:**
- [ ] Test on macOS (Big Sur+)
- [ ] Test on Windows 10/11
- [ ] Test on Ubuntu 20.04+

**Feature Testing:**
1. **Create CLAUDE.md:**
   - [ ] Open dialog from menu
   - [ ] Agent executes and completes
   - [ ] Review dialog shows content
   - [ ] Save writes to project root
   - [ ] Status updates to "Present"

2. **Reference Existing:**
   - [ ] File picker opens filtered to .md
   - [ ] Select valid .md file
   - [ ] Overwrite warning if exists
   - [ ] File copies successfully
   - [ ] Status updates to "Present"

3. **Edit CLAUDE.md:**
   - [ ] Menu item enabled when file exists
   - [ ] Menu item disabled when file missing
   - [ ] Clicking opens system editor
   - [ ] File opens in correct application

4. **Error Handling:**
   - [ ] Agent timeout shows retry option
   - [ ] Permission errors show helpful message
   - [ ] Large file shows warning
   - [ ] Missing file shows error

**Edge Cases:**
- [ ] Project path contains spaces
- [ ] Project path contains unicode characters
- [ ] Read-only project directory
- [ ] Network drive project location
- [ ] Multiple rapid status checks
- [ ] Agent generates empty output
- [ ] Agent generates invalid markdown

## Migration & Compatibility

### Backwards Compatibility

**No Breaking Changes:**
- Feature is purely additive
- Doesn't modify existing workflows
- Doesn't change existing file structures
- Doesn't alter agent definitions

**Compatibility Requirements:**
- Existing projects work without CLAUDE.md
- CLAUDE.md presence is optional, not required
- Projects with manually-created CLAUDE.md work correctly

### Version Requirements

**Dependencies:**
- Python 3.8+ (existing requirement)
- tkinter (existing requirement)
- No new external dependencies

**Agent Requirements:**
- `claude-md-creator` agent must exist in `.claude/agents/`
- Agent definition follows standard format
- Claude API key configured in settings

## Performance Considerations

### Agent Execution Time

**Expected Duration:** 60-90 seconds

**Factors:**
- Project size (number of files to scan)
- Claude API response time (30-60s typical)
- File I/O for reading samples

**Optimization:**
- Agent runs in background thread (UI stays responsive)
- Working dialog shows progress animation
- User can cancel if taking too long (future enhancement)

### UI Responsiveness

**Goals:**
- Menu operations: < 100ms
- Status checks: < 10ms
- File copy: < 100ms
- Editor launch: < 500ms

**Implementation:**
- All file operations are synchronous (fast enough)
- Agent execution is asynchronous (background thread)
- Working dialog prevents UI blocking

### Resource Usage

**Memory:**
- Dialog: ~5MB
- Agent execution: ~50MB (Claude process)
- Total impact: < 60MB

**Disk:**
- CLAUDE.md file: < 50KB (typically 5-15KB)
- Log files: ~10KB per agent execution
- No persistent storage beyond CLAUDE.md file

## Security Considerations

### File System Security

**Path Validation:**
```python
def validate_path_safety(path: Path, project_root: Path) -> bool:
    """Ensure path is safe and within project bounds."""
    try:
        # Resolve symlinks and relative paths
        abs_path = path.resolve()
        abs_root = project_root.resolve()

        # Verify within project (prevent directory traversal)
        abs_path.relative_to(abs_root)
        return True
    except ValueError:
        return False
```

**Write Permissions:**
- Check write permissions before agent invocation
- Fail fast if project root is read-only
- Show clear error message with path

### Agent Input Safety

**Sanitization:**
- Project root path validated before passing to agent
- No user input passed to shell commands
- Agent operates only on project files (no external access)

**Output Validation:**
- Verify agent output is valid markdown
- Check output size (prevent malicious large files)
- Scan for suspicious content patterns

### API Security

**Claude API Key:**
- Stored securely in settings (existing pattern)
- Never logged or displayed
- Used only for agent invocation

## Code Examples

### Example 1: Create CLAUDE.md Handler

```python
# In main.py
def show_create_claude_md(self):
    """Handler for Create CLAUDE.md menu item."""
    if not self.queue:
        messagebox.showwarning(
            "Not Connected",
            "Please connect to a project first."
        )
        return

    # Check if already exists
    status = self.queue.check_claude_md_status()
    if status.exists:
        response = messagebox.askyesno(
            "CLAUDE.md Exists",
            "CLAUDE.md already exists in this project.\n\n"
            "Generate a new one? (This will overwrite the existing file)"
        )
        if not response:
            return

    # Open creation dialog
    from .dialogs.claude_md_manager import ClaudeMdDialog
    ClaudeMdDialog(
        parent=self.root,
        queue_interface=self.queue,
        settings=self.settings,
        on_complete=self.update_claude_md_status
    )
```

### Example 2: Agent Invocation

```python
# In cmat_interface.py
def run_claude_md_agent(self, callback: Callable[[ExecutionResult], None]) -> None:
    """Execute claude-md-creator agent asynchronously."""

    def execute_agent():
        """Run in background thread."""
        try:
            result = self.tasks.execute_direct(
                agent_name="claude-md-creator",
                input_file=None,
                output_dir=str(self.project_root),
                task_description="Generate CLAUDE.md for project",
                task_type="documentation"
            )
            callback(result)
        except Exception as e:
            callback(ExecutionResult(
                success=False,
                status=None,
                exit_code=1,
                output_dir=str(self.project_root),
                log_file="",
                duration_seconds=0
            ))

    thread = threading.Thread(target=execute_agent, daemon=True)
    thread.start()
```

### Example 3: Review Dialog

```python
# In claude_md_manager.py
def show_review_dialog(self, content: str):
    """Show generated content for review."""
    review_dialog = tk.Toplevel(self.dialog)
    review_dialog.title("Review Generated CLAUDE.md")
    review_dialog.geometry("700x600")
    review_dialog.transient(self.dialog)
    review_dialog.grab_set()

    # Content display
    frame = ttk.Frame(review_dialog, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="Review the generated CLAUDE.md:",
        font=('Arial', 11, 'bold')
    ).pack(pady=(0, 10))

    text_frame = ttk.Frame(frame)
    text_frame.pack(fill="both", expand=True, pady=(0, 10))

    text_widget = tk.Text(text_frame, wrap="word", height=25)
    scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)

    text_widget.insert("1.0", content)
    text_widget.configure(state="disabled")

    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Buttons
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x")

    ttk.Button(
        btn_frame,
        text="Cancel",
        command=review_dialog.destroy
    ).pack(side="right", padx=(5, 0))

    ttk.Button(
        btn_frame,
        text="Save to Project",
        command=lambda: self.approve_and_save(content, review_dialog),
        style="Accent.TButton"
    ).pack(side="right")
```

## Implementation Checklist

### Phase 1: Backend Foundation
- [ ] Add `check_claude_md_status()` to CMATInterface
- [ ] Add `open_claude_md_in_editor()` to CMATInterface
- [ ] Add `copy_file_to_claude_md()` to CMATInterface
- [ ] Write unit tests for file operations
- [ ] Test cross-platform editor launching

### Phase 2: Agent Integration
- [ ] Add `run_claude_md_agent()` to CMATInterface
- [ ] Wire up `TaskService.execute_direct()` call
- [ ] Add threading for async execution
- [ ] Test agent execution end-to-end
- [ ] Verify CLAUDE.md file generation

### Phase 3: Dialog UI
- [ ] Create `ClaudeMdDialog` class file
- [ ] Implement dialog initialization
- [ ] Implement working dialog display
- [ ] Implement review dialog
- [ ] Implement save logic
- [ ] Add error handling
- [ ] Test dialog flows

### Phase 4: Menu Integration
- [ ] Add "Project" top-level menu
- [ ] Add CLAUDE.md submenu
- [ ] Add Create menu item + handler
- [ ] Add Reference menu item + handler
- [ ] Add Edit menu item + handler
- [ ] Implement conditional enabling/disabling
- [ ] Test menu state management

### Phase 5: Status Display
- [ ] Enhance connection header with status indicator
- [ ] Add status update after create
- [ ] Add status update after reference
- [ ] Add status check on menu open
- [ ] Test status display updates

### Phase 6: Polish & Testing
- [ ] Add comprehensive error messages
- [ ] Add user feedback (success messages)
- [ ] Test on macOS
- [ ] Test on Windows
- [ ] Test on Linux
- [ ] Test edge cases (spaces, unicode, permissions)
- [ ] Update project version number in 3 places
- [ ] Update documentation

## Success Criteria

### Functional Criteria
✅ User can create CLAUDE.md via agent from menu
✅ User can reference/copy existing CLAUDE.md from menu
✅ User can edit CLAUDE.md from menu (when exists)
✅ Status indicator shows CLAUDE.md presence
✅ All operations work on Windows, macOS, and Linux

### Quality Criteria
✅ No UI blocking during agent execution
✅ Clear error messages for all failure modes
✅ Operations complete in expected timeframes
✅ No data loss or corruption
✅ Follows existing UI patterns consistently

### User Experience Criteria
✅ Feature is discoverable without documentation
✅ User successfully creates CLAUDE.md on first attempt
✅ Generated CLAUDE.md follows best practices (< 150 lines, project-specific)
✅ User feedback is immediate and clear
✅ No confusing states or dead ends

## Risks & Mitigation

### Risk 1: Agent Execution Time Exceeds Expectations
**Impact:** MEDIUM - Users may think UI is frozen

**Mitigation:**
- Show animated working dialog with time estimate
- Add progress messages if agent supports them
- Consider adding cancel button (future enhancement)

### Risk 2: Platform-Specific Editor Issues
**Impact:** LOW - Feature still usable without edit function

**Mitigation:**
- Test on all three platforms during development
- Provide fallback error message with file path
- Document known limitations in release notes

### Risk 3: Agent Produces Low-Quality Output
**Impact:** LOW - User can edit or regenerate

**Mitigation:**
- Review dialog allows user to inspect before saving
- User can always manually edit afterwards
- Future enhancement: Quality validation rules

### Risk 4: Permission Errors in Production
**Impact:** LOW - Clear error messages guide user

**Mitigation:**
- Pre-check permissions before agent invocation
- Show file path in error message
- Suggest concrete fixes (chmod, run as admin)

## Future Enhancements

Out of scope for this implementation, but worth planning for:

1. **Templates Library** - Pre-made CLAUDE.md templates for common project types
2. **Validation/Linting** - Check CLAUDE.md against best practices
3. **Multi-file Management** - Handle CLAUDE.md and CLAUDE.local.md
4. **Cancel Button** - Allow cancelling long-running agent execution
5. **Diff View** - Show differences when overwriting existing file
6. **Global Config** - Manage `~/.claude/CLAUDE.md` from UI
7. **AI Suggestions** - Recommend improvements to existing CLAUDE.md
8. **Version History** - Track CLAUDE.md changes over time

---

## Appendix: File Locations Reference

### Files to Create
- `src/ui/dialogs/claude_md_manager.py` - Main dialog implementation

### Files to Modify
- `src/ui/main.py` - Menu structure, handlers, status display
- `src/ui/utils/cmat_interface.py` - Backend methods

### Files Referenced (No Changes)
- `src/core/services/task_service.py` - Uses execute_direct()
- `.claude/agents/claude-md-creator-agent.md` - Existing agent
- `src/ui/dialogs/base_dialog.py` - Base class
- `src/ui/dialogs/mixins/claude_generator_mixin.py` - Mixin class
- `src/ui/dialogs/working.py` - Working dialog

## Appendix: Architecture Patterns Used

This implementation follows established CMAT patterns:

✅ **Menu Pattern:** Connection-dependent menus with state management
✅ **Dialog Pattern:** BaseDialog + Mixin for consistent behavior
✅ **Backend Pattern:** CMATInterface wraps core services
✅ **Async Pattern:** Threading + callbacks for long operations
✅ **Error Pattern:** Try/except with user-friendly messages
✅ **Service Pattern:** TaskService.execute_direct() for agent invocation

No new patterns introduced - all follow existing conventions.

---

**Implementation Ready:** This plan provides complete technical specifications for implementing the CLAUDE.md management feature. All architectural decisions are made, integration points identified, and implementation path clearly defined.
