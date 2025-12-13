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
# CYCLE 1: Configuration Flag Recognition
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
# CYCLE 3: Org-Scoped Team Creation
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


# ============================================================================
# CYCLE 4: Organization Membership
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
# CYCLE 5: Main Sync Function Integration
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
