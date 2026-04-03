"""CLI entrypoint: config, logging, Graph reads, chapters, report output."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from azure.identity import CertificateCredential, ClientSecretCredential

from m365_posture.aggregate import build_report
from m365_posture.chapters import (
    run_applications_chapter,
    run_devices_chapter,
    run_guests_chapter,
    run_privileged_chapter,
    run_signin_risk_chapter,
)
from m365_posture.chapters.base import ChapterResult
from m365_posture.config import AppConfig, ConfigError, load_config
from m365_posture.graph_client import execute_graph_get, get_all_odata_pages
from m365_posture.graph_errors import graph_failure_context
from m365_posture.graph_http import authenticated_get_factory
from m365_posture.logging_setup import configure_logging
from m365_posture.redact import redact_report
from m365_posture.render import render_html

_CHAPTER_ORDER = ("guests", "privileged", "applications", "devices", "signin_risk")

_URL_GUESTS = (
    "https://graph.microsoft.com/v1.0/users"
    "?$select=id,userType,userPrincipalName&$top=999"
)
_URL_PRIVILEGED = (
    "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments"
    "?$select=id,principalId,roleDefinitionId,directoryScopeId&$top=999"
)
_URL_APPLICATIONS = (
    "https://graph.microsoft.com/v1.0/applications?$select=id,displayName&$top=999"
)
_URL_DEVICES = (
    "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
    "?$select=id,complianceState,operatingSystem&$top=999"
)
_URL_SIGNINS = (
    "https://graph.microsoft.com/v1.0/auditLogs/signIns"
    "?$top=50&$select=id,createdDateTime"
)


def _utc_log_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def build_credential(cfg: AppConfig) -> CertificateCredential | ClientSecretCredential:
    if cfg.cert_path:
        kwargs: dict[str, Any] = {
            "tenant_id": cfg.tenant_id,
            "client_id": cfg.client_id,
            "certificate_path": str(Path(cfg.cert_path)),
        }
        if cfg.cert_password:
            kwargs["password"] = cfg.cert_password.encode("utf-8")
        return CertificateCredential(**kwargs)
    if not cfg.client_secret:
        raise ConfigError("CLIENT_SECRET is required when GRAPH_CERT_PATH is not set")
    return ClientSecretCredential(
        tenant_id=cfg.tenant_id,
        client_id=cfg.client_id,
        client_secret=cfg.client_secret,
    )


def _chapter_error_summary(chapter_id: str) -> str:
    return {
        "guests": "Guest users could not be retrieved.",
        "privileged": "Directory role assignments could not be retrieved.",
        "applications": "Application registrations could not be retrieved.",
        "devices": "Managed devices could not be retrieved.",
        "signin_risk": "Sign-in activity chapter failed unexpectedly.",
    }.get(chapter_id, "Chapter failed.")


def _log_chapter_failure(log: logging.Logger, exc: BaseException, operation: str) -> None:
    ctx = graph_failure_context(exc, operation)
    log.error("%s", json.dumps(ctx, default=str))


def run_pipeline(
    cfg: AppConfig,
    out_dir: Path,
    redact: bool,
    *,
    credential_factory: Callable[[AppConfig], Any] | None = None,
) -> int:
    """Execute enabled chapters, write report.json / report.html under ``out_dir``. Returns process exit code."""
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    log_path = runs_dir / f"{_utc_log_stamp()}.log"
    configure_logging(log_path)
    log = logging.getLogger("m365_posture")

    factory = credential_factory or build_credential
    try:
        credential = factory(cfg)
    except Exception as exc:
        _log_chapter_failure(log, exc, "build_credential")
        return 1

    getter = authenticated_get_factory(credential)

    def paged_list(initial_url: str) -> list[dict]:
        def fetch_page(next_url: str | None) -> dict[str, Any]:
            full_url = next_url or initial_url
            return execute_graph_get(full_url, getter)

        raw = get_all_odata_pages(fetch_page)
        return [x for x in raw if isinstance(x, dict)]

    results: list[ChapterResult] = []

    def run_guests() -> None:
        try:
            results.append(run_guests_chapter(lambda: paged_list(_URL_GUESTS)))
        except Exception as exc:  # noqa: BLE001 - CLI boundary
            _log_chapter_failure(log, exc, "chapter_guests")
            results.append(
                ChapterResult(
                    chapter_id="guests",
                    status="DEGRADED",
                    data={},
                    findings=[],
                    error_summary=_chapter_error_summary("guests"),
                )
            )

    def run_privileged() -> None:
        try:
            results.append(
                run_privileged_chapter(lambda: paged_list(_URL_PRIVILEGED))
            )
        except Exception as exc:  # noqa: BLE001
            _log_chapter_failure(log, exc, "chapter_privileged")
            results.append(
                ChapterResult(
                    chapter_id="privileged",
                    status="DEGRADED",
                    data={},
                    findings=[],
                    error_summary=_chapter_error_summary("privileged"),
                )
            )

    def run_applications() -> None:
        try:
            results.append(
                run_applications_chapter(lambda: paged_list(_URL_APPLICATIONS))
            )
        except Exception as exc:  # noqa: BLE001
            _log_chapter_failure(log, exc, "chapter_applications")
            results.append(
                ChapterResult(
                    chapter_id="applications",
                    status="DEGRADED",
                    data={},
                    findings=[],
                    error_summary=_chapter_error_summary("applications"),
                )
            )

    def run_devices() -> None:
        try:
            results.append(run_devices_chapter(lambda: paged_list(_URL_DEVICES)))
        except Exception as exc:  # noqa: BLE001
            _log_chapter_failure(log, exc, "chapter_devices")
            results.append(
                ChapterResult(
                    chapter_id="devices",
                    status="DEGRADED",
                    data={},
                    findings=[],
                    error_summary=_chapter_error_summary("devices"),
                )
            )

    def run_signin() -> None:
        try:
            def fetch_sign_ins() -> list[dict]:
                page = execute_graph_get(_URL_SIGNINS, getter)
                vals = page.get("value")
                if not isinstance(vals, list):
                    return []
                return [x for x in vals if isinstance(x, dict)]

            results.append(run_signin_risk_chapter(fetch_sign_ins))
        except Exception as exc:  # noqa: BLE001
            _log_chapter_failure(log, exc, "chapter_signin_risk")
            results.append(
                ChapterResult(
                    chapter_id="signin_risk",
                    status="DEGRADED",
                    data={},
                    findings=[],
                    error_summary=_chapter_error_summary("signin_risk"),
                )
            )

    dispatch: dict[str, Callable[[], None]] = {
        "guests": run_guests,
        "privileged": run_privileged,
        "applications": run_applications,
        "devices": run_devices,
        "signin_risk": run_signin,
    }

    for chapter_id in _CHAPTER_ORDER:
        if cfg.chapters.get(chapter_id):
            dispatch[chapter_id]()

    if not results:
        log.error(json.dumps({"operation": "pipeline", "message": "no chapters enabled"}))
        return 1

    report = build_report(results, tenant_id=cfg.tenant_id)
    if redact:
        report = redact_report(report)

    (out_dir / "report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "report.html").write_text(render_html(report), encoding="utf-8")

    ok = sum(1 for r in results if r.status == "OK")
    degraded = sum(1 for r in results if r.status == "DEGRADED")
    status_word = "SUCCESS" if degraded == 0 else "DEGRADED"
    print(f"STATUS={status_word} ok={ok} degraded={degraded}", file=sys.stdout)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return run_pipeline(cfg, Path(args.out), args.redact)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="m365-posture")
    subs = parser.add_subparsers(dest="command", required=True)
    run_p = subs.add_parser("run", help="Run posture chapters and write reports")
    run_p.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for report.json, report.html, and runs/*.log",
    )
    run_p.add_argument(
        "--redact",
        action="store_true",
        help="Redact report payload before writing JSON/HTML",
    )
    args = parser.parse_args(argv)
    if args.command == "run":
        return _cmd_run(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
