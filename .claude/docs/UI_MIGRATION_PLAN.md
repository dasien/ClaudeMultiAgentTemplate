# UI Migration Plan: ClaudeMultiAgentUI → ClaudeMultiAgentTemplate

## Executive Summary

This document outlines the plan for migrating the ClaudeMultiAgentUI Tkinter desktop application into the main ClaudeMultiAgentTemplate project as the **primary user interface**.

**Current State:**
- **UI Project:** Standalone Tkinter GUI (~10,500 lines across 26 dialogs + utils)
- **CMAT Core:** Python package at `.claude/cmat/` (v8.3.0)
- **Integration:** UI uses `CMATInterface` adapter class (880 lines) to bridge to CMAT

**Goal:** Single unified project where **UI is the default experience**.

### Launch Behavior

```bash
python -m cmat              # Launches UI (default)
python -m cmat <command>    # CLI mode when command provided
./run.py                    # Simple launcher script → UI
```

The UI becomes the natural entry point for most users. CLI commands remain available for automation, scripting, and Claude Code hooks.

---

## Architecture Analysis

### Current UI Structure

```
ClaudeMultiAgentUI/
├── src/
│   ├── main.py              # MainView class, entry point (1,037 lines)
│   ├── config.py            # UI settings (colors, sizes, Claude models)
│   ├── settings.py          # User settings persistence (~/.claude_queue_ui/)
│   ├── dialogs/             # 26 dialog windows (7,756+ lines)
│   │   ├── base_dialog.py   # BaseDialog ABC
│   │   ├── mixins/          # ClaudeGeneratorMixin
│   │   ├── workflow_*.py    # Workflow management (5 dialogs)
│   │   ├── agent_*.py       # Agent management (2 dialogs)
│   │   ├── task_*.py        # Task management (2 dialogs)
│   │   ├── enhancement_*.py # Enhancement creation (2 dialogs)
│   │   ├── learnings_*.py   # RAG browser
│   │   ├── models_manager.py
│   │   ├── install_cmat.py  # CMAT template installer
│   │   └── ...              # Other dialogs
│   ├── models/              # UI-specific models (531 lines)
│   │   ├── task.py          # Simplified Task for UI
│   │   ├── workflow_template.py
│   │   ├── queue_state.py
│   │   └── ...
│   └── utils/               # Utilities (2,266 lines)
│       ├── cmat_interface.py # Bridge to CMAT (880 lines)
│       ├── claude_api_client.py  # Direct Claude API calls
│       ├── cmat_installer.py     # Template installer logic
│       └── ...
├── assets/                  # Icons (16 PNG/SVG files)
├── requirements.txt         # pyyaml only
└── setup.py                 # Package config
```

### Current CMAT Core Structure

```
.claude/cmat/
├── __init__.py              # Package exports
├── __main__.py              # CLI entry point
├── cmat.py                  # CMAT orchestrator class
├── models/                  # Core data models
│   ├── task.py              # Full Task with enums, lifecycle
│   ├── workflow_template.py # Full WorkflowTemplate
│   └── ...
├── services/                # Business logic
│   ├── queue_service.py     # Task queue management
│   ├── workflow_service.py  # Workflow orchestration
│   ├── task_service.py      # Execution engine
│   ├── learnings_service.py # RAG system
│   └── ...
└── claude/                  # Claude CLI wrapper
```

### Integration Layer: CMATInterface

The `CMATInterface` class (880 lines) currently:
1. Initializes CMAT by adding `.claude/` to sys.path
2. Wraps CMAT service calls with UI-friendly signatures
3. Converts CMAT models to UI models (e.g., `convert_task()`)
4. Handles async execution via threading
5. Does direct JSON file manipulation for some operations

---

## Model Comparison

### Task Model

| Aspect | UI Model | CMAT Core Model |
|--------|----------|-----------------|
| Status | `str` ("pending", "active") | `TaskStatus` enum |
| Priority | `str` ("low", "normal") | `TaskPriority` enum |
| Timestamps | `str` (ISO) + `int` (Unix) | `datetime` objects |
| Metadata | `dict` (flat) | `TaskMetadata` dataclass |
| Lifecycle | None | `start()`, `complete()`, `fail()` methods |
| Duration | `runtime_seconds: int` | `get_duration_seconds()` method |

**Conversion:** `CMATInterface.convert_task()` handles translation (lines 169-234).

