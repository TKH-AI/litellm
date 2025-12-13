# Cycle 6: User SSO Login Integration

## Goal

Add users to org membership during SSO login when flag is enabled.

---

## 6.1 RED: Write Failing Tests

```python
# ============================================================================
# CYCLE 6: User SSO Login Integration
# ============================================================================

class TestUserSSOLoginIntegration:
    """Tests for adding users to orgs during SSO login."""

    @pytest.mark.asyncio
    async def test_adds_user_to_org_on_login_when_flag_enabled(self, sample_user):
        """User is added to org membership when flag=True."""
        from litellm.proxy.management_endpoints.ui_sso import add_user_to_teams_from_sso_response

        litellm.entra_groups_also_create_orgs = True

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123", "entra-group-456"]

        with patch('litellm.proxy.management_endpoints.ui_sso.add_missing_team_member', new_callable=AsyncMock):
            with patch('litellm.proxy.management_endpoints.ui_sso.add_user_to_org_membership', new_callable=AsyncMock) as mock_add_membership:
                await add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                # Verify membership was added for each org
                assert mock_add_membership.call_count == 2
                mock_add_membership.assert_any_call(
                    user_id="user@example.com",
                    organization_id="entra-group-123",
                )
                mock_add_membership.assert_any_call(
                    user_id="user@example.com",
                    organization_id="entra-group-456",
                )

    @pytest.mark.asyncio
    async def test_does_not_add_to_org_when_flag_disabled(self, sample_user):
        """User is NOT added to org membership when flag=False."""
        from litellm.proxy.management_endpoints.ui_sso import add_user_to_teams_from_sso_response

        litellm.entra_groups_also_create_orgs = False

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123"]

        with patch('litellm.proxy.management_endpoints.ui_sso.add_missing_team_member', new_callable=AsyncMock):
            with patch('litellm.proxy.management_endpoints.ui_sso.add_user_to_org_membership', new_callable=AsyncMock) as mock_add_membership:
                await add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                mock_add_membership.assert_not_called()

    @pytest.mark.asyncio
    async def test_still_adds_to_teams_regardless_of_flag(self, sample_user):
        """User is added to teams regardless of flag setting."""
        from litellm.proxy.management_endpoints.ui_sso import add_user_to_teams_from_sso_response

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123"]

        with patch('litellm.proxy.management_endpoints.ui_sso.add_missing_team_member', new_callable=AsyncMock) as mock_add_team:
            with patch('litellm.proxy.management_endpoints.ui_sso.add_user_to_org_membership', new_callable=AsyncMock):
                await add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                mock_add_team.assert_called_once()
```

### Run Tests (Should FAIL)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestUserSSOLoginIntegration -v
```

---

## 6.2 GREEN: Modify User Login Function

**File:** `litellm/proxy/management_endpoints/ui_sso.py`

Modify `add_user_to_teams_from_sso_response()`:

```python
async def add_user_to_teams_from_sso_response(
    result: Optional[Union[CustomOpenID, OpenID, dict]],
    user_info: Optional[Union[NewUserResponse, LiteLLM_UserTable]],
):
    """
    Add user to teams (and organizations if entra_groups_also_create_orgs is True)
    """
    if user_info is None:
        return

    sso_teams = getattr(result, "team_ids", [])

    # Add to teams (existing behavior)
    await add_missing_team_member(user_info=user_info, sso_teams=sso_teams)

    # NEW: Add to organizations if flag is enabled
    create_orgs = getattr(litellm, 'entra_groups_also_create_orgs', False)
    if create_orgs and user_info.user_id and sso_teams:
        from litellm.proxy.proxy_server import prisma_client

        try:
            if prisma_client:
                # 1. Fetch existing memberships for this user
                existing_memberships = await prisma_client.db.litellm_organizationmembership.find_many(
                    where={"user_id": user_info.user_id}
                )
                existing_org_ids = {m.organization_id for m in existing_memberships}

                # 2. Identify missing orgs
                missing_org_ids = [
                    org_id for org_id in sso_teams
                    if org_id not in existing_org_ids
                ]

                # 3. Add user to missing orgs
                if missing_org_ids:
                    for org_id in missing_org_ids:
                        await add_user_to_org_membership(
                            user_id=user_info.user_id,
                            organization_id=org_id,
                        )
        except Exception as e:
            verbose_proxy_logger.debug(
                f"[Non-Blocking] Error adding user to orgs: {e}"
            )
```

### Run Tests (Should PASS)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestUserSSOLoginIntegration -v
```

---

## 6.3 REFACTOR

No additional refactoring needed.

---

## Summary

**What changed:**
- Modified `add_user_to_teams_from_sso_response()` to add users to org memberships
- Only adds to orgs when `entra_groups_also_create_orgs=True`
- Checks existing memberships to avoid duplicates
- Preserves existing team membership behavior

**Why:**
- Integrates org membership into login flow
- Users are automatically added to their organizations
- Idempotent operation (safe to call multiple times)

**Dependencies:**
- Cycles 1-5 (all previous cycles)

**Next:** [Cycle 7: End-to-End Integration →](./CYCLE-7-E2E.md)

---

[← Back to Cycles README](./README.md) | [← Previous: Cycle 5](./CYCLE-5-SYNC-FUNCTION.md) | [Next: Cycle 7 →](./CYCLE-7-E2E.md)
