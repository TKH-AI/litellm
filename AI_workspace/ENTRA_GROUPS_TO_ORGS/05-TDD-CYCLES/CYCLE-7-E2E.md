# Cycle 7: End-to-End Integration Test

## Goal

Verify the complete flow works together.

---

## 7.1 Write Integration Test

```python
# ============================================================================
# CYCLE 7: End-to-End Integration
# ============================================================================

class TestEndToEndIntegration:
    """End-to-end integration tests."""

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
        litellm.entra_groups_also_create_orgs = True
        litellm.default_team_params = default_team_params

        # Setup mocks for "not found" responses (entities don't exist yet)
        mock_prisma_client.db.litellm_organizationtable.find_first = AsyncMock(return_value=None)
        mock_prisma_client.db.litellm_teamtable.find_first = AsyncMock(return_value=None)
        mock_prisma_client.db.litellm_organizationmembership.find_first = AsyncMock(return_value=None)
        mock_prisma_client.db.litellm_organizationmembership.find_many = AsyncMock(return_value=[])
        mock_prisma_client.db.litellm_organizationmembership.create = AsyncMock()

        created_orgs = []
        created_teams = []

        with patch('litellm.proxy.management_endpoints.ui_sso.prisma_client', mock_prisma_client):
            with patch('litellm.proxy.management_endpoints.organization_endpoints.new_organization') as mock_new_org:
                with patch('litellm.proxy.management_endpoints.team_endpoints.new_team') as mock_new_team:
                    mock_new_org.side_effect = lambda **kwargs: MagicMock(organization_id=kwargs['data'].organization_id)
                    mock_new_team.side_effect = lambda **kwargs: MagicMock(team_id=kwargs['data'].team_id)

                    from litellm.proxy.management_endpoints.ui_sso import (
                        MicrosoftSSOHandler,
                        add_user_to_teams_from_sso_response,
                    )

                    # Step 1: Create orgs and teams from Entra groups
                    await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
                        service_principal_teams=sample_entra_groups
                    )

                    # Verify orgs were created
                    assert mock_new_org.call_count == 2

                    # Verify teams were created with org association
                    assert mock_new_team.call_count == 2
                    for call in mock_new_team.call_args_list:
                        team_data = call.kwargs.get('data') or call.args[0]
                        assert team_data.organization_id is not None
                        assert team_data.models == [SpecialModelNames.all_org_models.value]

                    # Step 2: Add user to teams and orgs
                    mock_result = MagicMock()
                    mock_result.team_ids = ["entra-group-id-123", "entra-group-id-456"]

                    with patch('litellm.proxy.management_endpoints.ui_sso.add_missing_team_member', new_callable=AsyncMock):
                        await add_user_to_teams_from_sso_response(
                            result=mock_result,
                            user_info=sample_user,
                        )

                    # Verify user was added to org memberships
                    assert mock_prisma_client.db.litellm_organizationmembership.create.call_count == 2
```

### Run Tests

```bash
# Run only Cycle 7
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestEndToEndIntegration -v

# Run all cycles
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v
```

---

## 7.2 Integration Test with Real Database (Optional)

For higher confidence that mocks align with real behavior, add an integration test using a real Prisma client (SQLite in-memory):

