# Cycle 2: Organization Creation from SSO Group

## Goal

Create a function that creates an Organization from an Entra group.

---

## 2.1 RED: Write Failing Tests

Add these tests to your test file:

```python
# ============================================================================
# CYCLE 2: Organization Creation from SSO Group
# ============================================================================

class TestCreateOrgFromSSOGroup:
    """Tests for create_litellm_org_from_sso_group function."""

    @pytest.mark.asyncio
    async def test_creates_org_with_correct_id_and_alias(self, mock_prisma_client):
        """
        GIVEN: An Entra group ID and name
        WHEN: create_litellm_org_from_sso_group is called
        THEN: Organization is created with matching ID and alias
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        # Setup: org does not exist
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(return_value=None)

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.organization_endpoints.new_organization') as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="entra-group-123")

                result = await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="entra-group-123",
                    litellm_org_name="My Entra Group",
                )

                # Verify new_organization was called with correct params
                mock_new_org.assert_called_once()
                call_args = mock_new_org.call_args
                org_data = call_args.kwargs.get('data') or call_args.args[0]

                assert org_data.organization_id == "entra-group-123"
                assert org_data.organization_alias == "My Entra Group"

    @pytest.mark.asyncio
    async def test_applies_default_team_params_to_org(self, mock_prisma_client, default_team_params):
        """
        GIVEN: default_team_params is configured
        WHEN: create_litellm_org_from_sso_group is called
        THEN: Organization is created with default_team_params values
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.default_team_params = default_team_params
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(return_value=None)

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.organization_endpoints.new_organization') as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="entra-group-123",
                    litellm_org_name="My Entra Group",
                )

                call_args = mock_new_org.call_args
                org_data = call_args.kwargs.get('data') or call_args.args[0]

                assert org_data.max_budget == 100.0
                assert org_data.budget_duration == "30d"
                assert org_data.models == ["gpt-4", "gpt-3.5-turbo"]
                assert org_data.tpm_limit == 10000
                assert org_data.rpm_limit == 1000

    @pytest.mark.asyncio
    async def test_does_not_create_duplicate_org(self, mock_prisma_client):
        """
        GIVEN: An organization already exists with the given ID
        WHEN: create_litellm_org_from_sso_group is called
        THEN: No new organization is created, existing org is returned
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        existing_org = MagicMock()
        existing_org.organization_id = "entra-group-123"
        existing_org.model_dump.return_value = {"organization_id": "entra-group-123"}
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(return_value=existing_org)

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.organization_endpoints.new_organization') as mock_new_org:
                result = await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="entra-group-123",
                    litellm_org_name="My Entra Group",
                )

                # new_organization should NOT be called
                mock_new_org.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_no_default_team_params(self, mock_prisma_client):
        """
        GIVEN: No default_team_params configured
        WHEN: create_litellm_org_from_sso_group is called
        THEN: Organization is created with no budget/model restrictions
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.default_team_params = None
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(return_value=None)

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.organization_endpoints.new_organization') as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="entra-group-123",
                    litellm_org_name="My Entra Group",
                )

                call_args = mock_new_org.call_args
                org_data = call_args.kwargs.get('data') or call_args.args[0]

                # Should create org without budget restrictions
                assert org_data.organization_id == "entra-group-123"
```

