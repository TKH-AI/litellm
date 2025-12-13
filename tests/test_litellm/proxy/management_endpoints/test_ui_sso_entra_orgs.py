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
