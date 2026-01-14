# Technical Diagrams and Detailed Specifications

## Sequence Diagrams

### Create CLAUDE.md Flow

```
User          MainView       ClaudeMdDialog    CMATInterface    TaskService    claude-md-creator
 │                │                 │                │               │                │
 │  Click Create  │                 │                │               │                │
 │───────────────>│                 │                │               │                │
 │                │                 │                │               │                │
 │                │  Open Dialog    │                │               │                │
 │                │────────────────>│                │               │                │
 │                │                 │                │               │                │
 │                │                 │ Show Working   │               │                │
 │                │                 │    Dialog      │               │                │
 │                │                 │◀───────────────┘               │                │
 │                │                 │                │               │                │
 │                │                 │  run_claude_   │               │                │
 │                │                 │  md_agent()    │               │                │
 │                │                 │───────────────>│               │                │
 │                │                 │                │               │                │
 │                │                 │                │ execute_      │                │
 │                │                 │                │ direct()      │                │
 │                │                 │                │──────────────>│                │
 │                │                 │                │               │                │
 │                │                 │                │               │ Invoke Agent   │
 │                │                 │                │               │───────────────>│
 │                │                 │                │               │                │
 │    [60-90 seconds: Agent analyzes project and generates content]  │                │
 │                │                 │                │               │                │
 │                │                 │                │               │   Returns      │
 │                │                 │                │               │   CLAUDE.md    │
 │                │                 │                │               │<───────────────│
 │                │                 │                │               │                │
 │                │                 │                │  Execution    │                │
 │                │                 │                │  Result       │                │
 │                │                 │                │<──────────────│                │
 │                │                 │                │               │                │
 │                │                 │  Callback      │               │                │
 │                │                 │  (result)      │               │                │
 │                │                 │<───────────────┘               │                │
 │                │                 │                │               │                │
 │                │                 │ Close Working  │               │                │
 │                │                 │ Show Review    │               │                │
 │                │                 │    Dialog      │               │                │
 │                │                 │────────────────┐               │                │
 │                │                 │                │               │                │
 │  Review Content│                 │                │               │                │
 │◀───────────────────────────────────────────────────               │                │
 │                │                 │                │               │                │
 │  Click Save    │                 │                │               │                │
 │───────────────────────────────>│                │               │                │
 │                │                 │                │               │                │
 │                │                 │ Write to       │               │                │
 │                │                 │ project root   │               │                │
 │                │                 │────────────────┐               │                │
 │                │                 │                │               │                │
 │                │                 │ Show Success   │               │                │
 │                │                 │────────────────┐               │                │
 │                │                 │                │               │                │
 │                │  update_claude_ │                │               │                │
 │                │  md_status()    │                │               │                │
 │                │<────────────────┘                │               │                │
 │                │                 │                │               │                │
 │  Status        │                 │                │               │                │
 │  Updated       │                 │                │               │                │
 │◀───────────────┘                 │                │               │                │
```

### Reference Existing Flow

```
User          MainView       FilePicker      CMATInterface
 │                │               │                 │
 │  Click         │               │                 │
 │  Reference     │               │                 │
 │───────────────>│               │                 │
 │                │               │                 │
 │                │  Open File    │                 │
 │                │  Picker       │                 │
 │                │──────────────>│                 │
 │                │               │                 │
 │  Select File   │               │                 │
 │───────────────────────────────>│                 │
 │                │               │                 │
 │                │  file_path    │                 │
 │                │<──────────────┘                 │
 │                │               │                 │
 │                │  copy_file_   │                 │
 │                │  to_claude_md()                 │
 │                │────────────────────────────────>│
 │                │               │                 │
 │                │               │  Check Size     │
 │                │               │  Check Exists   │
 │                │               │  [if large]     │
 │                │               │    Show Warning │
 │                │               │  [if exists]    │
 │                │               │    Confirm      │
 │                │               │    Overwrite    │
 │                │               │                 │
 │                │               │  Copy File      │
 │                │               │─────────────────┐
 │                │               │                 │
 │                │  (success,    │                 │
 │                │   message)    │                 │
 │                │<────────────────────────────────┘
 │                │               │                 │
 │                │  Show Success │                 │
 │                │  Message      │                 │
 │                │───────────────┐                 │
 │                │               │                 │
 │  Success       │               │                 │
 │  Shown         │               │                 │
 │◀───────────────┘               │                 │
```

