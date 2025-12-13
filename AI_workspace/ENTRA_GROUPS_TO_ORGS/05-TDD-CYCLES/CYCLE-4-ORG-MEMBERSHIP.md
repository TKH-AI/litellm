# Cycle 4: Organization Membership

## Goal

Add users to organization membership when they log in.

---

## 4.1 RED: Write Failing Tests

```python
# ============================================================================
# CYCLE 4: Organization Membership
# ============================================================================

class TestOrgMembership:
    """Tests for adding users to organization membership."""

    @pytest.mark.asyncio
    async def test_adds_user_to_org_membership(self, mock_prisma_client, sample_user):
        """User is added to org membership when function called."""
        from litellm.proxy.management_endpoints.ui_sso import add_user_to_org_membership

        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(return_value=None)
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            await add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="entra-group-123",
            )

            mock_prisma_client.db.litellm_organizationmembership.create.assert_called_once()
            create_call = mock_prisma_client.db.litellm_organizationmembership.create.call_args

            assert create_call.kwargs['data']['user_id'] == "user@example.com"
            assert create_call.kwargs['data']['organization_id'] == "entra-group-123"
            assert create_call.kwargs['data']['user_role'] == "internal_user"

    @pytest.mark.asyncio
    async def test_does_not_create_duplicate_membership(self, mock_prisma_client):
        """No duplicate membership is created."""
        from litellm.proxy.management_endpoints.ui_sso import add_user_to_org_membership

        existing_membership = MagicMock()
        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(return_value=existing_membership)
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            await add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="entra-group-123",
            )

            mock_prisma_client.db.litellm_organizationmembership.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_user_role(self, mock_prisma_client):
        """Membership is created with custom role when provided."""
        from litellm.proxy.management_endpoints.ui_sso import add_user_to_org_membership

        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(return_value=None)
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            await add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="entra-group-123",
                user_role="org_admin",
            )

            create_call = mock_prisma_client.db.litellm_organizationmembership.create.call_args
            assert create_call.kwargs['data']['user_role'] == "org_admin"
```

### Run Tests (Should FAIL)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestOrgMembership -v
```

---

## 4.2 GREEN: Implement Organization Membership Function

**File:** `litellm/proxy/management_endpoints/ui_sso.py`

Add this function (can be a standalone function, not in a class):

```python
async def add_user_to_org_membership(
    user_id: str,
    organization_id: str,
    user_role: str = "internal_user",
) -> None:
    """
    Adds a user to an organization's membership if not already a member.

    Args:
        user_id: The user's ID
        organization_id: The organization ID
        user_role: Role in the org (default: internal_user)
    """
    from litellm.proxy.proxy_server import prisma_client

    if prisma_client is None:
        return

    try:
        # Check if membership already exists
        existing_membership = await prisma_client.db.litellm_organizationmembership.find_first(
            where={
                "user_id": user_id,
                "organization_id": organization_id,
            }
        )

        if existing_membership:
            verbose_proxy_logger.debug(
                f"User {user_id} already member of org {organization_id}"
            )
            return

        # Create membership
        await prisma_client.db.litellm_organizationmembership.create(
            data={
                "user_id": user_id,
                "organization_id": organization_id,
                "user_role": user_role,
            }
        )

        verbose_proxy_logger.info(
            f"Added user {user_id} to organization {organization_id}"
        )

    except Exception as e:
        verbose_proxy_logger.debug(
            f"[Non-Blocking] Error adding user to org membership: {e}"
        )
```

### Run Tests (Should PASS)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestOrgMembership -v
```

---

## 4.3 REFACTOR

No additional refactoring needed.

---

## Summary

**What changed:**
- Added `add_user_to_org_membership()` function
- Checks for duplicate memberships
- Supports custom user roles
- Non-blocking error handling

**Why:**
- Enables user membership in organizations
- Idempotent operation (safe to call multiple times)
- Supports different user roles in organizations

**Dependencies:**
- Cycle 3 (org-scoped teams)

**Next:** [Cycle 5: Main Sync Function →](./CYCLE-5-SYNC-FUNCTION.md)

---

[← Back to Cycles README](./README.md) | [← Previous: Cycle 3](./CYCLE-3-ORG-SCOPED-TEAMS.md) | [Next: Cycle 5 →](./CYCLE-5-SYNC-FUNCTION.md)