### WorkflowTemplate Model

| Aspect | UI Model | CMAT Core Model |
|--------|----------|-----------------|
| ID field | `slug: str` | `id: str` |
| Steps | `WorkflowStep` (UI) | `WorkflowStep` (core) |
| Input field | `input: str` | `input: str` |
| Validation | `validate_chain()` | None built-in |

**Issue:** UI uses `.slug`, CMAT uses `.id`. Same data, different names.

### QueueState (UI-Only)

Groups tasks by status for display. No CMAT equivalent - this is purely for UI rendering.

---

## Migration Options Analysis

### Option A: Keep CMATInterface (Minimal Changes)

**Approach:** Move UI to `.claude/cmat/gui/`, keep CMATInterface as adapter.

**Pros:**
- Lowest risk - UI continues working
- Clean separation between UI and core
- CMATInterface already handles conversions

**Cons:**
- 880 lines of adapter code to maintain
- Two sets of models
- Some operations bypass services (direct JSON manipulation)

### Option B: Remove CMATInterface, Direct Service Calls

**Approach:** UI calls CMAT services directly, uses core models.

**Pros:**
- Single source of truth
- No adapter maintenance
- Cleaner architecture

**Cons:**
- Higher migration effort
- UI must handle enum-to-string conversions inline
- Threading logic moves to dialogs
- Risk of breaking changes

### Option C: Hybrid - Thin Adapter Layer

**Approach:** Keep minimal adapter for async/threading and model conversion only.

**Pros:**
- Best of both worlds
- Clean async handling
- Reduced code duplication

**Cons:**
- Still some adapter code
- Need to decide what stays vs goes

---

## Recommendation: Option C (Hybrid)

### What to Keep in Adapter

1. **Async execution wrapper** - Threading for long-running tasks
2. **Model conversion helpers** - Core → UI display formats
3. **Service property accessors** - `@property learnings`, `@property models`

### What to Remove from Adapter

1. **Direct JSON file manipulation** - Use service methods
2. **Duplicate queue operations** - Use `QueueService` directly
3. **Workflow template CRUD** - Use `WorkflowService` methods
4. **Skills operations** - Use `SkillsService` directly

### Migration Steps

#### Phase 1: Project Structure (Day 1)

1. Create `.claude/cmat/ui/` directory
2. Move UI source files:
   ```
   .claude/cmat/ui/
   ├── __init__.py
   ├── main.py
   ├── config.py
   ├── settings.py
   ├── dialogs/
   ├── models/          # Keep UI models for now
   ├── utils/
   └── assets/
   ```
3. Update imports throughout

#### Phase 2: CLI Integration (Day 1)

1. Update `__main__.py` to launch UI by default:
   ```python
   def main():
       args = sys.argv[1:]

       # No args = launch UI
       if not args:
           from .ui import main as ui_main
           ui_main()
           return 0

       # Otherwise process CLI command
       cmd = args[0]
       ...
   ```

2. Add `run.py` launcher script at project root:
   ```python
   #!/usr/bin/env python3
   from cmat.ui import main
   main()
   ```

3. Update `pyproject.toml` with optional Pillow dependency:
   ```toml
   [project.optional-dependencies]
   icons = ["pillow>=9.0"]  # For high-res icons
   ```

#### Phase 3: Slim CMATInterface (Day 2-3)

1. Replace direct JSON operations with service calls:
   - `clear_finished_tasks()` → `QueueService` method
   - `reset_queue()` → `QueueService.init(force=True)`
   - Workflow template CRUD → `WorkflowService` methods

2. Move async execution to a utility:
   ```python
   # .claude/cmat/gui/utils/async_runner.py
   def run_async(func, on_success=None, on_error=None):
       """Run function in background thread with callbacks."""
       ...
   ```

3. Keep model conversion as simple functions:
   ```python
   # .claude/cmat/gui/utils/converters.py
   def task_to_display(cmat_task) -> dict:
       """Convert CMAT Task to display format."""
       ...
   ```

#### Phase 4: Model Consolidation (Day 3-4)

**Decision Point:** Should UI use core models directly?

**Option A: Keep UI models** (Recommended for initial migration)
- Less disruptive
- UI models can be deprecated later
- Conversion functions handle translation

**Option B: Remove UI models**
- Update all dialogs to use core models
- Handle enum-to-string conversions inline
- More work, cleaner result

