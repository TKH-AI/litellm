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
    original_flag = getattr(litellm, "entra_groups_also_create_orgs", None)
    original_params = getattr(litellm, "default_team_params", None)
    yield
    # Restore original values
    if original_flag is not None:
        litellm.entra_groups_also_create_orgs = original_flag
    elif hasattr(litellm, "entra_groups_also_create_orgs"):
        litellm.entra_groups_also_create_orgs = False
    if original_params is not None:
        litellm.default_team_params = original_params
    elif hasattr(litellm, "default_team_params"):
        litellm.default_team_params = None


# ============================================================================
# Configuration Flag Recognition
# ============================================================================


class TestConfigurationFlag:
    """Tests for entra_groups_also_create_orgs configuration flag."""

    def test_flag_exists_in_litellm_module(self):
        """
        GIVEN: The litellm module
        WHEN: Checking for entra_groups_also_create_orgs attribute
        THEN: The attribute should exist and default to False
        """
        assert hasattr(
            litellm, "entra_groups_also_create_orgs"
        ), "litellm module should have 'entra_groups_also_create_orgs' attribute"
        assert (
            litellm.entra_groups_also_create_orgs is False
        ), "Default value should be False"

    def test_flag_can_be_set_to_true(self):
        """
        GIVEN: The litellm module
        WHEN: Setting entra_groups_also_create_orgs to True
        THEN: The value should be True
        """
        litellm.entra_groups_also_create_orgs = True
        assert litellm.entra_groups_also_create_orgs is True

    def test_flag_settable_via_setattr(self):
        """
        GIVEN: The litellm module
        WHEN: Setting entra_groups_also_create_orgs via setattr (config loader mechanism)
        THEN: The value should be correctly set
        """
        # Simulate what proxy_server.py does
        setattr(litellm, "entra_groups_also_create_orgs", True)
        assert litellm.entra_groups_also_create_orgs is True

        setattr(litellm, "entra_groups_also_create_orgs", False)
        assert litellm.entra_groups_also_create_orgs is False


