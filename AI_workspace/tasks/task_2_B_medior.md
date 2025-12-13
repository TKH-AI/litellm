# Task 2-B: Organization Creation from SSO Group

| Field | Value |
|-------|-------|
| **Task ID** | 2-B |
| **Phase** | 2 (Core Components) |
| **Complexity** | Medior Engineer |
| **Dependencies** | Task 1-A completed |
| **Parallel With** | Tasks 2-C, 2-D |
| **Unlocks** | Task 3-E (when 2-B, 2-C, 2-D all complete) |

---

## Feature Context

First and foremost, see overall feature request: [ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md](../../issues_to_report/ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md)

---

## Objective

Implement `create_litellm_org_from_sso_group()` function that creates LiteLLM Organizations from Entra Group IDs.

---

## Required Reading

1. [03-REQUIREMENTS.md](../ENTRA_GROUPS_TO_ORGS/03-REQUIREMENTS.md) - Section "Organization Creation"
2. [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) - Sections 5.2, 5.3, 5.10

---

## Implementation Guide

Follow this TDD cycle:

**[CYCLE-2-ORG-CREATION.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-2-ORG-CREATION.md)**

---

## Deliverables

- [ ] Implement `create_litellm_org_from_sso_group()` in `ui_sso.py`
- [ ] Organization created with `organization_id` = Entra Group ID
- [ ] Organization created with `organization_alias` = Entra Group Display Name
- [ ] Apply `default_team_params` (models, max_budget, budget_duration, tpm_limit, rpm_limit)
- [ ] Idempotent: skip if org already exists
- [ ] Handle missing `default_team_params` gracefully
- [ ] Handle Prisma client unavailable
- [ ] All `TestCreateOrgFromSSOGroup` tests pass

---

## Key Behavior

```python
# When flag enabled and org doesn't exist:
Organization(
    organization_id="entra-group-123",      # From Entra Group ID
    organization_alias="Production Team",    # From Entra Group Display Name
    models=["gpt-4", "gpt-3.5-turbo"],      # From default_team_params
    max_budget=100.0,                        # From default_team_params
)

# When org already exists: return existing, don't update
```

---

## Verification

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestCreateOrgFromSSOGroup -v
```

---

## Reference Files

| Purpose | Path |
|---------|------|
| Implementation | `litellm/proxy/management_endpoints/ui_sso.py` |
| Tests | `tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py` |