### Edit CLAUDE.md Flow

```
User          MainView       CMATInterface    System Editor
 │                │                 │                 │
 │  Click Edit    │                 │                 │
 │───────────────>│                 │                 │
 │                │                 │                 │
 │                │  open_claude_   │                 │
 │                │  md_in_editor() │                 │
 │                │────────────────>│                 │
 │                │                 │                 │
 │                │                 │  Check Exists   │
 │                │                 │─────────────────┐
 │                │                 │                 │
 │                │                 │  Launch Editor  │
 │                │                 │  (platform-     │
 │                │                 │   specific)     │
 │                │                 │────────────────>│
 │                │                 │                 │
 │                │  (success,      │                 │
 │                │   message)      │                 │
 │                │<────────────────┘                 │
 │                │                 │                 │
 │                │                 │  Editor Opens   │
 │                │                 │  with File      │
 │                │                 │◀────────────────┘
 │                │                 │                 │
 │  User Edits in External Editor  │                 │
 │◀────────────────────────────────────────────────────
```

## State Diagrams

### Menu Item States

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE.md Menu Items                     │
└─────────────────────────────────────────────────────────────┘

                       ┌──────────────┐
                       │ DISCONNECTED │
                       │              │
                       │ All items    │
                       │ DISABLED     │
                       └──────┬───────┘
                              │
                              │ Connect to project
                              │
                       ┌──────▼───────┐
                       │  CONNECTED   │
                       │              │
                       │ Check status │
                       └──────┬───────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
         ┌───────▼────────┐       ┌───────▼────────┐
         │ CLAUDE.md      │       │ CLAUDE.md      │
         │ NOT EXISTS     │       │ EXISTS         │
         │                │       │                │
         │ Create: ✓      │       │ Create: ✓      │
         │ Reference: ✓   │       │ Reference: ✓   │
         │ Edit: ✗        │       │ Edit: ✓        │
         └────────────────┘       └────────────────┘
```

### Agent Execution States

```
┌─────────┐
│  IDLE   │
└────┬────┘
     │ User clicks Create
     │
┌────▼────────┐
│ VALIDATING  │  Check permissions
│             │  Check API key
└────┬────────┘
     │ Valid
     │
┌────▼────────┐
│  STARTING   │  Show working dialog
│             │  Spawn thread
└────┬────────┘
     │
┌────▼────────┐
│  EXECUTING  │  Agent analyzing
│             │  (60-90 seconds)
└────┬────────┘
     │
     ├─────────────┬─────────────┐
     │             │             │
┌────▼────┐   ┌────▼────┐   ┌───▼─────┐
│ SUCCESS │   │  ERROR  │   │ TIMEOUT │
│         │   │         │   │         │
│ Show    │   │ Show    │   │ Show    │
│ Review  │   │ Error   │   │ Retry   │
└────┬────┘   └────┬────┘   └───┬─────┘
     │             │             │
     │             └──────┬──────┘
     │                    │
     │             ┌──────▼──────┐
     │             │  CANCELLED  │
     │             │             │
     │             │  Return to  │
     │             │  IDLE       │
     │             └─────────────┘
     │
┌────▼────────┐
│  REVIEWING  │  User reviews content
│             │
└────┬────────┘
     │
     ├──────────────┬───────────────┐
     │              │               │
┌────▼────┐    ┌────▼────┐    ┌────▼────┐
│  SAVE   │    │ CANCEL  │    │  EDIT   │
│         │    │         │    │(future) │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     │              └───────┬──────┘
     │                      │
