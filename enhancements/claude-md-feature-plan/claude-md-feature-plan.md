# CLAUDE.md Management Feature - Implementation Plan

## Overview

Add the ability for users to create or reference a CLAUDE.md file for their projects. This file provides project context that Claude Code reads automatically when running workflows.

## Completed

- [x] Create Claude Markdown Creator agent definition (`claude-md-creator.md`)
- [x] Add agent entry to `agents.json`

## Remaining Tasks

### 1. Add Agent File to Repository

**Task**: Save the `claude-md-creator.md` file to the agents directory.

**Location**: `.claude/agents/claude-md-creator.md`

**Status**: Ready to commit (artifact created)

---

### 2. Update agents.json in Repository

**Task**: Update the `agents.json` file with the new agent entry.

**Location**: `.claude/agents/agents.json`

**Status**: Ready to commit (artifact created)

---

### 3. UI: Add Menu Option for CLAUDE.md Management

**Task**: Add a new menu item or button in the CMAT Desktop UI for managing CLAUDE.md files.

**Location**: UI project (likely in a menu or project settings area)

**Requirements**:
- Menu item labeled "CLAUDE.md" or "Project Context"
- Submenu or dialog with three options:
  - "Create CLAUDE.md" - Triggers the Claude Markdown Creator agent
  - "Reference Existing" - File picker to select/copy an existing CLAUDE.md
  - "Edit CLAUDE.md" - Opens existing file for editing (only shown if file exists)

**Acceptance Criteria**:
- Menu option visible when a project is connected
- Options appropriately enabled/disabled based on whether CLAUDE.md exists

---

### 4. UI: Implement "Create CLAUDE.md" Action

**Task**: Wire up the Create action to invoke the Claude Markdown Creator agent.

**Requirements**:
- Invoke the `claude-md-creator` agent as a one-off operation (not a workflow)
- Target the currently connected project directory
- Display agent output to user for review
- Save the generated CLAUDE.md to project root upon user approval

**Acceptance Criteria**:
- Agent runs and analyzes the project
- User sees the generated CLAUDE.md content
- User can approve/save or cancel
- File is written to `{project-root}/CLAUDE.md`

---

### 5. UI: Implement "Reference Existing" Action

**Task**: Allow user to select an existing CLAUDE.md file and copy it into the project.

**Requirements**:
- File picker dialog to select a `.md` file
- Copy selected file to `{project-root}/CLAUDE.md`
- Warn if CLAUDE.md already exists in project (offer to overwrite)

**Acceptance Criteria**:
- User can browse and select a file
- File is copied to project root
- Overwrite confirmation if file exists

---

### 6. UI: Implement "Edit CLAUDE.md" Action

**Task**: Open the existing CLAUDE.md for editing.

**Requirements**:
- Open file in system default editor, or
- Open in an in-app editor/viewer

**Acceptance Criteria**:
- User can view and edit the file
- Changes are saved

---

### 7. UI: Display CLAUDE.md Status

**Task**: Show whether the current project has a CLAUDE.md file.

**Location**: Project info panel or status area

**Requirements**:
- Indicator showing "CLAUDE.md: Present" or "CLAUDE.md: Not configured"
- Optional: Show if a global `~/.claude/CLAUDE.md` exists (informational only)

**Acceptance Criteria**:
- Status is visible when project is connected
- Status updates when file is created/deleted

---

### 8. Documentation

**Task**: Document the CLAUDE.md management feature.

**Requirements**:
- What CLAUDE.md is and why it matters
- How to create one (via agent or manually)
- How to reference an existing one
- What makes a good CLAUDE.md (brief summary, link to agent's guidance)

**Location**: CMAT user documentation / help system

---

## Implementation Order

Recommended sequence:

1. **Commit agent files** (Tasks 1-2) - No dependencies
2. **Add menu option** (Task 3) - UI scaffolding
3. **Implement Create action** (Task 4) - Core feature
4. **Implement Reference action** (Task 5) - Secondary feature
5. **Implement Edit action** (Task 6) - Convenience feature
6. **Add status display** (Task 7) - Polish
7. **Documentation** (Task 8) - Final step

---

## Open Questions

1. **In-app editor vs system editor**: Should "Edit CLAUDE.md" open the file in the system's default editor, or should CMAT have a built-in editor?

2. **Agent invocation mechanism**: How does the UI currently invoke one-off agent operations outside of workflows? Does this pattern exist, or does it need to be created?

3. **User approval flow**: After the agent generates a CLAUDE.md, what's the UI for reviewing and approving it? Modal dialog? Side panel? Diff view?

---

## Dependencies

- Claude Markdown Creator agent must be available in the agents directory
- UI must have a connected project to enable these features
- One-off agent invocation mechanism (may already exist for other features)
