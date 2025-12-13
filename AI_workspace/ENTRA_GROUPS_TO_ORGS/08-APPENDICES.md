# Appendices

## A: File Locations Quick Reference

| Purpose | File Path |
|---------|-----------|
| Global config vars | `litellm/__init__.py` |
| SSO handlers | `litellm/proxy/management_endpoints/ui_sso.py` |
| Team endpoints | `litellm/proxy/management_endpoints/team_endpoints.py` |
| Organization endpoints | `litellm/proxy/management_endpoints/organization_endpoints.py` |
| Type definitions | `litellm/proxy/_types.py` |
| SSO types | `litellm/types/proxy/management_endpoints/ui_sso.py` |
| Database schema | `litellm/proxy/schema.prisma` |
| Config loading | `litellm/proxy/proxy_server.py` |
| **NEW Test file** | `tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py` |

---

## B: TDD Cycle Summary

| Cycle | Goal | Test Class | Primary Implementation | Files Modified |
|-------|------|------------|----------------------|-----------------|
| 0 | Setup + Call Site Audit | Fixtures | Test infrastructure | `test_ui_sso_entra_orgs.py` |
| 1 | Config flag + Loading | `TestConfigurationFlag` | `entra_groups_also_create_orgs` flag | `litellm/__init__.py` |
| 2 | Org creation + Mock Validation | `TestCreateOrgFromSSOGroup` | `create_litellm_org_from_sso_group()` | `ui_sso.py` |
| 3 | Org-scoped teams | `TestOrgScopedTeamCreation` | Modify `create_litellm_team_from_sso_group()` | `ui_sso.py` |
| 4 | Org membership | `TestOrgMembership` | `add_user_to_org_membership()` | `ui_sso.py` |
| 5 | Main sync | `TestMainSyncFunction` | Modify `create_litellm_teams_from_service_principal_team_ids()` | `ui_sso.py` |
| 6 | User login | `TestUserSSOLoginIntegration` | Modify `add_user_to_teams_from_sso_response()` | `ui_sso.py` |
| 7 | E2E + DB Integration | `TestEndToEndIntegration`, `TestDatabaseIntegration` | Full integration test | `test_ui_sso_entra_orgs.py` |

---

## C: Running Tests

### All Feature Tests
```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v
```

### Specific Cycle
```bash
# Example: Run Cycle 1
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestConfigurationFlag -v
```

### With Coverage
```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v \
  --cov=litellm.proxy.management_endpoints.ui_sso \
  --cov=litellm \
  --cov-report=html
```

### In Watch Mode (requires pytest-watch)
```bash
poetry run ptw tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py
```

### Specific Test
```bash
# Example: Run one test
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestCreateOrgFromSSOGroup::test_creates_org_with_correct_id_and_alias -v
```

---

## D: Key Enums and Constants

### SpecialModelNames
**File:** `litellm/proxy/_types.py` (line ~2488)

```python
class SpecialModelNames(enum.Enum):
    all_team_models = "all-team-models"
    all_proxy_models = "all-proxy-models"
    all_org_models = "all-org-models"        # ← Used for org-scoped teams
    no_default_models = "no-default-models"
```

### LitellmUserRoles
**File:** `litellm/proxy/_types.py`

```python
class LitellmUserRoles(str, enum.Enum):
    PROXY_ADMIN = "proxy_admin"
    PROXY_ADMIN_READ_ONLY = "proxy_admin_read_only"
    # ... other roles
    # Use this for creating users with SSO
```

---

## E: Configuration Examples

### Minimal Configuration (Flag Disabled)
```yaml
litellm_settings:
  default_team_params:
    models: ["gpt-3.5-turbo"]
```

### With Feature Enabled
```yaml
litellm_settings:
  entra_groups_also_create_orgs: true

  default_team_params:
    models: ["gpt-4", "gpt-3.5-turbo"]
    max_budget: 100.0
    budget_duration: "30d"
    tpm_limit: 10000
    rpm_limit: 1000
```

### Environment Variable
```bash
# Enable feature via environment variable
export ENTRA_GROUPS_ALSO_CREATE_ORGS=true

# Azure/Entra configuration
export MICROSOFT_CLIENT_ID=your-client-id
export MICROSOFT_CLIENT_SECRET=your-client-secret
export MICROSOFT_TENANT=your-tenant-id
export MICROSOFT_SERVICE_PRINCIPAL_ID=your-service-principal-id
```

---

## E.1: How Configuration Loading Works

### The Loading Mechanism

The proxy server (`proxy_server.py:2160-2421`) loads `litellm_settings` from YAML:

```python
# From proxy_server.py (simplified)
litellm_settings = config.get("litellm_settings", {})
for key, value in litellm_settings.items():
    setattr(litellm, key, value)
```

This means:
1. Any key in `litellm_settings` is set as an attribute on the `litellm` module
2. No additional code needed to support new settings
3. Just add the default value to `litellm/__init__.py`

### Supported Configuration Methods

| Method | Example | Priority |
|--------|---------|----------|
| YAML file | `entra_groups_also_create_orgs: true` | Loaded at startup |
| Environment variable | `ENTRA_GROUPS_ALSO_CREATE_ORGS=true` | Mapped during config |
| Runtime assignment | `litellm.entra_groups_also_create_orgs = True` | Highest (overrides) |