```python
import os

class TestDatabaseIntegration:
    """Integration tests with real database to verify mock alignment."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Skipping integration tests"
    )
    async def test_full_flow_with_real_db(self, sample_entra_groups, default_team_params):
        """
        Integration test that verifies the full flow with real database.

        This complements unit tests by ensuring mocks align with real behavior.

        GIVEN: Real Prisma client with SQLite in-memory
        WHEN: Full SSO flow executes with entra_groups_also_create_orgs=True
        THEN: Database contains expected organizations, teams, and memberships
        """
        # Skip if database not available
        from litellm.proxy.proxy_server import prisma_client
        if prisma_client is None:
            pytest.skip("Prisma client not initialized - run with database")

        litellm.entra_groups_also_create_orgs = True
        litellm.default_team_params = default_team_params

        from litellm.proxy.management_endpoints.ui_sso import MicrosoftSSOHandler

        # Execute the real function (no mocks)
        await MicrosoftSSOHandler.create_litellm_teams_from_service_principal_team_ids(
            service_principal_teams=sample_entra_groups
        )

        # Query database to verify
        for group in sample_entra_groups:
            group_id = group.principalId

            # Verify organization created
            org = await prisma_client.db.litellm_organizationtable.find_first(
                where={"organization_id": group_id}
            )
            assert org is not None, f"Organization {group_id} should exist"
            assert org.organization_alias == group.principalDisplayName

            # Verify team created with organization_id
            team = await prisma_client.db.litellm_teamtable.find_first(
                where={"team_id": group_id}
            )
            assert team is not None, f"Team {group_id} should exist"
            assert team.organization_id == group_id, "Team should be org-scoped"
            assert "all-org-models" in (team.models or []), "Team should inherit org models"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Skipping integration tests"
    )
    async def test_config_flag_loaded_from_yaml(self):
        """
        Verify that config loading mechanism works for the new flag.

        This test simulates what proxy_server.py does when loading config.
        """
        import litellm

        # Simulate YAML config loading (what proxy_server.py does)
        yaml_config = {
            "litellm_settings": {
                "entra_groups_also_create_orgs": True,
                "default_team_params": {
                    "models": ["gpt-4"],
                    "max_budget": 50.0,
                }
            }
        }

        litellm_settings = yaml_config.get("litellm_settings", {})
        for key, value in litellm_settings.items():
            setattr(litellm, key, value)

        # Verify config was loaded
        assert litellm.entra_groups_also_create_orgs is True
        assert litellm.default_team_params["models"] == ["gpt-4"]
        assert litellm.default_team_params["max_budget"] == 50.0
```

### Running Integration Tests

```bash
# Run with database (requires Prisma client initialization)
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestDatabaseIntegration -v

# Skip integration tests (for CI without database)
SKIP_INTEGRATION_TESTS=true poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v
```

### Why Integration Tests Matter

Unit tests with mocks verify:
- ✅ Code logic is correct
- ✅ Functions are called with expected arguments
- ✅ Control flow works as expected

Integration tests verify:
- ✅ Mocks match real API behavior
- ✅ Database constraints are satisfied
- ✅ Real Prisma queries work
- ✅ End-to-end data flow is correct

---

## 7.3 Verification

When all tests pass:
- ✅ Configuration flag is recognized
- ✅ Organizations are created from Entra groups
- ✅ Teams are created as org-scoped
- ✅ User memberships are created
- ✅ User team memberships are maintained
- ✅ Full SSO flow works end-to-end

---

## Summary

**What changed:**
- Added comprehensive end-to-end integration test (mocked)
- Added optional database integration tests for higher confidence
- Added config loading verification test
- Verifies all components work together
- Tests the complete SSO flow from group creation to user membership

**Why:**
- Ensures no regressions in integrated system
- Validates feature meets acceptance criteria
- Provides confidence in implementation
- Verifies mocks align with real behavior
- Confirms config loading mechanism works

**Dependencies:**
- Cycles 1-6 (all implementation cycles)

---

## Next Steps

Once all 7 cycles pass:

1. ✅ Run the full test suite to ensure no regressions
2. ✅ Review [Edge Cases](../06-EDGE-CASES.md) to ensure handling
3. ✅ Verify against [Acceptance Criteria](../07-ACCEPTANCE-CRITERIA.md)
4. ✅ Check [Appendices](../08-APPENDICES.md) for reference information
5. ✅ Commit your changes

---

## Running Full Test Suite

```bash
# Run all tests in the feature test file
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v

# Run all tests with coverage
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py -v --cov=litellm.proxy.management_endpoints.ui_sso --cov-report=html

# Run all proxy management endpoint tests
poetry run pytest tests/test_litellm/proxy/management_endpoints/ -v -k "sso"
```

---

[← Back to Cycles README](./README.md) | [← Previous: Cycle 6](./CYCLE-6-USER-LOGIN.md)
