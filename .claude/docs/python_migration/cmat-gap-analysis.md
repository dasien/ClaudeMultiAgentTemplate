# CMAT Python Migration - Gap Analysis

## Summary

Based on the comprehensive bash analysis and review of actual Python files, here are the gaps and required changes.

---

## 1. Queue Service Gaps

### Commands Coverage

| Command | Bash | Python Status | Action |
|---------|------|---------------|--------|
| `add` | ✅ | ✅ Exists | Minor fix: task ID format |
| `start` | ✅ | ❌ Broken | Rewrite: must move to active_workflows |
| `complete` | ✅ | ❌ Broken | Fix: search active_workflows, not pending |
| `fail` | ✅ | ❌ Broken | Fix: search active_workflows, not pending |
| `cancel` | ✅ | ⚠️ Partial | Fix: handle active tasks + PID kill |
| `rerun` | ✅ | ❌ Missing | Add method |
| `cancel-all` | ✅ | ❌ Missing | Add method |
| `status` | ✅ | ❌ Missing | Add method |
| `list` (all types) | ✅ | ⚠️ Partial | Add `list_active()` |
| `metadata` | ✅ | ⚠️ Partial | Add `update_single_metadata(key, value)` |
| `preview-prompt` | ✅ | ❌ Missing | Add method (low priority) |
| `clear-finished` | ✅ | ⚠️ Partial | Exists as separate methods |
| `init` | ✅ | ❌ Missing | Add method |
| `show-task-cost` | ✅ | ❌ Missing | Add method (low priority) |
| `show-enhancement-cost` | ✅ | ❌ Missing | Add method (low priority) |

### Critical Fixes Required

1. **`start()`** - Currently only updates status in place. Must:
   - Move task from `pending_tasks` to `active_workflows`
   - NOT invoke agent (that's TaskService's job now)

2. **`complete()` and `fail()`** - Currently search `pending_tasks`. Must search `active_workflows`

3. **`get()`** - Missing `active_workflows` in search

---

## 2. Agent Service Gaps

### Commands Coverage

| Command | Bash | Python Status | Action |
|---------|------|---------------|--------|
| `list` | ✅ | ✅ Exists | OK |
| `invoke` | ✅ | ❌ Missing | Move to TaskService |
| `invoke-direct` | ✅ | ❌ Missing | Move to TaskService |
| `generate-json` | ✅ | ❌ Missing | Add method |

### Architecture Change

AgentService stays as a **pure registry** (CRUD only). All execution logic moves to the new **TaskService**.

---

## 3. Task Service (NEW)

This is a **new service** that doesn't exist yet. It handles all execution logic.

| Method | Source | Status |
|--------|--------|--------|
| `execute()` | bash `execute_agent_core` | ❌ Create |
| `execute_direct()` | bash `invoke_agent_direct` | ❌ Create |
| `build_prompt()` | bash template substitution | ❌ Create |
| `get_template()` | bash `load_task_template` | ❌ Create |
| `extract_status()` | bash regex extraction | ❌ Create |

---

## 4. Workflow Service Gaps

### Commands Coverage

| Command | Bash | Python Status | Action |
|---------|------|---------------|--------|
| `create` | ✅ | ❌ Missing | Add method |
| `list` | ✅ | ✅ Exists | OK |
| `show` | ✅ | ✅ Exists (as `get`) | OK |
| `delete` | ✅ | ✅ Exists | OK |
| `validate` | ✅ | ✅ Exists | OK |
| `add-step` | ✅ | ❌ Missing | Add method |
| `edit-step` | ✅ | ❌ Missing | Add method |
| `remove-step` | ✅ | ❌ Missing | Add method |
| `list-steps` | ✅ | ❌ Missing | Add method |
| `show-step` | ✅ | ✅ Exists (`get_step_at_index`) | OK |
| `add-transition` | ✅ | ❌ Missing | Add method |
| `remove-transition` | ✅ | ❌ Missing | Add method |
| `list-transitions` | ✅ | ❌ Missing | Add method |
| `start` | ✅ | ❌ Missing | Add `start_workflow()` |
| `auto-chain` | ✅ | ❌ Missing | Add `auto_chain()` |
| `validate-output` | ✅ | ❌ Missing | Add `validate_agent_outputs()` |
| `get-task-type` | ✅ | ❌ Missing | Add `get_task_type_for_agent()` |

### Orchestration Methods (Critical)

