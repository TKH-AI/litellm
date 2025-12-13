# Cycle 5: Main Sync Function Integration

## Goal

Modify `create_litellm_teams_from_service_principal_team_ids()` to create orgs when flag is enabled.

---

## 5.1 RED: Write Failing Tests

```python
# ============================================================================
# CYCLE 5: Main Sync Function Integration
# ============================================================================

class TestMainSyncFunction:
    """Tests for create_litellm_teams_from_service_principal_team_ids integration."""

    @pytest.mark.asyncio
    async def test_creates_org_and_team_when_flag_enabled(self, sample_entra_group):
        """Both organization and org-scoped team are created when flag=True."""
        from litellm.proxy.management_endpoints.ui_sso import MicrosoftSSOHandler

        litellm.entra_groups_also_create_orgs = True

        with patch.object(MicrosoftSSOHandler, 'create_litellm_org_from_sso_group', new_callable=AsyncMock) as mock_create_org:
            with patch.object(MicrosoftSSOHandler, 'create_litellm_team_from_sso_group', new_callable=AsyncMock) as mock_create_team:
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=[sample_entra_group]
                )

                # Verify org creation was called
                mock_create_org.assert_called_once_with(
                    litellm_org_id="entra-group-id-123",
                    litellm_org_name="Production LLM Team",
                )

                # Verify team creation was called with organization_id
                mock_create_team.assert_called_once_with(
                    litellm_team_id="entra-group-id-123",
                    litellm_team_name="Production LLM Team",
                    organization_id="entra-group-id-123",
                )

    @pytest.mark.asyncio
    async def test_only_creates_team_when_flag_disabled(self, sample_entra_group):
        """Only standalone team is created when flag=False."""
        from litellm.proxy.management_endpoints.ui_sso import MicrosoftSSOHandler

        litellm.entra_groups_also_create_orgs = False

        with patch.object(MicrosoftSSOHandler, 'create_litellm_org_from_sso_group', new_callable=AsyncMock) as mock_create_org:
            with patch.object(MicrosoftSSOHandler, 'create_litellm_team_from_sso_group', new_callable=AsyncMock) as mock_create_team:
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=[sample_entra_group]
                )

                # Verify org creation was NOT called
                mock_create_org.assert_not_called()

                # Verify team creation was called without organization_id
                mock_create_team.assert_called_once_with(
                    litellm_team_id="entra-group-id-123",
                    litellm_team_name="Production LLM Team",
                    organization_id=None,
                )

    @pytest.mark.asyncio
    async def test_handles_multiple_groups(self, sample_entra_groups):
        """Org and team are created for each group."""
        from litellm.proxy.management_endpoints.ui_sso import MicrosoftSSOHandler

        litellm.entra_groups_also_create_orgs = True

        with patch.object(MicrosoftSSOHandler, 'create_litellm_org_from_sso_group', new_callable=AsyncMock) as mock_create_org:
            with patch.object(MicrosoftSSOHandler, 'create_litellm_team_from_sso_group', new_callable=AsyncMock) as mock_create_team:
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=sample_entra_groups
                )

                assert mock_create_org.call_count == 2
                assert mock_create_team.call_count == 2
```

### Run Tests (Should FAIL)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestMainSyncFunction -v
```

---

## 5.2 GREEN: Modify Main Sync Function

**File:** `litellm/proxy/management_endpoints/ui_sso.py`

Modify `create_litellm_teams_from_service_principal_team_ids()`:

```python
@staticmethod
async def create_litellm_teams_from_service_principal_team_ids(
    service_principal_teams: List[MicrosoftServicePrincipalTeam],
):
    """
    Creates LiteLLM Teams (and optionally Organizations) from Service Principal Group IDs.

    When entra_groups_also_create_orgs is True:
    - Creates an Organization for each Entra group
    - Creates an org-scoped Team for each Entra group

    When entra_groups_also_create_orgs is False (default):
    - Creates standalone Teams only (current behavior)
    """
    verbose_proxy_logger.debug(
        f"Creating LiteLLM entities from Service Principal Teams: {service_principal_teams}"
    )

    create_orgs = getattr(litellm, 'entra_groups_also_create_orgs', False)

    for service_principal_team in service_principal_teams:
        litellm_team_id: Optional[str] = service_principal_team.get("principalId")
        litellm_team_name: Optional[str] = service_principal_team.get("principalDisplayName")

        if not litellm_team_id:
            verbose_proxy_logger.debug(
                f"Skipping service principal team with no principalId: {service_principal_team}"
            )
            continue

        organization_id: Optional[str] = None

        if create_orgs:
            # Create organization first
            await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                litellm_org_id=litellm_team_id,
                litellm_org_name=litellm_team_name,
            )
            organization_id = litellm_team_id

        # Create team (org-scoped if create_orgs is True)
        await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
            litellm_team_id=litellm_team_id,
            litellm_team_name=litellm_team_name,
            organization_id=organization_id,
        )
```

### Run Tests (Should PASS)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestMainSyncFunction -v
```

---

## 5.3 REFACTOR

No additional refactoring needed.

---

## Summary

**What changed:**
- Modified `create_litellm_teams_from_service_principal_team_ids()` to check `entra_groups_also_create_orgs` flag
- When flag=True: creates org first, then org-scoped team
- When flag=False: creates standalone team (existing behavior)

**Why:**
- Integrates org creation into main SSO flow
- Maintains backward compatibility (default behavior unchanged)
- Allows feature to be toggled via configuration

**Dependencies:**
- Cycles 1-4 (configuration, org creation, org-scoped teams, membership)

**Next:** [Cycle 6: User Login Integration →](./CYCLE-6-USER-LOGIN.md)

---

[← Back to Cycles README](./README.md) | [← Previous: Cycle 4](./CYCLE-4-ORG-MEMBERSHIP.md) | [Next: Cycle 6 →](./CYCLE-6-USER-LOGIN.md)
