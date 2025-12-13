# Feature Requirements

## New Configuration Option

```yaml
litellm_settings:
  entra_groups_also_create_orgs: true   # NEW FLAG

  default_team_params:                   # EXISTING - now applies to both
    max_budget: 100
    budget_duration: 30d
    models: ["gpt-4", "gpt-3.5-turbo"]
```

**Default Value:** `false` (preserves current behavior)

**Scope:** Can be set via:
- YAML configuration file
- Environment variable: `ENTRA_GROUPS_ALSO_CREATE_ORGS=true`
- At runtime: `litellm.entra_groups_also_create_orgs = True`

---

## Behavior When Flag is Enabled

For each Entra group assigned to the Enterprise Application:

### 1. Create Organization (if not exists)

- `organization_id` = Entra Group ID
- `organization_alias` = Entra Group Display Name
- Apply `default_team_params`:
  - `models`
  - `max_budget`
  - `budget_duration`
  - `tpm_limit`
  - `rpm_limit`

**Example:**
```python
Organization(
    organization_id="entra-group-123",
    organization_alias="Production LLM Team",
    models=["gpt-4", "gpt-3.5-turbo"],
    max_budget=100.0,
    budget_duration="30d",
)
```

### 2. Create Team (if not exists)

- `team_id` = Entra Group ID (same as org!)
- `team_alias` = Entra Group Display Name
- `organization_id` = Entra Group ID (org-scoped)
- `models` = `["all-org-models"]` (inherit from org)
- Apply other `default_team_params`:
  - `max_budget`
  - `budget_duration`
  - etc.

**Example:**
```python
Team(
    team_id="entra-group-123",
    team_alias="Production LLM Team",
    organization_id="entra-group-123",  # ← Links to org
    models=["all-org-models"],           # ← Inherits from org
    max_budget=100.0,
)
```

**Why same ID for both?**
- Different tables (no collision)
- Creates 1:1:1 mapping: Entra Group ↔ Org ↔ Team
- Simplifies migration and lookup

### 3. Add User to Organization

- Create entry in `LiteLLM_OrganizationMembership`
- `user_role` = `"internal_user"` (default)
- Happens when user logs in

**Example:**
```python
OrganizationMembership(
    user_id="alice@company.com",
    organization_id="entra-group-123",
    user_role="internal_user",
)
```

### 4. Add User to Team (existing behavior)

- Unchanged from current behavior
- User is added to the team they belong to

---

## Behavior When Flag is Disabled (Default)

No change. Current behavior is preserved:
- Only teams are created (standalone, no org)
- Users are added to teams only
- No organization memberships created

### Comparison Table

| Operation | Flag = `false` | Flag = `true` |
|-----------|----------------|---------------|
| Create Org | ❌ No | ✅ Yes |
| Create Team | ✅ Yes (standalone) | ✅ Yes (org-scoped) |
| Add to Team | ✅ Yes | ✅ Yes |
| Add to Org | ❌ No | ✅ Yes |
| Team Models | From defaults | `["all-org-models"]` |

---

## ID Strategy

Both `organization_id` and `team_id` use the same Entra Group ID. This is safe because:

1. **Different Tables:** They are primary keys in **different tables**
   - `organization_id` is PK in `LiteLLM_OrganizationTable`
   - `team_id` is PK in `LiteLLM_TeamTable`
   - No uniqueness conflict

2. **Clear Mapping:** Provides 1:1:1 mapping
   - One Entra Group → One Org → One Team
   - Easy to track relationships

3. **Migration Path:** Enables clean migration of existing standalone teams
   - Future: Could link existing standalone teams to new orgs
   - No retroactive ID changes needed

**Example IDs:**
```
Entra Group ID:     "550e8400-e29b-41d4-a716-446655440000"
→ Organization ID:  "550e8400-e29b-41d4-a716-446655440000"
→ Team ID:          "550e8400-e29b-41d4-a716-446655440000"
```

---

## Default Team Params Application

When creating organizations from Entra groups, the `default_team_params` configuration is applied:

```yaml
litellm_settings:
  entra_groups_also_create_orgs: true

  default_team_params:
    models: ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
    max_budget: 100.0
    budget_duration: "30d"
    tpm_limit: 10000
    rpm_limit: 1000
```

**Result for each Entra group:**

1. **Organization receives:**
   - `models`: ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
   - `max_budget`: 100.0
   - `budget_duration`: "30d"
   - `tpm_limit`: 10000
   - `rpm_limit`: 1000

2. **Team receives:**
   - `models`: ["all-org-models"] (overrides defaults, inherits from org)
   - `max_budget`: 100.0
   - `budget_duration`: "30d"
   - `tpm_limit`: 10000
   - `rpm_limit`: 1000

**Note:** If `default_team_params` is not set, organizations are created without budget/model restrictions.

---

## Model List Inheritance Explained

### Why "all-org-models" Instead of Copying?

The team's `models` field is set to `["all-org-models"]` (a special string value) rather than copying the organization's model list directly. This design choice provides:

1. **Dynamic Inheritance:** If the org's models are updated later, the team automatically inherits the change without requiring team updates.

2. **Validation Compliance:** The `_check_org_team_limits()` function in `team_endpoints.py:494` explicitly allows this special value for org-scoped teams.

3. **Runtime Resolution:** During API calls, `"all-org-models"` resolves to the org's current model list via the auth layer.

### How Runtime Resolution Works

**File:** `litellm/proxy/auth/model_checks.py`

When a team makes an API request:

```
1. Team's models field contains: ["all-org-models"]
2. Auth layer detects this special value
3. Fetches parent organization's current models list
4. Validates request model against org's models
```

**Example Flow:**
```python
# Database state:
Organization: models = ["gpt-4", "gpt-3.5-turbo"]
Team: models = ["all-org-models"], organization_id = "org-123"

# User requests gpt-4 via team key:
# → Auth resolves "all-org-models" → ["gpt-4", "gpt-3.5-turbo"]
# → "gpt-4" in ["gpt-4", "gpt-3.5-turbo"] → ✅ Allowed
```

### This is NOT a Circular Reference

The design is intentional:
- **Organization:** Stores **actual models** `["gpt-4", "gpt-3.5-turbo"]`
- **Team:** Stores **special value** `["all-org-models"]`
- **Runtime:** Team's special value **lookups** org's actual models

### Budget Enforcement

When both org and team have `max_budget`:
- **Org budget:** Enforced as upper bound (all teams combined cannot exceed)
- **Team budget:** Enforced per-team (each team cannot exceed its own limit)
- Both are active simultaneously
- Team budget must be ≤ org budget (enforced by validation)

---

## Idempotency

All operations must be idempotent:

- **Org Creation:** If org with same ID exists, use existing org
- **Team Creation:** If team with same ID exists, do not update (preserves manual config)
- **User Membership:** If membership exists, do not duplicate
- **User Team Membership:** If user already in team, do not duplicate

This allows the feature to be enabled/disabled and re-enabled without issues.

---

## Related Documentation

- See [Architecture](./02-ARCHITECTURE.md) for current system flow
- See [TDD Cycles](./05-TDD-CYCLES/) for detailed implementation
- See [Edge Cases](./06-EDGE-CASES.md) for special scenarios

---

[← Back to README](./README.md) | [← Previous: Architecture](./02-ARCHITECTURE.md) | [Next: TDD Cycles →](./05-TDD-CYCLES/)
