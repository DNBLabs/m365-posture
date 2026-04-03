# Microsoft Graph permissions matrix

This document lists the Microsoft Graph API permissions required for each chapter of the posture report.

| Chapter   | Minimum permission | Justification | Microsoft Learn |
|-----------|-------------------|---------------|-----------------|
| `guests`  | `User.Read.All`   | Read directory users to detect guest accounts (`userType`, UPN patterns) when listing users the application can access. | [User resource permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#user-permissions) (`User.Read.All` is listed under delegated and application permissions for User). |
| `privileged` | `RoleManagement.Read.Directory` (preferred) or `Directory.Read.All` | List directory role assignments (`/roleManagement/directory/roleAssignments`) to summarize how many principals hold admin roles. `Directory.Read.All` is broader but commonly used when role management scopes are unavailable. | [Role management permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#rolemanagement-permissions) · [Directory permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#directory-permissions) |
| `applications` | `Application.Read.All` | Read the application registration collection (`/applications`) to count enterprise applications the tool can enumerate app-only. | [Application permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#application-permissions) |
| `devices` | `DeviceManagementManagedDevices.Read.All` | Read Intune managed devices (`/deviceManagement/managedDevices`) to summarize compliance state and operating system mix. | [Device management permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#intune-device-management-permissions) (`DeviceManagementManagedDevices.Read.All`) |
