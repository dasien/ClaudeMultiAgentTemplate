---
enhancement: claude-md-feature-plan
agent: requirements-analyst
task_id: task_1767462734_14875
timestamp: 2026-01-03T22:52:00Z
status: READY_FOR_DEVELOPMENT
---

# Requirements Analysis: CLAUDE.md Management Feature

## Executive Summary

This enhancement adds CLAUDE.md file management capabilities to the CMAT Desktop UI, enabling users to create, reference, edit, and monitor project-specific Claude Code context files. The feature leverages the existing `claude-md-creator` agent to generate contextually-aware CLAUDE.md files through automated project analysis.

## Background

### What is CLAUDE.md?

CLAUDE.md is a special configuration file that Claude Code automatically reads when working in a project directory. It provides persistent project context including:
- Architecture patterns and conventions
- Development workflows
- Tech stack and dependencies
- Project structure
- Repository etiquette (branching, merge strategies)
- Environment setup instructions

**Key Characteristics:**
- Automatically pulled into Claude's context at conversation start
- Can be placed in project root, parent directories, or `~/.claude/CLAUDE.md` globally
- Treated as immutable system rules (higher priority than user prompts)
- Should be concise, human-readable, and contain only universally applicable instructions
- Best practice: Check into git for team sharing, or use `CLAUDE.local.md` for personal configs

### Current State

The `claude-md-creator` agent exists and can analyze projects to generate CLAUDE.md files, but there is no UI integration to:
1. Invoke the agent from the desktop application
2. Allow users to reference/copy existing CLAUDE.md files
3. Edit existing CLAUDE.md files
4. See CLAUDE.md status for the connected project

## Business Requirements

### Primary Goals

1. **Lower barrier to adoption**: Make it easy for CMAT users to create project-specific Claude Code context
2. **Discoverability**: Users should know whether their project has a CLAUDE.md configured
3. **Flexibility**: Support both AI-generated and user-provided CLAUDE.md files
4. **Iterability**: Allow users to edit and refine their CLAUDE.md over time

### User Stories

**US-1: As a developer, I want to generate a CLAUDE.md file for my project so that Claude Code has relevant project context**
- **Acceptance Criteria:**
  - UI provides a menu option to create CLAUDE.md
  - System invokes `claude-md-creator` agent to analyze project
  - User can review generated content before saving
  - File is saved to project root as `CLAUDE.md`

**US-2: As a developer, I want to copy an existing CLAUDE.md from another project so that I can reuse proven configurations**
- **Acceptance Criteria:**
  - UI provides file picker to select any `.md` file
  - System copies file to project root as `CLAUDE.md`
  - User is warned if CLAUDE.md already exists with option to overwrite

**US-3: As a developer, I want to edit my CLAUDE.md file so that I can refine the project context**
- **Acceptance Criteria:**
  - UI provides option to edit existing CLAUDE.md
  - File opens in appropriate editor (system default or in-app)
  - Changes are saved to the file

**US-4: As a developer, I want to see if my project has a CLAUDE.md so that I know the configuration status**
- **Acceptance Criteria:**
  - UI displays CLAUDE.md status in project info area
  - Status shows "Present" or "Not configured"
  - Status updates dynamically when file is created/deleted

## Functional Requirements

### FR-1: Menu Integration
- Add "CLAUDE.md" menu item under appropriate top-level menu
- Menu should be enabled only when project is connected
- Submenu contains: "Create", "Reference Existing", "Edit" (conditional)

### FR-2: Create CLAUDE.md Action
- Invokes `claude-md-creator` agent as one-off operation (not workflow)
- Provides agent with project root path
- Displays progress/working dialog during generation
- Shows generated content in review dialog
- User can approve/save or cancel
- Saves to `{project-root}/CLAUDE.md`

### FR-3: Reference Existing Action
- Opens file picker dialog filtered to `.md` files
- Copies selected file to `{project-root}/CLAUDE.md`
- Warns if target file exists with confirm/cancel options
- Shows success message on completion

### FR-4: Edit CLAUDE.md Action
- Only enabled when CLAUDE.md exists in project
- Opens file in editor (implementation decision needed)
- Changes are saved directly to file

### FR-5: Status Display
- Shows CLAUDE.md presence indicator in project status area
- Updates when file is created/deleted/modified
- Optional: Indicate if global `~/.claude/CLAUDE.md` exists

## Non-Functional Requirements

### NFR-1: Performance
- CLAUDE.md creation should complete within 60 seconds for typical projects
- UI must remain responsive during agent execution (use threading)
- File operations should be near-instantaneous

### NFR-2: Usability
- Feature must be discoverable without documentation
- Working dialogs must show progress indication
- Error messages must be clear and actionable
- Generated CLAUDE.md should follow best practices (concise, specific, example-driven)

