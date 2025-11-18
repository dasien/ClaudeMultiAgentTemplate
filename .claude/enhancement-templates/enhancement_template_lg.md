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
- Target platform/environment (e.g., 6502 emulated machine)
- Memory constraints (RAM/ROM available)
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
- **Memory:** [Budget constraints, optimization needs]
- **Reliability:** [Error handling, edge cases]
- **Compatibility:** [Backwards compatibility, platform support]

### Must Have (MVP)
- [ ] Core feature X
- [ ] Essential behavior Y
- [ ] Basic error handling

### Should Have (if time permits)
- [ ] Enhancement A
- [ ] Nice-to-have B

### Won't Have (out of scope)
- Feature X (reason: complexity/time)
- Feature Y (reason: not MVP)

## Open Questions
> These need answers before architecture review

1. [Question about memory layout / design approach]
2. [Question about API/interface decisions]
3. [Question about user requirements]
4. [Question about testing approach]

## Constraints & Limitations
**Technical Constraints:**
- Maximum memory usage: [X KB]
- Must not break: [existing features]
- Must use: [specific APIs/patterns]

**Business/Timeline Constraints:**
- Deadline: [if applicable]
- Cannot change: [locked decisions]

## Success Criteria
**Definition of Done:**
- [ ] Core functionality works as described
- [ ] All acceptance tests pass
- [ ] Documentation updated
- [ ] No regressions in existing features
- [ ] Performance metrics met

**Acceptance Tests:**
1. Given [initial state], when [action], then [expected result]
2. Given [scenario], when [action], then [expected outcome]
3. Edge case: [specific test case]

## Security & Safety Considerations
- Data validation requirements
- Error handling approach
- Resource cleanup needs
- Potential risks and mitigations

## UI/UX Considerations (if applicable)
- User interaction flow
- Input/output format
- Error messages
- Help/documentation needs

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

## References & Research
- [Link to relevant documentation]
- [Similar implementations]
- [Technical specifications]
- [Design inspiration]

## Notes for PM Subagent
> Instructions for how to process this enhancement

- If [X] is unclear, ask before proceeding
- Consider alternative approaches for [Y]
- Flag if this seems to require [breaking changes]

## Notes for Architect Subagent
> Key architectural considerations

- Pay special attention to [memory layout / performance]
- Consider impact on [existing component]
- Evaluate tradeoffs between [approach A vs B]

## Notes for Implementer Subagent
> Implementation guidance

- Reuse existing [utility/pattern] where possible
- Add tests for [specific edge cases]
- Update documentation at [location]

## Notes for Testing Subagent
> Testing and validation guidance

- Focus testing on [critical functionality/edge cases]
- Validate [performance requirements/memory constraints]
- Test [hardware integration/timing-critical sections]
- Verify [backwards compatibility/regression scenarios]
- Include [manual testing scenarios] for hardware validation