### Verification

To verify the flag is loaded correctly:
```python
import litellm
print(f"Feature enabled: {litellm.entra_groups_also_create_orgs}")
print(f"Default params: {litellm.default_team_params}")
```

---

## F: Database Schema References

### Organization Table
```prisma
model LiteLLM_OrganizationTable {
  organization_id     String @id
  organization_alias  String
  models              String[]
  max_budget          Float?
  spend               Float @default(0.0)
  metadata            Json @default("{}")
  // ... relationships
  teams               LiteLLM_TeamTable[]
  members             LiteLLM_OrganizationMembership[]
}
```

### Team Table
```prisma
model LiteLLM_TeamTable {
  team_id             String @id
  team_alias          String?
  organization_id     String?  // ← NULL for standalone, set for org-scoped
  models              String[]
  max_budget          Float?
  // ... relationships
  litellm_organization_table LiteLLM_OrganizationTable? @relation(...)
}
```

### Organization Membership
```prisma
model LiteLLM_OrganizationMembership {
  user_id             String
  organization_id     String
  user_role           String?
  spend               Float?
  @@id([user_id, organization_id])
  // ... relationships
}
```

---

## G: Common Issues & Solutions

### Issue: Import Error for `MicrosoftServicePrincipalTeam`
**Solution:** Ensure the type is imported from correct module:
```python
from litellm.types.proxy.management_endpoints.ui_sso import MicrosoftServicePrincipalTeam
```

### Issue: Prisma Client Not Found
**Solution:** Ensure `prisma_client` is initialized before running SSO flow:
```python
from litellm.proxy.proxy_server import prisma_client
# prisma_client should be initialized during proxy server startup
```

### Issue: Tests Fail with "fixture not found"
**Solution:** Ensure fixture is in correct scope and conftest.py is present:
```bash
# Check conftest.py exists in test directory
ls tests/test_litellm/proxy/management_endpoints/conftest.py
```

### Issue: Asyncio Tests Fail
**Solution:** Ensure `@pytest.mark.asyncio` decorator is on each async test:
```python
@pytest.mark.asyncio
async def test_something():
    # test code
```

---

## H: Debugging Tips

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific module
logging.getLogger('litellm.proxy.management_endpoints.ui_sso').setLevel(logging.DEBUG)
```

### Check Feature Flag
```python
import litellm
print(f"Feature enabled: {litellm.entra_groups_also_create_orgs}")
print(f"Default params: {litellm.default_team_params}")
```

### Mock Database for Testing
```python
from unittest.mock import AsyncMock, MagicMock

mock_prisma = MagicMock()
mock_prisma.db.litellm_organizationtable.find_first = AsyncMock(return_value=None)
# ... configure other mocks
```

### Check Existing Data
```python
# After running SSO flow, verify database:
# 1. Check organizations created:
SELECT * FROM litellm_organizationtable WHERE organization_id LIKE 'entra-group%';

# 2. Check org-scoped teams:
SELECT * FROM litellm_teamtable WHERE organization_id IS NOT NULL;

# 3. Check user memberships:
SELECT * FROM litellm_organizationmembership;
```

---

## I: References & Related Docs

### LiteLLM Documentation
- [SSO Configuration Guide](../../../tutorials/msft_sso.md)
- [Self-Serve SSO Docs](../../../proxy/self_serve.md)
- [Team Management](../../../proxy/team_management.md)
- [Organization Management](../../../proxy/organization_management.md)

### Microsoft Entra Documentation
- [Microsoft Graph API - Groups](https://learn.microsoft.com/en-us/graph/api/resources/group)
- [Azure AD Applications](https://learn.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)

### Prisma Documentation
- [Prisma ORM Docs](https://www.prisma.io/docs/)
- [Prisma Python Client](https://www.prisma.io/python)

---

## J: Glossary

| Term | Definition |
|------|-----------|
| **Entra Group** | Microsoft Entra ID group (formerly Azure AD group) |
| **SSO** | Single Sign-On (Microsoft OAuth authentication) |
| **Organization** | Top-level container with budget/model controls |
| **Org-Scoped Team** | Team linked to an organization |
| **Standalone Team** | Team with no organization link |
| **Service Principal** | Application identity in Azure (enables group sync) |
| **Graph API** | Microsoft's API for accessing Azure resources |
| **Idempotent** | Operation safe to run multiple times |
| **TDD** | Test-Driven Development (Red-Green-Refactor) |

---

## K: Support & Contact

### Getting Help

1. **Check Edge Cases** → [Edge Cases](./06-EDGE-CASES.md)
2. **Review Tests** → [TDD Cycles](./05-TDD-CYCLES/)
3. **Check Requirements** → [Requirements](./03-REQUIREMENTS.md)
4. **Search Logs** → Enable debug logging (see Section H)

### Reporting Issues

If you encounter issues:
1. Enable debug logging
2. Collect relevant logs
3. Check Edge Cases section for handling
4. File an issue with:
   - Error message
   - Logs
   - Configuration
   - Steps to reproduce

---

[← Back to README](./README.md) | [← Previous: Acceptance Criteria](./07-ACCEPTANCE-CRITERIA.md)
