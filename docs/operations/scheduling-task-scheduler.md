# Schedule m365-posture with Windows Task Scheduler

This guide runs **`m365-posture`** on a fixed schedule using Task Scheduler. The tool needs **Entra app-only credentials** (certificate or client secret) available in the task’s environment and a writable output folder.

## Before you start

- Install the package in the Python environment the task will use (`pip install -e ".[dev]"` from the repo, or install into a dedicated venv).
- Choose a **service account** (or gMSA / managed approach) that:
  - Can read the **PFX** if you use certificate auth (`GRAPH_CERT_PATH`), and
  - Can write to the report directory you pass to `--out`.
- Put **no secrets in the repository**; set `TENANT_ID`, `CLIENT_ID`, and either `GRAPH_CERT_PATH` (+ optional `GRAPH_CERT_PASSWORD`) or `CLIENT_SECRET` via Task Scheduler or system environment.

## Create the task

1. Open **Task Scheduler** → **Create Task…** (not “Create Basic Task” if you need full options).
2. **General:** Run whether user is logged on or not; run with highest privileges *only if required* for certificate file access; select the **account** that owns the cert file and Graph identity.
3. **Triggers:** Add your schedule (e.g. daily off-peak).
4. **Actions** → **New…**
   - **Action:** Start a program.
   - **Program/script:** `python` (if on `PATH` for that account), **or** the full path to `python.exe` (recommended for scheduled tasks), e.g. `C:\Path\To\Python311\python.exe`.
   - **Add arguments:**  
     `-m m365_posture run --out C:\path\to\out`  
     Add `--redact` if you want redacted reports:  
     `-m m365_posture run --out C:\path\to\out --redact`
   - **Start in (optional):** The repository root (folder containing `pyproject.toml`) if you rely on an editable install from the clone; otherwise set this to the working directory where your environment expects to run (often the venv root or a dedicated ops folder).

## Environment variables

The task process must see the same variables documented in **`.env.example`** at the repo root (`TENANT_ID`, `CLIENT_ID`, auth material, chapter toggles). Options:

- Set **user or system** environment variables for the service account in Windows (restart session or re-logon as needed for interactive tests).
- Or use Task Scheduler **“Start in”** plus a small wrapper `.cmd` that calls `set VAR=value` then `python -m m365_posture ...` (avoid storing secrets in plain files on shared disks; prefer the OS secret store or restricted ACLs on a script only the task account can read).

**Certificate path:** Use an absolute `GRAPH_CERT_PATH` for the PFX so the task does not depend on a varying working directory.

## Verify

Run the action once **manually** (“Run” on the task) and confirm `report.json`, `report.html`, and `runs\*.log` appear under the `--out` directory. Check **History** or the log file if the exit code is non-zero.