For Phase 4, recommend Option A - keep UI models for now, deprecate in future release.

#### Phase 5: Claude API Consolidation (Day 4-5)

The UI has its own `ClaudeAPIClient` for enhancement generation. Options:

**Option A: Keep separate** (Recommended)
- UI API client is for enhancement generation (uses raw API)
- CMAT's ClaudeClient is for agent execution (uses Claude Code CLI)
- Different purposes, keep separate

**Option B: Consolidate**
- Add API client to CMAT core
- UI uses core client
- More complexity for little benefit

#### Phase 6: Settings Consolidation (Day 5)

Current UI settings: `~/.claude_queue_ui/settings.json`
- Claude API key
- Selected model
- Last project path
- Max tokens, timeout

Options:
1. Keep separate settings file for GUI
2. Add GUI settings section to `.claude/settings.json`
3. Use CMAT's settings infrastructure

Recommend: Keep separate for now (`~/.claude_queue_ui/`), consider consolidation later.

---

## File Mapping

### Files to Move

| From | To |
|------|-----|
| `ClaudeMultiAgentUI/src/main.py` | `.claude/cmat/ui/main.py` |
| `ClaudeMultiAgentUI/src/config.py` | `.claude/cmat/ui/config.py` |
| `ClaudeMultiAgentUI/src/settings.py` | `.claude/cmat/ui/settings.py` |
| `ClaudeMultiAgentUI/src/dialogs/` | `.claude/cmat/ui/dialogs/` |
| `ClaudeMultiAgentUI/src/models/` | `.claude/cmat/ui/models/` |
| `ClaudeMultiAgentUI/src/utils/` | `.claude/cmat/ui/utils/` |
| `ClaudeMultiAgentUI/assets/` | `.claude/cmat/ui/assets/` |

### Files to Modify

| File | Changes                      |
|------|------------------------------|
| `.claude/cmat/__init__.py` | Export GUI launcher          |
| `.claude/cmat/__main__.py` | Add `startui` command        |
| `.claude/pyproject.toml` | Add UI optional dependency   |
| All `src/` imports | Update to `.cmat.ui.` prefix |

### Files to Remove/Consolidate

| File | Action |
|------|--------|
| `ClaudeMultiAgentUI/setup.py` | Not needed after merge |
| `ClaudeMultiAgentUI/requirements.txt` | Merge into pyproject.toml |
| `ClaudeMultiAgentUI/run.py` | Replace with `python -m cmat gui` |

---

## Pros and Cons of Removing CMATInterface

### Arguments FOR Removing CMATInterface

1. **Single Source of Truth**: No duplicate models, no conversion bugs
2. **Reduced Maintenance**: 880 fewer lines to maintain
3. **Direct Service Access**: UI gets all service features immediately
4. **Simpler Architecture**: One layer, not two
5. **Type Safety**: Core models have proper enums and types

### Arguments AGAINST Removing CMATInterface

1. **Higher Risk**: More code changes, more potential bugs
2. **Threading Complexity**: Need to handle async in each dialog
3. **Conversion Overhead**: Inline conversions in every dialog
4. **Development Time**: Significantly more effort
5. **Testing**: Need comprehensive tests for direct integration

### Verdict

**Keep a thin adapter layer** for:
- Async/threading utilities
- Model conversion helpers
- Service property accessors

Remove:
- Direct JSON manipulation
- Duplicate service logic
- Redundant wrapper methods

---

## Implementation Checklist

### Pre-Migration
- [ ] Create branch `feature/ui-integration`
- [ ] Document current UI functionality
- [ ] Identify all service calls used by UI
- [ ] List all CMATInterface methods that bypass services

### Phase 1: Structure
- [ ] Create `.claude/cmat/ui/` directory
- [ ] Move all UI source files
- [ ] Update all imports
- [ ] Verify UI launches from new location

### Phase 2: CLI
- [ ] Update `__main__.py` to launch UI by default (no args)
- [ ] Test `python -m cmat` launches UI
- [ ] Test `python -m cmat queue list` still works (CLI mode)
- [ ] Add `run.py` launcher script at project root
- [ ] Update pyproject.toml with optional Pillow dependency
- [ ] Document new launch behavior

