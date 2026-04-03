# m365-posture

[![CI](https://github.com/DNBLabs/m365-posture/actions/workflows/ci.yml/badge.svg)](https://github.com/DNBLabs/m365-posture/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Read-only **Microsoft 365 / Entra ID posture reporting** for a single tenant: pull normalized signals from **Microsoft Graph** (guest users, directory roles, applications, Intune-managed devices, optional sign-in and audit summaries), aggregate them into one **versioned JSON** model, and render **HTML** for quick review. Built as a **portfolio-grade** CLI—suitable for homelab or interview walk-through—with **least-privilege** Graph scopes, **no secrets in git**, **structured logging**, and **automated tests** in CI.

## Why this project

Helpdesk and junior automation roles often touch the same problems: scattered admin portals, one-off scripts, and reports that are hard to reproduce. This tool shows how to turn that into **repeatable, operator-friendly automation**: explicit configuration, documented permissions, graceful handling of partial API failures, and output you can schedule or diff over time.

## What it demonstrates

- **Microsoft Graph** integration (app-only auth via **Azure Identity** / **MSAL** patterns; certificate or client secret from the environment only).
- **Operational discipline**: pagination, throttling-aware retries, per-chapter degradation instead of failing the whole run, separate run logs under the output directory.
- **Security-minded defaults**: optional `--redact` for artifacts, permission matrix in-repo ([`docs/permissions.md`](docs/permissions.md)), no `.env` or keys committed.
- **Software quality**: modular “chapter” collectors, contract-style JSON output, **`pytest`** suite with fixtures, **GitHub Actions** on every push and PR.

Technical design notes and implementation history live under [`docs/`](docs/) (including a written specification used to drive development).

## Prerequisites

- **Python 3.11+**
- An **Entra ID app registration** with **application** permissions granted and **admin consent** for the chapters you enable (see [`docs/permissions.md`](docs/permissions.md)).
- **Authentication:** certificate (PFX path + optional password) **or** a **client secret** (certificates are preferred for long-running or scheduled jobs).

## Install

From the repository root:

```bash
pip install -e ".[dev]"
```

This installs the `m365-posture` console script and development dependencies (e.g. `pytest`).

## Configuration

Set environment variables before running. Use [`.env.example`](.env.example) as a template; copy real values into a local `.env` or your shell / Task Scheduler (never commit `.env`).

| Variable | Required | Description |
|----------|----------|-------------|
| `TENANT_ID` | Yes | Entra tenant (directory) ID |
| `CLIENT_ID` | Yes | Application (client) ID of the app registration |
| `GRAPH_CERT_PATH` | One of cert or secret | Filesystem path to the PFX used for app-only certificate auth |
| `GRAPH_CERT_PASSWORD` | If PFX is encrypted | Password for the PFX |
| `CLIENT_SECRET` | One of cert or secret | Client secret (when not using a certificate) |
| `CHAPTER_GUESTS` | No | `true` / `false` — guests chapter (default `true`) |
| `CHAPTER_PRIVILEGED` | No | Privileged roles chapter (default `true`) |
| `CHAPTER_APPLICATIONS` | No | Applications chapter (default `true`) |
| `CHAPTER_DEVICES` | No | Managed devices chapter (default `true`) |
| `CHAPTER_SIGNIN_RISK` | No | Optional sign-in / audit chapter (default `false`) |
| `OUTPUT_DIR` | No | In `.env.example` for consistency; the `run` command uses **`--out`** for report output |

## Run

```bash
m365-posture run --out ./out [--redact]
```

- **`--out`**: Directory for `report.json`, `report.html`, and `runs/*.log` (created if missing).
- **`--redact`**: Redact sensitive values in the generated JSON/HTML before write.

The CLI does not load `.env` automatically; export variables or use your scheduler’s environment block.

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
- **Operational hardening:** Prefer a certificate over a client secret for scheduled runs; restrict who can read the PFX and log files under `--out`.

## Scheduling on Windows

For Task Scheduler setup, see [`docs/operations/scheduling-task-scheduler.md`](docs/operations/scheduling-task-scheduler.md).

## License

This project is licensed under the [MIT License](LICENSE).
