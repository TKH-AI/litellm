# Cycle 0: Setup Test Infrastructure

## Goal

Set up the test file with necessary imports, fixtures, and test infrastructure before writing feature tests.

---

## 0.1 Create Test File

**File:** `tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py`

```python
"""
TDD Tests for entra_groups_also_create_orgs feature.

This feature automatically creates Organizations from Microsoft Entra ID groups
during SSO login, in addition to the existing team creation functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, List

import litellm
from litellm.proxy._types import (
    LiteLLM_OrganizationTable,
    LiteLLM_TeamTable,
    LiteLLM_UserTable,
    NewOrganizationRequest,
    NewTeamRequest,
    UserAPIKeyAuth,
    SpecialModelNames,
    LitellmUserRoles,
)
from litellm.types.proxy.management_endpoints.ui_sso import (
    MicrosoftServicePrincipalTeam,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_prisma_client():
    """Mock Prisma client for database operations."""
    mock_client = MagicMock()
    mock_client.db = MagicMock()
    mock_client.db.litellm_organizationtable = MagicMock()
    mock_client.db.litellm_teamtable = MagicMock()
    mock_client.db.litellm_organizationmembership = MagicMock()
    mock_client.db.litellm_usertable = MagicMock()
    return mock_client


@pytest.fixture
def sample_entra_group():
    """Sample Entra group data."""
    return MicrosoftServicePrincipalTeam(
        principalId="entra-group-id-123",
        principalDisplayName="Production LLM Team",
    )


@pytest.fixture
def sample_entra_groups():
    """Multiple sample Entra groups."""
    return [
        MicrosoftServicePrincipalTeam(
            principalId="entra-group-id-123",
            principalDisplayName="Production LLM Team",
        ),
        MicrosoftServicePrincipalTeam(
            principalId="entra-group-id-456",
            principalDisplayName="Development LLM Team",
        ),
    ]


@pytest.fixture
def sample_user():
    """Sample user data."""
    return LiteLLM_UserTable(
        user_id="user@example.com",
        teams=[],
    )


@pytest.fixture
def default_team_params():
    """Sample default_team_params configuration."""
    return {
        "max_budget": 100.0,
        "budget_duration": "30d",
        "models": ["gpt-4", "gpt-3.5-turbo"],
        "tpm_limit": 10000,
        "rpm_limit": 1000,
    }


@pytest.fixture(autouse=True)
def reset_litellm_settings():
    """Reset litellm settings before each test."""
    original_flag = getattr(litellm, 'entra_groups_also_create_orgs', None)
    original_params = getattr(litellm, 'default_team_params', None)
    yield
    # Restore original values
    if original_flag is not None:
        litellm.entra_groups_also_create_orgs = original_flag
    elif hasattr(litellm, 'entra_groups_also_create_orgs'):
        delattr(litellm, 'entra_groups_also_create_orgs')
    if original_params is not None:
        litellm.default_team_params = original_params
    elif hasattr(litellm, 'default_team_params'):
        litellm.default_team_params = None
```

---

## 0.2 Fixture Descriptions

### `mock_prisma_client`
Provides a mocked Prisma client with database access.
- `mock_client.db.litellm_organizationtable` - Mock for organizations
- `mock_client.db.litellm_teamtable` - Mock for teams
- `mock_client.db.litellm_organizationmembership` - Mock for memberships
- `mock_client.db.litellm_usertable` - Mock for users

### `sample_entra_group`
A single Entra group with:
- `principalId`: "entra-group-id-123"
- `principalDisplayName`: "Production LLM Team"

### `sample_entra_groups`
Multiple Entra groups for testing batch operations.

### `sample_user`
A test user with ID "user@example.com" and empty teams list.

### `default_team_params`
Standard configuration with:
- Budget: 100.0
- Duration: 30 days
- Models: ["gpt-4", "gpt-3.5-turbo"]
- TPM limit: 10,000
- RPM limit: 1,000

### `reset_litellm_settings` (autouse)
Automatically resets litellm module state before each test to prevent test interference.

---

## 0.3 Call Site Audit

Before modifying `create_litellm_team_from_sso_group()` in later cycles, we need to identify all existing call sites to ensure backward compatibility.

### Action

```bash
grep -rn "create_litellm_team_from_sso_group(" litellm/proxy/
```

### Known Call Sites (as of current codebase)

| Location | File | Line | Context |
|----------|------|------|---------|
| Main call | `ui_sso.py` | ~2334 | Inside `create_litellm_teams_from_service_principal_team_ids()` |

**Current Call Pattern:**
```python
await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
    litellm_team_id=litellm_team_id,
    litellm_team_name=litellm_team_name,
)
```

### Backward Compatibility Requirements

When we modify `create_litellm_team_from_sso_group()` in Cycle 3:

1. **New `organization_id` parameter MUST have a default value of `None`**
2. When `organization_id=None`, function behaves exactly as before (creates standalone team)
3. This ensures backward compatibility with any future call sites

### Verification During Implementation

- Cycle 3 includes test `test_standalone_team_when_no_organization_id` to verify this
- Cycle 5 updates the only call site to conditionally pass `organization_id` based on the feature flag

---

## 0.4 Verification

To verify setup is correct:

```bash
# Navigate to project root
cd /home/rioiart/workspace/litellm

# Install test dependencies (if not already installed)
poetry install

# Try importing the test file
poetry run python -c "import tests.test_litellm.proxy.management_endpoints.test_ui_sso_entra_orgs; print('✓ Test file imports successfully')"

# Verify pytest can discover tests
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py --collect-only
```

Expected output:
```
collected 0 items

<Module test_ui_sso_entra_orgs.py>
```

(0 items is expected since we haven't written any tests yet)

---

## Next Steps

Once setup is complete:
- [Cycle 1: Configuration Flag →](./CYCLE-1-CONFIG.md)

---

## Troubleshooting

**Import Error:** If fixtures fail to import, check that all types exist in `litellm/proxy/_types.py`

**Mock Error:** If `MagicMock` isn't working as expected, ensure `unittest.mock` is available (standard library)

**Fixture Error:** If fixtures can't be found, ensure file is in correct location with `conftest.py` or direct import

---

[← Back to Cycles README](./README.md) | [Next: Cycle 1 →](./CYCLE-1-CONFIG.md)