| Method | Priority | Status |
|--------|----------|--------|
| `start_workflow()` | **CRITICAL** | ❌ Missing |
| `run_task()` | **CRITICAL** | ❌ Missing |
| `auto_chain()` | **CRITICAL** | ❌ Missing |
| `validate_agent_outputs()` | HIGH | ❌ Missing |
| `set_services()` | HIGH | ❌ Missing |

---

## 5. Skills Service Gaps

### Commands Coverage

| Command | Bash | Python Status | Action |
|---------|------|---------------|--------|
| `list` | ✅ | ✅ Exists | OK |
| `get` | ✅ | ✅ Exists | OK |
| `load` | ✅ | ✅ Exists (`get_skill_content`) | OK |
| `prompt` | ✅ | ⚠️ Partial | Fix formatting in `build_skills_prompt()` |
| `test` | ✅ | ❌ Missing | Low priority |

### Fix Required

`get_combined_skill_content()` exists but doesn't match bash header/footer formatting. Need to add `build_skills_prompt()` with proper formatting.

---

## 6. Integration Service Gaps

| Command | Bash | Python Status | Action |
|---------|------|---------------|--------|
| `add` | ✅ | ❌ Missing | Deferred |
| `sync` | ✅ | ❌ Missing | Deferred |
| `sync-all` | ✅ | ❌ Missing | Deferred |

**Note:** Integration service is lower priority. It just creates tasks for `integration-coordinator` agent.

---

## 7. Claude Client Gaps

| Feature | Bash | Python Status | Action |
|---------|------|---------------|--------|
| Basic execution | ✅ | ✅ Exists | OK |
| PID tracking | ✅ | ❌ Missing | Add to TaskService |
| Background execution | ✅ | ❌ Missing | Add to TaskService |

---

## 8. Model Fixes Required

| Model | Issue | Fix |
|-------|-------|-----|
| `task.py` | `TaskStatus.IN_PROGRESS` | Rename to `ACTIVE` |
| `task.py` | `TaskPriority.MEDIUM` | Rename to `NORMAL` |
| `task.py` | Import `from .utils` | Change to `from cmat.utils` |

---

## 9. CMAT Entry Point Gaps

| Feature | Status | Action |
|---------|--------|--------|
| TaskService integration | ❌ Missing | Add |
| ClaudeClient integration | ❌ Missing | Add |
| Service dependency wiring | ❌ Missing | Add |

---

## 10. Implementation Priority

### Phase 1: Fix Foundations (BLOCKING)
- [ ] Fix `task.py` enums and import
- [ ] Fix `QueueService.start()` 
- [ ] Fix `QueueService.complete()` and `fail()`
- [ ] Add `QueueService.list_active()`
- [ ] Fix `QueueService.get()` to search active_workflows

### Phase 2: Add TaskService (CRITICAL)
- [ ] Create `task_service.py`
- [ ] Implement `execute()`
- [ ] Implement `build_prompt()`
- [ ] Implement `extract_status()`
- [ ] Implement `execute_direct()`

### Phase 3: Add Workflow Orchestration (CRITICAL)
- [ ] Add `WorkflowService.set_services()`
- [ ] Add `WorkflowService.start_workflow()`
- [ ] Add `WorkflowService.run_task()`
- [ ] Add `WorkflowService.auto_chain()`
- [ ] Add `WorkflowService.validate_agent_outputs()`
- [ ] Add `WorkflowService.get_task_type_for_agent()`

### Phase 4: Wire Up CMAT Entry Point (HIGH)
- [ ] Add TaskService to `cmat.py`
- [ ] Add ClaudeClient to `cmat.py`
- [ ] Wire service dependencies

### Phase 5: Complete Queue Commands (MEDIUM)
- [ ] Add `rerun()`
- [ ] Add `cancel_all()`
- [ ] Add `update_single_metadata()`
- [ ] Fix `cancel()` for active tasks

### Phase 6: Skills Formatting (MEDIUM)
- [ ] Add `build_skills_prompt()` with proper formatting

### Phase 7: Workflow Template CRUD (MEDIUM)
- [ ] Add `create()`
- [ ] Add `add_step()`
- [ ] Add `remove_step()`
- [ ] Add `add_transition()`
- [ ] Add `remove_transition()`

### Phase 8: Polish (LOW)
- [ ] Add `QueueService.status()`
- [ ] Add `QueueService.init()`
- [ ] Add `QueueService.preview_prompt()`
- [ ] Add cost aggregation methods
- [ ] Add `AgentService.generate_agents_json()`
- [ ] Add Integration Service
