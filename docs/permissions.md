# Microsoft Graph permissions matrix

This document lists the Microsoft Graph API permissions required for each chapter of the posture report.

| Chapter   | Minimum permission | Justification | Microsoft Learn |
|-----------|-------------------|---------------|-----------------|
| `guests`  | `User.Read.All`   | Read directory users to detect guest accounts (`userType`, UPN patterns) when listing users the application can access. | [User resource permissions](https://learn.microsoft.com/en-us/graph/permissions-reference#user-permissions) (`User.Read.All` is listed under delegated and application permissions for User). |
