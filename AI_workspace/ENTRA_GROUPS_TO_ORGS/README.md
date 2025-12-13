# Implementation Plan: Auto-create Organizations from Microsoft Entra Groups

This directory contains the comprehensive implementation plan for adding the `entra_groups_also_create_orgs` feature to LiteLLM.

## Overview

This feature allows automatic creation of LiteLLM Organizations (in addition to Teams) from Microsoft Entra ID groups during SSO login.

- **Estimated Complexity:** Medium
- **Primary Files:** `litellm/proxy/management_endpoints/ui_sso.py`
- **Feature Flag:** `entra_groups_also_create_orgs`
- **Methodology:** Test-Driven Development (TDD)

---

## Table of Contents

1. [Overview & Background](./01-OVERVIEW_AND_BACKGROUND.md) - What is LiteLLM and key entities
2. [Current System Architecture](./02-ARCHITECTURE.md) - Current SSO flow and relevant components
3. [Feature Requirements](./03-REQUIREMENTS.md) - New configuration and expected behavior
4. [TDD Implementation Cycles](./05-TDD-CYCLES/) - Step-by-step implementation with tests
5. [Edge Cases](./06-EDGE-CASES.md) - Scenarios and handling strategies
6. [Acceptance Criteria](./07-ACCEPTANCE-CRITERIA.md) - Feature completion checklist
7. [Appendices](./08-APPENDICES.md) - Quick references and useful information

---

## Quick Navigation

### By Role
- **DevOps/Admin:** See [Requirements](./03-REQUIREMENTS.md) to understand configuration
- **QA/Testing:** See [TDD Cycles](./05-TDD-CYCLES/) for test specifications
- **Backend Developer:** See [TDD Cycles](./05-TDD-CYCLES/) for implementation steps
- **Architect/Lead:** See [Architecture](./02-ARCHITECTURE.md) and [Requirements](./03-REQUIREMENTS.md)

### By Implementation Phase
1. Start: [Overview & Background](./01-OVERVIEW_AND_BACKGROUND.md)
2. Understand: [Current Architecture](./02-ARCHITECTURE.md)
3. Plan: [Requirements](./03-REQUIREMENTS.md)
4. Implement: [TDD Cycles](./05-TDD-CYCLES/) (Cycles 0-7)
5. Verify: [Edge Cases](./06-EDGE-CASES.md) + [Acceptance Criteria](./07-ACCEPTANCE-CRITERIA.md)
6. Reference: [Appendices](./08-APPENDICES.md)

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Organization** | Top-level container for teams with budget/model controls |
| **Org-Scoped Team** | Team with `organization_id` set (inherits org constraints) |
| **Entra Group** | Microsoft Entra ID group (source of truth for membership) |
| **SSO Login** | User logs in via Microsoft OAuth; groups are synced |
| **Feature Flag** | `entra_groups_also_create_orgs` - enables org creation |

---

## Implementation Methodology

This plan follows **Test-Driven Development (TDD)** with Red-Green-Refactor cycles:

1. **RED:** Write failing test
2. **GREEN:** Write minimal code to pass test
3. **REFACTOR:** Clean up while keeping tests green

Each cycle focuses on one specific feature aspect and includes:
- Failing tests that specify desired behavior
- Minimal implementation to satisfy tests
- Refactoring opportunities noted

---

## Status Tracking

Use this checklist to track progress:

- [ ] Cycle 0: Setup test infrastructure
- [ ] Cycle 1: Configuration flag recognition
- [ ] Cycle 2: Organization creation from SSO group
- [ ] Cycle 3: Org-scoped team creation
- [ ] Cycle 4: Organization membership
- [ ] Cycle 5: Main sync function integration
- [ ] Cycle 6: User SSO login integration
- [ ] Cycle 7: End-to-end integration test
- [ ] All edge cases handled
- [ ] Acceptance criteria met

---

## Files in This Directory

```
ENTRA_GROUPS_TO_ORGS/
├── README.md (this file)
├── 01-OVERVIEW_AND_BACKGROUND.md
├── 02-ARCHITECTURE.md
├── 03-REQUIREMENTS.md
├── 05-TDD-CYCLES/
│   ├── README.md
│   ├── CYCLE-0-SETUP.md
│   ├── CYCLE-1-CONFIG.md
│   ├── CYCLE-2-ORG-CREATION.md
│   ├── CYCLE-3-ORG-SCOPED-TEAMS.md
│   ├── CYCLE-4-ORG-MEMBERSHIP.md
│   ├── CYCLE-5-SYNC-FUNCTION.md
│   ├── CYCLE-6-USER-LOGIN.md
│   └── CYCLE-7-E2E.md
├── 06-EDGE-CASES.md
├── 07-ACCEPTANCE-CRITERIA.md
└── 08-APPENDICES.md
```

---

## Getting Started

**For a quick start:**
1. Read [Overview & Background](./01-OVERVIEW_AND_BACKGROUND.md) (5 min)
2. Review [Requirements](./03-REQUIREMENTS.md) (5 min)
3. Follow [TDD Cycles](./05-TDD-CYCLES/) in order (implementation time varies)

**For implementation support:**
- Run test commands from each cycle
- Refer to [Appendices](./08-APPENDICES.md) for file locations
- Check [Edge Cases](./06-EDGE-CASES.md) when handling special scenarios

---

## Questions?

Refer to the relevant section or appendix. Each document is self-contained but cross-references other sections for context.
