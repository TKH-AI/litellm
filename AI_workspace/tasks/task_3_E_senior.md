# Task 3-E: Main Sync Function Integration

| Field | Value |
|-------|-------|
| **Task ID** | 3-E |
| **Phase** | 3 (Integration) |
| **Complexity** | Senior Engineer |
| **Dependencies** | Tasks 2-B, 2-C, 2-D all completed |
| **Parallel With** | Task 3-F |
| **Unlocks** | Task 4-G |

---

## Feature Context

See overall feature request: [ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md](../../issues_to_report/ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md)

---

## Objective

Modify `create_litellm_teams_from_service_principal_team_ids()` to orchestrate org creation, org-scoped team creation, and membership in the correct order.

---

## Required Reading

1. [02-ARCHITECTURE.md](../ENTRA_GROUPS_TO_ORGS/02-ARCHITECTURE.md) - Section "How This Feature Extends the Flow"
2. [03-REQUIREMENTS.md](../ENTRA_GROUPS_TO_ORGS/03-REQUIREMENTS.md) - Full behavior spec
3. [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) - Section 5.2 (org creation failure)

---

## Implementation Guide

Follow this TDD cycle:

**[CYCLE-5-SYNC-FUNCTION.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-5-SYNC-FUNCTION.md)**

---

## Deliverables

- [ ] Modify `create_litellm_teams_from_service_principal_team_ids()` in `ui_sso.py`
- [ ] Check `litellm.entra_groups_also_create_orgs` flag
- [ ] When flag enabled, for each Entra group:
  1. Call `create_litellm_org_from_sso_group()` (from Task 2-B)
  2. Call `create_litellm_team_from_sso_group()` with `organization_id` (from Task 2-C)
- [ ] When flag disabled: unchanged behavior
- [ ] Graceful degradation: if org creation fails, still create team
- [ ] All `TestMainSyncFunction` tests pass

---

## Integration Flow

```
When entra_groups_also_create_orgs = True:

For each Entra group:
    │
    ├─→ create_litellm_org_from_sso_group()     [Task 2-B]
    │   └─→ Create Organization (or skip if exists)
    │
    └─→ create_litellm_team_from_sso_group()    [Task 2-C]
        └─→ Create org-scoped Team (or skip if exists)
```

---

## Error Handling

From [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) Section 5.2:

```python
try:
    await create_litellm_org_from_sso_group(...)
except Exception as e:
    verbose_proxy_logger.exception(f"Error creating organization: {e}")
    # Continue - still create team as standalone

await create_litellm_team_from_sso_group(...)
```

---

## Verification

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestMainSyncFunction -v
```

---

## Reference Files

| Purpose | Path |
|---------|------|
| Implementation | `litellm/proxy/management_endpoints/ui_sso.py` (~line 2311) |
