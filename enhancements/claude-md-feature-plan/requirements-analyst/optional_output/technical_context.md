# Technical Context: CLAUDE.md Management Feature

## Existing Codebase Patterns

### UI Architecture Pattern

The CMAT Desktop UI follows a consistent pattern:

```
MainView (src/ui/main.py)
├── Menu Bar → Command handlers
├── Dialog invocation → Specialized dialog classes
└── CMATInterface → Backend service layer
```

**Key Components:**

1. **Menu Bar Pattern** (`main.py:104-199`):
   - Menus defined in `build_menu_bar()`
   - Connection-dependent menus stored in `self.menus` dict
   - Enabled/disabled via `update_menu_states()`
   - Commands bound to handler methods

2. **Dialog Pattern** (`dialogs/base_dialog.py`, `dialogs/enhancement_create.py`):
   - Inherit from `BaseDialog` for consistent behavior
   - Use `ClaudeGeneratorMixin` for async Claude API calls
   - `WorkingDialog` for progress indication during long operations
   - Modal dialogs with approve/cancel flows

3. **Backend Interface** (`utils/cmat_interface.py`):
   - `CMATInterface` wraps CMAT core services
   - Provides `project_root`, `agents`, `queue`, etc.
   - Service-oriented architecture for clean separation

### Relevant Code Locations

**Menu System:**
- Main menu bar: `src/ui/main.py:104-199`
- Menu state management: `src/ui/main.py:200-223`
- Example connection-dependent menu: Lines 122-128 (Workflows)

**Dialog System:**
- Base dialog: `src/ui/dialogs/base_dialog.py`
- Claude generator mixin: `src/ui/dialogs/mixins/claude_generator_mixin.py`
- Working dialog: `src/ui/dialogs/working.py`
- Example usage: `src/ui/dialogs/enhancement_create.py:17-29`

**File Operations:**
- Path utilities: `src/ui/utils/path_utils.py`
- Project root access: `queue_interface.project_root`

## Agent Invocation Analysis

### Current Workflow-Based Pattern

Agents are currently invoked through workflows:

```python
# From workflow system
workflow_service.start_workflow(
    workflow_id=workflow_id,
    enhancement_name=enhancement_name
)
```

This uses:
- `WorkflowService` to manage workflow state
- `TaskService` to execute individual steps
- Task queue for persistence and tracking

### Enhancement Generator Pattern (Closest Match)

The enhancement generator dialog (`enhancement_create.py`) uses `ClaudeGeneratorMixin`:

```python
class CreateEnhancementDialog(BaseDialog, ClaudeGeneratorMixin):
    def __init__(self, parent, queue_interface, settings):
        BaseDialog.__init__(self, parent, "Title", 750, 700)
        ClaudeGeneratorMixin.__init__(self, settings)

    def generate_enhancement(self):
        self.call_claude_async(
            context="Generate enhancement spec...",
            system_prompt="You are an expert...",
            on_success=self.on_generated,
            on_error=self.on_error
        )
```

**However**: This calls Claude API directly, not via the agent system. The CLAUDE.md creator needs to:
1. Use the actual agent definition file
2. Invoke the agent with proper tools access
3. Potentially run multiple tool calls (Read, Glob, Grep, Bash, Write)

### Recommended Pattern for One-Off Agent Invocation

**Option 1: Extend TaskService**
```python
# In CMATInterface
def run_standalone_agent(
    agent_name: str,
    context: str,
    output_callback: Callable
) -> str:
    """Run an agent outside workflow system."""
    # Load agent definition
    # Execute with tools
    # Return result
```

**Option 2: Lightweight Workflow**
```python
# Create minimal workflow with single step
workflow = {
    "name": "claude-md-creation",
    "steps": [{
        "agent": "claude-md-creator",
        "status_transitions": {
            "COMPLETE": "done"
        }
    }]
}
```

**Recommendation**: Option 1 is cleaner for true one-off operations that aren't part of a workflow.

## File System Operations

### Platform-Specific Considerations

**Opening Files in System Editor:**

```python
import subprocess
import os
import platform

def open_in_editor(file_path: str):
    """Open file in system default editor."""
    system = platform.system()

    if system == "Darwin":  # macOS
        subprocess.run(["open", file_path])
    elif system == "Windows":
        os.startfile(file_path)
    else:  # Linux/Unix
        subprocess.run(["xdg-open", file_path])
```

**File Copy with Confirmation:**

```python
from pathlib import Path
from tkinter import messagebox

def copy_claude_md(source: Path, project_root: Path) -> bool:
    """Copy CLAUDE.md with overwrite confirmation."""
    target = project_root / "CLAUDE.md"

    if target.exists():
        response = messagebox.askyesno(
            "Overwrite Existing File",
            f"CLAUDE.md already exists in {project_root}\n\n"
            "Overwrite the existing file?"
        )
        if not response:
            return False

    try:
        import shutil
        shutil.copy2(source, target)
        return True
    except PermissionError:
        messagebox.showerror(
            "Permission Denied",
            f"Cannot write to {target}\n\n"
            "Check file permissions."
        )
        return False
```

**Status Check:**

```python
def check_claude_md_status(project_root: Path) -> dict:
    """Check CLAUDE.md presence and metadata."""
    claude_md = project_root / "CLAUDE.md"

    return {
        "exists": claude_md.exists(),
        "path": str(claude_md) if claude_md.exists() else None,
        "size": claude_md.stat().st_size if claude_md.exists() else 0,
        "modified": claude_md.stat().st_mtime if claude_md.exists() else None
    }
```

