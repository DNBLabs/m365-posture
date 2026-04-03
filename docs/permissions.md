# Microsoft Graph permissions matrix

The posture tool runs one Graph-backed **chapter** at a time. Each chapter calls specific Microsoft Graph endpoints; this page lists the **minimum application permissions** you should plan for when registering the Entra app, plus why each scope is needed.

Chapters implemented in code (and their env toggle names) are: **`guests`** (`CHAPTER_GUESTS`), **`privileged`** (`CHAPTER_PRIVILEGED`), **`applications`** (`CHAPTER_APPLICATIONS`), **`devices`** (`CHAPTER_DEVICES`), and optional **`signin_risk`** (`CHAPTER_SIGNIN_RISK`). Grant and consent only for chapters you enable.

| Chapter ID | Minimum permission | Justification | Microsoft Learn |
|------------|-------------------|---------------|-------------------|
| `guests` | `User.Read.All` | List directory users to detect guest accounts (`userType`, UPN patterns) within the data the application can read. | [User permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#user-permissions) |
| `privileged` | `RoleManagement.Read.Directory` (preferred) or `Directory.Read.All` | Read directory role assignments (`/roleManagement/directory/roleAssignments`) to summarize principals in admin roles. `Directory.Read.All` is broader but sometimes used when role-management read is not available. | [Role management](https://learn.microsoft.com/en-us/graph/permissions-reference#rolemanagement-permissions) · [Directory](https://learn.microsoft.com/en-us/graph/permissions-reference#directory-permissions) |
| `applications` | `Application.Read.All` | Enumerate application registrations (`/applications`) for an app-only summary. | [Application permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#application-permissions) |
| `devices` | `DeviceManagementManagedDevices.Read.All` | Read Intune managed devices (`/deviceManagement/managedDevices`) for compliance and OS mix. | [Intune device management](https://learn.microsoft.com/en-us/graph/permissions-reference#intune-device-management-permissions) |
| `signin_risk` *(optional)* | `AuditLog.Read.All` and/or `IdentityRiskEvent.Read.All` | Read sign-in audit samples and/or identity risk events. Many tenants restrict these; the chapter may be skipped or report **DEGRADED** without consent. | [Audit log](https://learn.microsoft.com/en-us/graph/permissions-reference#auditlog-permissions) · [Identity risk](https://learn.microsoft.com/en-us/graph/permissions-reference#identityrisk-permissions) |
