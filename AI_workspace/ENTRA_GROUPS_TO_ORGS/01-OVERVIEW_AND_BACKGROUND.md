# Overview & Background

## What is LiteLLM?

LiteLLM is a unified interface for 100+ LLM providers with a proxy server that handles authentication, rate limiting, and budget management.

---

## Key Entities

| Entity | Description | Table |
|--------|-------------|-------|
| **Organization** | Top-level container for teams. Has budget limits and model access controls. | `LiteLLM_OrganizationTable` |
| **Team** | Group of users with shared budget/model access. Can be standalone or org-scoped. | `LiteLLM_TeamTable` |
| **User** | Individual user. Can belong to multiple teams and organizations. | `LiteLLM_UserTable` |
| **Organization Membership** | Links users to organizations with roles. | `LiteLLM_OrganizationMembership` |

### Understanding Each Entity

**Organization**
- Top-level container in the hierarchy
- Has its own budget pool and model access list
- Can contain multiple teams
- Users can be members with specific roles

**Team**
- Group of users with shared configuration
- Can be **standalone** (no organization) or **org-scoped** (associated with an organization)
- Inherits some constraints from parent organization if org-scoped
- Has its own budget limits and model access

**Org-Scoped Team**
- A team that has an `organization_id` set
- Shares budget with the parent organization
- Model access is constrained by the organization's allowed models
- Managed within the organization's hierarchy

**User**
- Can be a member of multiple teams
- Can be a member of multiple organizations
- Has specific roles in each organization/team context

---

## Org-Scoped Teams

A team can be associated with an organization via the `organization_id` foreign key. Org-scoped teams:
- Inherit budget constraints from the org
- Must use models that are a subset of org's models (or use `"all-org-models"` special value)
- Are managed under the organization's hierarchy

### Example

```
Organization: "Production Team" (org_id: "entra-group-123")
├── Budget: $1000/month
├── Models: ["gpt-4", "gpt-3.5-turbo"]
│
└── Team: "API Developers" (team_id: "entra-group-123", organization_id: "entra-group-123")
    ├── Budget: Inherits from org
    ├── Models: ["all-org-models"] (resolves to org's models)
    │
    ├── User: alice@company.com
    └── User: bob@company.com
```

---

## Microsoft Entra ID Integration

LiteLLM supports SSO via Microsoft Entra ID (formerly Azure AD). When configured:
- Users log in via Microsoft OAuth
- LiteLLM fetches the user's group memberships via Microsoft Graph API
- Groups assigned to the Enterprise Application are synced as LiteLLM Teams

### How It Works

1. User clicks "Login with Microsoft"
2. Redirected to Microsoft login page
3. User authenticates and consents to group sync
4. Microsoft returns user info + group IDs
5. LiteLLM creates Teams from those group IDs
6. User is added to each Team
7. In the future, when flag enabled: User is also added to corresponding Organizations

---

## Related Documentation

- See [Architecture](./02-ARCHITECTURE.md) for current SSO flow diagram
- See [Requirements](./03-REQUIREMENTS.md) to understand the new behavior
- See [TDD Cycles](./05-TDD-CYCLES/) to start implementation

---

[← Back to README](./README.md) | [Next: Architecture →](./02-ARCHITECTURE.md)
