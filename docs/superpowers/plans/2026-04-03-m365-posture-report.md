# M365 Posture Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use @superpowers:subagent-driven-development (recommended) or @superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a read-only **Microsoft Graph** posture reporting CLI for one homelab tenant that writes `report.json`, `report.html`, and a timestamped run log under a chosen output directory, with tests/fixtures and documented permissions.

**Architecture:** **Python 3** CLI loads env-based config, acquires an app-only token via **Azure Identity** (certificate preferred), calls Graph through the official **Microsoft Graph Python SDK** with pagination and throttled retries, runs **chapter** collectors **sequentially**, merges into a versioned JSON document (`schemaVersion`), renders HTML, and applies optional **`--redact`** before write. Partial chapter failures mark that chapter **DEGRADED**; other chapters still run.

**Tech Stack:** Python **3.11+**, `azure-identity`, `msgraph-sdk`, `jinja2` (HTML template in v1), `pytest` (fixtures + golden tests). No secrets in repo. Operators use shell/Task Scheduler env, or optional `python-dotenv` if you add it explicitly in Task 2 (not required).

**Spec:** `docs/superpowers/specs/2026-04-03-m365-posture-report-design.md`

**v1 output scope:** Deliver **`report.html`** (and `report.json`). **Markdown report is out of scope for v1**; add later if needed (spec allows `.md` as an alternative format).

**Permission matrix cadence:** Maintain `docs/permissions.md` (source of truth) **as each chapter lands**—one row minimum per chapter with Graph permission + justification + doc link. Task 12 merges polish into `README.md` and does not defer the matrix to the end only.

---

## File structure (create)

| Path | Responsibility |
|------|----------------|
| `pyproject.toml` | Project metadata, deps, `[tool.pytest.ini_options]`, optional ruff/black config (minimal). |
| `requirements.txt` | Pinned runtime + dev deps (alternative or mirror to pyproject). |
| `.gitignore` | `.env`, `*.pfx`, `*.pem`, `dist/`, `out/`, `.venv/`, `__pycache__/`, `.pytest_cache/` (merge with existing repo `.gitignore` if present). |
| `.env.example` | `TENANT_ID`, `CLIENT_ID`, `GRAPH_CERT_PATH` (path to `.pfx`), optional `GRAPH_CERT_PASSWORD`, optional `CLIENT_SECRET`; `OUTPUT_DIR`; toggles `CHAPTER_GUESTS`, `CHAPTER_PRIVILEGED`, `CHAPTER_APPLICATIONS`, `CHAPTER_DEVICES`, **`CHAPTER_SIGNIN_RISK`** (default `false`). |
| `README.md` | Architecture diagram (ASCII ok), link to **`docs/permissions.md`**, homelab setup, run commands, Task Scheduler link. |
| `docs/permissions.md` | Living **permission matrix**; updated with each chapter task. |
| `docs/operations/scheduling-task-scheduler.md` | Default scheduling doc (Windows). |
| `src/m365_posture/__init__.py` | Package marker; `__version__`. |
| `src/m365_posture/config.py` | Load settings from environment; validate required fields; paths for cert/secret. |
| `src/m365_posture/logging_setup.py` | Run logger + stdout handler rules per spec (summary vs file). |
| `src/m365_posture/graph_client.py` | Build `GraphServiceClient`, token credential, `get_all_pages` helper, **capped exponential backoff + full jitter** on 429/transient errors, honor **`Retry-After`**. |
| `src/m365_posture/graph_errors.py` | Map SDK/HTTP failures to a **safe** structured dict for logging: operation name, HTTP status, Graph error JSON, **`request-id` / `client-request-id`** when present—**never** tokens or secrets. |
| `src/m365_posture/redact.py` | `--redact` transforms on dict/tree before serializing. |
| `src/m365_posture/chapters/base.py` | `ChapterResult` + **`Finding`** model: `severity` (`INFO` \| `WARN`), `code`, `message`, optional `evidence` (counts/ids subject to redaction at render time). |
| `src/m365_posture/chapters/guests.py` | Guest/user-type heuristics from directory objects (read-only). |
| `src/m365_posture/chapters/privileged.py` | Directory role assignments snapshot. |
| `src/m365_posture/chapters/applications.py` | App registrations / service principals summary. |
| `src/m365_posture/chapters/devices.py` | Intune/managed devices summary via Graph. |
| `src/m365_posture/chapters/signin_risk.py` | Optional; feature-flagged; catch permission errors → DEGRADED + message. |
| `src/m365_posture/aggregate.py` | Merge `ChapterResult`s → single dict with `schemaVersion`, `generatedAt`, `tenantId` (or redacted), `chapters`. |
| `src/m365_posture/render.py` | `report.json` serialization + Jinja2 or string-template **HTML** (`report.html`). |
| `src/m365_posture/cli.py` | `python -m m365_posture run --out ./dist [--redact]` argparse entrypoint. |
| `tests/conftest.py` | Shared fixtures paths. |
| `tests/fixtures/graph/` | Sanitized JSON snippets (no production IDs). |
| `tests/test_redact.py` | Redaction behavior. |
| `tests/test_aggregate.py` | Aggregation + DEGRADED merging. |
| `tests/test_render_contract.py` | Golden `report.json` snapshot (`schemaVersion` bump protocol). |
| `tests/test_graph_client_pagination.py` | Mock responses: `nextLink` loop (use `responses` or `httpx.MockTransport` if needed—prefer **`pytest-httpx`** only if approved; else unittest.mock). |
| `tests/test_chapter_guests.py` | Guests chapter against fixture. |
| `tests/test_chapter_privileged.py` | Privileged chapter against fixture. |
| *(Mirror tests for apps/devices as chapters stabilize)* | |

