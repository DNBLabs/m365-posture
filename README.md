# m365-posture

[![CI](https://github.com/DNBLabs/m365-posture/actions/workflows/ci.yml/badge.svg)](https://github.com/DNBLabs/m365-posture/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Read-only **Microsoft 365 / Entra ID posture reporting** for a single tenant: pull normalized signals from **Microsoft Graph** (guest users, directory roles, applications, Intune-managed devices, optional sign-in and audit summaries), aggregate them into one **versioned JSON** model, and render **HTML** for quick review. Built as a **portfolio-grade** CLI—suitable for homelab or interview walk-through—with **least-privilege** Graph scopes, **no secrets in git**, **structured logging**, and **automated tests** in CI.

## Why this project

Helpdesk and junior automation roles often touch the same problems: scattered admin portals, one-off scripts, and reports that are hard to reproduce. This tool shows how to turn that into **repeatable, operator-friendly automation**: explicit configuration, documented permissions, graceful handling of partial API failures, and output you can schedule or diff over time.

## What it demonstrates

- **Microsoft Graph** integration (app-only auth via **Azure Identity**; **certificate credentials are preferred**, client secret optional for quick lab tests).
- **Operational discipline**: pagination, throttling-aware retries, per-chapter degradation instead of failing the whole run, separate run logs under the output directory.
- **Security-minded defaults**: optional `--redact` for artifacts, permission matrix in-repo ([`docs/permissions.md`](docs/permissions.md)), no `.env` or keys committed.
- **Software quality**: modular “chapter” collectors, contract-style JSON output, **`pytest`** suite with fixtures, **GitHub Actions** on every push and PR.

Technical design notes and implementation history live under [`docs/`](docs/) (including a written specification used to drive development).

## Prerequisites

- **Python 3.11+**
- **Microsoft Entra ID** (Azure AD) with permission to create (or use) an **app registration** and grant **admin consent** for **application** permissions.
- **Preferred authentication:** an **X.509 certificate** (public key uploaded to the app registration; private key in a **PFX** file used locally). This avoids long-lived client secrets and matches how many production automations authenticate.
- **Optional:** a **client secret** only for short-lived lab setups—see [Client secret (alternative)](#client-secret-alternative).

---

## Quick start: Certificate auth + PowerShell

This walkthrough assumes a **homelab or dev tenant** where you can create app registrations. Use **least privilege**: grant only the Graph **application** permissions for the chapters you enable. The full matrix is in [`docs/permissions.md`](docs/permissions.md).

### 1. Create a certificate (homelab)

For a **local self-signed** cert suitable for testing (not for production attestation):

1. Open **PowerShell** and run from the repository root:

   ```powershell
   .\scripts\generate-homelab-cert.ps1
   ```

2. The script creates under **`./certs/`** (gitignored):
   - **`graph-app.cer`** — **public** cert: you will upload this to Entra.
   - **`graph-app.pfx`** — **private** key: keep on your machine; you will point `GRAPH_CERT_PATH` here.

   The script also imports the certificate into **`Cert:\CurrentUser\My`** for export. Remove it from the store when you are done testing if you do not want it left on that profile (e.g. shared machines or golden VM images).

   For production or employer policy, use your org’s process (internal CA, Key Vault, managed identity, etc.) instead of this script.

### 2. Register an app in Microsoft Entra ID

1. Sign in to the **[Microsoft Entra admin center](https://entra.microsoft.com/)** (or [Azure portal](https://portal.azure.com/) → **Microsoft Entra ID**).
2. Go to **Identity** → **Applications** → **App registrations** → **New registration**.
3. Set **Name** (e.g. `m365-posture-readonly`).
4. Choose **Supported account types** (typically **Accounts in this organizational directory only** for a single-tenant report).
5. Leave **Redirect URI** empty for this CLI (app-only / no interactive sign-in).
6. Click **Register**.
7. On the app’s **Overview** page, copy and save:
   - **Application (client) ID** → you will set `CLIENT_ID`.
   - **Directory (tenant) ID** → you will set `TENANT_ID`.

### 3. Upload the public certificate to the app

1. In the same app registration, open **Certificates & secrets**.
2. Under **Certificates**, click **Upload certificate**.
3. Select **`./certs/graph-app.cer`** (or your `.cer` / public PEM from your CA).
4. Add a description (optional) and save.

You do **not** upload the PFX to Entra—only the public certificate. The PFX stays on the host that runs the CLI.

### 4. Grant Microsoft Graph application permissions

The tool uses **app-only** (daemon) calls, so you need **Application** permissions—not Delegated.

1. Open **API permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions**.
2. Add the permissions that match the chapters you will turn on. For the **default** chapters (all on except optional sign-in), add at least:

   | Permission | Used for chapter |
   |------------|------------------|
   | `User.Read.All` | `guests` |
   | `RoleManagement.Read.Directory` | `privileged` (see [`docs/permissions.md`](docs/permissions.md) if your tenant requires an alternative) |
   | `Application.Read.All` | `applications` |
   | `DeviceManagementManagedDevices.Read.All` | `devices` |

3. If you set `CHAPTER_SIGNIN_RISK=true`, add the **application** permissions your tenant allows for that chapter—for example **`AuditLog.Read.All`** and/or **`IdentityRiskEvent.Read.All`** (see [`docs/permissions.md`](docs/permissions.md) for details and alternatives).

4. Click **Grant admin consent for &lt;your tenant&gt;** and confirm. Without admin consent, Graph returns **403** and chapters may show as **DEGRADED**.

### 5. Install this project (PowerShell)

From the **repository root**:

```powershell
cd "c:\path\to\m365-posture"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
```

If script activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 6. Set environment variables and run (PowerShell)

The CLI reads **process environment variables only**. It does **not** load a `.env` file automatically. Environment variables are convenient for local runs but are **not** a secrets vault (they are visible to the process and anything that can read that session’s environment—use a proper store for production).

Replace the placeholders with your tenant, client ID, and the **full path** to your PFX.

```powershell
$env:TENANT_ID   = "00000000-0000-0000-0000-000000000000"   # Directory (tenant) ID
$env:CLIENT_ID   = "00000000-0000-0000-0000-000000000000"   # Application (client) ID
$env:GRAPH_CERT_PATH = "C:\path\to\m365-posture\certs\graph-app.pfx"

# Only if your PFX is password-protected:
# $env:GRAPH_CERT_PASSWORD = "your-pfx-password"

m365-posture run --out .\out
# Optional: mask PII in HTML/JSON for screenshots or sharing:
# m365-posture run --out .\out --redact
```

Outputs:

- **`out\report.json`** — full machine-readable report.
- **`out\report.html`** — human-readable summary.
- **`out\runs\*.log`** — detailed diagnostics (errors, Graph correlation IDs)—**not** meant for public sharing.

You can also invoke the module directly (useful in Task Scheduler):

```powershell
python -m m365_posture run --out .\out
```

Reference copy of variable names: [`.env.example`](.env.example) (template only—you must still export variables in PowerShell or your scheduler).

---

## Client secret (alternative)

For a **quick lab test** only, you can use a **client secret** instead of a certificate:

1. In the app registration: **Certificates & secrets** → **New client secret** → copy the **Value** once (it is shown only at creation).
2. In PowerShell, set `TENANT_ID` and `CLIENT_ID`, **clear or omit** `GRAPH_CERT_PATH` (if `GRAPH_CERT_PATH` is set, the app **always uses certificate auth** and ignores `CLIENT_SECRET`), and set:

   ```powershell
   $env:CLIENT_SECRET = "your-secret-value"
   ```

Secrets are harder to rotate safely than certs and are easier to leak from logs; **prefer the certificate flow** above for anything recurring or shared.

---

## Configuration reference

| Variable | Required | Description |
|----------|----------|-------------|
| `TENANT_ID` | Yes | Entra tenant (directory) ID |
| `CLIENT_ID` | Yes | Application (client) ID of the app registration |
| `GRAPH_CERT_PATH` | One of cert or secret | Filesystem path to the PFX for certificate auth (**preferred**). If this is set, **certificate auth wins** even when `CLIENT_SECRET` is also set. |
| `GRAPH_CERT_PASSWORD` | If PFX is encrypted | Password for the PFX |
| `CLIENT_SECRET` | One of cert or secret | Client secret (alternative when `GRAPH_CERT_PATH` is unset; lab only recommended) |
| `CHAPTER_GUESTS` | No | `true` / `false` — guests chapter (default `true`) |
| `CHAPTER_PRIVILEGED` | No | Privileged roles chapter (default `true`) |
| `CHAPTER_APPLICATIONS` | No | Applications chapter (default `true`) |
| `CHAPTER_DEVICES` | No | Managed devices chapter (default `true`) |
| `CHAPTER_SIGNIN_RISK` | No | Optional sign-in / audit chapter (default `false`) |
| `OUTPUT_DIR` | No | Documented in `.env.example`; the **`run`** command uses **`--out`** for report output |

## Run (summary)

PowerShell (same as [step 6](#6-set-environment-variables-and-run-powershell)):

```powershell
m365-posture run --out .\out
# m365-posture run --out .\out --redact
```

On macOS/Linux or any shell:

```bash
m365-posture run --out ./out
# m365-posture run --out ./out --redact
```

- **`--out`**: Directory for `report.json`, `report.html`, and `runs/*.log` (created if missing).
- **`--redact`**: Redact sensitive values in the generated JSON/HTML before write.

## Architecture (data flow)

```
  [env + app registration]
            |
            v
        load config
            |
            v
    Microsoft Graph  (authenticated GETs)
            |
            v
   chapter runners  (guests, privileged, applications, devices, signin_risk)
            |
            v
       aggregate  (single report model)
            |
            v
    render HTML (+ JSON on disk)
```

## Security notes

- **No secrets in the repository:** Certificates, client secrets, and production tenant data belong in a secret store or host configuration, not in git. Use `.env.example` only as a template.
- **Least privilege:** Grant only the Graph application permissions each enabled chapter needs. Avoid broader directory scopes unless required—see [`docs/permissions.md`](docs/permissions.md).
- **Operational hardening:** Prefer **certificate** auth over client secrets for repeated or scheduled runs; restrict who can read the PFX and log files under `--out`.

## Scheduling on Windows

For Task Scheduler setup, see [`docs/operations/scheduling-task-scheduler.md`](docs/operations/scheduling-task-scheduler.md).

## License

This project is licensed under the [MIT License](LICENSE).