┌────▼────────┐      ┌──────▼──────┐
│   SAVED     │      │  CANCELLED  │
│             │      │             │
│ Update      │      │  Return to  │
│ Status      │      │  IDLE       │
│ Close       │      └─────────────┘
└─────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                          User Actions                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        │                     │                     │
  ┌─────▼─────┐        ┌──────▼─────┐       ┌──────▼──────┐
  │  Create   │        │ Reference  │       │    Edit     │
  │ CLAUDE.md │        │  Existing  │       │ CLAUDE.md   │
  └─────┬─────┘        └──────┬─────┘       └──────┬──────┘
        │                     │                     │
        │                     │                     │
  ┌─────▼──────────┐    ┌─────▼──────────┐   ┌─────▼──────────┐
  │ CMATInterface  │    │ CMATInterface  │   │ CMATInterface  │
  │ .run_claude_   │    │ .copy_file_to_ │   │ .open_claude_  │
  │ md_agent()     │    │ claude_md()    │   │ md_in_editor() │
  └─────┬──────────┘    └─────┬──────────┘   └─────┬──────────┘
        │                     │                     │
        │                     │                     │
  ┌─────▼──────────┐    ┌─────▼──────────┐   ┌─────▼──────────┐
  │ TaskService    │    │ File System    │   │ System Editor  │
  │ .execute_      │    │ Copy Operation │   │ Subprocess     │
  │ direct()       │    │                │   │                │
  └─────┬──────────┘    └─────┬──────────┘   └─────┬──────────┘
        │                     │                     │
        │                     │                     │
  ┌─────▼──────────┐          │                     │
  │ claude-md-     │          │                     │
  │ creator agent  │          │                     │
  │                │          │                     │
  │ - Glob project │          │                     │
  │ - Read files   │          │                     │
  │ - Generate MD  │          │                     │
  └─────┬──────────┘          │                     │
        │                     │                     │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              │
                    ┌─────────▼─────────┐
                    │  {project_root}/  │
                    │    CLAUDE.md      │
                    └───────────────────┘
```

## Module Dependency Graph

```
┌───────────────────────────────────────────────────────────────┐
│                         main.py                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ MainView                                                │  │
│  │  - build_project_menu()                                 │  │
│  │  - show_create_claude_md()                              │  │
│  │  - show_reference_claude_md()                           │  │
│  │  - show_edit_claude_md()                                │  │
│  │  - update_claude_md_status()                            │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────┬──────────────────────┬────────────────────┘
                    │                      │
         ┌──────────▼──────────┐  ┌────────▼──────────┐
         │ claude_md_manager.py│  │ cmat_interface.py │
         │ ┌──────────────────┐│  │ ┌────────────────┐│
         │ │ ClaudeMdDialog   ││  │ │ CMATInterface  ││
         │ │  (BaseDialog +   ││  │ │  + New Methods ││
         │ │   ClaudeGen      ││  │ │                ││
         │ │   Mixin)         ││  │ └────────────────┘│
         │ └──────────────────┘│  └──────────┬────────┘
         └──────────┬───────────┘            │
                    │                        │
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   TaskService           │
                    │   (core/services/)      │
                    │ ┌────────────────────┐  │
                    │ │ .execute_direct()  │  │
                    │ │  (existing method) │  │
                    │ └────────────────────┘  │
                    └─────────────────────────┘