**Open in implementation:** Exact Graph API paths per chapter follow Microsoft docs; trim permissions in README as you prove each call.

---

### Task 1: Scaffold and dependencies

**Files:**
- Create: `pyproject.toml`, `.gitignore` (or merge entries into existing), `.env.example`, `src/m365_posture/__init__.py` (`__version__ = "0.1.0"`), `README.md` (stub), `docs/permissions.md` (stub: title + “see tasks”)

- [ ] **Step 0:** If the directory is not yet a git repository, run `git init`. (Skip if `.git` already exists.)

- [ ] **Step 1:** Create or update **`.gitignore`** per file-structure table so `.env`, keys, and build artifacts never ship.

- [ ] **Step 2:** Create `pyproject.toml` with dependencies `azure-identity`, `msgraph-sdk`, `jinja2` (runtime); dev `pytest`. Set `packages`/`tool.setuptools.packages.find` or hatchling equivalent for `src` layout.

- [ ] **Step 3:** Create virtualenv, `pip install -e ".[dev]"` (or `pip install -r requirements.txt` + `pip install -e .`).

Run: `python -c "import m365_posture; print(m365_posture.__version__)"`  
Expected: `0.1.0`

- [ ] **Step 4:** Populate `.env.example` with dummy GUIDs and vars (**use `CHAPTER_SIGNIN_RISK`** consistently). No real secrets.

- [ ] **Step 5:** `README.md` one line: “Stub—expanded in Task 12.” Create `docs/permissions.md` stub.

- [ ] **Step 6:** Commit  
```bash
git add pyproject.toml .gitignore .env.example src/m365_posture/__init__.py README.md docs/permissions.md
git commit -m "chore: scaffold m365_posture package"
```

---

### Task 2: Config loading (TDD)

**Files:**
- Create: `src/m365_posture/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Failing test**

```python
# tests/test_config.py
import os
import pytest
from m365_posture.config import load_config, ConfigError

def test_load_config_requires_tenant_and_client(monkeypatch):
    monkeypatch.delenv("TENANT_ID", raising=False)
    monkeypatch.delenv("CLIENT_ID", raising=False)
    with pytest.raises(ConfigError):
        load_config()
```

- [ ] **Step 2:** Run `pytest tests/test_config.py -v` → expect FAIL (import or ConfigError not defined).

- [ ] **Step 3: Minimal implementation**

```python
# src/m365_posture/config.py
import os
from dataclasses import dataclass
from typing import Optional


class ConfigError(ValueError):
    pass


@dataclass
class AppConfig:
    tenant_id: str
    client_id: str
    cert_path: Optional[str]
    cert_password: Optional[str]
    client_secret: Optional[str]
    output_dir: str
    chapters: dict[str, bool]


def load_config() -> AppConfig:
    tenant_id = os.environ.get("TENANT_ID")
    client_id = os.environ.get("CLIENT_ID")
    if not tenant_id or not client_id:
        raise ConfigError("TENANT_ID and CLIENT_ID are required")
    cert_path = os.environ.get("GRAPH_CERT_PATH")
    cert_password = os.environ.get("GRAPH_CERT_PASSWORD")
    client_secret = os.environ.get("CLIENT_SECRET")
    if not cert_path and not client_secret:
        raise ConfigError("Either GRAPH_CERT_PATH or CLIENT_SECRET must be set for app-only auth")
    output_dir = os.environ.get("OUTPUT_DIR", "./dist")
    chapters = {
        "guests": os.environ.get("CHAPTER_GUESTS", "true").lower() == "true",
        "privileged": os.environ.get("CHAPTER_PRIVILEGED", "true").lower() == "true",
        "applications": os.environ.get("CHAPTER_APPLICATIONS", "true").lower() == "true",
        "devices": os.environ.get("CHAPTER_DEVICES", "true").lower() == "true",
        "signin_risk": os.environ.get("CHAPTER_SIGNIN_RISK", "false").lower() == "true",
    }
    return AppConfig(
        tenant_id=tenant_id,
        client_id=client_id,
        cert_path=cert_path,
        cert_password=cert_password,
        client_secret=client_secret,
        output_dir=output_dir,
        chapters=chapters,
    )
