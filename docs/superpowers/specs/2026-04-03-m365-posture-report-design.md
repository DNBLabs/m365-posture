# M365 / Entra ID / Intune Posture Report — Design Specification

**Date:** 2026-04-03  
**Status:** Draft — brainstorming complete; pending final human sign-off of this committed spec  
**Audience:** Homelab single-tenant; portfolio / interview artifact  

## 1. Purpose, scope, and success criteria

### Purpose

Deliver a repeatable scheduled or on-demand **health snapshot** for one **Microsoft Entra ID + Microsoft 365** tenant (homelab with E5). The tool collects **read-only** signals exposed primarily through **Microsoft Graph** (including Intune-related data where the APIs and licensing expose it) and produces:

- A **human-readable** report (HTML or Markdown).
- **Machine-readable JSON** suitable for diffing across runs (includes explicit **`schemaVersion`** for contract tests).
- **Structured logs** for operators (run summary, timing, and diagnostic detail on failure—without leaking secrets to public demos).

This mirrors work strong L2 teams do manually and signals **operational maturity** for junior automation-oriented roles.

### In scope (v1)

- **App-only** authentication to Microsoft Graph with **documented least-privilege** permissions (each permission justified in README or appendix). **Deliverable #1** in implementation is a **permission matrix** validated against real chapter code paths; the spec lists **illustrative** starting points below—not final grants.
- **Read-only** data collection (no tenant mutations in v1).
- **Findings** with severity (INFO / WARN) and **evidence** (counts, representative examples subject to redaction rules in §3).
- **Outputs:** timestamped `report.html` (or `.md`) + `report.json` + **one timestamped run log file per execution** (e.g. `runs/2026-04-03T14-22-01Z.log`), not a single ever-growing append file unless rotation is explicitly implemented.
- **Scheduling:** document one supported approach (e.g. Windows Task Scheduler, GitHub Actions, or Azure Automation) for recurring runs; implementation may ship with one default documented path.

### Illustrative Application permissions (validate minimum during implementation)

Use the **smallest** subset that satisfies each enabled chapter. **Anti-pattern:** granting `*.ReadWrite.All` or broad Directory write for v1 read-only tooling—avoid unless a future remediation phase is scoped separately.

| Area | Example *starting* Application permissions (confirm vs. Microsoft docs) |
|------|--------------------------------------------------------------------------|
| Users / groups / guests | `User.Read.All`, `Group.Read.All` (or narrower if chapter permits) |
| Directory roles | `RoleManagement.Read.Directory` (or equivalent read role assignment APIs) |
| Applications | `Application.Read.All` |
| Devices / Intune | `DeviceManagementConfiguration.Read.All`, `DeviceManagementManagedDevices.Read.All` (as needed) |
| Sign-in / audit / risk | **Varies** by API: sign-in and audit logs, and Identity Protection–style signals, may require different resources and Entra ID **P1/P2** capabilities. Implementer must document which calls are used and **omit** a chapter if the tenant or role model cannot satisfy it read-only. |

### Out of scope (v1)

- Automated remediation (license changes, user disable, Conditional Access edits, bulk deletes).
- Multi-tenant SaaS or hosted productization.
- Full web UI, persistent database, or SIEM replacement.
- Incident response depth (tool produces summaries only; caveats in report text).

### Success criteria

- A reviewer can **clone the repository**, configure **environment-based secrets** (and cert or secret per documented pattern), run **one primary command**, and receive artifacts in an output directory.
- Failures are **actionable** from logs (which collector failed, Graph error payload, request correlation when present).
- **Permissions are minimal** and explained in a permission matrix.
- Optional **`--redact`** mode masks PII in outputs for public demos per defaults in §3.

---

## 2. Architecture and components

### High-level architecture

```text
CLI (run) → Config → Graph client → Collectors (chapters) → Aggregator → Renderer → outputs + logs
```

### Components

1. **Config layer**  
   Tenant ID, application (client) ID, authentication mode (certificate preferred over long-lived client secret where practical), output directory, optional feature flags per chapter, optional schedule metadata for documentation.

2. **Graph client module**  
   **Authentication:** confidential client using **MSAL** (or language-equivalent), **certificate-based** client assertion preferred. Token acquisition, HTTP client with **retries and exponential backoff**, **pagination helpers** (`@odata.nextLink`), consistent error wrapping (operation name, status, Graph error body, `request-id` / `client-request-id` when returned).

