# Task 3-F: User Login Integration

| Field | Value |
|-------|-------|
| **Task ID** | 3-F |
| **Phase** | 3 (Integration) |
| **Complexity** | Senior Engineer |
| **Dependencies** | Tasks 2-B, 2-C, 2-D all completed |
| **Parallel With** | Task 3-E |
| **Unlocks** | Task 4-G |

---

## Feature Context

See overall feature request: [ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md](../../issues_to_report/ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md)

---

## Objective

Modify `add_user_to_teams_from_sso_response()` to also add users to organization memberships when the feature flag is enabled.

---

## Required Reading

1. [02-ARCHITECTURE.md](../ENTRA_GROUPS_TO_ORGS/02-ARCHITECTURE.md) - Current SSO flow
2. [03-REQUIREMENTS.md](../ENTRA_GROUPS_TO_ORGS/03-REQUIREMENTS.md) - User management section
3. [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) - Sections 5.4, 5.9

---

## Implementation Guide

Follow this TDD cycle:

**[CYCLE-6-USER-LOGIN.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-6-USER-LOGIN.md)**

---

## Deliverables

- [ ] Modify `add_user_to_teams_from_sso_response()` in `ui_sso.py`
- [ ] Check `litellm.entra_groups_also_create_orgs` flag
- [ ] When flag enabled: call `add_user_to_org_membership()` for each org
- [ ] When flag disabled: unchanged behavior (teams only)
- [ ] Handle users with multiple Entra groups (add to all orgs)
- [ ] Idempotent on re-login
- [ ] All `TestUserSSOLoginIntegration` tests pass

---

## Integration Flow

```
User logs in via SSO:
    │
    ├─→ [Existing] Add user to teams
    │
    └─→ [NEW] When flag enabled:
        For each team/org:
            └─→ add_user_to_org_membership()  [Task 2-D]
```

---

## Key Behavior

```python
# When flag enabled:
# 1. User added to teams (existing behavior)
# 2. User added to org memberships (new behavior)

# Multiple orgs example:
# User in Entra groups: [group-A, group-B, group-C]
# Result: User is member of orgs A, B, C AND teams A, B, C
```

---

## Verification

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestUserSSOLoginIntegration -v
```

---

## Reference Files

| Purpose | Path |
|---------|------|
| Implementation | `litellm/proxy/management_endpoints/ui_sso.py` (~line 1477) |