## UI Integration Points

### Recommended Menu Structure

**Option A: Under File Menu**
```
File
├── Install...
├── Connect...
├── ────────────
├── CLAUDE.md ►
│   ├── Create...
│   ├── Reference Existing...
│   └── Edit (conditional)
├── ────────────
├── Reset Queue...
```

**Option B: New Project Menu (Recommended)**
```
Project (NEW)
├── CLAUDE.md ►
│   ├── Create...
│   ├── Reference Existing...
│   └── Edit (conditional)
├── ────────────
├── Project Info...
└── Project Settings...
```

### Status Display Location

Current UI has a connection header at top. Recommended addition:

```
┌─────────────────────────────────────────────────────────┐
│ Connected to: /path/to/project    [CLAUDE.md: Present] │
│                                    [v10.0.0]            │
└─────────────────────────────────────────────────────────┘
```

Implementation in `main.py:224-244` (connection header section).

## Error Handling Scenarios

### Scenario 1: Agent Execution Failure
**Cause**: Claude API error, timeout, rate limit
**Handling**:
- Show error dialog with retry option
- Log error details
- Don't corrupt existing CLAUDE.md

### Scenario 2: Permission Denied
**Cause**: No write access to project root
**Handling**:
- Check permissions before agent invocation
- Show clear error with file path
- Suggest fixes (chmod, run as admin, etc.)

### Scenario 3: Agent Produces Invalid Output
**Cause**: Agent fails to generate CLAUDE.md
**Handling**:
- Validate output structure
- Show error if invalid
- Allow user to retry or cancel

### Scenario 4: Large File Warning
**Cause**: Referenced file is extremely large
**Handling**:
- Check file size before copy
- Warn if > 50KB (CLAUDE.md should be concise)
- Allow user to proceed or cancel

### Scenario 5: Not Connected
**Cause**: User tries to access feature without project connection
**Handling**:
- Menu items disabled when not connected
- If somehow invoked, show "Connect to a project first" message

## Testing Considerations

### Unit Tests
- File system operations (mock Path objects)
- Status check logic
- Menu state management
- Error handling branches

### Integration Tests
- End-to-end create flow with mock agent
- File copy with temporary directories
- Editor invocation (platform-specific)

### Manual Tests
- Cross-platform (Windows, macOS, Linux)
- Various project structures
- Edge cases: spaces in paths, unicode characters
- Permissions: read-only directories, network drives

## Performance Considerations

### Agent Execution Time

The `claude-md-creator` agent:
- Reads multiple files (3-5 source files)
- Runs Glob/Grep operations
- Calls Claude API (30-60 seconds typical)
- Total: 60-90 seconds expected

**Mitigation**:
- Use `ClaudeGeneratorMixin` for async execution
- Show working dialog with progress animation
- Keep UI responsive via threading

### File Operations

All file operations (check status, copy, write) should be < 100ms.
No performance concerns for typical usage.

### Status Polling

If implementing periodic status checks:
- Poll no more than once per 5 seconds
- Use file modification time to detect changes
- Only poll when window has focus

## Security Considerations

### File Path Validation

```python
def validate_file_path(path: Path, project_root: Path) -> bool:
    """Ensure file path is safe and within project."""
    # Resolve to absolute path
    abs_path = path.resolve()
    abs_root = project_root.resolve()

    # Check it's within project (prevent directory traversal)
    try:
        abs_path.relative_to(abs_root)
        return True
    except ValueError:
        return False
```

### Agent Input Sanitization

When invoking agent:
- Use absolute paths only
- Validate project root exists and is readable
- Don't pass user input directly to shell commands
- Limit output size to prevent memory issues

### File Write Safety

- Check disk space before writing
- Use atomic write operations (write to temp, then rename)
- Backup existing CLAUDE.md before overwrite
- Verify write succeeded before showing success

## Future Enhancement Opportunities

Not in scope for initial implementation, but worth noting:

1. **CLAUDE.md Templates Library**: Pre-made templates for common project types
2. **Multi-file Management**: Handle both CLAUDE.md and CLAUDE.local.md
3. **Validation/Linting**: Check CLAUDE.md against best practices
4. **Version History**: Track CLAUDE.md changes over time
5. **Team Sync**: Share CLAUDE.md configs across team
6. **AI Suggestions**: Recommend improvements to existing CLAUDE.md
7. **Context Preview**: Show what Claude sees when loading CLAUDE.md
8. **Global Config Manager**: Manage `~/.claude/CLAUDE.md` from UI

---

## Quick Reference: Key Files to Modify

| File | Purpose | Changes Needed |
|------|---------|----------------|
| `src/ui/main.py` | Main window | Add menu items, handlers, status display |
| `src/ui/dialogs/claude_md_manager.py` | NEW | Dialog for create/review flow |
| `src/ui/utils/cmat_interface.py` | Backend interface | Add `run_standalone_agent()` method |
| `src/core/services/task_service.py` | Task execution | Support standalone agent invocation |
| `templates/.claude/agents/agents.json` | Agent registry | Ensure claude-md-creator is registered |

## Key Design Decisions Needed

Before implementation can begin, architecture must decide:

1. ✋ **Agent invocation mechanism**: How to run agents outside workflows?
2. ✋ **Menu location**: Where do CLAUDE.md options live?
3. ✋ **Editor approach**: System editor vs in-app editor?
4. ✋ **Status update strategy**: On-demand, polling, or file watching?
5. ✋ **Output approval flow**: Modal dialog, side panel, or diff view?

These are blocking decisions for implementation planning.