### Run Tests (Should FAIL)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestCreateOrgFromSSOGroup -v
```

Expected: All tests fail with `AttributeError` because function doesn't exist yet.

---

## 2.2 GREEN: Implement Organization Creation Function

**File:** `litellm/proxy/management_endpoints/ui_sso.py`

Add imports at the top:
```python
from litellm.proxy._types import NewOrganizationRequest, LiteLLM_OrganizationTable
```

Add this function in the `SSOAuthenticationHandler` class (after `create_litellm_team_from_sso_group`):

```python
@staticmethod
async def create_litellm_org_from_sso_group(
    litellm_org_id: str,
    litellm_org_name: Optional[str] = None,
) -> Optional[LiteLLM_OrganizationTable]:
    """
    Creates a LiteLLM Organization from a SSO Group ID.

    Args:
        litellm_org_id: The ID for the org (Entra Group ID)
        litellm_org_name: The display name for the org (Entra Group Display Name)

    Returns:
        The created/existing organization, or None on error
    """
    from litellm.proxy.proxy_server import prisma_client
    from litellm.proxy.management_endpoints.organization_endpoints import new_organization

    if prisma_client is None:
        raise ProxyException(
            message="Prisma client not found",
            type=ProxyErrorTypes.auth_error,
            param="prisma_client",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        # Check if org already exists
        existing_org = await prisma_client.db.litellm_organizationtable.find_first(
            where={"organization_id": litellm_org_id}
        )

        if existing_org:
            verbose_proxy_logger.debug(
                f"Organization already exists: {litellm_org_id} - {litellm_org_name}"
            )
            return LiteLLM_OrganizationTable(**existing_org.model_dump())

        # Build organization request
        org_data = NewOrganizationRequest(
            organization_id=litellm_org_id,
            organization_alias=litellm_org_name or litellm_org_id,
        )

        # Apply default_team_params if set
        if litellm.default_team_params:
            default_params = litellm.default_team_params
            if isinstance(default_params, dict):
                if "models" in default_params:
                    org_data.models = default_params["models"]
                if "max_budget" in default_params:
                    org_data.max_budget = default_params["max_budget"]
                if "budget_duration" in default_params:
                    org_data.budget_duration = default_params["budget_duration"]
                if "tpm_limit" in default_params:
                    org_data.tpm_limit = default_params["tpm_limit"]
                if "rpm_limit" in default_params:
                    org_data.rpm_limit = default_params["rpm_limit"]
            else:
                # DefaultTeamSSOParams object
                org_data.models = default_params.models or []
                org_data.max_budget = default_params.max_budget
                org_data.budget_duration = default_params.budget_duration
                org_data.tpm_limit = default_params.tpm_limit
                org_data.rpm_limit = default_params.rpm_limit

        # Create the organization
        created_org = await new_organization(
            data=org_data,
            user_api_key_dict=UserAPIKeyAuth(
                user_role=LitellmUserRoles.PROXY_ADMIN,
                token="",
                key_alias=f"litellm.{SSOAuthenticationHandler.__name__}",
            ),
        )

        verbose_proxy_logger.info(
            f"Created organization from SSO group: {litellm_org_id} - {litellm_org_name}"
        )

        return created_org

    except Exception as e:
        verbose_proxy_logger.exception(f"Error creating organization from SSO group: {e}")
        return None
```

### Run Tests (Should PASS)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestCreateOrgFromSSOGroup -v
```

---

## 2.3 REFACTOR

Consider extracting the `default_team_params` application logic into a helper method if needed:

---

## 2.4 Mock Realism Validation

### Current Mock Strategy

Tests mock `new_organization()` to bypass database calls. This is **appropriate for unit tests** but may miss integration issues.

### Why Mocks Are Necessary

The real `new_organization()` function:
- Requires a live Prisma client connection
- Performs database writes
- Has complex validation logic

For fast, isolated unit tests, we mock this function.

### Ensuring Mocks Match Reality

**Step 1: Verify Real Function Signature**
```bash
grep -A 15 "async def new_organization" litellm/proxy/management_endpoints/organization_endpoints.py
```

**Step 2: Add Mock Validation in Tests**

The tests should validate that mock calls match the expected API:

```python
# In test methods, add these assertions:
call_args = mock_new_org.call_args
org_data = call_args.kwargs.get('data') or call_args.args[0]

# Verify data type matches NewOrganizationRequest
assert isinstance(org_data, NewOrganizationRequest)

# Verify required fields are present
assert org_data.organization_id is not None
assert org_data.organization_alias is not None
```

### Known Implementation Considerations

The `new_organization()` function requires:

1. **`user_api_key_dict`** with `PROXY_ADMIN` role
   - Our code provides this via:
     ```python
     UserAPIKeyAuth(
         user_role=LitellmUserRoles.PROXY_ADMIN,
         token="",
         key_alias=f"litellm.{SSOAuthenticationHandler.__name__}",
     )
     ```

2. **Valid `NewOrganizationRequest`** object
   - Must pass Pydantic validation
   - Our tests verify the structure of this object

### Integration Test Coverage

Cycle 7 includes integration tests that verify the complete chain works correctly. See [Cycle 7: E2E](./CYCLE-7-E2E.md) for database integration tests.

### Model List Clarification

**Important:** The organization's `models` list copied from `default_team_params` is the **source of truth**. Org-scoped teams will store `["all-org-models"]` which **resolves to** this org model list at runtime.

This is NOT a circular reference - it's a deliberate design:
- **Org:** Stores actual models `["gpt-4", "gpt-3.5-turbo"]`
- **Team:** Stores special value `["all-org-models"]`
- **Runtime:** Team's special value lookups org's actual models

```python
@staticmethod
def _apply_default_params_to_org_request(
    org_request: NewOrganizationRequest,
    default_params: Optional[Union[DefaultTeamSSOParams, Dict]],
) -> NewOrganizationRequest:
    """Apply default_team_params to organization request."""
    if not default_params:
        return org_request

    if isinstance(default_params, dict):
        org_request.models = default_params.get("models", org_request.models)
        org_request.max_budget = default_params.get("max_budget", org_request.max_budget)
        org_request.budget_duration = default_params.get("budget_duration", org_request.budget_duration)
        org_request.tpm_limit = default_params.get("tpm_limit", org_request.tpm_limit)
        org_request.rpm_limit = default_params.get("rpm_limit", org_request.rpm_limit)

    return org_request
```

---

## Verification Checklist

- [ ] All 4 tests pass
- [ ] Organization is created with correct ID and alias
- [ ] `default_team_params` are applied to org
- [ ] Duplicate orgs are not created
- [ ] Orgs can be created without `default_team_params`
- [ ] Logging is present for created orgs

---

## Summary

**What changed:**
- Added `create_litellm_org_from_sso_group()` static method to `SSOAuthenticationHandler`
- Function creates organizations from Entra group IDs
- Applies `default_team_params` if configured
- Checks for duplicates to ensure idempotency

**Why:**
- Enables organization creation from SSO groups
- Applies global configuration to new organizations
- Prevents duplicate organization creation

**Dependencies:**
- Cycle 1 (configuration flag)
- `new_organization()` function in `organization_endpoints.py`

**Next:** [Cycle 3: Org-Scoped Teams →](./CYCLE-3-ORG-SCOPED-TEAMS.md)

---

[← Back to Cycles README](./README.md) | [← Previous: Cycle 1](./CYCLE-1-CONFIG.md) | [Next: Cycle 3 →](./CYCLE-3-ORG-SCOPED-TEAMS.md)
