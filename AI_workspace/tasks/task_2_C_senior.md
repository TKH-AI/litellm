# Task 2-C: Org-Scoped Team Creation

| Field | Value |
|-------|-------|
| **Task ID** | 2-C |
| **Phase** | 2 (Core Components) |
| **Complexity** | Senior Engineer |
| **Dependencies** | Task 1-A completed |
| **Parallel With** | Tasks 2-B, 2-D |
| **Unlocks** | Task 3-E (when 2-B, 2-C, 2-D all complete) |

---

## Feature Context

See overall feature request: [ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md](../../issues_to_report/ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md)

---

## Objective

Modify `create_litellm_team_from_sso_group()` to create org-scoped teams when the feature flag is enabled.

---

## Required Reading

1. [03-REQUIREMENTS.md](../ENTRA_GROUPS_TO_ORGS/03-REQUIREMENTS.md) - Section "Team Creation"
2. [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) - Sections 5.1, 5.5

---

## Implementation Guide

Follow this TDD cycle:

**[CYCLE-3-ORG-SCOPED-TEAMS.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-3-ORG-SCOPED-TEAMS.md)**

---

## Deliverables

- [ ] Modify `create_litellm_team_from_sso_group()` in `ui_sso.py`
- [ ] Add `organization_id` parameter
- [ ] When flag enabled: set `organization_id` on new teams
- [ ] When flag enabled: set `models` to `["all-org-models"]`
- [ ] When flag disabled: unchanged behavior (standalone teams)
- [ ] Do NOT update existing standalone teams
- [ ] Do NOT update existing org-scoped teams
- [ ] All `TestOrgScopedTeamCreation` tests pass

---

## Key Behavior

```python
# Flag ENABLED - new team:
Team(
    team_id="entra-group-123",
    team_alias="Production Team",
    organization_id="entra-group-123",  # Links to org
    models=["all-org-models"],           # Inherits from org
)

# Flag DISABLED - new team:
Team(
    team_id="entra-group-123",
    team_alias="Production Team",
    organization_id=None,                # Standalone
    models=["gpt-4"],                    # From default_team_params
)

# Existing team (any flag state): DO NOT MODIFY
```

---

## Critical: Preserve Existing Teams

See [06-EDGE-CASES.md](../ENTRA_GROUPS_TO_ORGS/06-EDGE-CASES.md) Section 5.1:
- Existing standalone teams stay standalone
- Existing org-scoped teams stay unchanged
- Only NEW teams get org-scoped when flag enabled

---

## Verification

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestOrgScopedTeamCreation -v
```

---

## Reference Files

| Purpose | Path |
|---------|------|
| Implementation | `litellm/proxy/management_endpoints/ui_sso.py` (~line 1534) |
| Special model names | `litellm/proxy/_types.py` (SpecialModelNames enum) |
