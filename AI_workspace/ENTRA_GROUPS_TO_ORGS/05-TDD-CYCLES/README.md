# TDD Implementation Cycles

This folder contains the complete step-by-step implementation plan using Test-Driven Development (TDD).

## What is TDD?

Test-Driven Development follows the **Red-Green-Refactor** cycle:

1. **RED:** Write a failing test that specifies desired behavior
2. **GREEN:** Write minimal code to make the test pass
3. **REFACTOR:** Clean up the code while keeping tests green

---

## Implementation Cycles

| Cycle | Goal | Test Class | File |
|-------|------|------------|------|
| 0 | Setup test infrastructure | Fixtures | [CYCLE-0-SETUP.md](./CYCLE-0-SETUP.md) |
| 1 | Config flag recognition | `TestConfigurationFlag` | [CYCLE-1-CONFIG.md](./CYCLE-1-CONFIG.md) |
| 2 | Org creation from SSO | `TestCreateOrgFromSSOGroup` | [CYCLE-2-ORG-CREATION.md](./CYCLE-2-ORG-CREATION.md) |
| 3 | Org-scoped teams | `TestOrgScopedTeamCreation` | [CYCLE-3-ORG-SCOPED-TEAMS.md](./CYCLE-3-ORG-SCOPED-TEAMS.md) |
| 4 | Organization membership | `TestOrgMembership` | [CYCLE-4-ORG-MEMBERSHIP.md](./CYCLE-4-ORG-MEMBERSHIP.md) |
| 5 | Main sync function integration | `TestMainSyncFunction` | [CYCLE-5-SYNC-FUNCTION.md](./CYCLE-5-SYNC-FUNCTION.md) |
| 6 | User SSO login integration | `TestUserSSOLoginIntegration` | [CYCLE-6-USER-LOGIN.md](./CYCLE-6-USER-LOGIN.md) |
| 7 | End-to-end integration | `TestEndToEndIntegration` | [CYCLE-7-E2E.md](./CYCLE-7-E2E.md) |

---

## How to Use This Section

### For Implementation
1. Start with [CYCLE-0-SETUP.md](./CYCLE-0-SETUP.md)
2. Follow each cycle in order (0 → 7)
3. For each cycle:
   - Read the **RED** section (understand the tests)
   - Run the tests (they should fail)
   - Read the **GREEN** section (implement the code)
   - Run the tests again (they should pass)
   - Refactor if needed

### For Code Review
- Check each cycle's implementation against its test specifications
- Verify refactoring doesn't break any tests
- Ensure edge cases are handled (see [Edge Cases](../06-EDGE-CASES.md))

### For Testing/QA
- Run all test files to verify implementation
- Use the test specifications as acceptance criteria
- Verify no regressions in existing functionality

---

## Running All Tests

```bash
# Run all feature tests
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v

# Run specific cycle
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestConfigurationFlag -v

# Run with coverage
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v --cov=litellm.proxy.management_endpoints.ui_sso
```

---

## Key Files Involved

| Phase | File | Location |
|-------|------|----------|
| Config | `litellm/__init__.py` | Module-level settings |
| Implementation | `litellm/proxy/management_endpoints/ui_sso.py` | Main SSO handler |
| Types | `litellm/proxy/_types.py` | Type definitions |
| Tests | `tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py` | Test file |

---

## Cycle Navigation

- [← Back to Main README](../README.md)
- [Cycle 0: Setup →](./CYCLE-0-SETUP.md)

---

## FAQ

**Q: Do I need to run cycles in order?**
A: Yes. Each cycle depends on previous ones. Start with Cycle 0.

**Q: What if a test fails?**
A: Check the error message and review the corresponding implementation section.

**Q: Can I skip cycles?**
A: No. Each cycle builds on previous ones. Skip nothing.

**Q: How long does each cycle take?**
A: Varies, but typically 15-30 minutes per cycle including tests and implementation.