3. **Collectors (“chapters”)**  
   One logical module per domain. Each returns **normalized data** plus **zero or more findings**. **Default execution order: sequential** (parallelism at most 1–2 only if proven safe). Initial suggested chapters (exact endpoints and fields finalized during implementation based on tenant behavior):

   | Chapter | Intent (read-only) |
   |---------|---------------------|
   | Guests / external collaboration | Guest counts, aging heuristics, collaboration posture signals available via Graph |
   | Privileged access | Directory role assignments (read-only snapshot); caveats in narrative where interpretation is limited |
   | Applications / service principals | High-level counts and outliers (e.g., credential age signals if safely readable—implementation validates availability) |
   | Devices / Intune (Graph) | Compliance and OS/version summaries where APIs succeed in the homelab |
   | Sign-in / risk (as available) | Summary metrics only; explicit “not IR” disclaimer in report. **Note:** sign-in logs, audit logs, and identity protection–style data differ by API surface, app role, and **Entra ID P1/P2**; v1 may omit this chapter if the homelab cannot access the intended APIs read-only. |

4. **Report renderer**  
   Merges chapter outputs into a **stable JSON document** with top-level **`schemaVersion`** and generates HTML or Markdown from a template.

5. **CLI entrypoint**  
   Example: `run --out ./dist [--redact]`. Non-zero exit on fatal configuration or authentication failure; partial chapter failure does not necessarily fail the overall process (see Section 3).

### Tooling note (Cursor)

Use Cursor for scaffolding (pagination, types), refactoring collectors as chapters grow, tests from fixtures, and README/diagrams—not for bypassing permission or tenant safety review.

---

## 3. Data flow, rate limits, and error handling

### Data flow

1. CLI loads configuration from environment and optional CLI flags.  
2. Acquire app-only token for Microsoft Graph.  
3. Execute collectors **sequentially by default**; optional **low bounded concurrency** (at most 1–2) only when justified.  
4. Aggregate results; apply redaction if enabled.  
5. Write `report.json`, `report.html` or `report.md`, and **timestamped** run log file under the output directory.  
6. Emit **short summary only** to stdout (suitable for scheduled job dashboards). **Full diagnostic detail** (Graph bodies, correlation IDs) goes to the **log file**, not stdout.

### Reliability and throttling

- All list operations must handle **pagination**.  
- On HTTP 429 or transient errors: **backoff with jitter**; respect `Retry-After` when present.  
- Cap parallelism to reduce throttling risk in small tenants.

### Partial success

- If one chapter fails, **other chapters continue** where feasible.  
- Final report marks failed chapter as **DEGRADED** with a short user-facing reason.  
- Log files may contain **operational** diagnostics (HTTP status, Graph error JSON, `request-id`). **Never log** access tokens, refresh tokens, client secrets, certificate private keys, or raw authorization headers.

### Security posture

- **No secrets committed.** Provide `.env.example` with dummy placeholders; real `.env` gitignored.  
- Prefer **certificate-based** client authentication for the app registration; if client secret is used for homelab-only speed, document rotation and never commit the value.  
- **`--redact` defaults** (refine in implementation; document in README): mask **UPNs and email**; mask **display names**; replace or hash **object IDs (GUIDs)**; strip or generalize **tenant-specific domain names** in narrative text where feasible. Option to keep **last 4 characters** of a UPN for debugging in private runs only (off when redact is on).

---

## 4. Testing and interview narrative

### Testing strategy

- **Unit tests** for finding logic and aggregation using **sanitized static JSON fixtures** (recorded from Graph responses stripped of PII). **Fixtures must not contain production tenant identifiers**—only homelab or synthetic values.  
- **Contract / golden tests** for output JSON schema stability (update goldens intentionally when **`schemaVersion`** bumps).  
- **Optional local smoke test** documented against the homelab (not required in CI if no tenant secrets in pipeline).

### Interview talking points

- Why each Graph permission exists; how you would **reduce** scope further.  
- Pagination, throttling, and **degraded** partial reports.  
- Why v1 is **read-only** and how you would add **gated remediation** later (approval, idempotency, audit).

---

## 5. Open decisions (implementation phase)

- Primary language: **PowerShell 7+** vs **Python 3** (team familiarity and CI ergonomics)—to be chosen in the implementation plan.  
- Default scheduler documentation target: Task Scheduler vs GitHub Actions vs Azure Automation.  
- Final chapter list after validating Graph responses in the E5 homelab.

---

## 6. Approval and review gate

- **Design direction** (Sections 1–4 narrative from brainstorming) was accepted on 2026-04-03.  
- **This committed spec** must be explicitly **read and approved** by the human maintainer before starting implementation planning (`writing-plans` skill). Edits after that approval should bump a short revision note at the bottom of this file or in commit history.
