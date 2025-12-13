import Image from '@theme/IdealImage';

# Microsoft SSO: Sync Groups, Members with LiteLLM

Sync Microsoft SSO Groups, Members with LiteLLM Teams. 

<Image img={require('../../img/litellm_entra_id.png')}  style={{ width: '800px', height: 'auto' }} />

<br />
<br />


## Prerequisites

- An Azure Entra ID account with administrative access
- A LiteLLM Enterprise App set up in your Azure Portal
- Access to Microsoft Entra ID (Azure AD)


## Overview of this tutorial

1. Auto-Create Entra ID Groups on LiteLLM Teams 
2. Sync Entra ID Team Memberships
3. Set default params for new teams and users auto-created on LiteLLM

## 1. Auto-Create Entra ID Groups on LiteLLM Teams 

In this step, our goal is to have LiteLLM automatically create a new team on the LiteLLM DB when there is a new Group Added to the LiteLLM Enterprise App on Azure Entra ID.

### 1.1 Create a new group in Entra ID


Navigate to [your Azure Portal](https://portal.azure.com/) > Groups > New Group. Create a new group. 

<Image img={require('../../img/entra_create_team.png')}  style={{ width: '800px', height: 'auto' }} />

### 1.2 Assign the group to your LiteLLM Enterprise App

On your Azure Portal, navigate to `Enterprise Applications` > Select your litellm app 

<Image img={require('../../img/msft_enterprise_app.png')}  style={{ width: '800px', height: 'auto' }} />

<br />
<br />

Once you've selected your litellm app, click on `Users and Groups` > `Add user/group` 

<Image img={require('../../img/msft_enterprise_assign_group.png')}  style={{ width: '800px', height: 'auto' }} />

<br />

Now select the group you created in step 1.1. And add it to the LiteLLM Enterprise App. At this point we have added `Production LLM Evals Group` to the LiteLLM Enterprise App. The next steps is having LiteLLM automatically create the `Production LLM Evals Group` on the LiteLLM DB when a new user signs in.

<Image img={require('../../img/msft_enterprise_select_group.png')}  style={{ width: '800px', height: 'auto' }} />


### 1.3 Sign in to LiteLLM UI via SSO

Sign into the LiteLLM UI via SSO. You should be redirected to the Entra ID SSO page. This SSO sign in flow will trigger LiteLLM to fetch the latest Groups and Members from Azure Entra ID.

<Image img={require('../../img/msft_sso_sign_in.png')}  style={{ width: '800px', height: 'auto' }} />

### 1.4 Check the new team on LiteLLM UI

On the LiteLLM UI, Navigate to `Teams`, You should see the new team `Production LLM Evals Group` auto-created on LiteLLM. 

<Image img={require('../../img/msft_auto_team.png')}  style={{ width: '900px', height: 'auto' }} />

#### How this works

When a SSO user signs in to LiteLLM:
- LiteLLM automatically fetches the Groups under the LiteLLM Enterprise App
- It finds the Production LLM Evals Group assigned to the LiteLLM Enterprise App
- LiteLLM checks if this group's ID exists in the LiteLLM Teams Table
- Since the ID doesn't exist, LiteLLM automatically creates a new team with:
  - Name: Production LLM Evals Group
  - ID: Same as the Entra ID group's ID

## 2. Sync Entra ID Team Memberships

In this step, we will have LiteLLM automatically add a user to the `Production LLM Evals` Team on the LiteLLM DB when a new user is added to the `Production LLM Evals` Group in Entra ID.

### 2.1 Navigate to the `Production LLM Evals` Group in Entra ID

Navigate to the `Production LLM Evals` Group in Entra ID.

<Image img={require('../../img/msft_member_1.png')}  style={{ width: '800px', height: 'auto' }} />


### 2.2 Add a member to the group in Entra ID

Select `Members` > `Add members`

In this stage you should add the user you want to add to the `Production LLM Evals` Team.

<Image img={require('../../img/msft_member_2.png')}  style={{ width: '800px', height: 'auto' }} />



### 2.3 Sign in as the new user on LiteLLM UI

Sign in as the new user on LiteLLM UI. You should be redirected to the Entra ID SSO page. This SSO sign in flow will trigger LiteLLM to fetch the latest Groups and Members from Azure Entra ID. During this step LiteLLM sync it's teams, team members with what is available from Entra ID

<Image img={require('../../img/msft_sso_sign_in.png')}  style={{ width: '800px', height: 'auto' }} />



### 2.4 Check the team membership on LiteLLM UI

On the LiteLLM UI, Navigate to `Teams`, You should see the new team `Production LLM Evals Group`. Since your are now a member of the `Production LLM Evals Group` in Entra ID, you should see the new team `Production LLM Evals Group` on the LiteLLM UI.

<Image img={require('../../img/msft_member_3.png')}  style={{ width: '900px', height: 'auto' }} />

## 3. Set default params for new teams auto-created on LiteLLM

Since litellm auto creates a new team on the LiteLLM DB when there is a new Group Added to the LiteLLM Enterprise App on Azure Entra ID, we can set default params for new teams created.

This allows you to set a default budget, models, etc for new teams created.

### 3.1 Set `default_team_params` on litellm

Navigate to your litellm config file and set the following params

```yaml showLineNumbers title="litellm config with default_team_params"
litellm_settings:
  default_team_params:             # Default Params to apply when litellm auto creates a team from SSO IDP provider
    max_budget: 100                # Optional[float], optional): $100 budget for the team
    budget_duration: 30d           # Optional[str], optional): 30 days budget_duration for the team
    models: ["gpt-3.5-turbo"]      # Optional[List[str]], optional): models to be used by the team
```

### 3.2 Auto-create a new team on LiteLLM

- In this step you should add a new group to the LiteLLM Enterprise App on Azure Entra ID (like we did in step 1.1). We will call this group `Default LiteLLM Prod Team` on Azure Entra ID.
- Start litellm proxy server with your config
- Sign into LiteLLM UI via SSO
- Navigate to `Teams` and you should see the new team `Default LiteLLM Prod Team` auto-created on LiteLLM
- Note LiteLLM will set the default params for this new team.

<Image img={require('../../img/msft_default_settings.png')}  style={{ width: '900px', height: 'auto' }} />

## 3.5 Auto-Create Organizations from Entra Groups

In addition to creating Teams, LiteLLM can automatically create **Organizations** from your Entra ID groups. This enables hierarchical budget management and model access control at the organization level.

### When to use this feature

Use `entra_groups_also_create_orgs` when you want:
- **Organization-level budgets**: Set budget limits that apply to all teams under an organization
- **Model inheritance**: Define allowed models at the org level, teams inherit via `all-org-models`
- **Hierarchical structure**: Create a 1:1:1 mapping between Entra Groups → Organizations → Teams

### 3.5.1 Enable Organization Creation

Add `entra_groups_also_create_orgs: true` to your config:

```yaml showLineNumbers title="litellm config with org creation enabled"
litellm_settings:
  entra_groups_also_create_orgs: true  # 👈 NEW: Also create orgs from Entra groups

  default_team_params:
    models: ["gpt-4", "gpt-3.5-turbo"]
    max_budget: 100.0
    budget_duration: "30d"
    tpm_limit: 10000
    rpm_limit: 1000
```

Or via environment variable:

```bash
export ENTRA_GROUPS_ALSO_CREATE_ORGS=true
```

### 3.5.2 How it works

When `entra_groups_also_create_orgs` is enabled:

| Operation | Flag = `false` (default) | Flag = `true` |
|-----------|--------------------------|---------------|
| Create Organization | No | Yes |
| Create Team | Yes (standalone) | Yes (org-scoped) |
| Add User to Team | Yes | Yes |
| Add User to Org | No | Yes |
| Team Models | From `default_team_params` | `["all-org-models"]` (inherits from org) |

**What gets created for each Entra group:**

1. **Organization**:
   - `organization_id` = Entra Group ID
   - `organization_alias` = Entra Group Display Name
   - Budget/model settings from `default_team_params`

2. **Team** (org-scoped):
   - `team_id` = Entra Group ID (same as org)
   - `organization_id` = Entra Group ID
   - `models` = `["all-org-models"]` (inherits from organization)

3. **User Membership**:
   - User added to Team (existing behavior)
   - User added to Organization membership (new behavior)

### 3.5.3 Example: Full Configuration

```yaml showLineNumbers title="Complete config with org creation"
litellm_settings:
  entra_groups_also_create_orgs: true

  default_team_params:
    models: ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
    max_budget: 500.0
    budget_duration: "30d"
    tpm_limit: 50000
    rpm_limit: 5000
```

When a user from "Production LLM Team" (Entra Group ID: `abc-123`) logs in:

```
Organization Created:
  - organization_id: "abc-123"
  - organization_alias: "Production LLM Team"
  - models: ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
  - max_budget: 500.0

Team Created:
  - team_id: "abc-123"
  - team_alias: "Production LLM Team"
  - organization_id: "abc-123"  ← Links to org
  - models: ["all-org-models"]  ← Inherits from org

User Added:
  - To Team "abc-123"
  - To Organization membership "abc-123"
```

### 3.5.4 Behavior with Existing Data

The feature is designed to be **non-destructive**:

| Scenario | Behavior |
|----------|----------|
| Existing standalone team (no org) | Team is NOT modified - remains standalone |
| Existing org-scoped team | Team is NOT modified |
| User already in org | Skip - no duplicate membership created |
| Org creation fails | Team still created as standalone (graceful degradation) |
| Flag disabled → enabled | Only new groups get orgs; existing teams unchanged |
| Flag enabled → disabled | Existing orgs/teams remain; new groups get standalone teams |

### 3.5.5 Troubleshooting

**Organizations not being created?**

1. Verify the flag is enabled:
```python
import litellm
print(f"Feature enabled: {litellm.entra_groups_also_create_orgs}")
```

2. Check logs for errors:
```python
import logging
logging.getLogger('litellm.proxy.management_endpoints.ui_sso').setLevel(logging.DEBUG)
```

**Teams showing `organization_id = None`?**

- If the team existed before enabling the flag, it remains standalone
- New teams created after enabling will be org-scoped

**Budget not applied to organization?**

- Ensure `default_team_params` is configured with the desired budget settings
- Check that the settings are loaded before the SSO flow runs


## 4. Using Entra ID App Roles for User Permissions

You can assign user roles directly from Entra ID using App Roles. LiteLLM will automatically read the app roles from the JWT token during SSO sign-in and assign the corresponding role to the user.

### 4.1 Supported Roles

LiteLLM supports the following app roles (case-insensitive):

- `proxy_admin` - Admin over the entire LiteLLM platform
- `proxy_admin_viewer` - Read-only admin access (can view all keys and spend)
- `org_admin` - Admin over a specific organization (can create teams and users within their org)
- `internal_user` - Standard user (can create/view/delete their own keys and view their own spend)

### 4.2 Create App Roles in Entra ID

1. Navigate to your App Registration on https://portal.azure.com/
2. Go to **App roles** > **Create app role**

3. Configure the app role:
   - **Display name**: Proxy Admin (or your preferred display name)
   - **Value**: `proxy_admin` (use one of the supported role values above)
   - **Description**: Administrator access to LiteLLM proxy
   - **Allowed member types**: Users/Groups


4. Click **Apply** to save the role

### 4.3 Assign Users to App Roles

1. Navigate to **Enterprise Applications** on https://portal.azure.com/
2. Select your LiteLLM application
3. Go to **Users and groups** > **Add user/group**
4. Select the user and assign them to one of the app roles you created


### 4.4 Test the Role Assignment

1. Sign in to LiteLLM UI via SSO as a user with an assigned app role
2. LiteLLM will automatically extract the app role from the JWT token
3. The user will be assigned the corresponding LiteLLM role in the database
4. The user's permissions will reflect their assigned role

**How it works:**
- When a user signs in via Microsoft SSO, LiteLLM extracts the `roles` claim from the JWT `id_token`
- If any of the roles match a valid LiteLLM role (case-insensitive), that role is assigned to the user
- If multiple roles are present, LiteLLM uses the first valid role it finds
- This role assignment persists in the LiteLLM database and determines the user's access level

## Video Walkthrough

This walks through setting up sso auto-add for **Microsoft Entra ID**

Follow along this video for a walkthrough of how to set this up with Microsoft Entra ID

<iframe width="840" height="500" src="https://www.loom.com/embed/ea711323aa9a496d84a01fd7b2a12f54?sid=c53e238c-5bfd-4135-b8fb-b5b1a08632cf" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>