# ============================================================================
# Organization Creation from SSO Group
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
        from litellm.proxy.management_endpoints.ui_sso import (
            SSOAuthenticationHandler,
        )

        # Setup: org does not exist
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.organization_endpoints.new_organization"
            ) as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="entra-group-123")

                result = await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="entra-group-123",
                    litellm_org_name="My Entra Group",
                )

                # Verify new_organization was called with correct params
                mock_new_org.assert_called_once()
                call_args = mock_new_org.call_args
                org_data = call_args.kwargs.get("data") or call_args.args[0]

                assert org_data.organization_id == "entra-group-123"
                assert org_data.organization_alias == "My Entra Group"

    @pytest.mark.asyncio
    async def test_applies_default_team_params_to_org(
        self, mock_prisma_client, default_team_params
    ):
        """
        GIVEN: default_team_params is configured
        WHEN: create_litellm_org_from_sso_group is called
        THEN: Organization is created with default_team_params values
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            SSOAuthenticationHandler,
        )

        litellm.default_team_params = default_team_params
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.organization_endpoints.new_organization"
            ) as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="entra-group-123",
                    litellm_org_name="My Entra Group",
                )

                call_args = mock_new_org.call_args
                org_data = call_args.kwargs.get("data") or call_args.args[0]

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
        from litellm.proxy.management_endpoints.ui_sso import (
            SSOAuthenticationHandler,
        )

        existing_org = MagicMock()
        existing_org.organization_id = "entra-group-123"
        existing_org.model_dump.return_value = {"organization_id": "entra-group-123"}
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=existing_org
        )

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.organization_endpoints.new_organization"
            ) as mock_new_org:
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
        from litellm.proxy.management_endpoints.ui_sso import (
            SSOAuthenticationHandler,
        )

        litellm.default_team_params = None
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.organization_endpoints.new_organization"
            ) as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="entra-group-123",
                    litellm_org_name="My Entra Group",
                )

                call_args = mock_new_org.call_args
                org_data = call_args.kwargs.get("data") or call_args.args[0]

                # Should create org without budget restrictions
                assert org_data.organization_id == "entra-group-123"


# ============================================================================
# Org-Scoped Team Creation
# ============================================================================


class TestOrgScopedTeamCreation:
    """Tests for org-scoped team creation."""

    @pytest.mark.asyncio
    async def test_creates_team_with_organization_id(self, mock_prisma_client):
        """
        GIVEN: An organization_id is provided
        WHEN: create_litellm_team_from_sso_group is called
        THEN: Team is created with organization_id set
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                mock_new_team.return_value = MagicMock(team_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    organization_id="entra-group-123",  # NEW PARAMETER
                )

                call_args = mock_new_team.call_args
                team_data = call_args.kwargs.get("data") or call_args.args[0]
                assert team_data.organization_id == "entra-group-123"

    @pytest.mark.asyncio
    async def test_sets_models_to_all_org_models_when_org_scoped(
        self, mock_prisma_client
    ):
        """
        GIVEN: An organization_id is provided
        WHEN: create_litellm_team_from_sso_group is called
        THEN: Team models is set to ['all-org-models']
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                mock_new_team.return_value = MagicMock(team_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    organization_id="entra-group-123",
                )

                call_args = mock_new_team.call_args
                team_data = call_args.kwargs.get("data") or call_args.args[0]
                assert team_data.models == [SpecialModelNames.all_org_models.value]

    @pytest.mark.asyncio
    async def test_does_not_update_existing_team_fields(self, mock_prisma_client):
        """
        GIVEN: An existing standalone team (organization_id=None)
        WHEN: create_litellm_team_from_sso_group is called with organization_id
        THEN: Existing team is NOT updated
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        existing_team = MagicMock()
        existing_team.team_id = "entra-group-123"
        existing_team.organization_id = None  # Standalone
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(
            return_value=existing_team
        )
        mock_prisma_client.db.litellm_teamtable.update = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    organization_id="entra-group-123",
                )

                # new_team should NOT be called for existing teams
                mock_new_team.assert_not_called()
                # No update should be performed
                mock_prisma_client.db.litellm_teamtable.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_standalone_team_when_no_organization_id(self, mock_prisma_client):
        """
        GIVEN: No organization_id provided
        WHEN: create_litellm_team_from_sso_group is called
        THEN: Standalone team is created (organization_id=None)
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                mock_new_team.return_value = MagicMock(team_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    # No organization_id
                )

                call_args = mock_new_team.call_args
                team_data = call_args.kwargs.get("data") or call_args.args[0]
                assert team_data.organization_id is None

    @pytest.mark.asyncio
    async def test_does_not_update_already_org_scoped_team(self, mock_prisma_client):
        """
        GIVEN: An existing org-scoped team (organization_id already set)
        WHEN: create_litellm_team_from_sso_group is called
        THEN: Existing team is NOT updated
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        existing_team = MagicMock()
        existing_team.team_id = "entra-group-123"
        existing_team.organization_id = "entra-group-123"  # Already org-scoped
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(
            return_value=existing_team
        )
        mock_prisma_client.db.litellm_teamtable.update = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    organization_id="entra-group-123",
                )

                # new_team should NOT be called for existing teams
                mock_new_team.assert_not_called()
                # No update should be performed
                mock_prisma_client.db.litellm_teamtable.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_models_override_after_default_team_params(
        self, mock_prisma_client, default_team_params
    ):
        """
        GIVEN: default_team_params with models configured AND organization_id provided
        WHEN: create_litellm_team_from_sso_group is called
        THEN: Team models is set to ['all-org-models'], overriding default_team_params
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.default_team_params = default_team_params  # Has models: ["gpt-4", ...]
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                mock_new_team.return_value = MagicMock(team_id="entra-group-123")

                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="My Team",
                    organization_id="entra-group-123",
                )

                call_args = mock_new_team.call_args
                team_data = call_args.kwargs.get("data") or call_args.args[0]
                # Models should be overridden to all-org-models, NOT default_team_params models
                assert team_data.models == [SpecialModelNames.all_org_models.value]
                # But other default_team_params should still be applied
                assert team_data.max_budget == 100.0
                # Critical: organization_id must be preserved
                assert team_data.organization_id == "entra-group-123"


# ============================================================================
# Organization Membership
# ============================================================================


class TestOrgMembership:
    """Tests for adding users to organization membership."""

    @pytest.mark.asyncio
    async def test_adds_user_to_org_membership(self, mock_prisma_client):
        """User is added to org membership when function called."""
        from litellm.proxy.management_endpoints.ui_sso import (
            SSOAuthenticationHandler,
        )

        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(
            return_value=None
        )
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            await SSOAuthenticationHandler.add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="entra-group-123",
            )

            mock_prisma_client.db.litellm_organizationmembership.create.assert_called_once()
            create_call = (
                mock_prisma_client.db.litellm_organizationmembership.create.call_args
            )

            assert create_call.kwargs["data"]["user_id"] == "user@example.com"
            assert create_call.kwargs["data"]["organization_id"] == "entra-group-123"
            assert create_call.kwargs["data"]["user_role"] == "internal_user"

    @pytest.mark.asyncio
    async def test_does_not_create_duplicate_membership(self, mock_prisma_client):
        """No duplicate membership is created."""
        from litellm.proxy.management_endpoints.ui_sso import (
            SSOAuthenticationHandler,
        )

        existing_membership = MagicMock()
        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(
            return_value=existing_membership
        )
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            await SSOAuthenticationHandler.add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="entra-group-123",
            )

            mock_prisma_client.db.litellm_organizationmembership.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_user_role(self, mock_prisma_client):
        """Membership is created with custom role when provided."""
        from litellm.proxy.management_endpoints.ui_sso import (
            SSOAuthenticationHandler,
        )

        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(
            return_value=None
        )
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            await SSOAuthenticationHandler.add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="entra-group-123",
                user_role="org_admin",
            )

            create_call = (
                mock_prisma_client.db.litellm_organizationmembership.create.call_args
            )
            assert create_call.kwargs["data"]["user_role"] == "org_admin"


# ============================================================================
# Main Sync Function Integration
# ============================================================================


class TestMainSyncFunction:
    """Tests for create_litellm_teams_from_service_principal_team_ids integration."""

    @pytest.mark.asyncio
    async def test_creates_org_and_team_when_flag_enabled(self, sample_entra_group):
        """
        GIVEN: entra_groups_also_create_orgs is True
        WHEN: create_litellm_teams_from_service_principal_team_ids is called
        THEN: Both organization and org-scoped team are created
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = True

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            new_callable=AsyncMock,
        ) as mock_create_org:
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_team:
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
        """
        GIVEN: entra_groups_also_create_orgs is False
        WHEN: create_litellm_teams_from_service_principal_team_ids is called
        THEN: Only standalone team is created (no organization)
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = False

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            new_callable=AsyncMock,
        ) as mock_create_org:
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_team:
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
        """
        GIVEN: entra_groups_also_create_orgs is True and multiple Entra groups
        WHEN: create_litellm_teams_from_service_principal_team_ids is called
        THEN: Org and team are created for each group
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = True

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            new_callable=AsyncMock,
        ) as mock_create_org:
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_team:
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=sample_entra_groups
                )

                assert mock_create_org.call_count == 2
                assert mock_create_team.call_count == 2

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_org_creation_failure(
        self, sample_entra_group
    ):
        """
        GIVEN: entra_groups_also_create_orgs is True but org creation fails
        WHEN: create_litellm_teams_from_service_principal_team_ids is called
        THEN: Team is still created as standalone (graceful degradation)
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = True

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection error"),
        ) as mock_create_org:
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_team:
                # Should not raise exception
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=[sample_entra_group]
                )

                # Verify org creation was attempted
                mock_create_org.assert_called_once()

                # Verify team creation was still called with organization_id=None
                # (fallback to standalone team)
                mock_create_team.assert_called_once_with(
                    litellm_team_id="entra-group-id-123",
                    litellm_team_name="Production LLM Team",
                    organization_id=None,
                )


# ============================================================================
# User SSO Login Integration
# ============================================================================


class TestUserSSOLoginIntegration:
    """Tests for adding users to orgs during SSO login."""

    @pytest.mark.asyncio
    async def test_adds_user_to_org_on_login_when_flag_enabled(self, sample_user):
        """User is added to org membership when flag=True."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.entra_groups_also_create_orgs = True

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123", "entra-group-456"]

        with patch(
            "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
            new_callable=AsyncMock,
        ):
            with patch.object(
                SSOAuthenticationHandler,
                "add_user_to_org_membership",
                new_callable=AsyncMock,
            ) as mock_add_membership:
                await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
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
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.entra_groups_also_create_orgs = False

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123"]

        with patch(
            "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
            new_callable=AsyncMock,
        ):
            with patch.object(
                SSOAuthenticationHandler,
                "add_user_to_org_membership",
                new_callable=AsyncMock,
            ) as mock_add_membership:
                await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                mock_add_membership.assert_not_called()

    @pytest.mark.asyncio
    async def test_still_adds_to_teams_regardless_of_flag(self, sample_user):
        """User is added to teams regardless of flag setting."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123"]

        with patch(
            "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
            new_callable=AsyncMock,
        ) as mock_add_team:
            with patch.object(
                SSOAuthenticationHandler,
                "add_user_to_org_membership",
                new_callable=AsyncMock,
            ):
                await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                mock_add_team.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_empty_team_ids(self, sample_user):
        """No org membership is added when team_ids is empty."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.entra_groups_also_create_orgs = True

        mock_result = MagicMock()
        mock_result.team_ids = []

        with patch(
            "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
            new_callable=AsyncMock,
        ):
            with patch.object(
                SSOAuthenticationHandler,
                "add_user_to_org_membership",
                new_callable=AsyncMock,
            ) as mock_add_membership:
                await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                mock_add_membership.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_none_user_info(self):
        """No org membership is added when user_info is None."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.entra_groups_also_create_orgs = True

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123"]

        with patch(
            "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
            new_callable=AsyncMock,
        ) as mock_add_team:
            with patch.object(
                SSOAuthenticationHandler,
                "add_user_to_org_membership",
                new_callable=AsyncMock,
            ) as mock_add_membership:
                await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=None,
                )

                # Neither team nor org membership should be added
                mock_add_team.assert_not_called()
                mock_add_membership.assert_not_called()

    @pytest.mark.asyncio
    async def test_idempotent_on_relogin(self, sample_user, mock_prisma_client):
        """Re-login doesn't create duplicate memberships (idempotent)."""
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.entra_groups_also_create_orgs = True

        mock_result = MagicMock()
        mock_result.team_ids = ["entra-group-123"]

        # Simulate user already being a member
        existing_membership = MagicMock()
        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(
            return_value=existing_membership
        )
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch(
            "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
            new_callable=AsyncMock,
        ):
            with patch(
                "litellm.proxy.proxy_server.prisma_client",
                mock_prisma_client,
            ):
                await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                # Membership should not be created again
                mock_prisma_client.db.litellm_organizationmembership.create.assert_not_called()


