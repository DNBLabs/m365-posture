# M365 / Entra ID / Intune Posture Report — Design Specification

**Date:** 2026-04-03  
**Status:** Approved (brainstorming)  
**Audience:** Homelab single-tenant; portfolio / interview artifact  

## 1. Purpose, scope, and success criteria

### Purpose

Deliver a repeatable scheduled or on-demand **health snapshot** for one **Microsoft Entra ID + Microsoft 365** tenant (homelab with E5). The tool collects **read-only** signals exposed primarily through **Microsoft Graph** (including Intune-related data where the APIs and licensing expose it) and produces:

- A **human-readable** report (HTML or Markdown).
- **Machine-readable JSON** suitable for diffing across runs.
- **Structured logs** for operators (run summary, timing, and diagnostic detail on failure—without leaking secrets to public demos).

This mirrors work strong L2 teams do manually and signals **operational maturity** for junior automation-oriented roles.

### In scope (v1)

- **App-only** authentication to Microsoft Graph with **documented least-privilege** permissions (each permission justified in README or appendix).
- **Read-only** data collection (no tenant mutations in v1).
- **Findings** with severity (INFO / WARN) and **evidence** (counts, representative examples subject to redaction rules).
- **Outputs:** timestamped `report.html` (or `.md`) + `report.json` + append-only **run log** (structured text or JSON lines).
- **Scheduling:** document one supported approach (e.g. Windows Task Scheduler, GitHub Actions, or Azure Automation) for recurring runs; implementation may ship with one default documented path.

### Out of scope (v1)

- Automated remediation (license changes, user disable, Conditional Access edits, bulk deletes).
- Multi-tenant SaaS or hosted productization.
- Full web UI, persistent database, or SIEM replacement.
- Incident response depth (tool produces summaries only; caveats in report text).

### Success criteria

- A reviewer can **clone the repository**, configure **environment-based secrets** (and cert or secret per documented pattern), run **one primary command**, and receive artifacts in an output directory.
- Failures are **actionable** from logs (which collector failed, Graph error payload, request correlation when present).
- **Permissions are minimal** and explained in a permission matrix.
- Optional **`--redact`** mode masks PII in outputs for public demos.

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
   Token acquisition, HTTP client with **retries and exponential backoff**, **pagination helpers** (`@odata.nextLink`), consistent error wrapping (operation name, status, Graph error body, `request-id` / `client-request-id` when returned).

3. **Collectors (“chapters”)**  
   One logical module per domain. Each returns **normalized data** plus **zero or more findings**. Initial suggested chapters (exact endpoints and fields finalized during implementation based on tenant behavior):

   | Chapter | Intent (read-only) |
   |---------|---------------------|
   | Guests / external collaboration | Guest counts, aging heuristics, collaboration posture signals available via Graph |
   | Privileged access | Directory role assignments (read-only snapshot); caveats in narrative where interpretation is limited |
   | Applications / service principals | High-level counts and outliers (e.g., credential age signals if safely readable—implementation validates availability) |
   | Devices / Intune (Graph) | Compliance and OS/version summaries where APIs succeed in the homelab |
   | Sign-in / risk (as available) | Summary metrics only; explicit “not IR” disclaimer in report |

4. **Report renderer**  
   Merges chapter outputs into a **stable JSON schema** (versioned) and generates HTML or Markdown from a template.

5. **CLI entrypoint**  
   Example: `run --out ./dist [--redact]`. Non-zero exit on fatal configuration or authentication failure; partial chapter failure does not necessarily fail the overall process (see Section 3).

### Tooling note (Cursor)

Use Cursor for scaffolding (pagination, types), refactoring collectors as chapters grow, tests from fixtures, and README/diagrams—not for bypassing permission or tenant safety review.

---

## 3. Data flow, rate limits, and error handling

### Data flow

1. CLI loads configuration from environment and optional CLI flags.  
2. Acquire app-only token for Microsoft Graph.  
3. Execute collectors **sequentially** or with **low bounded concurrency** (default: conservative; parallelism at most 1–2 unless proven safe).  
4. Aggregate results; apply redaction if enabled.  
5. Write `report.json`, `report.html` or `report.md`, and run log.  
6. Emit summary to stdout (suitable for scheduled job capture).

### Reliability and throttling

- All list operations must handle **pagination**.  
- On HTTP 429 or transient errors: **backoff with jitter**; respect `Retry-After` when present.  
- Cap parallelism to reduce throttling risk in small tenants.

### Partial success

- If one chapter fails, **other chapters continue** where feasible.  
- Final report marks failed chapter as **DEGRADED** with a short user-facing reason.  
- Logs retain **full diagnostic detail** for the operator (still no raw secrets).

### Security posture

- **No secrets committed.** Provide `.env.example` with dummy placeholders; real `.env` gitignored.  
- Prefer **certificate-based** client authentication for the app registration; if client secret is used for homelab-only speed, document rotation and never commit the value.  
- **Redaction** for public artifacts: toggles masking display names, UPNs, and tenant-specific IDs as configured.

---

## 4. Testing and interview narrative

### Testing strategy

- **Unit tests** for finding logic and aggregation using **sanitized static JSON fixtures** (recorded from Graph responses stripped of PII).  
- **Contract / golden tests** for output JSON schema stability (update goldens intentionally when schema version bumps).  
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

## 6. Approval

Design sections 1–4 approved by stakeholder conversation on 2026-04-03 (“all yes”). Proceed to implementation plan (`writing-plans` skill) after human review of this document.
