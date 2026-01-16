---
slug: feature-name-here
status: NEW
created: YYYY-MM-DD
author: Your Name
priority: low|medium|high|critical
---

# Enhancement: [Brief Title]

## Overview
**Goal:** [One sentence describing what this enhancement accomplishes]

**User Story:**
As a [type of user], I want [goal] so that [benefit/reason].

## Context & Background
**Current State:**
- What exists today in the codebase
- Relevant system components
- Why this enhancement is needed now

**Technical Context:**
- Target platform/environment
- Performance requirements
- Integration points with existing systems

**Dependencies:**
- Other features or components this relies on
- External libraries or tools needed
- Related enhancements (reference other slugs)

## Requirements

### Functional Requirements
1. [Specific capability the system must have]
2. [Another required function]
3. [User-facing behavior]

### Non-Functional Requirements
- **Performance:** [Response time, throughput, resource usage]
- **Reliability:** [Error handling, edge cases]
- **Compatibility:** [Backwards compatibility, platform support]

### Required Work
> All items in this section MUST be completed for the enhancement to be considered done.
> Do not skip any items. Do not treat any items as optional.

- [ ] [Specific task 1]
- [ ] [Specific task 2]
- [ ] [Specific task 3]

### Out of Scope
> Explicitly list what this enhancement does NOT include to prevent scope creep.
> These items should not be worked on as part of this enhancement.

- [Feature X] - Will be addressed in a separate enhancement
- [Feature Y] - Not needed for this use case

## Open Questions
> These need answers before implementation begins.
> If questions remain unanswered, the agent should ask for clarification.

1. [Question about design approach]
2. [Question about API/interface decisions]

## Constraints & Limitations
**Technical Constraints:**
- Must not break: [existing features]
- Must use: [specific APIs/patterns]
- Must maintain: [backwards compatibility requirements]

## Success Criteria

### Definition of Done
> ALL of these criteria must be met. This is not a checklist of options.

- [ ] All Required Work items completed
- [ ] All acceptance tests pass
- [ ] No regressions in existing features
- [ ] Code imports/compiles without errors

### Acceptance Tests
> Concrete, verifiable test cases. Each must pass.

1. Given [initial state], when [action], then [expected result]
2. Given [scenario], when [action], then [expected outcome]
3. Edge case: [specific test case]

### Verification Commands
> Commands to run to verify the enhancement is complete.

```bash
# Example: Verify no messagebox imports remain
grep -l "from tkinter import.*messagebox" src/ui/dialogs/*.py
# Expected: Only base_dialog.py

# Example: Verify application launches
python -c "from src.ui.dialogs import *"
# Expected: No errors
```

## Security & Safety Considerations
- Data validation requirements
- Error handling approach
- Resource cleanup needs
- Potential risks and mitigations

## UI/UX Considerations (if applicable)
- User interaction flow
- Input/output format
- Error messages

## Testing Strategy
**Unit Tests:**
- [Component A: test cases]
- [Component B: test cases]

**Integration Tests:**
- [System interaction X]
- [Edge case Y]

**Manual Test Scenarios:**
1. [Step-by-step test case]
2. [Another verification scenario]

## Implementation Checklist
> Specific files and changes required. Be explicit about what needs to change.

### Files to Modify
| File | Changes Required |
|------|------------------|
| `path/to/file1.py` | [Specific changes] |
| `path/to/file2.py` | [Specific changes] |

### Implementation Pattern
> If a pattern should be applied repeatedly, document it clearly.

```python
# BEFORE:
[old code pattern]

# AFTER:
[new code pattern]
```

## References & Research
- [Link to relevant documentation]
- [Similar implementations]
- [Technical specifications]

## Notes for Subagents

### For Architect
- Pay special attention to [specific concerns]
- Consider impact on [existing component]
- ALL Required Work items must be included in the implementation plan

### For Implementer
- Complete ALL items in Required Work section
- Follow the Implementation Pattern exactly
- Do not skip any files listed in Implementation Checklist
- Run Verification Commands before marking complete

### For Tester
- Verify ALL Acceptance Tests pass
- Run ALL Verification Commands
- Test ALL files listed in Implementation Checklist
- Report any items from Required Work that are incomplete