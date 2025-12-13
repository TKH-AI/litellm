# Current System Architecture

## Relevant Environment Variables

```bash
MICROSOFT_CLIENT_ID              # OAuth Client ID
MICROSOFT_CLIENT_SECRET          # OAuth Client Secret
MICROSOFT_TENANT                 # Azure Tenant ID
MICROSOFT_SERVICE_PRINCIPAL_ID   # Enterprise Application ID (enables group syncing)
```

---

## Relevant Configuration

```yaml
litellm_settings:
  default_team_params:           # Applied to auto-created teams
    max_budget: 100
    budget_duration: 30d
    models: ["gpt-3.5-turbo"]
    tpm_limit: 10000
    rpm_limit: 1000
```

**Note:** These parameters are currently applied to Teams. With this feature, they will also be applied to Organizations when created.

---

## Current SSO Flow Diagram

**File:** `litellm/proxy/management_endpoints/ui_sso.py`

```
User clicks SSO Login
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ /sso/callback endpoint (line ~689)                                  │
│  └── Calls MicrosoftSSOHandler.get_microsoft_callback_response()    │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ MicrosoftSSOHandler.get_user_groups_from_graph_api() (line ~2138)   │
│                                                                     │
│  1. If MICROSOFT_SERVICE_PRINCIPAL_ID is set:                       │
│     → get_group_ids_from_service_principal() (line ~2267)           │
│     → create_litellm_teams_from_service_principal_team_ids()        │
│       (line ~2311)                                                  │
│                                                                     │
│  2. Fetch user's groups via /me/memberOf Graph API                  │
│                                                                     │
│  3. Return intersection of user's groups and service principal      │
│     groups                                                          │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ create_litellm_teams_from_service_principal_team_ids() (line ~2311) │
│                                                                     │
│  For each Entra group:                                              │
│   → create_litellm_team_from_sso_group() (line ~1534)               │
│     - team_id = Entra Group ID                                      │
│     - team_alias = Entra Group Display Name                         │
│     - Apply default_team_params if set                              │
│     - organization_id = None (standalone team)                      │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ add_user_to_teams_from_sso_response() (line ~1477)                  │
│  └── add_missing_team_member() (line ~446)                          │
│      - Compare user's current teams with SSO teams                  │
│      - Add user to any missing teams                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Functions to Understand

### `create_litellm_team_from_sso_group()` (line ~1534)

```python
@staticmethod
async def create_litellm_team_from_sso_group(
    litellm_team_id: str,
    litellm_team_name: Optional[str] = None,
):
    """
    Creates a Litellm Team from a SSO Group ID
    - Checks if team already exists (by team_id)
    - If not, creates team with default_team_params
    - organization_id is NOT set (standalone team)
    """
```

### `add_missing_team_member()` (line ~446)

```python
async def add_missing_team_member(
    user_info: Union[NewUserResponse, LiteLLM_UserTable],
    sso_teams: List[str]
):
    """
    - Computes: missing_teams = sso_teams - user's current teams
    - Adds user to each missing team
    """
```

---

## Database Schema (Relevant Parts)

**File:** `litellm/proxy/schema.prisma`

```prisma
model LiteLLM_OrganizationTable {
  organization_id    String @id @default(uuid())
  organization_alias String
  budget_id          String
  models             String[]
  spend              Float @default(0.0)
  metadata           Json @default("{}")
  // ... other fields
  teams              LiteLLM_TeamTable[]
  members            LiteLLM_OrganizationMembership[]
  litellm_budget_table LiteLLM_BudgetTable? @relation(...)
}

model LiteLLM_TeamTable {
  team_id         String @id @default(uuid())
  team_alias      String?
  organization_id String?  // NULL for standalone teams
  models          String[]
  max_budget      Float?
  // ... other fields
  litellm_organization_table LiteLLM_OrganizationTable? @relation(...)
}

model LiteLLM_OrganizationMembership {
  user_id         String
  organization_id String
  user_role       String?
  spend           Float?
  budget_id       String?
  @@id([user_id, organization_id])
}
```

**Key Observations:**
- `organization_id` in `LiteLLM_TeamTable` is optional (NULL for standalone teams)
- `LiteLLM_OrganizationMembership` links users to organizations
- Teams can be independently created with no organization

---

## Special Model Names

**File:** `litellm/proxy/_types.py` (line ~2488)

```python
class SpecialModelNames(enum.Enum):
    all_team_models = "all-team-models"
    all_proxy_models = "all-proxy-models"
    all_org_models = "all-org-models"    # ← Use this for org-scoped teams
    no_default_models = "no-default-models"
```

The `"all-org-models"` value is a special placeholder that resolves at runtime to the parent organization's models.

**Note:** This value is already implemented in the codebase.

---

## How This Feature Extends the Flow

With `entra_groups_also_create_orgs=True`, the flow becomes:

```
create_litellm_teams_from_service_principal_team_ids()
  │
  ├─→ create_litellm_org_from_sso_group()     [NEW]
  │   └─→ Create Organization with ID = Entra Group ID
  │
  ├─→ create_litellm_team_from_sso_group()    [MODIFIED]
  │   └─→ Create org-scoped Team with organization_id set
  │
  └─→ add_user_to_org_membership()            [NEW]
      └─→ Create membership record for user ↔ organization
```

---

## Related Documentation

- See [Requirements](./03-REQUIREMENTS.md) for the new configuration and behavior
- See [TDD Cycles](./05-TDD-CYCLES/) for implementation details
- See [Appendices](./08-APPENDICES.md) for file location reference

---

[← Back to README](./README.md) | [← Previous: Overview](./01-OVERVIEW_AND_BACKGROUND.md) | [Next: Requirements →](./03-REQUIREMENTS.md)
