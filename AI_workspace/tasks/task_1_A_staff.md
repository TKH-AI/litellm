# Task 1-A: Foundation & Configuration Setup

| Field | Value |
|-------|-------|
| **Task ID** | 1-A |
| **Phase** | 1 (Foundation) |
| **Complexity** | Staff Engineer |
| **Dependencies** | None |
| **Unlocks** | Tasks 2-B, 2-C, 2-D (can start in parallel after this) |

---

## Feature Context

See overall feature request: [ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md](../../issues_to_report/ENTRA_GROUPS_TO_ORGS_FEATURE_REQUEST.md)

---

## Objective

Set up test infrastructure, implement the configuration flag, and define function interfaces for parallel development.

---

## Required Reading

1. [README.md](../ENTRA_GROUPS_TO_ORGS/README.md) - Full project overview
2. [01-OVERVIEW_AND_BACKGROUND.md](../ENTRA_GROUPS_TO_ORGS/01-OVERVIEW_AND_BACKGROUND.md) - Key entities
3. [02-ARCHITECTURE.md](../ENTRA_GROUPS_TO_ORGS/02-ARCHITECTURE.md) - Current SSO flow
4. [03-REQUIREMENTS.md](../ENTRA_GROUPS_TO_ORGS/03-REQUIREMENTS.md) - Configuration and behavior

---

## Implementation Guide

Follow these TDD cycles in order:

1. **[CYCLE-0-SETUP.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-0-SETUP.md)** - Test infrastructure
2. **[CYCLE-1-CONFIG.md](../ENTRA_GROUPS_TO_ORGS/05-TDD-CYCLES/CYCLE-1-CONFIG.md)** - Configuration flag

---

## Deliverables

- [ ] Test file: `tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py`
- [ ] Test fixtures (mock prisma client, test data)
- [ ] Config flag `entra_groups_also_create_orgs` in `litellm/__init__.py`
- [ ] Flag defaults to `False`
- [ ] Environment variable support: `ENTRA_GROUPS_ALSO_CREATE_ORGS`
- [ ] Function stubs for Tasks 2-B, 2-C, 2-D in `ui_sso.py`
- [ ] All Cycle 0 and Cycle 1 tests pass

---

## Function Stubs to Create

Add to `litellm/proxy/management_endpoints/ui_sso.py`:

```python
# Stub for Task 2-B
async def create_litellm_org_from_sso_group(
    litellm_org_id: str,
    litellm_org_name: Optional[str] = None,
) -> Optional[LiteLLM_OrganizationTable]:
    """Creates Organization from SSO Group. Implemented in Task 2-B."""
    raise NotImplementedError("Task 2-B")

# Stub for Task 2-D
async def add_user_to_org_membership(
    user_id: str,
    organization_id: str,
    user_role: str = "internal_user",
) -> None:
    """Adds user to org membership. Implemented in Task 2-D."""
    raise NotImplementedError("Task 2-D")
```

---

## Verification

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestConfigurationFlag -v
python -c "import litellm; print(litellm.entra_groups_also_create_orgs)"
```

---

## Reference Files

See [08-APPENDICES.md](../ENTRA_GROUPS_TO_ORGS/08-APPENDICES.md) Section A.
