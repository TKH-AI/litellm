# Task 4-G: End-to-End Testing

| Field | Value |
|-------|-------|
| **Task ID** | 4-G |
| **Phase** | 4 (Validation) |
| **Complexity** | Medior Engineer |
| **Dependencies** | Tasks 3-E, 3-F completed |
| **Parallel With** | Task 4-H |
| **Unlocks** | Feature complete |

---

## Feature Context

See overall feature request: [ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md](../../issues_to_report/ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md)

---

## Objective

Implement comprehensive end-to-end integration tests and validate all edge cases.

---

## Required Reading

1. [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) - All edge cases
2. [07-ACCEPTANCE-CRITERIA.md](../ENTRA_GROUPS_TO_ORGS/07-ACCEPTANCE-CRITERIA.md) - Full checklist

---

## Implementation Guide

Follow this TDD cycle:

**[CYCLE-7-E2E.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-7-E2E.md)**

---

## Deliverables

- [ ] Implement `TestEndToEndIntegration` test class
- [ ] Implement `TestDatabaseIntegration` test class
- [ ] Test full SSO flow end-to-end
- [ ] Validate all edge cases from [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md)
- [ ] Test idempotency (re-login scenarios)
- [ ] Test flag toggle scenarios (enable/disable)
- [ ] All tests pass

---

## Edge Cases to Test

From [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md):

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 5.1 | Existing standalone team | Don't update |
| 5.2 | Org creation fails | Create team anyway |
| 5.3 | No default_team_params | Create with no limits |
| 5.4 | User already in org | Skip duplicate |
| 5.5 | Team already org-scoped | No update |
| 5.6 | Flag disabled → enabled | Create new orgs only |
| 5.7 | Flag enabled → disabled | Keep existing orgs |
| 5.8 | Empty Entra group | Create org/team |
| 5.9 | User in multiple orgs | Add to all |
| 5.10 | Prisma unavailable | Log and error |

---

## E2E Test Scenario

```python
async def test_full_sso_flow_with_orgs():
    """
    1. User clicks "Login with Microsoft"
    2. Organizations created from Entra groups
    3. Teams created as org-scoped
    4. User created
    5. User added to teams
    6. User added to org memberships
    """
```

---

## Verification

```bash
# Run all tests
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v

# Run with coverage
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v --cov=litellm.proxy.management_endpoints.ui_sso
```

---

## Acceptance Criteria Validation

Go through [07-ACCEPTANCE-CRITERIA.md](../ENTRA_GROUPS_TO_ORGS/07-ACCEPTANCE-CRITERIA.md) and check off all items.

---

## Reference Files

| Purpose | Path |
|---------|------|
| Test file | `tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py` |
| Edge cases | `AI_workspace/ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md` |
| Acceptance | `AI_workspace/ENTRA_GROUPS_TO_ORGS/07-ACCEPTANCE-CRITERIA.md` |
