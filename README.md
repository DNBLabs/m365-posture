# m365-posture

**m365-posture** collects read-only signals from Microsoft Graph across a fixed set of “chapters” (guest users, privileged role assignments, applications, managed devices, optional sign-in risk), aggregates them into one JSON model, and renders HTML for quick review. It is meant for security and identity teams who want a repeatable snapshot without storing tenant secrets in the repository.

Graph permission choices and chapter-to-scope mapping are documented in [docs/permissions.md](docs/permissions.md).

## Prerequisites

- **Python 3.11+**
- An **Entra ID (Azure AD) app registration** with application permissions granted and admin consent as needed for your chosen chapters (see [docs/permissions.md](docs/permissions.md))
- **Authentication:** certificate-based auth (PFX path + optional password) **or** a **client secret** (prefer certificates for long-running or scheduled jobs)

## Install

From the repository root:

```bash
pip install -e ".[dev]"
```

This installs the `m365-posture` console script and development dependencies (e.g. `pytest`).

## Configuration

Set environment variables before running. Use [.env.example](.env.example) as a template of names and safe placeholders; copy secrets and real IDs into a local `.env` file or into your shell / scheduled task (never commit `.env`).

| Variable | Required | Description |
|----------|----------|-------------|
| `TENANT_ID` | Yes | Entra tenant (directory) ID |
| `CLIENT_ID` | Yes | Application (client) ID of the app registration |
| `GRAPH_CERT_PATH` | One of cert or secret | Filesystem path to the PFX used for app-only certificate auth |
| `GRAPH_CERT_PASSWORD` | If PFX is encrypted | Password for the PFX |
| `CLIENT_SECRET` | One of cert or secret | Client secret (when not using a certificate) |
| `CHAPTER_GUESTS` | No | `true` / `false` — enable guests chapter (default `true`) |
| `CHAPTER_PRIVILEGED` | No | Enable privileged chapter (default `true`) |
| `CHAPTER_APPLICATIONS` | No | Enable applications chapter (default `true`) |
| `CHAPTER_DEVICES` | No | Enable devices chapter (default `true`) |
| `CHAPTER_SIGNIN_RISK` | No | Enable optional sign-in / audit chapter (default `false`) |
| `OUTPUT_DIR` | No | Present in `.env.example` for consistency; the **`run` command uses `--out`** for where reports are written |

## Run

```bash
m365-posture run --out ./out [--redact]
```

- **`--out`**: Directory for `report.json`, `report.html`, and `runs/*.log` (created if missing).
- **`--redact`**: Redact sensitive values in the generated JSON/HTML before write.

Ensure `TENANT_ID`, `CLIENT_ID`, and either `GRAPH_CERT_PATH` or `CLIENT_SECRET` are set in the environment (the CLI does not load `.env` automatically).

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

- **No secrets in the repo:** Certificates, client secrets, and tenant-specific IDs belong in environment variables or a secure secret store, not in git. Use `.env.example` only as a template.
- **Least privilege:** Grant only the Graph application permissions each enabled chapter needs; avoid broader directory scopes unless required. See [docs/permissions.md](docs/permissions.md).
- **Operational hardening:** Prefer a certificate over a client secret for scheduled runs; use a dedicated service account / managed identity posture where your platform supports it, and restrict who can read the PFX and logs under `--out`.

## Scheduling on Windows

For running this tool on a schedule with Task Scheduler, see [docs/operations/scheduling-task-scheduler.md](docs/operations/scheduling-task-scheduler.md).
