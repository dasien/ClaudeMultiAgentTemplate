# Detailed User Stories and Acceptance Criteria

## Epic: CLAUDE.md Management

**As a** CMAT user
**I want** integrated CLAUDE.md file management
**So that** I can easily provide project-specific context to Claude Code

---

## User Story 1: Generate CLAUDE.md with AI Assistance

**As a** developer setting up a new project in CMAT
**I want** Claude to analyze my project and generate a CLAUDE.md file
**So that** I don't have to manually document all my project conventions

### Acceptance Criteria

#### AC-1.1: Menu Access
- **Given** I have connected to a project
- **When** I open the CLAUDE.md menu
- **Then** I see a "Create..." option
- **And** clicking it initiates the CLAUDE.md creation flow

#### AC-1.2: Agent Invocation
- **Given** I clicked "Create..."
- **When** the create dialog opens
- **Then** I see a working/progress dialog
- **And** the `claude-md-creator` agent is invoked with my project root
- **And** the UI remains responsive during generation

#### AC-1.3: Content Review
- **Given** the agent has completed analysis
- **When** generation is successful
- **Then** I see a preview dialog showing the generated CLAUDE.md content
- **And** the content is displayed in readable format (scrollable text)
- **And** I have options to "Save" or "Cancel"

#### AC-1.4: Save to Project
- **Given** I reviewed the generated content
- **When** I click "Save"
- **Then** the content is written to `{project-root}/CLAUDE.md`
- **And** I see a success confirmation
- **And** the CLAUDE.md status indicator updates to "Present"

#### AC-1.5: Error Handling - API Failure
- **Given** the Claude API call fails (timeout, rate limit, network error)
- **When** the error occurs
- **Then** I see an error dialog with clear message
- **And** I have option to "Retry" or "Cancel"
- **And** no CLAUDE.md file is created

#### AC-1.6: Error Handling - Permission Denied
- **Given** I lack write permissions to project root
- **When** I attempt to save
- **Then** I see an error dialog explaining permission issue
- **And** the error includes the target file path
- **And** I'm given guidance on how to fix (check permissions, run as admin, etc.)

#### AC-1.7: Cancel Flow
- **Given** I am reviewing generated content
- **When** I click "Cancel"
- **Then** the dialog closes
- **And** no CLAUDE.md file is created
- **And** I can retry if desired

#### AC-1.8: Existing File Warning
- **Given** my project already has a CLAUDE.md
- **When** I initiate "Create..."
- **Then** I see a warning that file exists
- **And** I can choose to "Overwrite", "Cancel", or "View Existing"
- **And** "Overwrite" proceeds with generation (after confirmation)

### Test Scenarios

1. **Happy Path**: New project → Create → Review → Save → Success
2. **Retry After Error**: Create → API error → Retry → Success
3. **Cancel During Progress**: Create → Working dialog → Cancel → No file
4. **Overwrite Existing**: Has CLAUDE.md → Create → Confirm overwrite → New file
5. **Permission Failure**: Read-only directory → Create → Permission error

---

## User Story 2: Reference Existing CLAUDE.md

**As a** developer with a proven CLAUDE.md from another project
**I want** to copy that file into my current project
**So that** I can reuse effective configurations without starting from scratch

### Acceptance Criteria

#### AC-2.1: Menu Access
- **Given** I have connected to a project
- **When** I open the CLAUDE.md menu
- **Then** I see a "Reference Existing..." option
- **And** clicking it opens a file picker dialog

#### AC-2.2: File Selection
- **Given** the file picker is open
- **When** I browse my filesystem
- **Then** I can select any file (preferably filtered to `.md` files)
- **And** I see file names and paths clearly
- **And** I can navigate to any directory

#### AC-2.3: Copy Operation
- **Given** I selected a source file
- **When** I confirm selection
- **Then** the file is copied to `{project-root}/CLAUDE.md`
- **And** I see a success message with target path
- **And** the CLAUDE.md status indicator updates to "Present"

#### AC-2.4: Overwrite Confirmation
- **Given** my project already has a CLAUDE.md
- **When** I complete file selection
- **Then** I see a confirmation dialog warning file exists
- **And** the dialog shows both source and target paths
- **And** I can choose "Overwrite" or "Cancel"
- **And** "Overwrite" replaces existing file
- **And** "Cancel" aborts operation

#### AC-2.5: Error Handling - Large File Warning
- **Given** I selected a file larger than 50KB
- **When** I confirm selection
- **Then** I see a warning that CLAUDE.md should be concise
- **And** the file size is shown
- **And** I can choose "Continue Anyway" or "Cancel"

#### AC-2.6: Error Handling - Invalid File
- **Given** I selected a binary file or corrupted file
- **When** I confirm selection
- **Then** I see an error message
- **And** no file is copied
- **And** existing CLAUDE.md (if any) is not affected

#### AC-2.7: Cancel Flow
- **Given** the file picker is open
- **When** I click "Cancel" or close the dialog
- **Then** no file is copied
- **And** existing CLAUDE.md (if any) is not affected

### Test Scenarios

