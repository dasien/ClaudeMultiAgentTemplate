---
slug: bug-fix-name
status: NEW
created: YYYY-MM-DD
author: Your Name
priority: low|medium|high|critical
bug-id: UNIQUE-BUG-ID
---

# Bug Fix: [Brief Title]

**Summary:** [One sentence describing the bug and fix needed]

**Impact:** [Who/what is affected - users, features, systems]

## Bug Details

**Environment:**
- Platform: [6502 emulated machine, web, mobile, etc.]
- Software Version: [Specific version where bug occurs]
- Browser/OS: [If applicable]
- Connection: [WiFi, 4G, etc. if network-related]

**Bug Classification:**
- **Severity:** Critical | High | Medium | Low
- **Priority:** P1 | P2 | P3 | P4 | P5
- **Type:** Crash | Data Loss | Functional | UI/UX | Performance

## Reproduction

**Steps to Reproduce:**
1. [Specific step - be detailed]
2. [Next step - include exact clicks/inputs]
3. [Final step that triggers the bug]

**Reproduction Rate:** [X out of Y attempts] or [Always|Sometimes|Rarely]

**Test Data Needed:**
- [Specific user accounts, files, or conditions required]
- [Any special setup or configuration]

## Expected vs Actual Behavior

**Expected Result:**
[What should happen when following the reproduction steps]

**Actual Result:**
[What actually happens - include error messages, crashes, wrong outputs]

**Screenshots/Evidence:**
- [ ] Screenshot attached showing the bug
- [ ] Error logs captured
- [ ] Console output included (if applicable)

## Root Cause Analysis

**Suspected Cause:**
[Initial theory about what's causing the bug - can be updated during investigation]

**Code Areas Affected:**
- [Module/file likely involved]
- [Related components that might be impacted]

## Fix Requirements

### Required Work
> ALL items MUST be completed. Do not skip any items.

- [ ] Resolve the core issue described above
- [ ] Ensure no regression in related functionality
- [ ] Handle edge cases mentioned in reproduction

### Out of Scope
> These items should NOT be addressed as part of this bug fix.

- [Related issues that are separate bugs]
- [Improvements that should be separate enhancements]

### Constraints
- **Memory Budget:** [Maximum additional memory if applicable]
- **Performance:** [Cannot slow down X by more than Y]
- **Compatibility:** [Must maintain backward compatibility with...]

## Testing Strategy

**Unit Tests Required:**
- [ ] Test the specific bug scenario
- [ ] Test edge cases that could trigger similar issues
- [ ] Verify related functionality still works

**Integration Tests:**
- [ ] End-to-end workflow that includes the fixed functionality
- [ ] Cross-browser/platform testing (if applicable)

**Manual Test Cases:**
1. **Verify Fix:** Follow reproduction steps → should now work correctly
2. **Regression Test:** [Test related features that could be affected]
3. **Edge Cases:** [Test boundary conditions, error states]

**Test Data:**
- Use the same test data from reproduction steps
- Additional test scenarios: [list any special cases]

## Success Criteria
> ALL criteria must be met for completion.

**Definition of Done:**
- [ ] All Required Work items completed
- [ ] Bug no longer reproduces following original steps
- [ ] All new unit tests pass
- [ ] No regressions detected in related functionality
- [ ] Manual testing verification complete

**Acceptance Criteria:**
- Given [original reproduction scenario], when [steps are followed], then [expected behavior occurs]
- Given [edge case], when [action], then [system handles gracefully]

## Verification Commands
```bash
# [Verify the bug no longer reproduces]
[command]
# Expected: [result]

# [Verify no regressions]
[command]
# Expected: [result]
```

## Notes for Subagents

**For Architect:** ALL Required Work items must be included in implementation plan.

**For Implementer:** Complete ALL Required Work items. Do not skip any. Start by reproducing the bug exactly as described. Write the failing test first, then implement the fix. Run Verification Commands before marking complete.

**For Tester:** Verify ALL tests pass. Test both the original bug scenario AND regression scenarios. Report any incomplete Required Work items.