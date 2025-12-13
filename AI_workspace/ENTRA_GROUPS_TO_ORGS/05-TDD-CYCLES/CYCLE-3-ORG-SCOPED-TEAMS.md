# Cycle 3: Org-Scoped Team Creation

## Goal

Modify team creation to support org-scoped teams with `organization_id` and `"all-org-models"`.

---

## 3.1 RED: Write Failing Tests

```python
# ============================================================================
# CYCLE 3: Org-Scoped Team Creation
# ============================================================================

class TestOrgScopedTeamCreation:
    """Tests for org-scoped team creation."""

    @pytest.mark.asyncio
    async def test_creates_team_with_organization_id(self, mock_prisma_client):
        """Team is created with organization_id set when provided."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.team_endpoints.new_team') as mock_new_team:
                mock_new_team.return_value = MagicMock(team_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    organization_id="entra-group-123",  # NEW PARAMETER
                )

                call_args = mock_new_team.call_args
                team_data = call_args.kwargs.get('data') or call_args.args[0]
                assert team_data.organization_id == "entra-group-123"

    @pytest.mark.asyncio
    async def test_sets_models_to_all_org_models_when_org_scoped(self, mock_prisma_client):
        """Team models is set to ['all-org-models'] when org-scoped."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.team_endpoints.new_team') as mock_new_team:
                mock_new_team.return_value = MagicMock(team_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    organization_id="entra-group-123",
                )

                call_args = mock_new_team.call_args
                team_data = call_args.kwargs.get('data') or call_args.args[0]
                assert team_data.models == [SpecialModelNames.all_org_models.value]

    @pytest.mark.asyncio
    async def test_does_not_update_existing_team_fields(self, mock_prisma_client):
        """Existing standalone teams are NOT updated."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        existing_team = MagicMock()
        existing_team.team_id = "entra-group-123"
        existing_team.organization_id = None  # Standalone
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=existing_team)
        mock_prisma_client.db.litellm_teamtable.update = AsyncMock()

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                litellm_team_id="entra-group-123",
                litellm_team_name="My Team",
                organization_id="entra-group-123",
            )

            mock_prisma_client.db.litellm_teamtable.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_standalone_team_when_no_organization_id(self, mock_prisma_client):
        """Standalone team is created when no organization_id provided."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.team_endpoints.new_team') as mock_new_team:
                mock_new_team.return_value = MagicMock(team_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    # No organization_id
                )

                call_args = mock_new_team.call_args
                team_data = call_args.kwargs.get('data') or call_args.args[0]
                assert team_data.organization_id is None
```

### Run Tests (Should FAIL)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestOrgScopedTeamCreation -v
```

---

## 3.2 GREEN: Modify Team Creation Function

**File:** `litellm/proxy/management_endpoints/ui_sso.py`

Modify `create_litellm_team_from_sso_group()`:

```python
@staticmethod
async def create_litellm_team_from_sso_group(
    litellm_team_id: str,
    litellm_team_name: Optional[str] = None,
    organization_id: Optional[str] = None,  # NEW PARAMETER
):
    """
    Creates a Litellm Team from a SSO Group ID

    Args:
        litellm_team_id: The ID of the team (Entra Group ID)
        litellm_team_name: The display name (Entra Group Display Name)
        organization_id: If provided, team will be org-scoped
    """
    from litellm.proxy.proxy_server import prisma_client

    if prisma_client is None:
        raise ProxyException(
            message="Prisma client not found",
            type=ProxyErrorTypes.auth_error,
            param="prisma_client",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        team_obj = await prisma_client.db.litellm_teamtable.find_first(
            where={"team_id": litellm_team_id}
        )

        if team_obj:
            verbose_proxy_logger.debug(
                f"Team already exists: {litellm_team_id} - {litellm_team_name}"
            )
            # Do NOT update existing teams
            return

        team_request = NewTeamRequest(
            team_id=litellm_team_id,
            team_alias=litellm_team_name,
            organization_id=organization_id,  # NEW: Set org association
        )

        # If org-scoped, set models to inherit from org
        if organization_id:
            team_request.models = [SpecialModelNames.all_org_models.value]

        if litellm.default_team_params:
            team_request = SSOAuthenticationHandler._cast_and_deepcopy_litellm_default_team_params(
                default_team_params=litellm.default_team_params,
                litellm_team_id=litellm_team_id,
                litellm_team_name=litellm_team_name,
                team_request=team_request,
            )
            # Override models for org-scoped teams (after applying defaults)
            if organization_id:
                team_request.models = [SpecialModelNames.all_org_models.value]

        await new_team(
            data=team_request,
            http_request=Request(scope={"type": "http", "method": "POST"}),
            user_api_key_dict=UserAPIKeyAuth(
                token="",
                key_alias=f"litellm.{MicrosoftSSOHandler.__name__}",
            ),
        )

        verbose_proxy_logger.info(
            f"Created team from SSO group: {litellm_team_id} (org_scoped={organization_id is not None})"
        )

    except Exception as e:
        verbose_proxy_logger.exception(f"Error creating Litellm Team: {e}")
```

### Run Tests (Should PASS)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestOrgScopedTeamCreation -v
```

---

## 3.3 REFACTOR

No additional refactoring needed.

---

## Summary

**What changed:**
- Added `organization_id` parameter to `create_litellm_team_from_sso_group()`
- When `organization_id` is provided, team models default to `["all-org-models"]`
- Existing teams are not modified (preserves manual configuration)

**Why:**
- Enables org-scoped team creation
- Teams inherit org's model restrictions
- Preserves existing team configurations

**Dependencies:**
- Cycle 2 (organization creation)

**Next:** [Cycle 4: Organization Membership →](./CYCLE-4-ORG-MEMBERSHIP.md)

---

[← Back to Cycles README](./README.md) | [← Previous: Cycle 2](./CYCLE-2-ORG-CREATION.md) | [Next: Cycle 4 →](./CYCLE-4-ORG-MEMBERSHIP.md)
