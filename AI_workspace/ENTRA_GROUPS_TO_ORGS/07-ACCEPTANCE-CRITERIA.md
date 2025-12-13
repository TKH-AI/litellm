# Acceptance Criteria

Use this checklist to verify that the feature is complete and working correctly.

---

## Configuration & Setup

- [ ] `entra_groups_also_create_orgs` flag exists in `litellm` module
- [ ] Flag defaults to `False`
- [ ] Flag can be set via environment variable: `ENTRA_GROUPS_ALSO_CREATE_ORGS=true`
- [ ] Flag can be set via YAML configuration
- [ ] Flag can be set at runtime: `litellm.entra_groups_also_create_orgs = True`

---

## When Flag is `False` (Default)

- [ ] Current behavior is completely preserved
- [ ] Only teams are created (standalone, no org)
- [ ] Users are added to teams only
- [ ] No organization memberships are created
- [ ] Existing configurations work unchanged

---

## When Flag is `True`

### Organization Creation

- [ ] Organizations are created from Entra groups
- [ ] `organization_id` = Entra Group ID
- [ ] `organization_alias` = Entra Group Display Name
- [ ] `default_team_params` are applied to org:
  - [ ] `models` field
  - [ ] `max_budget` field
  - [ ] `budget_duration` field
  - [ ] `tpm_limit` field
  - [ ] `rpm_limit` field
- [ ] Organizations with same ID are not duplicated
- [ ] Organizations can be created without `default_team_params`

### Team Creation

- [ ] Teams are created as org-scoped
- [ ] `team_id` = Entra Group ID
- [ ] `team_alias` = Entra Group Display Name
- [ ] `organization_id` = Entra Group ID (links to org)
- [ ] `models` = `["all-org-models"]` (inherit from org)
- [ ] Teams with same ID are not duplicated
- [ ] Existing standalone teams are NOT modified
- [ ] Existing org-scoped teams are NOT modified

### User Management

- [ ] Users are added to teams on login
- [ ] Users are added to organization membership on login
- [ ] Users are not added to orgs multiple times (duplicates prevented)
- [ ] Users with multiple Entra groups are added to all corresponding orgs

---

## Integration & Flow

- [ ] Full SSO flow works end-to-end:
  1. User clicks "Login with Microsoft"
  2. Organizations are created from Entra groups (if not exist)
  3. Teams are created as org-scoped (if not exist)
  4. User is created (if not exist)
  5. User is added to teams
  6. User is added to organization memberships
- [ ] All operations are idempotent (safe to run multiple times)
- [ ] Re-login of same user doesn't create duplicates

---

## Error Handling

- [ ] Organization creation failures don't break SSO flow
- [ ] Team creation still works if org creation fails
- [ ] User membership creation errors are logged but non-blocking
- [ ] Appropriate error messages are logged for debugging
- [ ] Feature gracefully handles missing `default_team_params`

---

## Backward Compatibility

- [ ] Existing SSO configurations work unchanged
- [ ] Existing organizations remain unchanged
- [ ] Existing standalone teams remain standalone (not converted)
- [ ] Existing org-scoped teams remain unchanged
- [ ] Existing user memberships remain unchanged
- [ ] Feature can be disabled without affecting existing data

---

## Edge Cases (See [Edge Cases](./06-EDGE-CASES.md) for details)

- [ ] Existing standalone team with same ID as Entra group is NOT modified
- [ ] Org creation failure doesn't prevent team creation
- [ ] Users without `default_team_params` configured are handled
- [ ] User already in org membership is not duplicated
- [ ] Team already org-scoped is not modified
- [ ] Flag can be toggled (disabled ↔ enabled) safely
- [ ] Empty Entra groups create org/team structure
- [ ] Users in multiple Entra groups are added to all orgs
- [ ] Prisma client unavailable is handled gracefully

---

## Database State

- [ ] `LiteLLM_OrganizationTable` has new org entries
- [ ] `LiteLLM_TeamTable` has org-scoped team entries
- [ ] `LiteLLM_OrganizationMembership` has user membership entries
- [ ] All foreign key relationships are valid
- [ ] No orphaned records are created
- [ ] No conflicts with existing data

---

## Logging & Debugging

- [ ] Organization creation is logged (info level)
- [ ] Team creation is logged (info level)
- [ ] User membership creation is logged (info level)
- [ ] Duplicate skips are logged (debug level)
- [ ] Errors are logged with full context (exception level)
- [ ] Feature flag setting is visible in logs

---

## Testing

- [ ] All 7 TDD cycles have passing tests
- [ ] Configuration flag test passes
- [ ] Organization creation tests pass
- [ ] Org-scoped team tests pass
- [ ] Organization membership tests pass
- [ ] Main sync function integration tests pass
- [ ] User login integration tests pass
- [ ] End-to-end integration test passes
- [ ] All tests are idempotent and independent
- [ ] No test interference (proper fixture cleanup)

---

## Performance

- [ ] Organization creation doesn't cause noticeable delays
- [ ] Team creation doesn't cause noticeable delays
- [ ] User membership creation doesn't cause noticeable delays
- [ ] Duplicate checks use efficient queries
- [ ] Batch operations are considered for multiple groups

---

## Documentation

- [ ] Feature is documented in configuration docs
- [ ] Flag usage is explained
- [ ] Default behavior is clarified
- [ ] Example configurations are provided
- [ ] Migration path is documented

---

## Deployment Checklist

Before deploying to production:

- [ ] All tests pass
- [ ] Code review is complete
- [ ] Performance testing is done
- [ ] Database migrations are tested
- [ ] Rollback plan is documented
- [ ] Monitoring alerts are configured
- [ ] Support team is trained
- [ ] Release notes are prepared

---

## Post-Deployment Verification

After deploying to production:

- [ ] Monitor logs for errors
- [ ] Verify organizations are being created
- [ ] Verify teams are being created with correct fields
- [ ] Verify users are being added to memberships
- [ ] Verify backward compatibility with existing SSO configs
- [ ] Collect metrics on feature usage
- [ ] Gather feedback from users

---

## Sign-Off

- [ ] **Developer:** All tests passing, code reviewed
- [ ] **QA:** Feature tested, edge cases verified
- [ ] **DevOps:** Deployment ready, monitoring configured
- [ ] **Product:** Acceptance criteria met, documentation complete

---

## Tracking Progress

Use this checklist during implementation:

| Phase | Status | Date | Notes |
|-------|--------|------|-------|
| Setup & Configuration | ⬜ | | |
| Core Implementation | ⬜ | | |
| Integration & Testing | ⬜ | | |
| Edge Cases | ⬜ | | |
| Documentation | ⬜ | | |
| Review & Approval | ⬜ | | |
| Deployment | ⬜ | | |

---

## Related Documentation

- See [TDD Cycles](./05-TDD-CYCLES/) for implementation details
- See [Edge Cases](./06-EDGE-CASES.md) for scenario handling
- See [Requirements](./03-REQUIREMENTS.md) for detailed requirements
- See [Appendices](./08-APPENDICES.md) for references

---

[← Back to README](./README.md) | [← Previous: Edge Cases](./06-EDGE-CASES.md) | [Next: Appendices →](./08-APPENDICES.md)