1. **Happy Path**: Reference → Select file → Confirm → Success
2. **Overwrite**: Has CLAUDE.md → Reference → Confirm overwrite → New file
3. **Large File**: Select 100KB file → Warning → Continue → Copied
4. **Cancel Selection**: Reference → Browse → Cancel → No change
5. **Read Error**: Select locked file → Error → No change

---

## User Story 3: Edit Existing CLAUDE.md

**As a** developer refining my project configuration
**I want** to open and edit my CLAUDE.md file
**So that** I can improve the project context over time

### Acceptance Criteria

#### AC-3.1: Conditional Menu Item
- **Given** my project has a CLAUDE.md file
- **When** I open the CLAUDE.md menu
- **Then** I see "Edit" option enabled
- **And** clicking it opens the file in an editor

- **Given** my project does NOT have a CLAUDE.md file
- **When** I open the CLAUDE.md menu
- **Then** the "Edit" option is disabled or hidden

#### AC-3.2: Open in System Editor
- **Given** I clicked "Edit"
- **When** the command executes
- **Then** my system's default text editor opens
- **And** the CLAUDE.md file is loaded
- **And** I can edit and save from that editor
- **And** the CMAT UI remains open and usable

#### AC-3.3: Cross-Platform Support
- **Given** I am on macOS
- **When** I click "Edit"
- **Then** `open {path}` command is used

- **Given** I am on Windows
- **When** I click "Edit"
- **Then** `os.startfile({path})` is used

- **Given** I am on Linux
- **When** I click "Edit"
- **Then** `xdg-open {path}` command is used

#### AC-3.4: Error Handling - File Missing
- **Given** CLAUDE.md existed but was recently deleted
- **When** I click "Edit"
- **Then** I see an error that file no longer exists
- **And** the status indicator updates to "Not configured"
- **And** I'm offered option to "Create New"

#### AC-3.5: Error Handling - No Default Editor
- **Given** system has no default text editor configured
- **When** I click "Edit"
- **Then** I see an error message
- **And** I'm given instructions to configure default editor
- **And** (optional) fallback to basic in-app viewer

### Test Scenarios

1. **Happy Path**: Edit → Opens in VS Code/Sublime/Notepad → Edit → Save
2. **File Deleted**: Edit → File missing error → Create new option
3. **Cross-Platform**: Test on Windows, macOS, Linux
4. **Multiple Editors**: Test with different default editors

---

## User Story 4: Monitor CLAUDE.md Status

**As a** developer working on multiple projects
**I want** to see whether my current project has CLAUDE.md configured
**So that** I know if project context is available to Claude Code

### Acceptance Criteria

#### AC-4.1: Status Indicator Display
- **Given** I have connected to a project
- **When** the connection completes
- **Then** I see CLAUDE.md status in the project info area
- **And** the status is clearly visible without scrolling

#### AC-4.2: Status - Present
- **Given** my project has a CLAUDE.md file
- **When** I view the status indicator
- **Then** it shows "CLAUDE.md: ✓ Present" (or similar positive indicator)
- **And** the indicator has positive styling (green color, checkmark icon)

#### AC-4.3: Status - Not Configured
- **Given** my project does NOT have a CLAUDE.md file
- **When** I view the status indicator
- **Then** it shows "CLAUDE.md: Not configured" (or similar)
- **And** the indicator has neutral styling (gray color)
- **And** (optional) clicking it opens CLAUDE.md menu

#### AC-4.4: Dynamic Updates - After Create
- **Given** I view a project without CLAUDE.md
- **When** I successfully create a CLAUDE.md file
- **Then** the status indicator immediately updates to "Present"
- **And** no manual refresh is required

#### AC-4.5: Dynamic Updates - After Delete
- **Given** my project has a CLAUDE.md
- **When** I delete the file externally (outside CMAT)
- **And** I refresh or interact with CMAT
- **Then** the status indicator updates to "Not configured"

#### AC-4.6: Tooltip Information
- **Given** I hover over the status indicator
- **When** the tooltip appears
- **Then** I see additional info:
  - Full path to CLAUDE.md
  - File size
  - Last modified date (if applicable)

#### AC-4.7: Status Without Connection
- **Given** I have not connected to a project
- **When** I view the connection area
- **Then** no CLAUDE.md status is shown (or shows as "N/A")

### Test Scenarios

1. **Initial Load**: Connect → Status shows correct state
2. **After Create**: Create CLAUDE.md → Status updates immediately
3. **After Reference**: Copy file → Status updates immediately
4. **After External Edit**: Edit outside CMAT → Refresh → Size updates
5. **After External Delete**: Delete outside CMAT → Refresh → Status updates

---

## User Story 5: Recover from Errors Gracefully

**As a** developer encountering issues
**I want** clear error messages and recovery options
**So that** I can resolve problems without losing work or getting stuck

### Acceptance Criteria

#### AC-5.1: API Key Not Configured
- **Given** I attempt to create CLAUDE.md
- **When** no Claude API key is configured
- **Then** I see a warning before agent invocation
- **And** I'm directed to Claude settings
- **And** operation is cancelled (not failed)