```

- [ ] **Step 4:** `pytest tests/test_config.py -v` → PASS

- [ ] **Step 5:** Add second test: with env set, `load_config()` returns `AppConfig` with expected tenant. Run → PASS.

- [ ] **Step 6 (optional):** If you want `python-dotenv`, add dependency + call `load_dotenv()` only when env `M365_POSTURE_LOAD_DOTENV=1` (or explicit CLI flag later) so production/Task Scheduler behavior stays explicit. Document in README.

- [ ] **Step 7:** Commit `feat: add env-based configuration`

_Chapter env var in code must read_ **`CHAPTER_SIGNIN_RISK`** _for the sign-in/risk toggle._

---

### Task 3: Structured logging

**Files:**
- Create: `src/m365_posture/logging_setup.py`
- Create: `tests/test_logging_setup.py` (smoke: logger has file handler, not token in formatter)

- [ ] **Step 1:** Implement `configure_logging(log_file: Path)` — file handler DEBUG, root logger; document that **callers** log full Graph errors to file only. stdout: CLI prints one-line summary in `cli.py`, not via secret-bearing log records.

- [ ] **Step 2:** Test: after configure, logging a dummy message writes to temp log file. Commit `feat: add run log file handler`

---

### Task 4: Graph client wrapper + pagination + errors (TDD with mocks)

**Files:**
- Create: `src/m365_posture/graph_errors.py`
- Create: `src/m365_posture/graph_client.py`
- Create: `tests/test_graph_client_pagination.py`, `tests/test_graph_errors.py`

- [ ] **Step 1: Failing test** — mock HTTP: first response `{"value":[1], "odata.nextLink":"https://graph.microsoft.com/v1.0/next"}` second `{"value":[2]}`; assert merged `[1,2]`.

- [ ] **Step 2:** Implement `get_all_pages(client, start_path)` using SDK request builder or raw `httpx` from SDK internals—prefer **public SDK patterns** from Microsoft Graph SDK docs (Kiota). If SDK pagination is iterator-based, test the public iterator. **Default test stack:** `unittest.mock` only (no extra HTTP mock libs unless you got approval).

- [ ] **Step 3:** **Retries:** On 429 or selected 5xx, retry with **capped exponential backoff + full jitter** (e.g. base 0.5s, cap 60s, multiply by ~2^n, add random 0–250ms). If response has **`Retry-After`** (seconds), use `max(backoff, Retry-After)` for that attempt. Document constants in `graph_client.py`.

- [ ] **Step 4:** **`graph_errors.py`:** Function `graph_failure_context(exc, operation: str) -> dict` extracts status, Graph error body (sanitized), `request-id` / `client-request-id` from response headers or SDK error types. **Never** place token or secret strings in this dict.

- [ ] **Step 5:** Test: simulated Graph error includes correlation fields in the dict. Log sink in tests can assert keys present.

- [ ] **Step 6:** Commit `feat: graph pagination, throttling retries, structured errors`

---

### Task 5: Redaction

**Files:**
- Create: `src/m365_posture/redact.py`
- Create: `tests/test_redact.py`

- [ ] **Step 1: Failing test**

```python
from m365_posture.redact import redact_report

def test_redact_masks_upn():
    data = {"users": [{"userPrincipalName": "alice@contoso.lab"}]}
    out = redact_report(data)
    assert "@" not in (out["users"][0].get("userPrincipalName") or "")
