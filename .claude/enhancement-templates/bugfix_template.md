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

### Must Fix
- [ ] Resolve the core issue described above
- [ ] Ensure no regression in related functionality
- [ ] Handle edge cases mentioned in reproduction

### Should Fix (if related)
- [ ] Similar issues in related code
- [ ] Improve error messages/handling

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

**Definition of Done:**
- [ ] Bug no longer reproduces following original steps
- [ ] All new unit tests pass
- [ ] No regressions detected in related functionality
- [ ] Code review completed
- [ ] Manual testing verification complete

**Acceptance Criteria:**
- Given [original reproduction scenario], when [steps are followed], then [expected behavior occurs]
- Given [edge case], when [action], then [system handles gracefully]

## Notes for Implementer Subagent

- **Investigation Priority:** Start by reproducing the bug exactly as described
- **Code Areas:** Focus initial investigation on [specific modules/files]
- **Testing Approach:** Write the failing test first, then implement the fix
- **Documentation:** Update any relevant docs if behavior changes

## Notes for Tester Subagent

- **Verification Steps:** Must test both the original bug scenario AND regression scenarios
- **Test Environments:** Verify fix works across [list specific environments]
- **Sign-off Requirements:** Manual testing + automated tests