### NFR-3: Reliability
- File operations must handle permissions errors gracefully
- Agent failures must not crash the UI
- System must validate file write permissions before agent execution

### NFR-4: Compatibility
- Must work on Windows, macOS, and Linux
- Must respect system file permissions
- Must handle paths with spaces and special characters

## Integration Points

### Existing System Integration

1. **Agent System**:
   - Use existing `claude-md-creator` agent definition
   - Follow one-off agent invocation pattern (if exists) or create new pattern

2. **UI Menu System**:
   - Integrate with existing `build_menu_bar()` in `main.py`
   - Follow connection-dependent menu enabling pattern
   - Add to appropriate menu (suggest: File or new top-level "Project" menu)

3. **Dialog System**:
   - Leverage `ClaudeGeneratorMixin` for async agent invocation
   - Use `WorkingDialog` for progress indication
   - Follow `BaseDialog` pattern for review/approval

4. **File System**:
   - Use existing `PathUtils` for path operations
   - Respect project root from `queue_interface.project_root`

## Risk Assessment

### Technical Challenges

**Challenge 1: One-off Agent Invocation Pattern**
- **Issue**: Current system uses workflow-based agent invocation; need to confirm one-off pattern exists
- **Impact**: MEDIUM - Core feature functionality
- **Mitigation**: If pattern doesn't exist, may need to create lightweight invocation wrapper

**Challenge 2: Editor Selection**
- **Issue**: Unclear whether to use system editor vs build in-app editor
- **Impact**: LOW - Feature still usable with either approach
- **Mitigation**: Start with system editor (simpler), consider in-app editor in future iteration

**Challenge 3: Real-time Status Updates**
- **Issue**: File status monitoring may require polling or file system watching
- **Impact**: LOW - Status can be checked on demand vs real-time
- **Mitigation**: Start with on-demand check, add polling/watching if needed

### Areas Requiring Specialist Input

1. **Architecture**: How to invoke agents outside workflow system?
2. **Architecture**: Best location for new menu items (File vs new Project menu)?
3. **Implementation**: Preferred editor approach (system vs in-app)?
4. **Testing**: How to test file system operations across platforms?

## Project Scope & Boundaries

### In Scope

✅ UI menu options for CLAUDE.md management
✅ Create action using `claude-md-creator` agent
✅ Reference/copy existing CLAUDE.md files
✅ Edit action to open existing CLAUDE.md
✅ Status indicator showing CLAUDE.md presence
✅ User approval flow for generated content
✅ File overwrite warnings
✅ Error handling for common failure scenarios

### Out of Scope

❌ Modification of `claude-md-creator` agent behavior
❌ CLAUDE.md validation or linting
❌ CLAUDE.md templates library
❌ Version control integration for CLAUDE.md
❌ Multi-file CLAUDE.md management (local vs shared)
❌ In-app CLAUDE.md syntax highlighting or preview
❌ Automatic CLAUDE.md updates based on project changes
❌ CLAUDE.md recommendations or suggestions

## Implementation Phases

### Phase 1: Foundation (Priority: HIGH)
**Goal**: Basic create and reference functionality

- Add menu structure and items
- Implement "Create CLAUDE.md" with agent invocation
- Implement "Reference Existing" with file picker
- Add basic status indicator

**Deliverables:**
- Menu items visible and functional
- Agent generates CLAUDE.md successfully
- File copy operation works correctly
- Status shows present/absent

**Success Criteria:**
- User can create CLAUDE.md via agent
- User can copy existing CLAUDE.md
- No crashes or data loss

### Phase 2: Enhancement (Priority: MEDIUM)
**Goal**: Edit functionality and polish

- Implement "Edit CLAUDE.md" action
- Add file overwrite confirmations
- Improve error messaging
- Add progress indicators

**Deliverables:**
- Edit action opens file correctly
- User confirmation dialogs
- Comprehensive error handling

**Success Criteria:**
- User can edit CLAUDE.md
- All edge cases handled gracefully
- User feedback is clear and helpful

### Phase 3: Polish (Priority: LOW)
**Goal**: Status improvements and documentation

- Real-time or periodic status updates
- Global CLAUDE.md indicator
- User documentation
- Feature announcement

**Deliverables:**
- Dynamic status updates
- Complete user guide
- Help system integration

**Success Criteria:**
- Documentation complete
- Feature fully discoverable
- Users understand CLAUDE.md value

## Dependencies

### Technical Dependencies

1. **Existing Agent**: `claude-md-creator` agent must be available in agents directory
2. **Connected Project**: All features require active project connection
3. **Agent Invocation**: Need pattern/API for invoking agents outside workflows
4. **File System Access**: Read/write permissions to project root