```

- [ ] **Step 2:** Implement per spec §3: UPN/email, displayName, object GUIDs hashed or placeholder, domain generalized.

- [ ] **Step 3:** `pytest tests/test_redact.py -v` → PASS. Commit `feat: add report redaction`

---

### Task 6: Chapter base + findings model + guests chapter

**Files:**
- Create: `src/m365_posture/chapters/base.py`, `src/m365_posture/chapters/guests.py`
- Create: `tests/fixtures/graph/guest_users_page.json`
- Create: `tests/test_chapter_guests.py`

- [ ] **Step 1:** In `base.py`, define `@dataclass` **`Finding`**: `severity: Literal["INFO","WARN"]`, `code: str`, `message: str`, `evidence: Optional[dict]` (small JSON-safe dict). Define **`ChapterResult`**: `chapter_id`, `status` (`OK` \| `DEGRADED`), `data`, `findings: list[Finding]`, `error_summary: Optional[str]`.

- [ ] **Step 2:** Fixture: one page of users with `userType: Guest` and members mixed.

- [ ] **Step 3:** Test: `run_guests_chapter(fake_client)` returns `OK`, with at least one **`Finding`** (`INFO` or `WARN`) that includes guest count in `evidence`. Implement `guests.py` using SDK—document exact OData in **`docs/permissions.md`** (add row: chapter, permission, link).

- [ ] **Step 4:** Commit `feat: guests chapter`

---

### Task 7: Privileged + applications + devices chapters

**Files:**
- Create: `src/m365_posture/chapters/privileged.py`, `src/m365_posture/chapters/applications.py`, `src/m365_posture/chapters/devices.py`
- Create: matching `tests/fixtures/*` under `tests/fixtures/graph/` + `tests/test_chapter_*.py`

- [ ] **Steps:** One chapter per commit where possible; each with fixture-first test; **update `docs/permissions.md`** with that chapter’s Graph permissions before or in the same commit.

---

### Task 8: Optional sign-in / risk chapter (feature-flagged)

**Files:**
- Create: `src/m365_posture/chapters/signin_risk.py`
- Test: when mocked 403, status is `DEGRADED` and other chapters unaffected in orchestration test. Append **`docs/permissions.md`** row or mark “omitted if tenant cannot consent.”

- [ ] **Commit** `feat: optional signin chapter with graceful degradation`

---

### Task 9: Aggregate + contract / golden

**Files:**
- Create: `src/m365_posture/aggregate.py`
- Create: `tests/test_aggregate.py`, `tests/test_render_contract.py`
- Create: `tests/golden/report_v1.json` (initial golden)

- [ ] **Step 1:** `aggregate.py` sets `schemaVersion: 1`, ISO8601 `generatedAt`, `chapters` map keyed by id.

- [ ] **Step 2:** Golden test: feed fixed list of `ChapterResult`, compare serialized JSON (normalize timestamps in test or freeze `generatedAt` via injectable clock).

- [ ] **Step 3:** Commit `feat: aggregate report envelope with schemaVersion`

---

### Task 10: HTML render (v1 only; no `.md` report)

**Files:**
- Create: `src/m365_posture/render.py`, embedded template string or `templates/report.html.j2` (use **`jinja2`**)
- Test: snapshot HTML contains chapter titles and **INFO/WARN** finding severities (substring asserts).

- [ ] **Commit** `feat: render html report`

---

### Task 11: CLI orchestration

**Files:**
- Create: `src/m365_posture/cli.py`
- Modify: `pyproject.toml` — `[project.scripts] m365-posture = "m365_posture.cli:main"`

- [ ] **Step 1:** `run` subcommand: load config → setup logging to `out/runs/<utc-timestamp>.log` → build credential (`CertificateCredential` or `ClientSecretCredential`) → build Graph client → for each enabled chapter in order call collector → aggregate → optional redact → write `report.json`, `report.html`, stdout one-line summary `STATUS=SUCCESS chapters=5 degraded=0`.

- [ ] **Step 2:** Integration smoke: `m365-posture run --out ...` with env against homelab (manual, documented); CI skips.

- [ ] **Step 3:** Commit `feat: cli run orchestration`

---

### Task 12: Documentation consolidation

**Files:**
- Modify: `README.md`
- Modify: `docs/permissions.md` (ensure complete, dedupe, cross-check against code paths)
- Create: `docs/operations/scheduling-task-scheduler.md`

- [ ] **Step 1:** README links **`docs/permissions.md`** as canonical matrix; ensure each chapter from code is represented.

- [ ] **Step 2:** Document certificate upload to app registration, admin consent, and **never commit** private key.

- [ ] **Step 3:** Task Scheduler: program `pwsh.exe` or `python.exe`, arguments, working directory, “Run whether user is logged on or not”, use of encrypted OS secret store optional note.

- [ ] **Commit** `docs: readme and task scheduler operations`

---

### Task 13: CI skeleton (optional but recommended)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step:** Run `pytest` on push (no live Graph). Pin Python 3.11.

- [ ] **Commit** `ci: run pytest on github actions`

---

## Plan review checklist (self-serve)

- [ ] Every spec §3 invariant reflected (no token logging; stdout vs file).
- [ ] Graph failures log **`request-id` / `client-request-id`** via `graph_errors` + file logger—not stdout.
- [ ] `schemaVersion` and golden update process documented in `test_render_contract.py` header comment.
- [ ] Homelab-only secrets story matches `.gitignore` (`.env`, `*.pfx`, `*.pem`).

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-03-m365-posture-report.md`.

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task; review between tasks. Use @superpowers:subagent-driven-development.

**2. Inline Execution** — Run tasks in this chat using @superpowers:executing-plans with checkpoints.

Which approach do you want?
