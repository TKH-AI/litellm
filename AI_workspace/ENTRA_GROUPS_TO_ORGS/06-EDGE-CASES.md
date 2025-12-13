# Edge Cases

## Overview

This section documents special scenarios and how they are handled.

---

## 5.1 Existing Standalone Team

### Scenario

A team already exists with:
- `team_id` = Entra Group ID
- `organization_id` = NULL (standalone)

And the flag is now enabled to create orgs.

### Test

`TestOrgScopedTeamCreation::test_does_not_update_existing_team_fields` (Cycle 3)

### Handling

**Do not modify the existing team.** Instead:
1. Create the Organization
2. Add the user to the Organization
3. Leave the Team as standalone

**Rationale:**
- Preserves manual configurations
- Prevents unexpected changes to existing teams
- Allows manual linking/unlinking if desired in the future
- Maintains data integrity

**Example:**
```python
# Before feature enabled:
Team(team_id="entra-group-123", organization_id=None)  # Standalone

# After feature enabled:
Organization(organization_id="entra-group-123")        # Created
Team(team_id="entra-group-123", organization_id=None)  # Unchanged!
```

---

## 5.2 Organization Creation Fails

### Scenario

Organization creation fails (e.g., database error, invalid data).

### Handling

1. Log the error
2. Still attempt to create standalone team (graceful degradation)
3. Do not fail the entire SSO flow

**Rationale:**
- Keeps users authenticated even if org creation fails
- Non-critical feature failure doesn't break authentication
- Allows users to retry or investigate later
- Logs error for debugging

**Code Pattern:**
```python
try:
    await create_litellm_org_from_sso_group(...)
except Exception as e:
    verbose_proxy_logger.exception(f"Error creating organization: {e}")
    # Continue - still create team

await create_litellm_team_from_sso_group(...)
```

---

## 5.3 No `default_team_params` Configured

### Scenario

`default_team_params` is not set in configuration.

### Test

`TestCreateOrgFromSSOGroup::test_handles_no_default_team_params` (Cycle 2)

### Handling

Create organization with no budget/model restrictions:
- No models specified (empty list)
- No max budget set
- No TPM/RPM limits
- No budget duration

**Rationale:**
- Allows flexible configuration
- Users can set limits later if desired
- Doesn't break functionality if config is missing

---

## 5.4 User Already in Organization

### Scenario

User is already a member of the organization from a previous login.

### Test

`TestOrgMembership::test_does_not_create_duplicate_membership` (Cycle 4)

### Handling

1. Check if membership exists
2. If exists, skip creation (idempotent)
3. If not exists, create membership

**Rationale:**
- Idempotent operation (safe to call multiple times)
- Prevents duplicate records
- Handles re-logins gracefully

---

## 5.5 Team Already Org-Scoped

### Scenario

A team already exists and is already org-scoped with `organization_id` set.

### Test

`TestOrgScopedTeamCreation::test_does_not_update_already_org_scoped_team` (Cycle 3)

### Handling

No update needed. The team is already correctly configured:
1. Team is not modified
2. User is simply added to the existing team
3. User is added to the organization

**Rationale:**
- Preserves existing configuration
- Prevents overwriting manual changes
- Treats idempotently

---

## 5.6 Flag Toggled: Disabled → Enabled

### Scenario

Feature flag is disabled initially, then enabled later.

### Handling

When flag is enabled:
1. New Entra groups → Trigger org + team creation
2. Existing standalone teams → Remain standalone (see 5.1)
3. New users logging in → Added to both teams and orgs

**Rationale:**
- Clean, non-destructive migration path
- Existing data is preserved
- New behavior applies to new groups

---

## 5.7 Flag Toggled: Enabled → Disabled

### Scenario

Feature flag is enabled initially, then disabled later.

### Handling

When flag is disabled:
1. Existing organizations → Remain in database
2. Existing org-scoped teams → Remain org-scoped
3. New Entra groups → Create as standalone teams (current behavior)
4. New users → Added to teams only (not orgs)

**Rationale:**
- Non-destructive downgrade
- Existing data is preserved
- New behavior is applied going forward
- Users can manually clean up if desired

---

## 5.8 Empty Entra Groups List

### Scenario

An Entra group has no members.

### Handling

Organization and team are still created:
- Team exists even if empty
- Team is ready for future users
- When first user logs in, they're added

**Rationale:**
- Consistent behavior
- Supports future group membership
- No special casing needed

---

## 5.9 User with Multiple Organizations

### Scenario

A user is a member of multiple Entra groups (and thus multiple orgs).

### Handling

User is added to all organizations they're a member of:
1. For each Entra group the user belongs to:
   - Add user to corresponding organization
   - Add user to corresponding team

**Rationale:**
- Complete org membership sync
- Users have access to all their groups' resources
- Consistent with team membership behavior

---

## 5.10 Prisma Client Not Initialized

### Scenario

Prisma client is None (database not initialized).

### Handling

Gracefully handle and log:
- For org creation: Raise ProxyException
- For membership creation: Return early (non-blocking)
- For team creation: Raise ProxyException (existing behavior)

**Rationale:**
- Prevents silent failures
- Logs errors for debugging
- Maintains feature consistency
- Respects existing error patterns

---

## Summary Table

| Scenario | Handling | Non-Breaking |
|----------|----------|--------------|
| Existing standalone team | Don't update | ✅ Yes |
| Org creation fails | Create team anyway | ✅ Yes |
| No default params | Create with no limits | ✅ Yes |
| User already in org | Skip duplicate | ✅ Yes |
| Team already org-scoped | No update | ✅ Yes |
| Flag disabled → enabled | Create new orgs | ✅ Yes |
| Flag enabled → disabled | Keep existing orgs | ✅ Yes |
| Empty Entra group | Create org/team | ✅ Yes |
| User in multiple orgs | Add to all | ✅ Yes |
| Prisma unavailable | Log and error | ✅ Partial |

---

## Related Documentation

- See [TDD Cycles](./05-TDD-CYCLES/) for test implementations
- See [Acceptance Criteria](./07-ACCEPTANCE-CRITERIA.md) for feature validation
- See [Requirements](./03-REQUIREMENTS.md) for expected behavior

---

[← Back to README](./README.md) | [Next: Acceptance Criteria →](./07-ACCEPTANCE-CRITERIA.md)