### Workflow Dependencies

1. Agent files must be committed to repository (Tasks 1-2 in original plan)
2. Architecture must define one-off agent invocation pattern
3. Implementation depends on architecture decisions

## Constraints & Assumptions

### Constraints

1. **No Agent Modifications**: Use existing `claude-md-creator` agent as-is
2. **Project Root Only**: CLAUDE.md always created in project root (not subdirectories)
3. **Single File**: Manage only one CLAUDE.md per project (not `.local` variants)
4. **UI-Initiated Only**: Agent invoked by user action (not automatic/background)

### Assumptions

1. Users have write permissions to project root
2. Claude API key is configured for agent execution
3. Projects are standard directory structures (not exotic layouts)
4. CLAUDE.md filename is fixed (not configurable)
5. System default editor is acceptable for editing

## Success Metrics

### Quantitative Metrics

- **Adoption Rate**: % of connected projects with CLAUDE.md after 30 days
- **Creation Method**: Ratio of agent-generated vs referenced CLAUDE.md files
- **Error Rate**: % of failed create/reference operations
- **Time to Create**: Average time from menu click to saved file

### Qualitative Metrics

- **User Feedback**: Positive sentiment about feature discoverability
- **Documentation Requests**: Low volume indicates good usability
- **Feature Requests**: Types of enhancement requests indicate usage patterns

### Validation Criteria

✅ Feature is discoverable without reading documentation
✅ Users successfully create CLAUDE.md on first attempt
✅ Generated CLAUDE.md files follow best practices (under 150 lines, project-specific)
✅ No file system corruption or permission issues
✅ Feature works consistently across Windows/macOS/Linux

## Open Questions for Architecture/Implementation

### Question 1: Agent Invocation Pattern
**Question**: How should the UI invoke one-off agents outside the workflow system?

**Context**: Current system uses `WorkflowService` and `TaskService` for agent execution within workflows. Need pattern for standalone agent invocation.

**Options**:
- A) Create lightweight wrapper in `TaskService` for one-off agents
- B) Add `run_standalone_agent()` method to `CMATInterface`
- C) Direct agent file execution without service layer
- D) Treat as minimal workflow (single-step)

**Recommendation**: Option B seems cleanest - matches existing UI pattern of calling through interface

### Question 2: Menu Location
**Question**: Where should CLAUDE.md menu items live?

**Options**:
- A) Under "File" menu (fits with project-level operations)
- B) New top-level "Project" menu (room for future project config)
- C) Under "Tools" or "Utilities" menu
- D) Submenu under connection header

**Recommendation**: Option B (new "Project" menu) - scalable for future project-level features

### Question 3: Editor Selection
**Question**: Should "Edit CLAUDE.md" use system editor or in-app editor?

**Options**:
- A) System default editor (via `subprocess` or `os.startfile()`)
- B) In-app text editor widget
- C) Read-only viewer with "Open in Editor" button
- D) User preference setting

**Recommendation**: Start with Option A (system editor) for simplicity, consider Option D later

### Question 4: Status Update Mechanism
**Question**: How should UI update CLAUDE.md status when file changes?

**Options**:
- A) Check on-demand when user views status area
- B) Poll filesystem every N seconds
- C) File system watcher (OS-level notifications)
- D) Only update after UI actions (create/delete)

**Recommendation**: Start with Option D, add Option B if users report stale status

## References & Resources

### External Documentation
- [Using CLAUDE.MD files: Customizing Claude Code for your codebase](https://claude.com/blog/using-claude-md-files)
- [What is CLAUDE.md in Claude Code | ClaudeLog](https://claudelog.com/faqs/what-is-claude-md/)
- [Writing a good CLAUDE.md | HumanLayer Blog](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Manage Claude's memory - Claude Code Docs](https://code.claude.com/docs/en/memory)

### Internal References
- Agent Definition: `.claude/agents/claude-md-creator-agent.md`
- Original Implementation Plan: `enhancements/claude-md-feature-plan/claude-md-feature-plan.md`
- UI Main Entry: `src/ui/main.py`
- Dialog Mixin: `src/ui/dialogs/mixins/claude_generator_mixin.py`
- Enhancement Dialog: `src/ui/dialogs/enhancement_create.py`

---

## Handoff Notes for Architecture Team

This requirements analysis defines **WHAT** needs to be built. The Architecture team should address:

1. **HOW** to structure one-off agent invocation (see Question 1)
2. **WHERE** to place menu items in UI hierarchy (see Question 2)
3. **WHICH** technical patterns to follow for file operations
4. **WHAT** error handling strategies to implement

The implementation is relatively straightforward once these architectural decisions are made. The primary unknowns are around agent invocation patterns and UI integration points.