### Phase 3: Adapter Cleanup
- [ ] List CMATInterface methods
- [ ] Identify which use direct JSON access
- [ ] Replace with service calls
- [ ] Test each replaced method

### Phase 4: Models
- [ ] Mark UI models as deprecated (but keep)
- [ ] Document conversion functions
- [ ] Add TODO comments for future removal

### Phase 5: Claude API
- [ ] Keep UI's Claude API client separate
- [ ] Document purpose difference

### Phase 6: Settings
- [ ] Keep GUI settings separate for now
- [ ] Document settings locations

### Post-Migration
- [ ] Update README with GUI launch instructions
- [ ] Update INSTALLATION.md with GUI deps
- [ ] Bump version to 9.0.0
- [ ] Archive or delete ClaudeMultiAgentUI repo

---

## Version Considerations

This is a major structural change. Recommend:
- Version: **9.0.0** (major version bump)
- Breaking change: Launch command changes
- New feature: Integrated GUI component

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Import errors after move | High | Medium | Comprehensive import search/replace |
| Threading issues | Medium | High | Keep async utilities isolated |
| Model conversion bugs | Medium | Medium | Keep UI models initially |
| Settings compatibility | Low | Medium | Keep settings file separate |
| Feature regression | Medium | High | Manual testing of all dialogs |

---

## Open Questions

1. **Installer functionality**: Keep CMAT installer in GUI, or move to CLI?
2. **Settings location**: Should GUI settings move to project-level config?
3. **Future TUI**: Plan for Textual TUI alongside Tkinter GUI?
4. **Separate package**: Should GUI be `cmat[gui]` optional extra or always included?

---

## Combined Directory Structure (Post-Migration)

After migration, the unified project will have this structure:

