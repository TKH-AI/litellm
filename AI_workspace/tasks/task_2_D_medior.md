# Task 2-D: Organization Membership

| Field | Value |
|-------|-------|
| **Task ID** | 2-D |
| **Phase** | 2 (Core Components) |
| **Complexity** | Medior Engineer |
| **Dependencies** | Task 1-A completed |
| **Parallel With** | Tasks 2-B, 2-C |
| **Unlocks** | Task 3-E, 3-F (when 2-B, 2-C, 2-D all complete) |

---

## Feature Context

See overall feature request: [ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md](../../issues_to_report/ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md)

---

## Objective

Implement `add_user_to_org_membership()` function to create organization membership records for users.

---

## Required Reading

1. [03-REQUIREMENTS.md](../ENTRA_GROUPS_TO_ORGS/03-REQUIREMENTS.md) - Section "Add User to Organization"
2. [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) - Sections 5.4, 5.9

---

## Implementation Guide

Follow this TDD cycle:

**[CYCLE-4-ORG-MEMBERSHIP.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-4-ORG-MEMBERSHIP.md)**

---

## Deliverables

- [ ] Implement `add_user_to_org_membership()` in `ui_sso.py`
- [ ] Create `LiteLLM_OrganizationMembership` record
- [ ] Set `user_role` to `"internal_user"` by default
- [ ] Idempotent: skip if membership already exists
- [ ] Handle Prisma client unavailable (log, don't crash)
- [ ] Support users in multiple organizations
- [ ] All `TestOrgMembership` tests pass

---

## Key Behavior

```python
# Create membership:
OrganizationMembership(
    user_id="alice@company.com",
    organization_id="entra-group-123",
    user_role="internal_user",
)

# If membership exists: skip silently (idempotent)
# If Prisma unavailable: log error, return (non-blocking)
```

---

## Database Schema Reference

```prisma
model LiteLLM_OrganizationMembership {
  user_id         String
  organization_id String
  user_role       String?
  spend           Float?
  budget_id       String?
  @@id([user_id, organization_id])  # Composite primary key
}
```

---

## Verification

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestOrgMembership -v
```

---

## Reference Files

| Purpose | Path |
|---------|------|
| Implementation | `litellm/proxy/management_endpoints/ui_sso.py` |
| Schema | `litellm/proxy/schema.prisma` |