#### AC-5.2: Network Timeout
- **Given** agent invocation is in progress
- **When** network request times out
- **Then** I see error: "Request timed out after N seconds"
- **And** I can retry the operation
- **And** no partial file is created

#### AC-5.3: Rate Limited
- **Given** I've made many API requests
- **When** rate limit is hit
- **Then** I see error explaining rate limit
- **And** I see estimated wait time if available
- **And** I can retry after waiting

#### AC-5.4: Disk Full
- **Given** target disk is full
- **When** attempting to save CLAUDE.md
- **Then** I see error: "Insufficient disk space"
- **And** the error includes space needed vs available
- **And** no corrupted file is left behind

#### AC-5.5: Agent Execution Error
- **Given** the agent crashes or returns invalid output
- **When** this occurs
- **Then** I see error: "Failed to generate CLAUDE.md"
- **And** error details are logged for debugging
- **And** I can report the issue
- **And** I can try manual creation instead

### Test Scenarios

1. **No API Key**: Unset key → Create → Warning → Cancel
2. **Timeout**: Create → Slow network → Timeout → Retry
3. **Rate Limit**: Rapid requests → Rate limit → Wait → Retry
4. **Disk Full**: Fill disk → Create → Error → Clear space
5. **Agent Crash**: Mock agent error → Create → Error dialog

---

## Cross-Story Integration Tests

### Integration Test 1: Complete Workflow
1. Connect to new project (no CLAUDE.md)
2. Verify status shows "Not configured"
3. Create CLAUDE.md via agent
4. Review and save content
5. Verify status shows "Present"
6. Edit CLAUDE.md in system editor
7. Make changes and save
8. Verify file updated (check timestamp)
9. Reference different CLAUDE.md
10. Confirm overwrite
11. Verify new content loaded
12. Verify status still "Present"

### Integration Test 2: Error Recovery
1. Attempt create without API key → Warning
2. Configure API key
3. Retry create → Success
4. Attempt edit with locked file → Error
5. Unlock file
6. Retry edit → Success

### Integration Test 3: Multi-Project Switching
1. Connect to Project A (has CLAUDE.md)
2. Verify status "Present"
3. Connect to Project B (no CLAUDE.md)
4. Verify status "Not configured"
5. Create CLAUDE.md for Project B
6. Switch back to Project A
7. Verify correct status for each

---

## Non-Functional Requirements Validation

### NFR-1: Performance
- **Requirement**: CLAUDE.md creation completes within 60 seconds
- **Test**: Measure agent execution time across various project sizes
- **Success Criteria**: 95% of projects complete within 60 seconds

### NFR-2: Usability
- **Requirement**: Feature is discoverable without documentation
- **Test**: New user testing with 5 users
- **Success Criteria**: 4/5 users find and use feature without help

### NFR-3: Reliability
- **Requirement**: No file system corruption
- **Test**: Fault injection (kill process during save, remove permissions, etc.)
- **Success Criteria**: No corrupted or partial CLAUDE.md files left behind

### NFR-4: Compatibility
- **Requirement**: Works on Windows, macOS, Linux
- **Test**: Execute all test scenarios on each platform
- **Success Criteria**: 100% pass rate on all platforms

---

## Edge Cases to Test

1. **Unicode in paths**: Project path with non-ASCII characters
2. **Spaces in paths**: `/path with spaces/project`
3. **Very deep paths**: Paths exceeding 256 characters (Windows)
4. **Network drives**: Project on mapped network drive
5. **Symlinks**: Project root is a symlink
6. **Read-only filesystem**: Project on read-only mount
7. **Case-sensitive filesystems**: Linux with CLAUDE.md vs claude.md
8. **Empty CLAUDE.md**: File exists but is 0 bytes
9. **Very large CLAUDE.md**: File exceeds best practice size (> 1MB)
10. **Concurrent edits**: CMAT and external editor both modifying file

---

## Definition of Done

For this feature to be considered complete:

✅ All acceptance criteria pass for US-1 through US-5
✅ Integration tests pass
✅ Cross-platform tests pass on Windows, macOS, Linux
✅ Error handling covers all identified scenarios
✅ Code reviewed and approved
✅ Unit tests achieve >80% coverage
✅ Manual testing by product owner successful
✅ No P0 or P1 bugs remain open
✅ User documentation updated
✅ Feature flag enabled (if applicable)

---

## Prioritization

### Must Have (Phase 1)
- US-1: Generate CLAUDE.md with AI (core value)
- US-2: Reference existing CLAUDE.md (flexibility)
- US-4: Monitor CLAUDE.md status (visibility)

### Should Have (Phase 2)
- US-3: Edit existing CLAUDE.md (convenience)
- US-5: Error recovery (polish)

### Could Have (Phase 3)
- Enhanced status with metadata
- Global CLAUDE.md indicator
- In-app editor option
- CLAUDE.md templates

### Won't Have (Out of Scope)
- Validation/linting
- Version history
- Team sync
- AI-powered suggestions