# ============================================================================
# End-to-End Integration Tests
# ============================================================================


class TestEndToEndIntegration:
    """End-to-end integration tests for full SSO flow."""

    @pytest.mark.asyncio
    async def test_full_sso_flow_with_org_creation(
        self,
        mock_prisma_client,
        sample_entra_groups,
        sample_user,
        default_team_params,
    ):
        """
        GIVEN: Entra groups and entra_groups_also_create_orgs=True
        WHEN: Full SSO flow executes
        THEN: Orgs, teams, and memberships are all created correctly
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = True
        litellm.default_team_params = default_team_params

        # Setup mocks for "not found" responses (entities don't exist yet)
        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(
            return_value=None
        )
        mock_prisma_client.db.litellm_organizationmembership.find_many = AsyncMock(
            return_value=[]
        )
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        created_orgs = []
        created_teams = []

        async def mock_create_org(litellm_org_id: str, litellm_org_name: str = None):
            """Mock for create_litellm_org_from_sso_group that returns an org."""
            org = MagicMock()
            org.organization_id = litellm_org_id
            created_orgs.append(org)
            return org

        async def mock_create_team(
            litellm_team_id: str,
            litellm_team_name: str = None,
            organization_id: str = None,
        ):
            """Mock for create_litellm_team_from_sso_group that tracks calls."""
            team = MagicMock()
            team.team_id = litellm_team_id
            team.organization_id = organization_id
            created_teams.append(team)
            return team

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            side_effect=mock_create_org,
        ):
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                side_effect=mock_create_team,
            ):
                # Step 1: Create orgs and teams from Entra groups
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=sample_entra_groups
                )

                # Verify orgs were created
                assert len(created_orgs) == 2

                # Verify teams were created with org association
                assert len(created_teams) == 2
                for team in created_teams:
                    assert team.organization_id is not None

                # Step 2: Add user to teams and orgs
                mock_result = MagicMock()
                mock_result.team_ids = ["entra-group-id-123", "entra-group-id-456"]

                with patch(
                    "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
                    new_callable=AsyncMock,
                ):
                    with patch(
                        "litellm.proxy.proxy_server.prisma_client",
                        mock_prisma_client,
                    ):
                        await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
                            result=mock_result,
                            user_info=sample_user,
                        )

                # Verify user was added to org memberships
                assert (
                    mock_prisma_client.db.litellm_organizationmembership.create.call_count
                    == 2
                )

    @pytest.mark.asyncio
    async def test_full_flow_preserves_existing_standalone_teams(
        self,
        mock_prisma_client,
        sample_entra_group,
        default_team_params,
    ):
        """
        GIVEN: An existing standalone team and entra_groups_also_create_orgs=True
        WHEN: Full SSO flow executes
        THEN: Existing standalone team is NOT updated to org-scoped
        """
        from litellm.proxy.management_endpoints.ui_sso import MicrosoftSSOHandler

        litellm.entra_groups_also_create_orgs = True
        litellm.default_team_params = default_team_params

        # Setup existing standalone team
        existing_team = MagicMock()
        existing_team.team_id = "entra-group-id-123"
        existing_team.organization_id = None  # Standalone team

        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(
            return_value=existing_team
        )
        mock_prisma_client.db.litellm_teamtable.update = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client", mock_prisma_client
        ):
            with patch(
                "litellm.proxy.management_endpoints.organization_endpoints.new_organization"
            ) as mock_new_org:
                with patch(
                    "litellm.proxy.management_endpoints.ui_sso.new_team"
                ) as mock_new_team:
                    mock_new_org.return_value = MagicMock(
                        organization_id="entra-group-id-123"
                    )

                    await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                        service_principal_teams=[sample_entra_group]
                    )

                    # Org should still be created
                    mock_new_org.assert_called_once()

                    # But team should NOT be created (existing team)
                    mock_new_team.assert_not_called()

                    # And existing team should NOT be updated
                    mock_prisma_client.db.litellm_teamtable.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_flag_toggle_disabled_to_enabled(
        self,
        mock_prisma_client,
        sample_entra_groups,
    ):
        """
        GIVEN: Flag starts disabled, then becomes enabled
        WHEN: SSO flow executes after enabling
        THEN: New orgs are created for new groups
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch(
            "litellm.proxy.proxy_server.prisma_client", mock_prisma_client
        ):
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_org_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_org:
                with patch.object(
                    SSOAuthenticationHandler,
                    "create_litellm_team_from_sso_group",
                    new_callable=AsyncMock,
                ) as mock_create_team:
                    # First run with flag disabled
                    litellm.entra_groups_also_create_orgs = False
                    await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                        service_principal_teams=sample_entra_groups[:1]  # Just one group
                    )

                    # Org creation should NOT be called
                    mock_create_org.assert_not_called()
                    # Team creation should be called with organization_id=None
                    assert mock_create_team.call_count == 1
                    assert mock_create_team.call_args.kwargs["organization_id"] is None

                    mock_create_org.reset_mock()
                    mock_create_team.reset_mock()

                    # Now enable the flag and run again
                    litellm.entra_groups_also_create_orgs = True
                    await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                        service_principal_teams=sample_entra_groups[1:]  # Second group
                    )

                    # Org creation should be called now
                    mock_create_org.assert_called_once()
                    # Team creation should be called with organization_id set
                    assert mock_create_team.call_count == 1
                    assert (
                        mock_create_team.call_args.kwargs["organization_id"]
                        == "entra-group-id-456"
                    )

    @pytest.mark.asyncio
    async def test_flag_toggle_enabled_to_disabled(
        self,
        mock_prisma_client,
        sample_entra_groups,
    ):
        """
        GIVEN: Flag starts enabled, then becomes disabled
        WHEN: SSO flow executes after disabling
        THEN: New teams are created as standalone (no orgs)
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)

        with patch(
            "litellm.proxy.proxy_server.prisma_client", mock_prisma_client
        ):
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_org_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_org:
                with patch.object(
                    SSOAuthenticationHandler,
                    "create_litellm_team_from_sso_group",
                    new_callable=AsyncMock,
                ) as mock_create_team:
                    # First run with flag enabled
                    litellm.entra_groups_also_create_orgs = True
                    await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                        service_principal_teams=sample_entra_groups[:1]
                    )

                    mock_create_org.assert_called_once()
                    assert (
                        mock_create_team.call_args.kwargs["organization_id"]
                        == "entra-group-id-123"
                    )

                    mock_create_org.reset_mock()
                    mock_create_team.reset_mock()

                    # Now disable the flag
                    litellm.entra_groups_also_create_orgs = False
                    await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                        service_principal_teams=sample_entra_groups[1:]
                    )

                    # Org creation should NOT be called
                    mock_create_org.assert_not_called()
                    # Team should be standalone
                    assert mock_create_team.call_args.kwargs["organization_id"] is None

    @pytest.mark.asyncio
    async def test_user_in_multiple_orgs(
        self,
        mock_prisma_client,
        sample_user,
    ):
        """
        GIVEN: A user belongs to multiple Entra groups
        WHEN: User logs in with entra_groups_also_create_orgs=True
        THEN: User is added to ALL corresponding organization memberships
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.entra_groups_also_create_orgs = True

        # User has 3 teams/orgs
        mock_result = MagicMock()
        mock_result.team_ids = ["org-1", "org-2", "org-3"]

        # No existing memberships
        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(
            return_value=None
        )
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch(
            "litellm.proxy.management_endpoints.ui_sso.add_missing_team_member",
            new_callable=AsyncMock,
        ):
            with patch(
                "litellm.proxy.proxy_server.prisma_client",
                mock_prisma_client,
            ):
                await SSOAuthenticationHandler.add_user_to_teams_from_sso_response(
                    result=mock_result,
                    user_info=sample_user,
                )

                # Verify user was added to all 3 organizations
                assert (
                    mock_prisma_client.db.litellm_organizationmembership.create.call_count
                    == 3
                )

    @pytest.mark.asyncio
    async def test_empty_entra_groups_handled(
        self,
        mock_prisma_client,
    ):
        """
        GIVEN: An empty list of Entra groups
        WHEN: SSO flow executes
        THEN: No orgs or teams are created, no errors thrown
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = True

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            new_callable=AsyncMock,
        ) as mock_create_org:
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_team:
                # Should not raise exception
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=[]
                )

                mock_create_org.assert_not_called()
                mock_create_team.assert_not_called()


class TestDatabaseIntegration:
    """Integration tests verifying database operations and config loading."""

    @pytest.mark.asyncio
    async def test_config_flag_loaded_from_yaml(self):
        """
        Verify that config loading mechanism works for the new flag.

        This test simulates what proxy_server.py does when loading config.
        """
        # Save original value
        original_value = getattr(litellm, "entra_groups_also_create_orgs", False)

        try:
            # Simulate YAML config loading (what proxy_server.py does)
            yaml_config = {
                "litellm_settings": {
                    "entra_groups_also_create_orgs": True,
                    "default_team_params": {
                        "models": ["gpt-4"],
                        "max_budget": 50.0,
                    },
                }
            }

            litellm_settings = yaml_config.get("litellm_settings", {})
            for key, value in litellm_settings.items():
                setattr(litellm, key, value)

            # Verify config was loaded
            assert litellm.entra_groups_also_create_orgs is True
            assert litellm.default_team_params["models"] == ["gpt-4"]
            assert litellm.default_team_params["max_budget"] == 50.0
        finally:
            # Restore original value
            litellm.entra_groups_also_create_orgs = original_value

    @pytest.mark.asyncio
    async def test_config_flag_loaded_from_env(self):
        """
        Verify that the flag can be set via environment variable.
        """
        import os

        # Save original value
        original_value = getattr(litellm, "entra_groups_also_create_orgs", False)
        original_env = os.environ.get("ENTRA_GROUPS_ALSO_CREATE_ORGS")

        try:
            # Simulate environment variable loading
            os.environ["ENTRA_GROUPS_ALSO_CREATE_ORGS"] = "true"

            # In proxy_server.py, env vars are processed before setattr
            # Simulate that behavior
            env_value = os.environ.get("ENTRA_GROUPS_ALSO_CREATE_ORGS", "false")
            litellm.entra_groups_also_create_orgs = env_value.lower() == "true"

            # Verify config was loaded
            assert litellm.entra_groups_also_create_orgs is True
        finally:
            # Restore original values
            litellm.entra_groups_also_create_orgs = original_value
            if original_env is not None:
                os.environ["ENTRA_GROUPS_ALSO_CREATE_ORGS"] = original_env
            elif "ENTRA_GROUPS_ALSO_CREATE_ORGS" in os.environ:
                del os.environ["ENTRA_GROUPS_ALSO_CREATE_ORGS"]

    @pytest.mark.asyncio
    async def test_prisma_client_unavailable_for_org_creation(
        self,
    ):
        """
        GIVEN: Prisma client is None
        WHEN: create_litellm_org_from_sso_group is called
        THEN: ProxyException is raised
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler
        from litellm.proxy._types import ProxyException

        with patch("litellm.proxy.proxy_server.prisma_client", None):
            with pytest.raises(ProxyException) as exc_info:
                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="test-org",
                    litellm_org_name="Test Org",
                )

            assert "Prisma client not found" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_prisma_client_unavailable_for_membership_non_blocking(
        self,
    ):
        """
        GIVEN: Prisma client is None
        WHEN: add_user_to_org_membership is called
        THEN: Function returns early without error (non-blocking)
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        with patch("litellm.proxy.proxy_server.prisma_client", None):
            # Should not raise exception
            await SSOAuthenticationHandler.add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="test-org",
            )

    @pytest.mark.asyncio
    async def test_org_creation_with_all_default_params(
        self,
        mock_prisma_client,
    ):
        """
        GIVEN: Full default_team_params with all fields
        WHEN: create_litellm_org_from_sso_group is called
        THEN: Organization is created with all params correctly applied
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        full_params = {
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"],
            "max_budget": 500.0,
            "budget_duration": "7d",
            "tpm_limit": 50000,
            "rpm_limit": 5000,
        }
        litellm.default_team_params = full_params
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.organization_endpoints.new_organization"
            ) as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="test-org")

                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="test-org",
                    litellm_org_name="Test Organization",
                )

                call_args = mock_new_org.call_args
                org_data = call_args.kwargs.get("data") or call_args.args[0]

                assert org_data.models == ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
                assert org_data.max_budget == 500.0
                assert org_data.budget_duration == "7d"
                assert org_data.tpm_limit == 50000
                assert org_data.rpm_limit == 5000


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests edge cases"""

    @pytest.mark.asyncio
    async def test_edge_case_5_1_existing_standalone_team(self, mock_prisma_client):
        """
        Edge Case: Existing standalone team should NOT be updated.
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        existing_team = MagicMock()
        existing_team.team_id = "entra-group-123"
        existing_team.organization_id = None  # Standalone
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(
            return_value=existing_team
        )
        mock_prisma_client.db.litellm_teamtable.update = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="Team",
                    organization_id="entra-group-123",  # Trying to make org-scoped
                )

                # Team should NOT be updated
                mock_new_team.assert_not_called()
                mock_prisma_client.db.litellm_teamtable.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_edge_case_5_2_org_creation_fails(self, sample_entra_group):
        """
        Edge Case: Org creation fails - team should still be created as standalone.
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = True

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            new_callable=AsyncMock,
            side_effect=Exception("Database error"),
        ):
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_team:
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=[sample_entra_group]
                )

                # Team should be created as standalone (organization_id=None)
                mock_create_team.assert_called_once()
                assert mock_create_team.call_args.kwargs["organization_id"] is None

    @pytest.mark.asyncio
    async def test_edge_case_5_3_no_default_team_params(self, mock_prisma_client):
        """
        Edge Case No default_team_params - org created with no limits.
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        litellm.default_team_params = None
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(
            return_value=None
        )

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.organization_endpoints.new_organization"
            ) as mock_new_org:
                mock_new_org.return_value = MagicMock(organization_id="test-org")

                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="test-org",
                    litellm_org_name="Test Org",
                )

                # Should be called without budget/model restrictions
                mock_new_org.assert_called_once()

    @pytest.mark.asyncio
    async def test_edge_case_5_4_user_already_in_org(self, mock_prisma_client):
        """
        Edge Case: User already in org - skip duplicate.
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        existing_membership = MagicMock()
        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(
            return_value=existing_membership
        )
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            await SSOAuthenticationHandler.add_user_to_org_membership(
                user_id="user@example.com",
                organization_id="entra-group-123",
            )

            # Should NOT create duplicate
            mock_prisma_client.db.litellm_organizationmembership.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_edge_case_5_5_team_already_org_scoped(self, mock_prisma_client):
        """
        Edge Case: Team already org-scoped - no update.
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler

        existing_team = MagicMock()
        existing_team.team_id = "entra-group-123"
        existing_team.organization_id = "entra-group-123"  # Already org-scoped
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(
            return_value=existing_team
        )
        mock_prisma_client.db.litellm_teamtable.update = AsyncMock()

        with patch(
            "litellm.proxy.proxy_server.prisma_client",
            mock_prisma_client,
        ):
            with patch(
                "litellm.proxy.management_endpoints.ui_sso.new_team"
            ) as mock_new_team:
                await SSOAuthenticationHandler.create_litellm_team_from_sso_group(
                    litellm_team_id="entra-group-123",
                    litellm_team_name="Team",
                    organization_id="entra-group-123",
                )

                mock_new_team.assert_not_called()
                mock_prisma_client.db.litellm_teamtable.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_edge_case_5_8_empty_entra_group_creates_structure(
        self,
        mock_prisma_client,
    ):
        """
        Edge Case: Empty Entra group - org/team still created.
        """
        from litellm.proxy.management_endpoints.ui_sso import (
            MicrosoftSSOHandler,
            SSOAuthenticationHandler,
        )

        litellm.entra_groups_also_create_orgs = True

        # A group with no users (but valid principalId)
        empty_group = MicrosoftServicePrincipalTeam(
            principalId="empty-group-id",
            principalDisplayName="Empty Group",
        )

        with patch.object(
            SSOAuthenticationHandler,
            "create_litellm_org_from_sso_group",
            new_callable=AsyncMock,
        ) as mock_create_org:
            with patch.object(
                SSOAuthenticationHandler,
                "create_litellm_team_from_sso_group",
                new_callable=AsyncMock,
            ) as mock_create_team:
                await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                    service_principal_teams=[empty_group]
                )

                # Both org and team should be created
                mock_create_org.assert_called_once()
                mock_create_team.assert_called_once()

    @pytest.mark.asyncio
    async def test_edge_case_5_10_prisma_unavailable_logs_error(self):
        """
        Edge Case: Prisma unavailable - logs and raises error for org.
        """
        from litellm.proxy.management_endpoints.ui_sso import SSOAuthenticationHandler
        from litellm.proxy._types import ProxyException

        with patch("litellm.proxy.proxy_server.prisma_client", None):
            with pytest.raises(ProxyException) as exc_info:
                await SSOAuthenticationHandler.create_litellm_org_from_sso_group(
                    litellm_org_id="test-org",
                    litellm_org_name="Test Org",
                )

            assert "Prisma client not found" in str(exc_info.value.message)