```

## Component Interface Specifications

### ClaudeMdDialog Public API

```python
class ClaudeMdDialog(BaseDialog, ClaudeGeneratorMixin):
    """
    Dialog for creating CLAUDE.md via agent.

    Lifecycle:
    1. __init__() - Initialize and show working dialog
    2. start_generation() - Invoke agent asynchronously
    3. on_agent_complete() - Handle success, show review
    4. save_claude_md() - Write to project root
    5. on_complete_callback() - Notify parent to update status

    Error Paths:
    - on_agent_error() - Handle agent failure
    - User cancels review - Close without saving
    """

    def __init__(
        self,
        parent: tk.Widget,
        queue_interface: CMATInterface,
        settings: Settings,
        on_complete: Optional[Callable[[], None]] = None
    ):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            queue_interface: Backend interface
            settings: Settings object (for API key)
            on_complete: Callback when operation succeeds
        """

    def start_generation(self) -> None:
        """
        Start agent execution.

        - Shows working dialog
        - Spawns background thread
        - Calls run_claude_md_agent()
        """

    def on_agent_complete(self, result: ExecutionResult) -> None:
        """
        Handle agent completion.

        Args:
            result: Execution result from TaskService

        Behavior:
        - Close working dialog
        - Read generated CLAUDE.md from result.output_dir
        - Show review dialog with content
        """

    def on_agent_error(self, error: Exception) -> None:
        """
        Handle agent failure.

        Args:
            error: Exception from agent execution

        Behavior:
        - Close working dialog
        - Show error message
        - Offer retry for timeout errors
        """

    def show_review_dialog(self, content: str) -> None:
        """
        Show review dialog for approval.

        Args:
            content: Generated CLAUDE.md content

        UI:
        - Read-only text widget with content
        - Cancel button - closes without saving
        - Save button - calls save_claude_md()
        """

    def save_claude_md(self, content: str) -> None:
        """
        Save content to project root.

        Args:
            content: CLAUDE.md content to write

        Behavior:
        - Write to {project_root}/CLAUDE.md
        - Show success message
        - Call on_complete callback
        - Close dialog
        """
```

### CMATInterface CLAUDE.md Methods

```python
class CMATInterface:
    """Backend interface - CLAUDE.md methods."""

    def run_claude_md_agent(
        self,
        callback: Callable[[ExecutionResult], None]
    ) -> None:
        """
        Execute claude-md-creator agent.

        Args:
            callback: Called with ExecutionResult when done

        Thread Safety:
        - Runs in background thread
        - Callback invoked on main thread

        Execution:
        - Calls TaskService.execute_direct()
        - Agent has full tools access
        - Logs to .claude/logs/

        Errors:
        - Calls callback with failed ExecutionResult
        - Never raises exceptions
        """

    def check_claude_md_status(self) -> ClaudeMdStatus:
        """
        Check CLAUDE.md status.

        Returns:
            Status object with exists, path, size, modified

        Performance:
        - < 10ms typical
        - Safe to call frequently
        - No I/O caching

        Thread Safety:
        - Thread-safe (only reads filesystem)
        """

    def open_claude_md_in_editor(self) -> Tuple[bool, str]:
        """
        Open CLAUDE.md in system editor.

        Returns:
            (success: bool, message: str)

        Platform Behavior:
        - macOS: Uses 'open' command
        - Windows: Uses os.startfile()
        - Linux: Uses 'xdg-open'

        Errors:
        - FileNotFoundError if CLAUDE.md missing
        - Returns (False, error_msg) on failure
        - Never raises exceptions
        """

    def copy_file_to_claude_md(
        self,
        source_path: str,
        overwrite_existing: bool = False
    ) -> Tuple[bool, str]:
        """
        Copy file to project root as CLAUDE.md.

        Args:
            source_path: Source .md file path
            overwrite_existing: Skip overwrite prompt

        Returns:
            (success: bool, message: str)

        Validations:
        - Source exists and readable
        - Source has .md extension
        - Target location writable
        - Size warning if > 50KB
        - Overwrite confirmation if exists

        Errors:
        - Returns (False, error_msg) on failure
        - Never raises exceptions
        """
```

## Error Handling Matrix

| Error Scenario | Detection Point | User Feedback | Recovery Action | Log Level |
|----------------|----------------|---------------|-----------------|-----------|
| API Key Missing | ClaudeGeneratorMixin | Warning dialog: "Configure API key in Settings" | User adds key | INFO |
| API Timeout | TaskService | Error dialog with Retry option | User retries or cancels | WARNING |
| API Rate Limit | TaskService | Error: "Rate limit exceeded. Wait 1 minute." | User waits and retries | WARNING |
| Permission Denied (Write) | copy_file_to_claude_md | Error: "Cannot write to {path}. Check permissions." | User fixes permissions | ERROR |
| Permission Denied (Read) | copy_file_to_claude_md | Error: "Cannot read {source}. Check permissions." | User fixes permissions | ERROR |
| File Not Found | copy_file_to_claude_md | Error: "Source file not found: {path}" | User selects correct file | WARNING |
| Large File Warning | copy_file_to_claude_md | Warning: "File is {size}KB. CLAUDE.md should be < 50KB. Continue?" | User confirms or cancels | INFO |
| CLAUDE.md Exists | copy_file_to_claude_md | Confirm: "Overwrite existing CLAUDE.md?" | User confirms or cancels | INFO |
| Invalid File Extension | copy_file_to_claude_md | Error: "File must be .md extension" | User selects .md file | WARNING |
| Editor Not Found | open_claude_md_in_editor | Error: "Cannot find editor for {platform}" | User manually opens file | ERROR |
| Editor Launch Failed | open_claude_md_in_editor | Error: "Failed to open editor: {error}" | User manually opens file | ERROR |
| Agent Output Invalid | on_agent_complete | Error: "Agent produced invalid output" | User retries or cancels | ERROR |
| Agent Crash | on_agent_error | Error: "Agent failed: {error}" | User retries or reports bug | ERROR |
| Network Error | TaskService | Error: "Network error. Check connection." | User checks network | ERROR |
| Disk Full | save_claude_md | Error: "Disk full. Free up space." | User frees disk space | ERROR |

## Performance Benchmarks

### Target Performance Metrics

| Operation | Target | Acceptable | Notes |
|-----------|--------|------------|-------|
| Menu Open | < 50ms | < 100ms | Status check included |
| Status Check | < 5ms | < 10ms | File existence check |
| File Copy | < 50ms | < 200ms | Depends on file size |
| Editor Launch | < 200ms | < 500ms | Platform-dependent |
| Agent Start | < 1s | < 3s | Thread spawn + validation |
| Agent Execute | 30-60s | 90s | Claude API call |
| Review Dialog Open | < 100ms | < 500ms | Load and render content |
| Save Operation | < 50ms | < 200ms | Write to disk |

### Optimization Strategies

1. **Status Checks:**
   - Cache status for 1 second
   - Invalidate cache after write operations
   - Use Path.exists() (fastest check)

2. **Agent Execution:**
   - Run in background thread (no UI blocking)
   - Show animated progress (perceived performance)
   - Consider caching project analysis (future)

3. **File Operations:**
   - Use shutil.copy2() for fast copy
   - Validate before copy (fail fast)
   - Use atomic writes (temp file + rename)

4. **Dialog Rendering:**
   - Lazy load text content
   - Use text widget pagination for large files
   - Limit initial render to 1000 lines

## Testing Matrix

### Unit Test Coverage

| Module | Test Cases | Coverage Target |
|--------|-----------|-----------------|
| cmat_interface.py | 15 tests | 90% |
| claude_md_manager.py | 12 tests | 85% |
| main.py (menu handlers) | 8 tests | 80% |

### Integration Test Scenarios

1. **Happy Path - Create:**
   - Connect → Create → Agent completes → Review → Save → Status updates

2. **Happy Path - Reference:**
   - Connect → Reference → Select file → Confirm overwrite → Copy → Status updates

3. **Happy Path - Edit:**
   - Connect → (CLAUDE.md exists) → Edit → Editor opens

4. **Error Path - API Key Missing:**
   - Create → Warning shown → User cancels

5. **Error Path - Permission Denied:**
   - Create → Agent completes → Save fails → Error shown

6. **Error Path - Agent Timeout:**
   - Create → Agent times out → Retry option → User retries → Success

7. **Edge Case - Large File:**
   - Reference → Select 100KB file → Warning shown → User cancels

8. **Edge Case - Special Characters:**
   - Create with path containing spaces, unicode → Success

### Manual Test Checklist

#### Cross-Platform Testing
- [ ] macOS Monterey+: All operations work
- [ ] Windows 10/11: All operations work
- [ ] Ubuntu 20.04+: All operations work

#### Menu Behavior
- [ ] Project menu appears when connected
- [ ] Project menu disappears when disconnected
- [ ] Edit enabled only when CLAUDE.md exists
- [ ] Edit disabled when CLAUDE.md missing
- [ ] Keyboard shortcuts work (if implemented)

#### Create Flow
- [ ] Dialog opens instantly
- [ ] Working dialog shows progress
- [ ] Agent completes in < 90 seconds
- [ ] Review dialog shows content
- [ ] Save writes to correct location
- [ ] Status updates after save
- [ ] Success message shown

#### Reference Flow
- [ ] File picker opens filtered to .md
- [ ] Can navigate filesystem
- [ ] Overwrite confirmation shown if exists
- [ ] Copy succeeds
- [ ] Status updates after copy
- [ ] Large file warning shown if > 50KB

#### Edit Flow
- [ ] Editor opens with correct file
- [ ] macOS: Opens with default app
- [ ] Windows: Opens with default app
- [ ] Linux: Opens with default app
- [ ] Error shown if editor fails

#### Error Handling
- [ ] API key missing shows warning
- [ ] Permission errors show clear message
- [ ] Agent timeout offers retry
- [ ] Network errors handled gracefully
- [ ] Invalid file extension rejected

#### Edge Cases
- [ ] Path with spaces works
- [ ] Path with unicode works
- [ ] Read-only project shows error
- [ ] Network drive works (if applicable)
- [ ] Multiple rapid operations don't crash
- [ ] Empty CLAUDE.md content handled
- [ ] Very large CLAUDE.md (> 100KB) handled

---

This document provides detailed technical diagrams and specifications to complement the main implementation plan.