```
ClaudeMultiAgentTemplate/
├── run.py                           # Simple launcher → UI
├── demo/                            # Demo project for testing
│   ├── calculator.py
│   └── test_calculator.py
├── enhancements/                    # Enhancement workspaces
│   └── {enhancement-name}/
│       ├── {agent}/required_output/
│       └── logs/
│
└── .claude/                         # CMAT system directory
    ├── pyproject.toml               # Package config (updated)
    ├── settings.json                # Claude Code settings
    ├── manifest.json                # Project metadata
    │
    ├── cmat/                        # Main Python package
    │   ├── __init__.py              # Exports CMAT class + version
    │   ├── __main__.py              # Entry point: UI default, CLI with args
    │   ├── cmat.py                  # CMAT orchestrator class
    │   ├── utils.py                 # Shared utilities
    │   │
    │   ├── models/                  # Core data models
    │   │   ├── __init__.py
    │   │   ├── task.py              # Task, TaskStatus, TaskPriority
    │   │   ├── task_metadata.py     # TaskMetadata
    │   │   ├── agent.py             # Agent
    │   │   ├── skill.py             # Skill
    │   │   ├── workflow_template.py # WorkflowTemplate
    │   │   ├── workflow_step.py     # WorkflowStep
    │   │   ├── step_transition.py   # StepTransition
    │   │   ├── learning.py          # Learning (RAG)
    │   │   ├── claude_model.py      # ClaudeModel, ModelPricing
    │   │   ├── enhancement.py       # Enhancement
    │   │   └── tool.py              # Tool
    │   │
    │   ├── services/                # Business logic layer
    │   │   ├── __init__.py
    │   │   ├── queue_service.py     # Task queue management
    │   │   ├── agent_service.py     # Agent registry
    │   │   ├── skills_service.py    # Skills management
    │   │   ├── workflow_service.py  # Workflow orchestration
    │   │   ├── task_service.py      # Execution engine
    │   │   ├── learnings_service.py # RAG system
    │   │   └── model_service.py     # Claude model config
    │   │
    │   ├── claude/                  # Claude CLI wrapper
    │   │   ├── __init__.py
    │   │   ├── client.py            # ClaudeClient
    │   │   ├── config.py            # ClaudeClientConfig
    │   │   └── response.py          # ClaudeResponse
    │   │
    │   └── ui/                      # ← NEW: Tkinter GUI (from ClaudeMultiAgentUI)
    │       ├── __init__.py          # Exports main()
    │       ├── main.py              # MainView class
    │       ├── config.py            # UI config (colors, sizes)
    │       ├── settings.py          # User settings (~/.claude_queue_ui/)
    │       │
    │       ├── dialogs/             # 26 dialog windows
    │       │   ├── __init__.py
    │       │   ├── base_dialog.py   # BaseDialog ABC
    │       │   ├── mixins/          # ClaudeGeneratorMixin
    │       │   │   ├── __init__.py
    │       │   │   └── claude_generator_mixin.py
    │       │   ├── about.py
    │       │   ├── agent_details.py
    │       │   ├── agent_list.py
    │       │   ├── claude_settings.py
    │       │   ├── connect.py
    │       │   ├── enhancement_create.py
    │       │   ├── enhancement_preview.py
    │       │   ├── install_cmat.py
    │       │   ├── integration_dashboard.py
    │       │   ├── learnings_browser.py
    │       │   ├── log_viewer.py
    │       │   ├── models_manager.py
    │       │   ├── skills_list.py
    │       │   ├── task_create.py
    │       │   ├── task_details.py
    │       │   ├── workflow_launcher.py
    │       │   ├── workflow_step_editor.py
    │       │   ├── workflow_template_editor.py
    │       │   ├── workflow_template_manager.py
    │       │   ├── workflow_transition_editor.py
    │       │   ├── workflow_viewer.py
    │       │   └── working.py
    │       │
    │       ├── models/              # UI-specific models (deprecated)
    │       │   ├── __init__.py
    │       │   ├── task.py          # Simplified Task for display
    │       │   ├── workflow_template.py
    │       │   ├── queue_state.py
    │       │   ├── connection_state.py
    │       │   ├── queue_ui_state.py
    │       │   ├── agent.py
    │       │   ├── agent_status.py
    │       │   ├── agent_persona.py
    │       │   ├── tool.py
    │       │   └── enhancement_source.py
    │       │
    │       ├── utils/               # UI utilities
    │       │   ├── __init__.py
    │       │   ├── cmat_interface.py  # Adapter (slimmed)
    │       │   ├── claude_api_client.py  # Direct API for generation
    │       │   ├── cmat_installer.py     # Template installer
    │       │   ├── path_utils.py
    │       │   └── time_utils.py
    │       │
    │       └── assets/              # Icons and images
    │           ├── icon.png
    │           ├── icon.svg
    │           └── ...
    │
    ├── agents/                      # Agent definitions
    │   ├── agents.json
    │   ├── requirements-analyst.md
    │   ├── architect.md
    │   ├── implementer.md
    │   ├── tester.md
    │   └── documenter.md
    │
    ├── skills/                      # Skill definitions
    │   ├── skills.json
    │   └── {skill-name}/
    │       └── SKILL.md
    │
    ├── data/                        # Runtime data
    │   ├── task_queue.json
    │   ├── workflow_templates.json
    │   ├── learnings.json
    │   └── models.json
    │
    ├── docs/                        # Documentation
    │   ├── CLI_REFERENCE.md
    │   ├── WORKFLOW_GUIDE.md
    │   ├── QUEUE_SYSTEM_GUIDE.md
    │   ├── LEARNINGS_GUIDE.md
    │   └── ...
    │
    ├── hooks/                       # Claude Code hooks
    │   └── SubAgentComplete.js
    │
    ├── logs/                        # System logs
    │   └── queue_operations.log
    │
    └── tests/                       # Unit tests
        ├── test_models.py
        ├── test_services.py
        └── ...
```

### Key Structural Changes

| Aspect | Before | After |
|--------|--------|-------|
| UI location | Separate repo | `.claude/cmat/ui/` |
| Launch method | `python ClaudeMultiAgentUI/run.py` | `python -m cmat` or `./run.py` |
| CLI commands | `python -m cmat <cmd>` | Same (when args provided) |
| Settings | `~/.claude_queue_ui/` | Same (unchanged) |
| Assets | `ClaudeMultiAgentUI/assets/` | `.claude/cmat/ui/assets/` |

---

## Summary

**Recommended Approach:**
1. Move UI files to `.claude/cmat/ui/`
2. UI launches by default (`python -m cmat` with no args)
3. CLI commands still work when args provided
4. Keep thin adapter layer for async + conversions
5. Remove direct JSON manipulation from adapter
6. Keep UI models for now (deprecate later)
7. Keep separate Claude API clients
8. Keep separate settings files

**Estimated Effort:** 5 days
**Risk Level:** Medium
**Version Bump:** 8.3.0 → 9.0.0yes
