"""Optional sign-in activity sample chapter (read-only, graceful degradation)."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding


def run_signin_risk_chapter(fetch_sign_ins: Callable[[], list[dict]]) -> ChapterResult:
    """Summarize sign-in records from ``fetch_sign_ins`` without failing the pipeline.

    Args:
        fetch_sign_ins: Callable returning sign-in dicts (typically one API page).

    Returns:
        ``OK`` with a count when data is available, or ``DEGRADED`` with a short
        ``error_summary`` when permissions are missing or the call fails.
    """
    try:
        sign_ins = fetch_sign_ins()
    except PermissionError:
        return ChapterResult(
            chapter_id="signin_risk",
            status="DEGRADED",
            data={},
            findings=[],
            error_summary=(
                "Sign-in activity could not be read (directory or audit permissions may be missing)."
            ),
        )
    except Exception:  # noqa: BLE001
        return ChapterResult(
            chapter_id="signin_risk",
            status="DEGRADED",
            data={},
            findings=[],
            error_summary="Sign-in activity could not be retrieved.",
        )

    count = len(sign_ins)
    finding = Finding(
        severity="INFO",
        code="signin_risk.count",
        message=f"Collected {count} sign-in record(s) in sample.",
        evidence={"sign_in_record_count": count},
    )

    return ChapterResult(
        chapter_id="signin_risk",
        status="OK",
        data={"sign_in_record_count": count},
        findings=[finding],
        error_summary=None,
    )
